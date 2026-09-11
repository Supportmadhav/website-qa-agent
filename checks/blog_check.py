import json
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from urllib.parse import (
    urljoin,
    urlparse,
)

import requests


BLOG_WORDS = (
    "blog",
    "news",
    "insights",
    "articles",
)

COMMON_BLOG_PATHS = (
    "/blog/",
    "/news/",
    "/insights/",
    "/articles/",
)


def _normalize_host(hostname):
    hostname = (
        hostname
        or
        ""
    ).strip().lower()

    if hostname.startswith(
        "www."
    ):
        hostname = hostname[4:]

    return hostname


def _looks_like_blog(
    text,
    href,
):
    combined = (
        f"{text} {href}"
        .lower()
    )

    return any(
        word in combined
        for word in BLOG_WORDS
    )


def _candidate_score(
    text,
    href,
):
    text_lower = (
        text
        or
        ""
    ).strip().lower()

    path = (
        urlparse(
            href
        ).path
        .rstrip("/")
        .lower()
    )

    score = 0

    if text_lower == "blog":
        score += 100

    elif "blog" in text_lower:
        score += 70

    if path == "/blog":
        score += 100

    elif "/blog/" in (
        path
        +
        "/"
    ):
        score += 65

    if text_lower in (
        "news",
        "insights",
        "articles",
    ):
        score += 45

    if any(
        token in path
        for token in (
            "/news",
            "/insights",
            "/articles",
        )
    ):
        score += 35

    return score


def _probe_candidate(
    url,
    headers,
):
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=(
                3,
                5,
            ),
            allow_redirects=True,
            stream=True,
        )

        status = (
            response.status_code
        )

        final_url = (
            response.url
        )

        content_type = (
            response.headers.get(
                "Content-Type",
                ""
            )
        )

        response.close()

        return {
            "url":
                url,

            "final_url":
                final_url,

            "status":
                status,

            "content_type":
                content_type,
        }

    except requests.RequestException:
        return {
            "url":
                url,

            "final_url":
                url,

            "status":
                None,

            "content_type":
                "",
        }


def _find_blog_url(
    page,
):
    current_url = (
        page.url
    )

    current_parsed = (
        urlparse(
            current_url
        )
    )

    current_host = (
        _normalize_host(
            current_parsed.hostname
        )
    )

    current_path = (
        current_parsed.path
        .lower()
    )

    # If the user scans the blog page directly,
    # use the current URL immediately.
    if any(
        token in current_path
        for token in (
            "/blog",
            "/news",
            "/insights",
            "/articles",
        )
    ):
        return {
            "url":
                current_url,

            "source":
                "Current page",
        }

    anchors = page.evaluate(
        """
        () => Array
            .from(
                document.querySelectorAll(
                    "a[href]"
                )
            )
            .map(
                anchor => ({
                    text:
                        (
                            anchor.innerText
                            ||
                            anchor.textContent
                            ||
                            ""
                        )
                        .replace(
                            /\\s+/g,
                            " "
                        )
                        .trim(),

                    href:
                        anchor.href
                        ||
                        ""
                })
            )
        """
    )

    candidates = []
    seen = set()

    for anchor in anchors:
        href = (
            anchor.get(
                "href"
            )
            or
            ""
        ).strip()

        text = (
            anchor.get(
                "text"
            )
            or
            ""
        ).strip()

        if not href:
            continue

        parsed = (
            urlparse(
                href
            )
        )

        if parsed.scheme.lower() not in (
            "http",
            "https",
        ):
            continue

        if (
            _normalize_host(
                parsed.hostname
            )
            !=
            current_host
        ):
            continue

        if not _looks_like_blog(
            text,
            href,
        ):
            continue

        if href in seen:
            continue

        seen.add(
            href
        )

        candidates.append(
            {
                "url":
                    href,

                "text":
                    text,

                "score":
                    _candidate_score(
                        text,
                        href,
                    ),
            }
        )

    if candidates:
        candidates.sort(
            key=lambda item:
                item[
                    "score"
                ],
            reverse=True,
        )

        return {
            "url":
                candidates[
                    0
                ][
                    "url"
                ],

            "source":
                "HTML link",
        }

    # Fallback: quickly probe common same-domain paths.
    origin = (
        f"{current_parsed.scheme}://"
        f"{current_parsed.netloc}"
    )

    urls = [
        urljoin(
            origin,
            path,
        )
        for path in COMMON_BLOG_PATHS
    ]

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

    probe_results = []

    with ThreadPoolExecutor(
        max_workers=
            len(
                urls
            )
    ) as executor:
        futures = {
            executor.submit(
                _probe_candidate,
                url,
                headers,
            ):
                url

            for url in urls
        }

        for future in as_completed(
            futures
        ):
            try:
                probe_results.append(
                    future.result()
                )

            except Exception:
                pass

    priority = {
        "/blog/": 1,
        "/news/": 2,
        "/insights/": 3,
        "/articles/": 4,
    }

    valid = []

    for result in probe_results:
        status = (
            result.get(
                "status"
            )
        )

        if (
            status is None
            or
            status >= 400
        ):
            continue

        final_url = (
            result.get(
                "final_url"
            )
            or
            result.get(
                "url"
            )
        )

        final_path = (
            urlparse(
                final_url
            ).path
        )

        # Avoid treating a redirect back to the homepage
        # as a valid blog page.
        if final_path in (
            "",
            "/",
        ):
            continue

        valid.append(
            {
                "url":
                    final_url,

                "priority":
                    priority.get(
                        urlparse(
                            result[
                                "url"
                            ]
                        ).path,
                        99,
                    ),
            }
        )

    if valid:
        valid.sort(
            key=lambda item:
                item[
                    "priority"
                ]
        )

        return {
            "url":
                valid[
                    0
                ][
                    "url"
                ],

            "source":
                "Common-path probe",
        }

    return None


def _scroll_short(
    page,
):
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

                const total =
                    Math.max(
                        document.body.scrollHeight,
                        document.documentElement.scrollHeight
                    );

                const viewport =
                    Math.max(
                        window.innerHeight,
                        600
                    );

                const steps =
                    Math.max(
                        1,
                        Math.min(
                            8,
                            Math.ceil(
                                total
                                /
                                (viewport * 1.5)
                            )
                        )
                    );

                for (
                    let index = 0;
                    index <= steps;
                    index += 1
                ) {
                    window.scrollTo(
                        0,
                        (
                            total
                            -
                            viewport
                        )
                        *
                        (
                            index
                            /
                            steps
                        )
                    );

                    await wait(
                        60
                    );
                }

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


def _extract_posts(
    blog_page,
    blog_url,
):
    """
    Extract post title, URL and featured image from common
    WordPress/Elementor/card structures.
    """

    posts = blog_page.evaluate(
        """
        () => {
            function clean(value) {
                return (
                    value
                    ||
                    ""
                )
                .replace(
                    /\\s+/g,
                    " "
                )
                .trim();
            }

            function imageInfo(container) {
                if (!container) {
                    return {
                        url: "",
                        alt: "",
                        type: ""
                    };
                }

                const image =
                    container.querySelector(
                        "img"
                    );

                if (image) {
                    return {
                        url:
                            image.currentSrc
                            ||
                            image.getAttribute(
                                "src"
                            )
                            ||
                            image.getAttribute(
                                "data-src"
                            )
                            ||
                            image.getAttribute(
                                "data-lazy-src"
                            )
                            ||
                            "",

                        alt:
                            image.getAttribute(
                                "alt"
                            )
                            ||
                            "",

                        type:
                            "IMG"
                    };
                }

                const elements = [
                    container,
                    ...container.querySelectorAll(
                        "*"
                    )
                ];

                for (
                    const element of elements
                ) {
                    const background =
                        getComputedStyle(
                            element
                        ).backgroundImage;

                    const match =
                        background
                        &&
                        background.match(
                            /url\\(["']?(.*?)["']?\\)/
                        );

                    if (
                        match
                        &&
                        match[1]
                    ) {
                        return {
                            url:
                                match[1],

                            alt:
                                "",

                            type:
                                "Background"
                        };
                    }
                }

                return {
                    url: "",
                    alt: "",
                    type: ""
                };
            }

            const rows = [];
            const seen = new Set();

            let cards =
                Array.from(
                    document.querySelectorAll(
                        "article"
                    )
                );

            if (!cards.length) {
                cards =
                    Array.from(
                        document.querySelectorAll(
                            ".elementor-post,"
                            + ".elementor-loop-item,"
                            + ".post,"
                            + ".blog-card,"
                            + ".news-card,"
                            + ".card"
                        )
                    );
            }

            for (
                const card of cards
            ) {
                const titleElement =
                    card.querySelector(
                        "h1 a,h2 a,h3 a,h4 a,"
                        + ".entry-title a,"
                        + ".elementor-heading-title a"
                    )
                    ||
                    card.querySelector(
                        "h1,h2,h3,h4"
                    );

                if (!titleElement) {
                    continue;
                }

                const title =
                    clean(
                        titleElement.innerText
                        ||
                        titleElement.textContent
                    );

                let url =
                    titleElement.href
                    ||
                    titleElement.closest(
                        "a[href]"
                    )?.href
                    ||
                    card.querySelector(
                        "a[href]"
                    )?.href
                    ||
                    "";

                if (
                    !title
                    ||
                    !url
                    ||
                    seen.has(
                        url
                    )
                ) {
                    continue;
                }

                seen.add(
                    url
                );

                const image =
                    imageInfo(
                        card
                    );

                rows.push({
                    title,
                    url,
                    image_url:
                        image.url,

                    image_alt:
                        image.alt,

                    image_type:
                        image.type
                });
            }

            // Fallback for simple archives where the cards do not
            // have recognizable wrapper classes.
            if (!rows.length) {
                const headings =
                    Array.from(
                        document.querySelectorAll(
                            "main h2 a,"
                            + "main h3 a,"
                            + "main h4 a"
                        )
                    );

                for (
                    const link of headings
                ) {
                    const title =
                        clean(
                            link.innerText
                            ||
                            link.textContent
                        );

                    const url =
                        link.href
                        ||
                        "";

                    if (
                        !title
                        ||
                        !url
                        ||
                        seen.has(
                            url
                        )
                    ) {
                        continue;
                    }

                    seen.add(
                        url
                    );

                    const card =
                        link.closest(
                            "article,"
                            + ".elementor-post,"
                            + ".elementor-loop-item,"
                            + ".post,"
                            + ".card,"
                            + "div"
                        );

                    const image =
                        imageInfo(
                            card
                        );

                    rows.push({
                        title,
                        url,
                        image_url:
                            image.url,

                        image_alt:
                            image.alt,

                        image_type:
                            image.type
                    });
                }
            }

            return rows.slice(
                0,
                100
            );
        }
        """
    )

    # Remove links that simply point back to the archive itself.
    normalized_blog = (
        blog_url.rstrip(
            "/"
        )
    )

    return [
        post
        for post in posts
        if (
            (
                post.get(
                    "url"
                )
                or
                ""
            )
            .rstrip(
                "/"
            )
            !=
            normalized_blog
        )
    ]


def check_blog_page(
    page,
):
    print(
        "\nBlog Page Check"
    )

    print(
        "---------------"
    )

    detection = (
        _find_blog_url(
            page
        )
    )

    if not detection:
        data = {
            "detected":
                False,

            "blog_url":
                None,

            "detection_source":
                None,

            "http_status":
                None,

            "page_title":
                "",

            "h1":
                "",

            "posts":
                [],
        }

        print(
            "QA_BLOG_DATA|"
            +
            json.dumps(
                data,
                ensure_ascii=False,
            )
        )

        print(
            "INFO | Blog Detection | "
            "No obvious Blog / News / Insights page detected"
        )

        print(
            "\nBlog Page Check Complete"
        )

        return

    blog_url = (
        detection[
            "url"
        ]
    )

    blog_page = (
        page.context.new_page()
    )

    response = None

    try:
        response = blog_page.goto(
            blog_url,
            wait_until=
                "domcontentloaded",
            timeout=
                20_000,
        )

        blog_page.wait_for_timeout(
            200
        )

        _scroll_short(
            blog_page
        )

        page_title = (
            blog_page.title()
        )

        h1_locator = (
            blog_page.locator(
                "h1"
            )
        )

        h1 = (
            h1_locator
            .first
            .inner_text()
            .strip()
            if h1_locator.count()
            else ""
        )

        posts = (
            _extract_posts(
                blog_page,
                blog_page.url,
            )
        )

        final_blog_url = (
            blog_page.url
        )

        http_status = (
            response.status
            if response
            else None
        )

        data = {
            "detected":
                True,

            "blog_url":
                final_blog_url,

            "detection_source":
                detection[
                    "source"
                ],

            "http_status":
                http_status,

            "page_title":
                page_title,

            "h1":
                h1,

            "posts":
                posts,
        }

        print(
            "QA_BLOG_DATA|"
            +
            json.dumps(
                data,
                ensure_ascii=False,
            )
        )

        print(
            "PASS | Blog Detection | "
            "Blog / News / Insights page detected"
        )

        print(
            "INFO | Blog Page URL |",
            final_blog_url
        )

        print(
            "INFO | Blog Detection Source |",
            detection[
                "source"
            ]
        )

        if (
            http_status is not None
            and
            http_status >= 400
        ):
            print(
                "FAIL | Blog Page HTTP |",
                http_status
            )

        else:
            print(
                "PASS | Blog Page HTTP |",
                (
                    http_status
                    if http_status is not None
                    else "Loaded"
                )
            )

        if page_title:
            print(
                "PASS | Blog Page Title |",
                page_title
            )

        else:
            print(
                "WARNING | Blog Page Title | Missing page title"
            )

        if h1:
            print(
                "PASS | Blog H1 |",
                h1
            )

        else:
            print(
                "WARNING | Blog H1 | No H1 detected on blog page"
            )

        if posts:
            print(
                "PASS | Blog Posts |",
                len(
                    posts
                ),
                "post(s) detected"
            )

        else:
            print(
                "WARNING | Blog Posts | No obvious blog post cards detected"
            )

        posts_with_image = sum(
            1
            for post in posts
            if post.get(
                "image_url"
            )
        )

        posts_with_img_alt = sum(
            1
            for post in posts
            if (
                post.get(
                    "image_type"
                ) == "IMG"
                and
                (
                    post.get(
                        "image_alt"
                    )
                    or
                    ""
                ).strip()
            )
        )

        img_posts = sum(
            1
            for post in posts
            if post.get(
                "image_type"
            ) == "IMG"
        )

        if posts:
            if (
                posts_with_image
                ==
                len(
                    posts
                )
            ):
                print(
                    "PASS | Featured Images | "
                    "Featured image detected for all post cards"
                )

            else:
                print(
                    "WARNING | Featured Images |",
                    (
                        f"{len(posts) - posts_with_image} "
                        "post(s) without a detected featured image"
                    )
                )

        if img_posts:
            if (
                posts_with_img_alt
                ==
                img_posts
            ):
                print(
                    "PASS | Blog Image ALT | "
                    "ALT text present on detected IMG featured images"
                )

            else:
                print(
                    "WARNING | Blog Image ALT |",
                    (
                        f"{img_posts - posts_with_img_alt} "
                        "IMG featured image(s) missing/empty ALT"
                    )
                )

        post_urls = [
            post.get(
                "url"
            )
            for post in posts
            if post.get(
                "url"
            )
        ]

        duplicate_count = (
            len(
                post_urls
            )
            -
            len(
                set(
                    post_urls
                )
            )
        )

        if duplicate_count:
            print(
                "WARNING | Duplicate Blog Posts |",
                duplicate_count
            )

        else:
            print(
                "PASS | Duplicate Blog Posts | "
                "No duplicate post URLs detected"
            )

        pagination_count = (
            blog_page.locator(
                ".pagination,"
                + ".nav-links,"
                + ".page-numbers,"
                + "a[rel='next'],"
                + "a[rel='prev']"
            ).count()
        )

        if pagination_count:
            print(
                "PASS | Blog Pagination | "
                "Pagination/navigation detected"
            )

        else:
            print(
                "INFO | Blog Pagination | "
                "No pagination detected"
            )

    finally:
        blog_page.close()

    print(
        "\nBlog Page Check Complete"
    )
