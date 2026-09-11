from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from urllib.parse import (
    urldefrag,
    urlparse,
)

import requests


MAX_EXTERNAL_WORKERS = 10


def _normalize_host(
    hostname,
):
    hostname = (
        hostname
        or
        ""
    ).strip().lower()

    if hostname.startswith(
        "www."
    ):
        hostname = (
            hostname[4:]
        )

    return hostname


def _is_http_url(
    url,
):
    try:
        return (
            urlparse(
                url
            ).scheme.lower()
            in (
                "http",
                "https",
            )
        )

    except Exception:
        return False


def _is_internal_url(
    url,
    current_host,
):
    try:
        host = (
            _normalize_host(
                urlparse(
                    url
                ).hostname
            )
        )

    except Exception:
        return False

    return (
        host ==
        current_host
    )


def _check_external_link(
    url,
    headers,
):
    """
    Check an external URL without downloading the full response body.

    IMPORTANT:
    External anti-bot/auth/rate-limit responses are not treated as
    confirmed broken links.
    """

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=(
                3,
                6,
            ),
            allow_redirects=True,
            stream=True,
        )

        status_code = (
            response.status_code
        )

        final_url = (
            response.url
        )

        response.close()

        # Confirmed working.
        if status_code < 400:
            state = "working"
            reason = (
                f"HTTP {status_code}"
            )

        # Confirmed missing/dead.
        elif status_code in (
            404,
            410,
        ):
            state = "broken"
            reason = (
                f"HTTP {status_code}"
            )

        # Confirmed server-side failure.
        elif status_code >= 500:
            state = "broken"
            reason = (
                f"HTTP {status_code}"
            )

        # External sites frequently return 400/401/403/405/406/418/429
        # to automated clients even when the public URL works in a browser.
        # Therefore these are UNVERIFIED rather than BROKEN.
        else:
            state = "unverified"
            reason = (
                f"HTTP {status_code} "
                "- external service refused or could not confirm automated request"
            )

        return {
            "url":
                url,

            "final_url":
                final_url,

            "status_code":
                status_code,

            "state":
                state,

            "reason":
                reason,

            "error":
                None,
        }

    except requests.RequestException as exc:
        return {
            "url":
                url,

            "final_url":
                url,

            "status_code":
                None,

            "state":
                "unverified",

            "reason":
                "Request/network error - could not confirm link",

            "error":
                str(
                    exc
                ),
        }


def _browser_check_internal_pages(
    page,
    page_entries,
):
    """
    Verify same-domain pages inside the browser.

    Why browser fetch?
    ------------------
    requests.get() can fail because of TLS, Cloudflare, cookies, hosting
    rules or bot protection even though the website works perfectly in the
    browser. Internal links therefore use same-origin browser fetch instead.

    Each page entry:
        {
            "url": "https://example.com/page/",
            "fragments": ["section-1", "section-2"]
        }

    Returned data includes:
    - HTTP status
    - final URL
    - soft-404 detection
    - fragment existence
    """

    if not page_entries:
        return {}

    try:
        results = page.evaluate(
            """
            async (entries) => {
                const output = {};
                const queue = [...entries];
                const concurrency = Math.min(
                    6,
                    Math.max(
                        1,
                        queue.length
                    )
                );

                function soft404FromDocument(doc) {
                    const title =
                        (
                            doc.title
                            ||
                            ""
                        )
                        .replace(
                            /\\s+/g,
                            " "
                        )
                        .trim()
                        .toLowerCase();

                    const h1 =
                        (
                            doc.querySelector(
                                "h1"
                            )
                            ?.textContent
                            ||
                            ""
                        )
                        .replace(
                            /\\s+/g,
                            " "
                        )
                        .trim()
                        .toLowerCase();

                    const strongPatterns = [
                        /^404$/,
                        /\\b404\\b/,
                        /page not found/,
                        /^not found$/,
                        /page does not exist/,
                        /page doesn't exist/,
                    ];

                    return strongPatterns.some(
                        pattern =>
                            pattern.test(
                                title
                            )
                            ||
                            pattern.test(
                                h1
                            )
                    );
                }

                function fragmentMap(
                    doc,
                    fragments
                ) {
                    const result = {};

                    for (
                        const fragment of fragments
                        ||
                        []
                    ) {
                        if (!fragment) {
                            continue;
                        }

                        let found = Boolean(
                            doc.getElementById(
                                fragment
                            )
                        );

                        if (!found) {
                            try {
                                const escaped =
                                    CSS.escape(
                                        fragment
                                    );

                                found = Boolean(
                                    doc.querySelector(
                                        `[name="${escaped}"]`
                                    )
                                );
                            }
                            catch (error) {
                                found = false;
                            }
                        }

                        result[
                            fragment
                        ] = found;
                    }

                    return result;
                }

                async function worker() {
                    while (
                        queue.length
                    ) {
                        const entry =
                            queue.shift();

                        try {
                            const response =
                                await fetch(
                                    entry.url,
                                    {
                                        method:
                                            "GET",

                                        credentials:
                                            "same-origin",

                                        redirect:
                                            "follow",

                                        cache:
                                            "no-store",
                                    }
                                );

                            const status =
                                response.status;

                            const contentType =
                                (
                                    response.headers.get(
                                        "content-type"
                                    )
                                    ||
                                    ""
                                ).toLowerCase();

                            let soft404 =
                                false;

                            let fragments =
                                {};

                            if (
                                status < 400
                                &&
                                contentType.includes(
                                    "text/html"
                                )
                            ) {
                                const html =
                                    await response.text();

                                const doc =
                                    new DOMParser()
                                    .parseFromString(
                                        html,
                                        "text/html"
                                    );

                                soft404 =
                                    soft404FromDocument(
                                        doc
                                    );

                                fragments =
                                    fragmentMap(
                                        doc,
                                        entry.fragments
                                    );
                            }

                            output[
                                entry.url
                            ] = {
                                status:
                                    status,

                                final_url:
                                    response.url
                                    ||
                                    entry.url,

                                soft404:
                                    soft404,

                                fragments:
                                    fragments,

                                error:
                                    null,
                            };
                        }
                        catch (error) {
                            output[
                                entry.url
                            ] = {
                                status:
                                    null,

                                final_url:
                                    entry.url,

                                soft404:
                                    false,

                                fragments:
                                    {},

                                error:
                                    String(
                                        error
                                    ),
                            };
                        }
                    }
                }

                await Promise.all(
                    Array.from(
                        {
                            length:
                                concurrency
                        },
                        () =>
                            worker()
                    )
                );

                return output;
            }
            """,
            page_entries,
        )

        return (
            results
            or
            {}
        )

    except Exception:
        return {}


def check_links(
    page,
):
    """
    Accurate Broken Links QA.

    Classification
    --------------

    PASS / WORKING
    - HTTP 200-399
    - internal fragment exists

    WARNING / UNVERIFIED
    - network/request error
    - timeout
    - external 4xx response that may be anti-bot/auth/rate limiting
    - href="#" placeholder

    FAIL / BROKEN
    - confirmed HTTP 404
    - confirmed HTTP 410
    - confirmed HTTP 5xx
    - confirmed internal 4xx
    - internal fragment target missing
    - conservative soft-404 detected from title/H1

    Request exceptions are NEVER automatically called broken.
    """

    print(
        "\nBroken Links Check"
    )

    print(
        "------------------"
    )

    current_url = (
        page.url
    )

    current_host = (
        _normalize_host(
            urlparse(
                current_url
            ).hostname
        )
    )

    # =====================================
    # COLLECT LINKS
    # =====================================

    anchors = page.evaluate(
        """
        () => Array
            .from(
                document.querySelectorAll(
                    "a[href]"
                )
            )
            .map(
                (anchor, index) => ({
                    index:
                        index + 1,

                    raw_href:
                        (
                            anchor.getAttribute(
                                "href"
                            )
                            ||
                            ""
                        ).trim(),

                    url:
                        anchor.href
                        ||
                        "",

                    text:
                        (
                            anchor.innerText
                            ||
                            anchor.textContent
                            ||
                            anchor.getAttribute(
                                "aria-label"
                            )
                            ||
                            anchor.getAttribute(
                                "title"
                            )
                            ||
                            anchor.querySelector(
                                "img[alt]"
                            )
                            ?.getAttribute(
                                "alt"
                            )
                            ||
                            ""
                        )
                        .replace(
                            /\\s+/g,
                            " "
                        )
                        .trim()
                })
            )
        """
    )

    http_links = []

    ignored_non_http = 0

    for anchor in anchors:
        url = (
            anchor.get(
                "url"
            )
            or
            ""
        ).strip()

        if not url:
            continue

        if not _is_http_url(
            url
        ):
            ignored_non_http += 1
            continue

        http_links.append(
            anchor
        )

    # Full URL dedupe keeps unique fragment links separately.
    unique_by_url = {}

    for link in http_links:
        url = (
            link[
                "url"
            ]
        )

        if url not in unique_by_url:
            unique_by_url[
                url
            ] = link

    unique_links = list(
        unique_by_url.values()
    )

    print(
        "INFO | HTML Links |",
        len(
            anchors
        ),
        "anchor(s)"
    )

    print(
        "INFO | Unique HTTP Links |",
        len(
            unique_links
        )
    )

    if ignored_non_http:
        print(
            "INFO | Ignored Non-HTTP Links |",
            ignored_non_http
        )

    # =====================================
    # SPLIT INTERNAL / EXTERNAL
    # =====================================

    internal_links = []
    external_links = []

    placeholder_links = []

    for link in unique_links:
        raw_href = (
            link.get(
                "raw_href"
            )
            or
            ""
        )

        url = (
            link[
                "url"
            ]
        )

        if raw_href == "#":
            placeholder_links.append(
                link
            )
            continue

        if _is_internal_url(
            url,
            current_host,
        ):
            internal_links.append(
                link
            )

        else:
            external_links.append(
                link
            )

    # =====================================
    # PREP INTERNAL BASE URL + FRAGMENTS
    # =====================================

    internal_page_map = {}

    for link in internal_links:
        full_url = (
            link[
                "url"
            ]
        )

        base_url, fragment = (
            urldefrag(
                full_url
            )
        )

        if not base_url:
            base_url = (
                current_url
            )

        if base_url not in internal_page_map:
            internal_page_map[
                base_url
            ] = set()

        if fragment:
            internal_page_map[
                base_url
            ].add(
                fragment
            )

    browser_entries = [
        {
            "url":
                base_url,

            "fragments":
                sorted(
                    fragments
                ),
        }
        for (
            base_url,
            fragments
        ) in (
            internal_page_map.items()
        )
    ]

    internal_page_results = (
        _browser_check_internal_pages(
            page,
            browser_entries,
        )
    )

    working = []
    broken = []
    unverified = []

    # =====================================
    # CLASSIFY INTERNAL LINKS
    # =====================================

    for link in internal_links:
        full_url = (
            link[
                "url"
            ]
        )

        base_url, fragment = (
            urldefrag(
                full_url
            )
        )

        if not base_url:
            base_url = (
                current_url
            )

        result = (
            internal_page_results.get(
                base_url
            )
            or
            {
                "status":
                    None,

                "final_url":
                    base_url,

                "soft404":
                    False,

                "fragments":
                    {},

                "error":
                    "Browser verification unavailable",
            }
        )

        status = (
            result.get(
                "status"
            )
        )

        # Network/browser fetch failed:
        # WARNING, never FAIL.
        if status is None:
            unverified.append(
                {
                    "url":
                        full_url,

                    "reason":
                        "Browser/network error - could not verify internal link",

                    "text":
                        link.get(
                            "text"
                        )
                        or
                        "",
                }
            )

            continue

        # Confirmed missing/dead internal page.
        if status in (
            404,
            410,
        ):
            broken.append(
                {
                    "url":
                        full_url,

                    "reason":
                        f"HTTP {status}",

                    "text":
                        link.get(
                            "text"
                        )
                        or
                        "",
                }
            )

            continue

        # Confirmed internal server failure.
        if status >= 500:
            broken.append(
                {
                    "url":
                        full_url,

                    "reason":
                        f"HTTP {status}",

                    "text":
                        link.get(
                            "text"
                        )
                        or
                        "",
                }
            )

            continue

        # Other internal 4xx responses are genuine internal failures
        # because we control the same origin being tested.
        if status >= 400:
            broken.append(
                {
                    "url":
                        full_url,

                    "reason":
                        f"HTTP {status}",

                    "text":
                        link.get(
                            "text"
                        )
                        or
                        "",
                }
            )

            continue

        # Conservative soft 404 check.
        if result.get(
            "soft404"
        ):
            broken.append(
                {
                    "url":
                        full_url,

                    "reason":
                        "Soft 404 suspected from page title/H1",

                    "text":
                        link.get(
                            "text"
                        )
                        or
                        "",
                }
            )

            continue

        # Fragment URL: base page is good, now verify the target.
        if fragment:
            fragment_exists = (
                result.get(
                    "fragments",
                    {}
                ).get(
                    fragment
                )
            )

            if fragment_exists is False:
                broken.append(
                    {
                        "url":
                            full_url,

                        "reason":
                            (
                                f'Anchor target "#{fragment}" '
                                "not found on the page"
                            ),

                        "text":
                            link.get(
                                "text"
                            )
                            or
                            "",
                    }
                )

                continue

            if fragment_exists is None:
                unverified.append(
                    {
                        "url":
                            full_url,

                        "reason":
                            (
                                f'Could not verify anchor target '
                                f'"#{fragment}"'
                            ),

                        "text":
                            link.get(
                                "text"
                            )
                            or
                            "",
                    }
                )

                continue

        working.append(
            {
                "url":
                    full_url,

                "reason":
                    f"HTTP {status}",

                "text":
                    link.get(
                        "text"
                    )
                    or
                    "",
            }
        )

    # =====================================
    # CLASSIFY EXTERNAL LINKS
    # =====================================

    if external_links:
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

        headers = {
            "User-Agent":
                user_agent,

            "Referer":
                current_url,
        }

        workers = min(
            MAX_EXTERNAL_WORKERS,
            len(
                external_links
            ),
        )

        with ThreadPoolExecutor(
            max_workers=
                workers
        ) as executor:
            futures = {
                executor.submit(
                    _check_external_link,
                    link[
                        "url"
                    ],
                    headers,
                ):
                    link

                for link in external_links
            }

            for future in as_completed(
                futures
            ):
                link = (
                    futures[
                        future
                    ]
                )

                try:
                    result = (
                        future.result()
                    )

                except Exception as exc:
                    result = {
                        "state":
                            "unverified",

                        "url":
                            link[
                                "url"
                            ],

                        "reason":
                            "External request error - could not verify link",

                        "error":
                            str(
                                exc
                            ),
                    }

                record = {
                    "url":
                        link[
                            "url"
                        ],

                    "reason":
                        result.get(
                            "reason"
                        )
                        or
                        "Unknown result",

                    "text":
                        link.get(
                            "text"
                        )
                        or
                        "",
                }

                state = (
                    result.get(
                        "state"
                    )
                )

                if state == "working":
                    working.append(
                        record
                    )

                elif state == "broken":
                    broken.append(
                        record
                    )

                else:
                    unverified.append(
                        record
                    )

    # href="#" is a placeholder, not a confirmed broken HTTP URL.
    for link in placeholder_links:
        unverified.append(
            {
                "url":
                    link[
                        "url"
                    ],

                "reason":
                    'Placeholder link href="#" has no destination',

                "text":
                    link.get(
                        "text"
                    )
                    or
                    "",
            }
        )

    # =====================================
    # REPORT
    # =====================================

    # Confirmed broken links are individual FAIL findings.
    if broken:
        print(
            "INFO | Confirmed Broken Links |",
            len(
                broken
            )
        )

        for item in broken:
            print(
                "FAIL | Broken URL |",
                f"{item['reason']} | "
                f"{item['url']}"
            )

    else:
        print(
            "PASS | Broken Links | "
            "No confirmed broken links detected"
        )

    # Unverified/blocked/network failures are WARNING only.
    if unverified:
        print(
            "INFO | Unverified Links |",
            len(
                unverified
            )
        )

        for item in unverified:
            print(
                "WARNING | Unverified URL |",
                f"{item['reason']} | "
                f"{item['url']}"
            )

    else:
        print(
            "PASS | Unverified Links | "
            "All checked links were verifiable"
        )

    print(
        "INFO | Working Links |",
        len(
            working
        )
    )

    print(
        "INFO | Link Check Summary |",
        f"Working {len(working)}, "
        f"Unverified {len(unverified)}, "
        f"Broken {len(broken)}, "
        f"Unique HTTP {len(unique_links)}"
    )

    print(
        "\nBroken Links Check Complete"
    )
