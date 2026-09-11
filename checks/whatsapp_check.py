from urllib.parse import urlparse, parse_qs, unquote


def check_whatsapp(page):
    """
    Check WhatsApp buttons and links on the webpage.

    Checks:
    1. Detect WhatsApp links/buttons
    2. Check whether buttons are visible
    3. Validate WhatsApp URL format
    4. Detect phone number
    5. Detect pre-filled message
    6. Check whether target opens in new tab
    7. Detect duplicate WhatsApp links
    """

    print("\nWhatsApp Check")
    print("--------------")

    # =====================================
    # FIND WHATSAPP LINKS
    # =====================================

    whatsapp_links = page.evaluate("""
        () => {

            const links = Array.from(
                document.querySelectorAll(
                    "a[href]"
                )
            );

            const results = [];

            for (const link of links) {

                const href =
                    link.href || "";

                const hrefLower =
                    href.toLowerCase();

                const isWhatsApp = (
                    hrefLower.includes(
                        "wa.me/"
                    )
                    ||
                    hrefLower.includes(
                        "api.whatsapp.com"
                    )
                    ||
                    hrefLower.includes(
                        "web.whatsapp.com"
                    )
                    ||
                    hrefLower.startsWith(
                        "whatsapp://"
                    )
                );

                if (!isWhatsApp) {
                    continue;
                }

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

                let className = "";

                if (
                    typeof link.className
                    === "string"
                ) {
                    className =
                        link.className;
                }

                results.push({
                    href:
                        href,

                    text:
                        (
                            link.innerText ||
                            link.getAttribute(
                                "aria-label"
                            ) ||
                            link.getAttribute(
                                "title"
                            ) ||
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

                    target:
                        link.getAttribute(
                            "target"
                        ) || "",

                    visible:
                        visible,

                    className:
                        className,

                    width:
                        Math.round(
                            rect.width
                        ),

                    height:
                        Math.round(
                            rect.height
                        )
                });
            }

            return results;
        }
    """)

    # =====================================
    # NO WHATSAPP LINK
    # =====================================

    if not whatsapp_links:

        print(
            "FAIL | WhatsApp Detection |",
            "No WhatsApp link or button detected"
        )

        print(
            "\nWhatsApp Check Complete"
        )

        print(
            "-----------------------"
        )

        return

    print(
        "PASS | WhatsApp Detection |",
        len(whatsapp_links),
        "WhatsApp link(s) detected"
    )

    # =====================================
    # VISIBLE BUTTONS
    # =====================================

    visible_links = [
        item
        for item in whatsapp_links
        if item["visible"]
    ]

    if visible_links:

        print(
            "PASS | WhatsApp Visibility |",
            len(visible_links),
            "visible button/link(s)"
        )

    else:

        print(
            "WARNING | WhatsApp Visibility |",
            "WhatsApp links exist but none are visible"
        )

    # =====================================
    # ANALYZE EACH LINK
    # =====================================

    valid_links = 0
    warning_links = 0
    invalid_links = 0

    phone_numbers = []
    messages = []

    new_tab_count = 0

    for index, item in enumerate(
        whatsapp_links,
        start=1
    ):

        href = item["href"]

        print(
            f"\nWhatsApp Link {index}"
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
        # PARSE URL
        # =====================================

        try:

            parsed_url = urlparse(
                href
            )

        except Exception:

            parsed_url = None

        href_lower = (
            href.lower()
        )

        # =====================================
        # VALIDATE WHATSAPP URL FORMAT
        # =====================================

        valid_format = False
        format_warning = None

        if parsed_url:

            hostname = (
                parsed_url.netloc
                .lower()
                .replace(
                    "www.",
                    ""
                )
            )

            # -------------------------------------
            # WA.ME FORMAT
            # -------------------------------------

            if hostname == "wa.me":

                wa_number = (
                    parsed_url.path
                    .strip("/")
                    .split("/")[0]
                )

                if (
                    wa_number
                    and
                    wa_number.isdigit()
                ):

                    valid_format = True

                elif wa_number:

                    format_warning = (
                        "wa.me phone number should "
                        "contain digits only"
                    )

            # -------------------------------------
            # WHATSAPP API FORMAT
            # -------------------------------------

            elif hostname in [
                "api.whatsapp.com",
                "web.whatsapp.com"
            ]:

                valid_format = True

            # -------------------------------------
            # WHATSAPP APP PROTOCOL
            # -------------------------------------

            elif href_lower.startswith(
                "whatsapp://"
            ):

                valid_format = True

        # =====================================
        # URL FORMAT RESULT
        # =====================================

        if valid_format:

            valid_links += 1

            print(
                "PASS | URL Format |",
                "Valid WhatsApp URL"
            )

        elif format_warning:

            warning_links += 1

            print(
                "WARNING | URL Format |",
                format_warning
            )

        else:

            invalid_links += 1

            print(
                "FAIL | URL Format |",
                "Invalid WhatsApp URL"
            )

        # =====================================
        # TARGET NEW TAB
        # =====================================

        if item["target"] == "_blank":

            new_tab_count += 1

            print(
                "PASS | Link Target |",
                "Opens in new tab"
            )

        else:

            print(
                "WARNING | Link Target |",
                "Does not use target=_blank"
            )

        # =====================================
        # EXTRACT PHONE NUMBER
        # =====================================

        phone_number = None

        if parsed_url:

            try:

                hostname = (
                    parsed_url.netloc
                    .lower()
                    .replace(
                        "www.",
                        ""
                    )
                )

                query = parse_qs(
                    parsed_url.query
                )

                # -------------------------------------
                # wa.me/PHONE
                # -------------------------------------

                if hostname == "wa.me":

                    phone_number = (
                        parsed_url.path
                        .strip("/")
                        .split("/")[0]
                    )

                # -------------------------------------
                # API / APP QUERY FORMAT
                # -------------------------------------

                if (
                    not phone_number
                    and
                    "phone" in query
                    and
                    query["phone"]
                ):

                    phone_number = (
                        query["phone"][0]
                    )

            except Exception:

                phone_number = None

        # =====================================
        # VALIDATE PHONE NUMBER
        # =====================================

        if phone_number:

            clean_phone = (
                phone_number
                .replace(
                    "+",
                    ""
                )
                .replace(
                    " ",
                    ""
                )
                .replace(
                    "-",
                    ""
                )
                .replace(
                    "(",
                    ""
                )
                .replace(
                    ")",
                    ""
                )
            )

            if (
                clean_phone.isdigit()
                and
                8 <= len(
                    clean_phone
                ) <= 15
            ):

                phone_numbers.append(
                    clean_phone
                )

                print(
                    "PASS | Phone Number |",
                    clean_phone
                )

            else:

                print(
                    "WARNING | Phone Number |",
                    phone_number,
                    "| Unusual phone format"
                )

        else:

            print(
                "INFO | Phone Number |",
                "No phone number found in URL"
            )

        # =====================================
        # PRE-FILLED MESSAGE
        # =====================================

        try:

            if parsed_url:

                query = parse_qs(
                    parsed_url.query
                )

            else:

                query = {}

            message = None

            if (
                "text" in query
                and
                query["text"]
            ):

                message = unquote(
                    query["text"][0]
                )

            if message:

                messages.append(
                    message
                )

                print(
                    "PASS | Prefilled Message |",
                    message[:150]
                )

            else:

                print(
                    "INFO | Prefilled Message |",
                    "No pre-filled WhatsApp message"
                )

        except Exception:

            print(
                "INFO | Prefilled Message |",
                "Unable to inspect message"
            )

    # =====================================
    # DUPLICATE LINK CHECK
    # =====================================

    all_urls = [
        item["href"]
        for item in whatsapp_links
    ]

    unique_urls = set(
        all_urls
    )

    duplicate_count = (
        len(all_urls)
        -
        len(unique_urls)
    )

    if duplicate_count > 0:

        print(
            "\nINFO | Duplicate WhatsApp Links |",
            duplicate_count,
            "duplicate link(s)"
        )

    else:

        print(
            "\nPASS | Duplicate WhatsApp Links |",
            "No duplicate URLs detected"
        )

    # =====================================
    # PHONE NUMBER CONSISTENCY
    # =====================================

    unique_numbers = set(
        phone_numbers
    )

    if len(
        unique_numbers
    ) > 1:

        print(
            "WARNING | Phone Consistency |",
            len(unique_numbers),
            "different WhatsApp numbers detected"
        )

        for number in sorted(
            unique_numbers
        ):

            print(
                "   ",
                number
            )

    elif len(
        unique_numbers
    ) == 1:

        print(
            "PASS | Phone Consistency |",
            next(
                iter(
                    unique_numbers
                )
            )
        )

    else:

        print(
            "INFO | Phone Consistency |",
            "No phone number available for comparison"
        )

    # =====================================
    # SUMMARY
    # =====================================

    print(
        "\nWhatsApp Summary"
    )

    print(
        "Total Links:",
        len(whatsapp_links)
    )

    print(
        "Visible:",
        len(visible_links)
    )

    print(
        "Valid URLs:",
        valid_links
    )

    print(
        "URL Warnings:",
        warning_links
    )

    print(
        "Invalid URLs:",
        invalid_links
    )

    print(
        "Open New Tab:",
        new_tab_count
    )

    print(
        "Phone Numbers:",
        len(
            unique_numbers
        )
    )

    print(
        "Prefilled Messages:",
        len(messages)
    )

    # =====================================
    # COMPLETE
    # =====================================

    print(
        "\nWhatsApp Check Complete"
    )

    print(
        "-----------------------"
    )