from urllib.parse import urlparse


def check_social_media(page):
    """
    Check social media links on the webpage.

    Platforms checked:
    - Facebook
    - Instagram
    - LinkedIn
    - YouTube
    - X / Twitter
    - Pinterest
    - TikTok

    Checks:
    1. Detect social media links/buttons
    2. Identify platform
    3. Check visibility
    4. Validate URL
    5. Check target=_blank
    6. Detect placeholder links
    7. Detect duplicate social URLs
    8. Detect multiple different URLs
       for the same platform
    """

    print("\nSocial Media Links Check")
    print("------------------------")

    # =====================================
    # PLATFORM CONFIGURATION
    # =====================================

    platform_domains = {
        "Facebook": [
            "facebook.com",
            "fb.com"
        ],

        "Instagram": [
            "instagram.com"
        ],

        "LinkedIn": [
            "linkedin.com"
        ],

        "YouTube": [
            "youtube.com",
            "youtu.be"
        ],

        "X / Twitter": [
            "twitter.com",
            "x.com"
        ],

        "Pinterest": [
            "pinterest.com",
            "pin.it"
        ],

        "TikTok": [
            "tiktok.com"
        ]
    }

    # =====================================
    # GET ALL POSSIBLE SOCIAL LINKS
    # =====================================

    links = page.evaluate("""
        () => {

            const anchors = Array.from(
                document.querySelectorAll(
                    "a"
                )
            );

            return anchors.map((link) => {

                const rect =
                    link.getBoundingClientRect();

                const style =
                    window.getComputedStyle(
                        link
                    );

                const visible = (
                    style.display !== "none" &&
                    style.visibility !== "hidden" &&
                    Number(style.opacity) !== 0 &&
                    rect.width > 0 &&
                    rect.height > 0
                );

                const className =
                    typeof link.className ===
                    "string"
                        ? link.className
                        : "";

                return {
                    href:
                        link.getAttribute(
                            "href"
                        ) || "",

                    resolvedHref:
                        link.href || "",

                    target:
                        link.getAttribute(
                            "target"
                        ) || "",

                    text:
                        (
                            link.innerText ||
                            ""
                        )
                        .trim()
                        .replace(
                            /\\s+/g,
                            " "
                        )
                        .slice(
                            0,
                            100
                        ),

                    ariaLabel:
                        (
                            link.getAttribute(
                                "aria-label"
                            ) ||
                            ""
                        )
                        .trim(),

                    title:
                        (
                            link.getAttribute(
                                "title"
                            ) ||
                            ""
                        )
                        .trim(),

                    className:
                        className,

                    visible:
                        visible
                };
            });
        }
    """)

    # =====================================
    # HELPER: DETECT PLATFORM
    # =====================================

    def detect_platform(item):

        href = (
            item["resolvedHref"]
            or
            item["href"]
            or
            ""
        ).lower()

        combined_text = (
            f'{item["text"]} '
            f'{item["ariaLabel"]} '
            f'{item["title"]} '
            f'{item["className"]}'
        ).lower()

        # -------------------------------------
        # DETECT FROM DOMAIN
        # -------------------------------------

        for (
            platform,
            domains
        ) in platform_domains.items():

            for domain in domains:

                if domain in href:

                    return platform

        # -------------------------------------
        # DETECT FROM TEXT / ICON CLASS
        # -------------------------------------

        text_platforms = {
            "Facebook": [
                "facebook",
                "fa-facebook"
            ],

            "Instagram": [
                "instagram",
                "fa-instagram"
            ],

            "LinkedIn": [
                "linkedin",
                "fa-linkedin"
            ],

            "YouTube": [
                "youtube",
                "fa-youtube"
            ],

            "X / Twitter": [
                "twitter",
                "fa-twitter",
                "fa-x-twitter"
            ],

            "Pinterest": [
                "pinterest",
                "fa-pinterest"
            ],

            "TikTok": [
                "tiktok",
                "fa-tiktok"
            ]
        }

        for (
            platform,
            keywords
        ) in text_platforms.items():

            for keyword in keywords:

                if keyword in combined_text:

                    return platform

        return None

    # =====================================
    # FIND SOCIAL LINKS
    # =====================================

    social_links = []

    for item in links:

        platform = detect_platform(
            item
        )

        if not platform:
            continue

        item[
            "platform"
        ] = platform

        social_links.append(
            item
        )

    # =====================================
    # NO SOCIAL LINKS
    # =====================================

    if not social_links:

        print(
            "WARNING | Social Media Detection |",
            "No social media links detected"
        )

        print(
            "\nSocial Media Links Check Complete"
        )

        print(
            "---------------------------------"
        )

        return

    print(
        "PASS | Social Media Detection |",
        len(social_links),
        "social media link(s) detected"
    )

    # =====================================
    # COUNTERS
    # =====================================

    visible_count = 0

    valid_count = 0

    warning_count = 0

    invalid_count = 0

    new_tab_count = 0

    platform_urls = {}

    all_urls = []

    # =====================================
    # ANALYZE EACH SOCIAL LINK
    # =====================================

    for index, item in enumerate(
        social_links,
        start=1
    ):

        platform = item[
            "platform"
        ]

        href = (
            item["resolvedHref"]
            or
            item["href"]
        )

        raw_href = (
            item["href"]
            or
            ""
        )

        print(
            f"\nSocial Link {index}"
        )

        print(
            "Platform |",
            platform
        )

        print(
            "URL |",
            href
        )

        if item["text"]:

            print(
                "Text |",
                item["text"]
            )

        # =====================================
        # VISIBILITY
        # =====================================

        if item[
            "visible"
        ]:

            visible_count += 1

            print(
                "PASS | Visibility |",
                "Social link is visible"
            )

        else:

            print(
                "INFO | Visibility |",
                "Social link exists but is currently hidden"
            )

        # =====================================
        # PLACEHOLDER LINK CHECK
        # =====================================

        placeholder_values = [
            "",
            "#",
            "/",
            "javascript:void(0)",
            "javascript:void(0);"
        ]

        if (
            raw_href.strip().lower()
            in placeholder_values
        ):

            invalid_count += 1

            print(
                "FAIL | Social URL |",
                "Placeholder or empty URL"
            )

            continue

        # =====================================
        # VALIDATE URL
        # =====================================

        try:

            parsed = urlparse(
                href
            )

            hostname = (
                parsed.netloc
                .lower()
                .replace(
                    "www.",
                    ""
                )
            )

        except Exception:

            hostname = ""

        expected_domains = (
            platform_domains[
                platform
            ]
        )

        valid_domain = any(
            (
                hostname == domain
                or
                hostname.endswith(
                    "." + domain
                )
            )
            for domain in
            expected_domains
        )

        if valid_domain:

            valid_count += 1

            print(
                "PASS | Social URL |",
                "Valid",
                platform,
                "domain"
            )

        else:

            warning_count += 1

            print(
                "WARNING | Social URL |",
                "Detected as",
                platform,
                "but URL does not match expected domain"
            )

        # =====================================
        # TARGET NEW TAB
        # =====================================

        if (
            item["target"]
            == "_blank"
        ):

            new_tab_count += 1

            print(
                "PASS | Link Target |",
                "Opens in new tab"
            )

        else:

            warning_count += 1

            print(
                "WARNING | Link Target |",
                "Social link does not use target=_blank"
            )

        # =====================================
        # STORE PLATFORM URL
        # =====================================

        platform_urls.setdefault(
            platform,
            []
        )

        platform_urls[
            platform
        ].append(
            href
        )

        all_urls.append(
            href
        )

    # =====================================
    # DUPLICATE URL CHECK
    # =====================================

    duplicate_count = (
        len(all_urls)
        -
        len(
            set(
                all_urls
            )
        )
    )

    if duplicate_count > 0:

        print(
            "\nINFO | Duplicate Social Links |",
            duplicate_count,
            "duplicate link(s)"
        )

    else:

        print(
            "\nPASS | Duplicate Social Links |",
            "No duplicate social URLs detected"
        )

    # =====================================
    # PLATFORM CONSISTENCY
    # =====================================

    consistency_warnings = 0

    for (
        platform,
        urls
    ) in platform_urls.items():

        unique_platform_urls = set(
            urls
        )

        if len(
            unique_platform_urls
        ) > 1:

            consistency_warnings += 1

            print(
                "WARNING |",
                platform,
                "| Multiple different URLs detected"
            )

            for url in sorted(
                unique_platform_urls
            ):

                print(
                    "   ",
                    url
                )

    if consistency_warnings == 0:

        print(
            "PASS | Platform Consistency |",
            "No conflicting social URLs detected"
        )

    # =====================================
    # PLATFORM SUMMARY
    # =====================================

    print(
        "\nPlatforms Detected"
    )

    for platform in (
        platform_urls.keys()
    ):

        unique_count = len(
            set(
                platform_urls[
                    platform
                ]
            )
        )

        print(
            platform,
            "|",
            unique_count,
            "unique URL(s)"
        )

    # =====================================
    # SUMMARY
    # =====================================

    print(
        "\nSocial Media Summary"
    )

    print(
        "Total Links:",
        len(social_links)
    )

    print(
        "Visible:",
        visible_count
    )

    print(
        "Valid URLs:",
        valid_count
    )

    print(
        "Warnings:",
        warning_count
    )

    print(
        "Invalid URLs:",
        invalid_count
    )

    print(
        "Open New Tab:",
        new_tab_count
    )

    print(
        "Platforms:",
        len(
            platform_urls
        )
    )

    # =====================================
    # COMPLETE
    # =====================================

    print(
        "\nSocial Media Links Check Complete"
    )

    print(
        "---------------------------------"
    )