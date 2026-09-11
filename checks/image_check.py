import base64
import json
import math
import re
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from urllib.parse import urlparse

import requests


IMAGE_SIZE_WARNING_KB = 300
MAX_IMAGE_WORKERS = 10


def load_lazy_images(
    page,
):
    """
    Trigger lazy loading quickly.

    Previous implementation could perform dozens of slow scroll steps.
    This version caps the number of scroll positions.
    """

    try:
        page.evaluate(
            """
            async () => {
                const wait = (ms) =>
                    new Promise(
                        resolve =>
                            setTimeout(
                                resolve,
                                ms
                            )
                    );

                const totalHeight =
                    Math.max(
                        document.body.scrollHeight,
                        document.documentElement.scrollHeight
                    );

                const viewport =
                    Math.max(
                        window.innerHeight,
                        600
                    );

                const maxSteps =
                    12;

                const estimatedSteps =
                    Math.ceil(
                        totalHeight
                        /
                        (viewport * 1.25)
                    );

                const steps =
                    Math.max(
                        1,
                        Math.min(
                            maxSteps,
                            estimatedSteps
                        )
                    );

                for (
                    let index = 0;
                    index <= steps;
                    index += 1
                ) {
                    const progress =
                        index / steps;

                    const y =
                        Math.max(
                            0,
                            (
                                totalHeight
                                -
                                viewport
                            )
                            *
                            progress
                        );

                    window.scrollTo(
                        0,
                        y
                    );

                    await wait(
                        55
                    );
                }

                await wait(
                    160
                );

                window.scrollTo(
                    0,
                    0
                );

                await wait(
                    100
                );
            }
            """
        )

    except Exception:
        pass


def _format_from_url(
    url,
):
    if not url:
        return "UNKNOWN"

    if url.startswith(
        "data:"
    ):
        match = re.match(
            r"^data:image/([^;,]+)",
            url,
            flags=re.IGNORECASE,
        )

        if match:
            value = (
                match.group(
                    1
                )
                .lower()
            )

            if value == "jpeg":
                return "JPG"

            if value == "svg+xml":
                return "SVG"

            return (
                value.upper()
            )

        return "DATA"

    try:
        path = (
            urlparse(
                url
            )
            .path
            .lower()
        )

    except Exception:
        path = (
            url.lower()
        )

    extension = (
        path.rsplit(
            ".",
            1,
        )[-1]
        if "." in path
        else ""
    )

    aliases = {
        "jpeg": "JPG",
        "jpg": "JPG",
        "png": "PNG",
        "webp": "WEBP",
        "avif": "AVIF",
        "gif": "GIF",
        "svg": "SVG",
        "bmp": "BMP",
        "ico": "ICO",
        "tif": "TIFF",
        "tiff": "TIFF",
    }

    return aliases.get(
        extension,
        extension.upper()
        if extension
        else "UNKNOWN",
    )


def _format_from_content_type(
    content_type,
):
    content_type = (
        content_type
        or
        ""
    ).lower()

    mapping = {
        "image/jpeg": "JPG",
        "image/jpg": "JPG",
        "image/png": "PNG",
        "image/webp": "WEBP",
        "image/avif": "AVIF",
        "image/gif": "GIF",
        "image/svg+xml": "SVG",
        "image/bmp": "BMP",
        "image/x-icon": "ICO",
        "image/vnd.microsoft.icon": "ICO",
        "image/tiff": "TIFF",
    }

    for mime, image_format in (
        mapping.items()
    ):
        if mime in content_type:
            return image_format

    return None


def _data_url_size_bytes(
    url,
):
    if not url.startswith(
        "data:"
    ):
        return None

    try:
        header, payload = (
            url.split(
                ",",
                1,
            )
        )

        if ";base64" in header.lower():
            return len(
                base64.b64decode(
                    payload,
                    validate=False,
                )
            )

        return len(
            payload.encode(
                "utf-8"
            )
        )

    except Exception:
        return None


def _parse_content_range_total(
    value,
):
    if not value:
        return None

    match = re.search(
        r"/(\d+)$",
        value.strip(),
    )

    if not match:
        return None

    try:
        return int(
            match.group(
                1
            )
        )

    except ValueError:
        return None


def _probe_remote_image_info(
    url,
    headers,
):
    """
    Fast remote image probe.

    Strategy:
    1. HEAD for Content-Length.
    2. Range GET only when HEAD does not provide size.
    3. Never download the entire image body just to calculate size.
    """

    result = {
        "size_bytes":
            None,

        "content_type":
            None,

        "http_status":
            None,
    }

    if not url:
        return result

    if url.startswith(
        "data:"
    ):
        return {
            "size_bytes":
                _data_url_size_bytes(
                    url
                ),

            "content_type":
                (
                    url.split(
                        ";",
                        1,
                    )[0]
                    .replace(
                        "data:",
                        ""
                    )
                ),

            "http_status":
                None,
        }

    if url.startswith(
        (
            "blob:",
            "javascript:",
        )
    ):
        return result

    try:
        response = requests.head(
            url,
            headers=headers,
            timeout=(
                3,
                4,
            ),
            allow_redirects=True,
        )

        result[
            "http_status"
        ] = (
            response.status_code
        )

        result[
            "content_type"
        ] = (
            response.headers.get(
                "Content-Type"
            )
        )

        content_length = (
            response.headers.get(
                "Content-Length"
            )
        )

        if content_length:
            try:
                result[
                    "size_bytes"
                ] = int(
                    content_length
                )

            except ValueError:
                pass

        response.close()

        if (
            result[
                "size_bytes"
            ] is not None
        ):
            return result

    except requests.RequestException:
        pass

    # HEAD unavailable or missing Content-Length.
    # Use a tiny Range request instead of downloading the entire image.
    try:
        range_headers = {
            **headers,
            "Range":
                "bytes=0-0",
        }

        response = requests.get(
            url,
            headers=range_headers,
            timeout=(
                3,
                5,
            ),
            allow_redirects=True,
            stream=True,
        )

        result[
            "http_status"
        ] = (
            response.status_code
        )

        result[
            "content_type"
        ] = (
            response.headers.get(
                "Content-Type"
            )
            or
            result[
                "content_type"
            ]
        )

        total_from_range = (
            _parse_content_range_total(
                response.headers.get(
                    "Content-Range"
                )
            )
        )

        if (
            total_from_range
            is not None
        ):
            result[
                "size_bytes"
            ] = (
                total_from_range
            )

        elif (
            response.status_code
            ==
            200
        ):
            content_length = (
                response.headers.get(
                    "Content-Length"
                )
            )

            if content_length:
                try:
                    result[
                        "size_bytes"
                    ] = int(
                        content_length
                    )

                except ValueError:
                    pass

        response.close()

    except requests.RequestException:
        pass

    return result


def _browser_resource_sizes(
    page,
):
    """
    Reuse browser Performance API sizes for resources already loaded.

    This avoids making a second HTTP request for most visible images.
    """

    try:
        entries = page.evaluate(
            """
            () => performance
                .getEntriesByType(
                    "resource"
                )
                .map(
                    entry => ({
                        url:
                            entry.name,

                        size:
                            entry.encodedBodySize
                            ||
                            entry.transferSize
                            ||
                            0,

                        initiator:
                            entry.initiatorType
                            ||
                            ""
                    })
                )
            """
        )

    except Exception:
        return {}

    output = {}

    for entry in entries:
        url = (
            entry.get(
                "url"
            )
            or
            ""
        )

        size = (
            entry.get(
                "size"
            )
            or
            0
        )

        if (
            url
            and
            size > 0
        ):
            output[
                url
            ] = {
                "size_bytes":
                    int(
                        size
                    ),

                "content_type":
                    None,

                "http_status":
                    None,
            }

    return output


def _size_label(
    size_bytes,
):
    if size_bytes is None:
        return "Unknown"

    size_kb = (
        size_bytes
        /
        1024
    )

    if size_kb >= 1024:
        return (
            f"{size_kb / 1024:.2f} MB"
        )

    return (
        f"{size_kb:.2f} KB"
    )


def _final_image_status(
    *,
    broken,
    http_status,
    size_kb,
    alt_state,
    oversized,
    non_lazy_below_fold,
    hidden,
    unknown_size,
    no_url,
):
    fail_issues = []
    warning_issues = []
    info_issues = []

    if broken:
        fail_issues.append(
            "Broken visible image"
        )

    if (
        http_status is not None
        and
        http_status >= 400
    ):
        fail_issues.append(
            f"HTTP {http_status}"
        )

    if (
        size_kb is not None
        and
        size_kb >
        IMAGE_SIZE_WARNING_KB
    ):
        warning_issues.append(
            f"File size > {IMAGE_SIZE_WARNING_KB} KB"
        )

    if alt_state == "Missing":
        warning_issues.append(
            "Missing ALT text"
        )

    elif alt_state == "Empty":
        warning_issues.append(
            "Empty ALT text"
        )

    if oversized:
        warning_issues.append(
            "Oversized dimensions"
        )

    if non_lazy_below_fold:
        warning_issues.append(
            "Non-lazy below fold"
        )

    if hidden:
        info_issues.append(
            "Hidden image"
        )

    if unknown_size:
        info_issues.append(
            "Unknown file size"
        )

    if no_url:
        info_issues.append(
            "No resolved image URL"
        )

    if fail_issues:
        status = "fail"

    elif warning_issues:
        status = "warning"

    elif info_issues:
        status = "info"

    else:
        status = "pass"

    issues = (
        fail_issues
        +
        warning_issues
        +
        info_issues
    )

    return (
        status,
        issues,
    )


def check_images(
    page,
):
    print(
        "\nImage Optimization Check"
    )

    print(
        "------------------------"
    )

    load_lazy_images(
        page
    )

    image_elements = page.evaluate(
        """
        () => Array
            .from(
                document.querySelectorAll(
                    "img"
                )
            )
            .map(
                (img, index) => {
                    const rect =
                        img.getBoundingClientRect();

                    const style =
                        window.getComputedStyle(
                            img
                        );

                    const visible =
                        (
                            rect.width > 0
                            &&
                            rect.height > 0
                            &&
                            style.display !== "none"
                            &&
                            style.visibility !== "hidden"
                            &&
                            Number(
                                style.opacity
                            ) !== 0
                        );

                    const rawUrl =
                        (
                            img.currentSrc
                            ||
                            img.getAttribute(
                                "src"
                            )
                            ||
                            img.getAttribute(
                                "data-src"
                            )
                            ||
                            img.getAttribute(
                                "data-lazy-src"
                            )
                            ||
                            ""
                        );

                    let resolvedUrl =
                        rawUrl;

                    if (
                        rawUrl
                        &&
                        !rawUrl.startsWith(
                            "data:"
                        )
                        &&
                        !rawUrl.startsWith(
                            "blob:"
                        )
                    ) {
                        try {
                            resolvedUrl =
                                new URL(
                                    rawUrl,
                                    document.baseURI
                                ).href;
                        }
                        catch (error) {
                            resolvedUrl =
                                rawUrl;
                        }
                    }

                    return {
                        index:
                            index + 1,

                        url:
                            resolvedUrl,

                        alt:
                            img.hasAttribute(
                                "alt"
                            )
                                ?
                                img.getAttribute(
                                    "alt"
                                )
                                :
                                null,

                        loading:
                            (
                                img.getAttribute(
                                    "loading"
                                )
                                ||
                                "default"
                            ).toLowerCase(),

                        complete:
                            !!img.complete,

                        naturalWidth:
                            img.naturalWidth
                            ||
                            0,

                        naturalHeight:
                            img.naturalHeight
                            ||
                            0,

                        displayWidth:
                            rect.width
                            ||
                            0,

                        displayHeight:
                            rect.height
                            ||
                            0,

                        absoluteTop:
                            rect.top
                            +
                            window.scrollY,

                        viewportHeight:
                            window.innerHeight,

                        visible:
                            visible
                    };
                }
            )
        """
    )

    total_images = (
        len(
            image_elements
        )
    )

    print(
        "INFO | Total Images |",
        total_images,
        "image element(s) found"
    )

    try:
        user_agent = (
            page.evaluate(
                "() => navigator.userAgent"
            )
        )

    except Exception:
        user_agent = (
            "Mozilla/5.0 Website-QA-Agent"
        )

    request_headers = {
        "User-Agent":
            user_agent,

        "Referer":
            page.url,
    }

    # =====================================
    # REUSE ALREADY-LOADED RESOURCE SIZES
    # =====================================

    remote_info_cache = (
        _browser_resource_sizes(
            page
        )
    )

    unique_urls = {
        (
            image.get(
                "url"
            )
            or
            ""
        )
        for image in image_elements
    }

    probe_urls = [
        url
        for url in unique_urls
        if (
            url
            and
            url not in remote_info_cache
            and
            not url.startswith(
                "data:"
            )
            and
            not url.startswith(
                "blob:"
            )
        )
    ]

    # =====================================
    # PARALLEL REMOTE PROBES
    # =====================================

    if probe_urls:
        workers = min(
            MAX_IMAGE_WORKERS,
            len(
                probe_urls
            ),
        )

        with ThreadPoolExecutor(
            max_workers=
                workers
        ) as executor:
            futures = {
                executor.submit(
                    _probe_remote_image_info,
                    url,
                    request_headers,
                ):
                    url

                for url in probe_urls
            }

            for future in as_completed(
                futures
            ):
                url = futures[
                    future
                ]

                try:
                    remote_info_cache[
                        url
                    ] = (
                        future.result()
                    )

                except Exception:
                    remote_info_cache[
                        url
                    ] = {
                        "size_bytes":
                            None,

                        "content_type":
                            None,

                        "http_status":
                            None,
                    }

    # Data URLs are calculated locally.
    for url in unique_urls:
        if (
            url
            and
            url.startswith(
                "data:"
            )
            and
            url not in remote_info_cache
        ):
            remote_info_cache[
                url
            ] = {
                "size_bytes":
                    _data_url_size_bytes(
                        url
                    ),

                "content_type":
                    (
                        url.split(
                            ";",
                            1,
                        )[0]
                        .replace(
                            "data:",
                            ""
                        )
                    ),

                "http_status":
                    None,
            }

    records = []

    for image in image_elements:
        image_url = (
            image.get(
                "url"
            )
            or
            ""
        )

        alt = (
            image.get(
                "alt"
            )
        )

        if alt is None:
            alt_state = (
                "Missing"
            )

        elif not alt.strip():
            alt_state = (
                "Empty"
            )

        else:
            alt_state = (
                "Present"
            )

        visible = bool(
            image.get(
                "visible"
            )
        )

        broken = bool(
            visible
            and
            not (
                image.get(
                    "complete"
                )
                and
                image.get(
                    "naturalWidth",
                    0,
                ) > 0
            )
        )

        natural_width = (
            image.get(
                "naturalWidth"
            )
            or
            0
        )

        natural_height = (
            image.get(
                "naturalHeight"
            )
            or
            0
        )

        display_width = (
            image.get(
                "displayWidth"
            )
            or
            0
        )

        display_height = (
            image.get(
                "displayHeight"
            )
            or
            0
        )

        detected_format = (
            _format_from_url(
                image_url
            )
        )

        is_vector_image = (
            detected_format ==
            "SVG"
        )

        oversized_width = bool(
            not is_vector_image
            and
            natural_width > 0
            and
            display_width > 0
            and
            natural_width
            >
            display_width * 2
        )

        oversized_height = bool(
            not is_vector_image
            and
            natural_height > 0
            and
            display_height > 0
            and
            natural_height
            >
            display_height * 2
        )

        oversized = bool(
            oversized_width
            or
            oversized_height
        )

        loading = (
            image.get(
                "loading"
            )
            or
            "default"
        ).lower()

        below_fold = bool(
            visible
            and
            (
                image.get(
                    "absoluteTop",
                    0,
                )
                >
                image.get(
                    "viewportHeight",
                    768,
                )
            )
        )

        non_lazy_below_fold = bool(
            below_fold
            and
            loading != "lazy"
        )

        hidden = (
            not visible
        )

        remote = (
            remote_info_cache.get(
                image_url,
                {
                    "size_bytes":
                        None,

                    "content_type":
                        None,

                    "http_status":
                        None,
                },
            )
        )

        size_bytes = (
            remote.get(
                "size_bytes"
            )
        )

        size_kb = (
            size_bytes / 1024
            if size_bytes is not None
            else None
        )

        unknown_size = (
            size_bytes is None
        )

        no_url = (
            not bool(
                image_url
            )
        )

        image_format = (
            detected_format
        )

        response_format = (
            _format_from_content_type(
                remote.get(
                    "content_type"
                )
            )
        )

        if (
            image_format == "UNKNOWN"
            and
            response_format
        ):
            image_format = (
                response_format
            )

        status, issues = (
            _final_image_status(
                broken=
                    broken,

                http_status=
                    remote.get(
                        "http_status"
                    ),

                size_kb=
                    size_kb,

                alt_state=
                    alt_state,

                oversized=
                    oversized,

                non_lazy_below_fold=
                    non_lazy_below_fold,

                hidden=
                    hidden,

                unknown_size=
                    unknown_size,

                no_url=
                    no_url,
            )
        )

        # Defensive consistency:
        if (
            oversized
            and
            status in (
                "pass",
                "info",
            )
        ):
            status = (
                "warning"
            )

            if (
                "Oversized dimensions"
                not in issues
            ):
                issues.insert(
                    0,
                    "Oversized dimensions"
                )

        record = {
            "index":
                image.get(
                    "index"
                ),

            "url":
                image_url,

            "format":
                image_format,

            "size_bytes":
                size_bytes,

            "size_kb":
                (
                    round(
                        size_kb,
                        2,
                    )
                    if size_kb is not None
                    else None
                ),

            "size_label":
                _size_label(
                    size_bytes
                ),

            "status":
                status,

            "issues":
                issues,

            "issue_text":
                (
                    "; ".join(
                        issues
                    )
                    if issues
                    else "No detected issue"
                ),

            "alt":
                (
                    alt
                    if alt is not None
                    else ""
                ),

            "alt_state":
                alt_state,

            "loading":
                loading,

            "visible":
                visible,

            "hidden":
                hidden,

            "broken":
                broken,

            "oversized":
                oversized,

            "oversized_width":
                oversized_width,

            "oversized_height":
                oversized_height,

            "natural_width":
                natural_width,

            "natural_height":
                natural_height,

            "display_width":
                round(
                    display_width,
                    2,
                ),

            "display_height":
                round(
                    display_height,
                    2,
                ),

            "natural_dimensions":
                (
                    f"{natural_width}x{natural_height}"
                    if (
                        natural_width > 0
                        and
                        natural_height > 0
                    )
                    else "Unknown"
                ),

            "display_dimensions":
                (
                    f"{round(display_width)}x{round(display_height)}"
                    if (
                        display_width > 0
                        and
                        display_height > 0
                    )
                    else "Hidden / 0x0"
                ),

            "below_fold":
                below_fold,

            "non_lazy_below_fold":
                non_lazy_below_fold,

            "http_status":
                remote.get(
                    "http_status"
                ),
        }

        records.append(
            record
        )

        print(
            "QA_IMAGE_ASSET|"
            +
            json.dumps(
                record,
                ensure_ascii=False,
            )
        )

    # =====================================
    # SUMMARY
    # =====================================

    pass_count = sum(
        1
        for item in records
        if item[
            "status"
        ] == "pass"
    )

    warning_count = sum(
        1
        for item in records
        if item[
            "status"
        ] == "warning"
    )

    fail_count = sum(
        1
        for item in records
        if item[
            "status"
        ] == "fail"
    )

    info_count = sum(
        1
        for item in records
        if item[
            "status"
        ] == "info"
    )

    missing_alt_count = sum(
        1
        for item in records
        if item[
            "alt_state"
        ] == "Missing"
    )

    empty_alt_count = sum(
        1
        for item in records
        if item[
            "alt_state"
        ] == "Empty"
    )

    oversized_count = sum(
        1
        for item in records
        if item[
            "oversized"
        ]
    )

    large_file_count = sum(
        1
        for item in records
        if (
            item[
                "size_kb"
            ] is not None
            and
            item[
                "size_kb"
            ]
            >
            IMAGE_SIZE_WARNING_KB
        )
    )

    broken_count = sum(
        1
        for item in records
        if (
            item[
                "broken"
            ]
            or
            (
                item[
                    "http_status"
                ] is not None
                and
                item[
                    "http_status"
                ] >= 400
            )
        )
    )

    hidden_count = sum(
        1
        for item in records
        if item[
            "hidden"
        ]
    )

    non_lazy_below_fold_count = sum(
        1
        for item in records
        if item[
            "non_lazy_below_fold"
        ]
    )

    unknown_size_count = sum(
        1
        for item in records
        if item[
            "size_bytes"
        ] is None
    )

    lazy_count = sum(
        1
        for item in records
        if item[
            "loading"
        ] == "lazy"
    )

    non_lazy_count = (
        total_images
        -
        lazy_count
    )

    if (
        missing_alt_count
        or
        empty_alt_count
    ):
        print(
            "WARNING | Alt Text |",
            f"{missing_alt_count} missing, "
            f"{empty_alt_count} empty"
        )

    else:
        print(
            "PASS | Alt Text |",
            "ALT text present on all image elements"
        )

    if broken_count:
        print(
            "FAIL | Broken Images |",
            broken_count,
            "broken/error image(s)"
        )

    else:
        print(
            "PASS | Broken Images |",
            "No broken images detected"
        )

    if oversized_count:
        print(
            "WARNING | Oversized Dimensions |",
            oversized_count,
            "image(s) have intrinsic width/height more than 2x displayed dimensions"
        )

    else:
        print(
            "PASS | Oversized Dimensions |",
            "No obvious oversized image dimensions detected"
        )

    if large_file_count:
        print(
            "WARNING | Image File Size |",
            large_file_count,
            f"image(s) exceed {IMAGE_SIZE_WARNING_KB} KB"
        )

    else:
        print(
            "PASS | Image File Size |",
            f"No measured image exceeds {IMAGE_SIZE_WARNING_KB} KB"
        )

    if non_lazy_below_fold_count:
        print(
            "WARNING | Non-Lazy Below Fold |",
            non_lazy_below_fold_count,
            "visible below-fold image(s) are not lazy-loaded"
        )

    else:
        print(
            "PASS | Non-Lazy Below Fold |",
            "No obvious below-fold lazy-loading issue detected"
        )

    if unknown_size_count:
        print(
            "INFO | Unknown Image Size |",
            unknown_size_count,
            "image(s) have unknown file size"
        )

    print(
        "INFO | Lazy Loading |",
        f"{lazy_count} lazy, "
        f"{non_lazy_count} non-lazy"
    )

    print(
        "INFO | Hidden Images |",
        hidden_count,
        "hidden image(s)"
    )

    print(
        "INFO | Image Asset Table |",
        len(
            records
        ),
        "image row(s) added to report"
    )

    print(
        "INFO | Image Status Summary |",
        f"Total {total_images}, "
        f"Pass {pass_count}, "
        f"Warning {warning_count}, "
        f"Fail {fail_count}, "
        f"Info {info_count}"
    )

    print(
        "\nImage Optimization Check Complete"
    )
