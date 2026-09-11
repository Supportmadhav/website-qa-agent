def check_sticky_header(page):
    """
    Check whether the website has a sticky/fixed header
    and whether it behaves correctly after scrolling.

    Checks:
    1. Detect header/nav elements
    2. Detect fixed or sticky positioning
    3. Scroll the page
    4. Confirm the header remains visible
    5. Check whether the sticky header overlaps page content
    """

    print("\nSticky Header Check")
    print("-------------------")

    # =====================================
    # FIND POSSIBLE HEADER ELEMENTS
    # =====================================

    header_selectors = [
        "header",
        ".site-header",
        ".elementor-location-header",
        ".elementor-sticky",
        ".sticky-header",
        ".header",
        "nav"
    ]

    detected_headers = []

    for selector in header_selectors:

        locator = page.locator(selector)

        count = locator.count()

        if count == 0:
            continue

        for i in range(count):

            element = locator.nth(i)

            try:

                if not element.is_visible():
                    continue

                info = element.evaluate("""
                    (el) => {

                        const rect =
                            el.getBoundingClientRect();

                        const style =
                            window.getComputedStyle(el);

                        return {
                            tag:
                                el.tagName,

                            className:
                                typeof el.className === "string"
                                    ? el.className
                                    : "",

                            position:
                                style.position,

                            top:
                                Math.round(rect.top),

                            bottom:
                                Math.round(rect.bottom),

                            height:
                                Math.round(rect.height),

                            width:
                                Math.round(rect.width),

                            zIndex:
                                style.zIndex
                        };
                    }
                """)

                detected_headers.append(
                    {
                        "selector": selector,
                        "index": i,
                        "element": element,
                        "info": info
                    }
                )

            except Exception:
                continue

    # =====================================
    # NO HEADER FOUND
    # =====================================

    if not detected_headers:

        print(
            "WARNING | Sticky Header |",
            "No visible header/navigation element detected"
        )

        return

    print(
        "Headers detected:",
        len(detected_headers)
    )

    # =====================================
    # SELECT BEST HEADER CANDIDATE
    # =====================================

    best_header = None

    for header in detected_headers:

        info = header["info"]

        # Prefer header elements near the top
        # and with a useful visible height
        if (
            info["top"] <= 150
            and info["height"] > 20
        ):

            best_header = header
            break

    if best_header is None:
        best_header = detected_headers[0]

    header_element = best_header["element"]
    initial_info = best_header["info"]

    print(
        "Detected header:",
        initial_info["tag"],
        "| position:",
        initial_info["position"],
        "| height:",
        initial_info["height"],
        "| top:",
        initial_info["top"]
    )

    # =====================================
    # CHECK INITIAL POSITION TYPE
    # =====================================

    initial_position = (
        initial_info["position"]
        .strip()
        .lower()
    )

    initially_sticky = (
        initial_position == "fixed"
        or initial_position == "sticky"
    )

    if initially_sticky:

        print(
            "PASS | Header positioning |",
            initial_position
        )

    else:

        print(
            "INFO | Header positioning |",
            initial_position,
            "| Header may become sticky after scroll"
        )

    # =====================================
    # GET PAGE HEIGHT
    # =====================================

    page_height = page.evaluate("""
        () => {
            return Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight
            );
        }
    """)

    viewport_height = page.evaluate(
        "() => window.innerHeight"
    )

    # =====================================
    # SHORT PAGE CHECK
    # =====================================

    if page_height <= viewport_height + 100:

        print(
            "WARNING | Sticky Header |",
            "Page is too short to test sticky behavior"
        )

        return

    # =====================================
    # SCROLL PAGE
    # =====================================

    scroll_position = min(
        800,
        max(
            300,
            page_height // 3
        )
    )

    page.evaluate(
        f"window.scrollTo(0, {scroll_position})"
    )

    # Give sticky JavaScript / CSS time to react
    page.wait_for_timeout(1000)

    # =====================================
    # CHECK HEADER AFTER SCROLL
    # =====================================

    try:

        after_scroll = header_element.evaluate("""
            (el) => {

                const rect =
                    el.getBoundingClientRect();

                const style =
                    window.getComputedStyle(el);

                return {
                    position:
                        style.position,

                    top:
                        Math.round(rect.top),

                    bottom:
                        Math.round(rect.bottom),

                    height:
                        Math.round(rect.height),

                    visible:
                        style.display !== "none" &&
                        style.visibility !== "hidden" &&
                        Number(style.opacity) !== 0 &&
                        rect.width > 0 &&
                        rect.height > 0
                };
            }
        """)

    except Exception:

        print(
            "WARNING | Sticky Header |",
            "Header element changed after scrolling"
        )

        page.evaluate(
            "window.scrollTo(0, 0)"
        )

        return

    # =====================================
    # DETERMINE IF HEADER IS STICKY
    # =====================================

    after_position = (
        after_scroll["position"]
        .strip()
        .lower()
    )

    stays_near_top = (
        after_scroll["top"] >= -5
        and after_scroll["top"] <= 10
    )

    sticky_after_scroll = (
        after_position == "fixed"
        or after_position == "sticky"
        or stays_near_top
    )

    if (
        after_scroll["visible"]
        and sticky_after_scroll
    ):

        print(
            "PASS | Sticky Header |",
            "Header remains visible after scroll",
            "| position:",
            after_position,
            "| top:",
            after_scroll["top"]
        )

    else:

        print(
            "INFO | Sticky Header |",
            "No sticky header behavior detected"
        )

    # =====================================
    # CHECK STICKY / FIXED UI OVERLAP
    # =====================================

    if sticky_after_scroll:

        header_rect = {
            "top": after_scroll["top"],
            "bottom": after_scroll["bottom"],
            "height": after_scroll["height"]
        }

        fixed_elements = page.evaluate("""
            () => {

                const elements = Array.from(
                    document.querySelectorAll("body *")
                );

                return elements
                    .filter((el) => {

                        const rect =
                            el.getBoundingClientRect();

                        const style =
                            window.getComputedStyle(el);

                        if (
                            style.display === "none" ||
                            style.visibility === "hidden" ||
                            Number(style.opacity) === 0 ||
                            rect.width <= 20 ||
                            rect.height <= 20
                        ) {
                            return false;
                        }

                        // Only inspect fixed/sticky UI
                        if (
                            style.position !== "fixed" &&
                            style.position !== "sticky"
                        ) {
                            return false;
                        }

                        // Ignore elements completely
                        // outside the current viewport
                        if (
                            rect.bottom <= 0 ||
                            rect.top >= window.innerHeight
                        ) {
                            return false;
                        }

                        return true;
                    })

                    .map((el) => {

                        const rect =
                            el.getBoundingClientRect();

                        return {
                            tag: el.tagName,

                            className:
                                typeof el.className === "string"
                                    ? el.className
                                    : "",

                            top:
                                Math.round(rect.top),

                            bottom:
                                Math.round(rect.bottom),

                            left:
                                Math.round(rect.left),

                            right:
                                Math.round(rect.right),

                            width:
                                Math.round(rect.width),

                            height:
                                Math.round(rect.height),

                            position:
                                window
                                    .getComputedStyle(el)
                                    .position
                        };
                    });
            }
        """)

        overlap_issues = []

        header_top = header_rect["top"]
        header_bottom = header_rect["bottom"]

        for item in fixed_elements:

            # Ignore the detected header itself
            if (
                abs(item["top"] - header_top) <= 2
                and
                abs(item["bottom"] - header_bottom) <= 2
            ):
                continue

            vertical_overlap = (
                min(
                    header_bottom,
                    item["bottom"]
                )
                -
                max(
                    header_top,
                    item["top"]
                )
            )

            # Only report meaningful overlap
            if vertical_overlap > 20:

                overlap_issues.append(
                    item
                )

        if overlap_issues:

            print(
                "WARNING | Sticky Header UI Overlap |",
                len(overlap_issues),
                "possible fixed/sticky element overlap(s)"
            )

            for item in overlap_issues[:10]:

                print(
                    "   ",
                    item["tag"],
                    "|",
                    item["className"],
                    "| position:",
                    item["position"],
                    "| top:",
                    item["top"],
                    "| bottom:",
                    item["bottom"]
                )

        else:

            print(
                "PASS | Sticky Header UI Overlap |",
                "No conflicting fixed/sticky elements detected"
            )

    else:

        print(
            "INFO | Sticky Header UI Overlap |",
            "Skipped because sticky behavior was not detected"
        )


    # =====================================
    # RETURN PAGE TO TOP
    # =====================================

    page.evaluate(
        "window.scrollTo(0, 0)"
    )

    page.wait_for_timeout(
        300
    )

    print(
        "\nSticky Header Check Complete"
    )

    print(
        "----------------------------"
    )