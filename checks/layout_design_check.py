def check_layout_design(page):
    """
    DOM-based Layout & Design QA.

    Checks:
    1. Very small readable text
    2. Text clipping / cut-off content
    3. Suspiciously tight line-height
    4. Overly wide paragraphs
    5. Distorted images
    6. Very small genuine buttons / CTAs

    Responsive overflow and sticky-header
    overlap are handled by separate modules.
    """

    print(
        "\nLayout & Design Check"
    )

    print(
        "---------------------"
    )

    # =====================================
    # TRIGGER LAZY / ANIMATED CONTENT
    # =====================================

    try:

        page.evaluate("""
            async () => {

                const sleep = (ms) =>
                    new Promise(
                        resolve =>
                            setTimeout(
                                resolve,
                                ms
                            )
                    );

                const height =
                    Math.max(
                        document.body.scrollHeight,
                        document.documentElement.scrollHeight
                    );

                const step =
                    Math.max(
                        window.innerHeight * 0.75,
                        400
                    );

                for (
                    let y = 0;
                    y < height;
                    y += step
                ) {

                    window.scrollTo(
                        0,
                        y
                    );

                    await sleep(
                        100
                    );
                }

                window.scrollTo(
                    0,
                    0
                );

                await sleep(
                    300
                );
            }
        """)

    except Exception:

        pass

    # =====================================
    # ANALYZE PAGE
    # =====================================

    results = page.evaluate("""
        () => {

            const result = {

                smallText: [],

                clippedText: [],

                tightLineHeight: [],

                wideParagraphs: [],

                distortedImages: [],

                smallButtons: []

            };


            // =================================
            // IGNORE SELECTORS
            // =================================

            const ignoredSelectors = [

                "script",
                "style",
                "noscript",

                ".skiptranslate",
                ".goog-te-gadget",
                ".goog-te-menu-frame",

                ".screen-reader-text",
                ".sr-only",

                ".swiper-slide-duplicate",

                "[aria-hidden='true']"

            ];


            // =================================
            // IGNORE CHECK
            // =================================

            function shouldIgnore(element) {

                for (
                    const selector of
                    ignoredSelectors
                ) {

                    try {

                        if (
                            element.matches(
                                selector
                            )
                            ||
                            element.closest(
                                selector
                            )
                        ) {

                            return true;

                        }

                    }
                    catch (error) {

                        // Ignore invalid selector

                    }

                }

                return false;

            }


            // =================================
            // VISIBILITY CHECK
            // =================================

            function isVisible(element) {

                const style =
                    window.getComputedStyle(
                        element
                    );

                const rect =
                    element.getBoundingClientRect();


                if (
                    style.display === "none"
                    ||
                    style.visibility === "hidden"
                    ||
                    Number(
                        style.opacity
                    ) === 0
                ) {

                    return false;

                }


                if (
                    rect.width <= 0
                    ||
                    rect.height <= 0
                ) {

                    return false;

                }


                return true;

            }


            // =================================
            // CLEAN TEXT
            // =================================

            function cleanText(text) {

                return (
                    text
                    ||
                    ""
                )
                .replace(
                    /\\s+/g,
                    " "
                )
                .trim();

            }


            // =================================
            // ELEMENT DESCRIPTION
            // =================================

            function describe(element) {

                const text =
                    cleanText(
                        element.innerText
                        ||
                        element.textContent
                    );


                return {

                    tag:
                        element.tagName,

                    text:
                        text.substring(
                            0,
                            160
                        ),

                    className:
                        typeof element.className === "string"
                            ?
                            element.className.substring(
                                0,
                                120
                            )
                            :
                            ""

                };

            }


            // =================================
            // TEXT ELEMENTS
            // =================================

            const textElements =
                document.querySelectorAll(
                    [
                        "p",
                        "h1",
                        "h2",
                        "h3",
                        "h4",
                        "h5",
                        "h6",
                        "li",
                        "label",
                        "button"
                    ].join(",")
                );


            for (
                const element of
                textElements
            ) {

                if (
                    !isVisible(
                        element
                    )
                    ||
                    shouldIgnore(
                        element
                    )
                ) {

                    continue;

                }


                const text =
                    cleanText(
                        element.innerText
                        ||
                        element.textContent
                    );


                if (
                    text.length < 3
                ) {

                    continue;

                }


                const style =
                    window.getComputedStyle(
                        element
                    );


                const rect =
                    element.getBoundingClientRect();


                const fontSize =
                    parseFloat(
                        style.fontSize
                    )
                    ||
                    0;


                // =================================
                // VERY SMALL TEXT
                // =================================

                if (
                    fontSize > 0
                    &&
                    fontSize < 11
                ) {

                    result.smallText.push({

                        ...describe(
                            element
                        ),

                        fontSize:
                            Math.round(
                                fontSize * 10
                            ) / 10

                    });

                }


                // =================================
                // LINE HEIGHT
                // =================================

                const lineHeight =
                    parseFloat(
                        style.lineHeight
                    );


                if (
                    text.length >= 25
                    &&
                    Number.isFinite(
                        lineHeight
                    )
                    &&
                    fontSize > 0
                    &&
                    lineHeight <
                        fontSize * 1.1
                ) {

                    result.tightLineHeight.push({

                        ...describe(
                            element
                        ),

                        fontSize:
                            Math.round(
                                fontSize * 10
                            ) / 10,

                        lineHeight:
                            Math.round(
                                lineHeight * 10
                            ) / 10

                    });

                }


                // =================================
                // CLIPPED TEXT
                // =================================

                const overflowX =
                    style.overflowX;

                const overflowY =
                    style.overflowY;


                const clipsX =
                    (
                        overflowX === "hidden"
                        ||
                        overflowX === "clip"
                    )
                    &&
                    element.scrollWidth >
                        element.clientWidth + 4;


                const clipsY =
                    (
                        overflowY === "hidden"
                        ||
                        overflowY === "clip"
                    )
                    &&
                    element.scrollHeight >
                        element.clientHeight + 4;


                if (
                    clipsX
                    ||
                    clipsY
                ) {

                    result.clippedText.push({

                        ...describe(
                            element
                        ),

                        direction:
                            clipsX && clipsY
                                ?
                                "horizontal + vertical"
                                :
                                clipsX
                                    ?
                                    "horizontal"
                                    :
                                    "vertical",

                        visibleWidth:
                            Math.round(
                                rect.width
                            ),

                        contentWidth:
                            element.scrollWidth,

                        visibleHeight:
                            Math.round(
                                rect.height
                            ),

                        contentHeight:
                            element.scrollHeight

                    });

                }


                // =================================
                // OVERLY WIDE PARAGRAPHS
                // =================================

                if (
                    element.tagName === "P"
                    &&
                    text.length >= 180
                    &&
                    rect.width > 1000
                ) {

                    result.wideParagraphs.push({

                        ...describe(
                            element
                        ),

                        width:
                            Math.round(
                                rect.width
                            )

                    });

                }

            }


            // =================================
            // IMAGE DISTORTION
            // =================================

            const images =
                document.querySelectorAll(
                    "img"
                );


            for (
                const image of
                images
            ) {

                if (
                    !isVisible(
                        image
                    )
                    ||
                    shouldIgnore(
                        image
                    )
                ) {

                    continue;

                }


                const rect =
                    image.getBoundingClientRect();


                if (
                    !image.naturalWidth
                    ||
                    !image.naturalHeight
                    ||
                    rect.width < 40
                    ||
                    rect.height < 40
                ) {

                    continue;

                }


                const naturalRatio =
                    image.naturalWidth
                    /
                    image.naturalHeight;


                const displayedRatio =
                    rect.width
                    /
                    rect.height;


                const difference =
                    Math.abs(
                        displayedRatio
                        -
                        naturalRatio
                    )
                    /
                    naturalRatio;


                // More than 12% ratio difference
                // can indicate image stretching.
                if (
                    difference > 0.12
                ) {

                    result.distortedImages.push({

                        src:
                            (
                                image.currentSrc
                                ||
                                image.src
                                ||
                                ""
                            )
                            .substring(
                                0,
                                180
                            ),

                        alt:
                            (
                                image.alt
                                ||
                                ""
                            )
                            .substring(
                                0,
                                100
                            ),

                        natural:
                            image.naturalWidth
                            +
                            "x"
                            +
                            image.naturalHeight,

                        displayed:
                            Math.round(
                                rect.width
                            )
                            +
                            "x"
                            +
                            Math.round(
                                rect.height
                            ),

                        differencePercent:
                            Math.round(
                                difference * 100
                            )

                    });

                }

            }


            // =================================
            // BUTTON / CTA SIZE
            // =================================

            const buttons =
                document.querySelectorAll(
                    [
                        "button",
                        "input[type='submit']",
                        "input[type='button']",
                        "a.elementor-button",
                        "a.wp-element-button",
                        ".elementor-button",
                        "[role='button']"
                    ].join(",")
                );


            // =================================
            // VISIBLE COLOR CHECK
            // =================================
            // Correctly identifies transparent
            // colors such as:
            //
            // transparent
            // rgba(0,0,0,0)
            // rgba(255,255,255,0)
            // =================================

            function hasVisibleColor(color) {

                if (!color) {

                    return false;

                }


                const normalized =
                    color
                    .replace(
                        /\\s+/g,
                        ""
                    )
                    .toLowerCase();


                if (
                    normalized ===
                    "transparent"
                ) {

                    return false;

                }


                const rgbaMatch =
                    normalized.match(
                        /^rgba\\(\\d+,\\d+,\\d+,([0-9.]+)\\)$/
                    );


                if (
                    rgbaMatch
                ) {

                    const alpha =
                        parseFloat(
                            rgbaMatch[1]
                        );


                    return (
                        alpha > 0.01
                    );

                }


                return true;

            }


            // =================================
            // VISIBLE BORDER CHECK
            // =================================

            function hasVisibleBorder(
                width,
                borderStyle,
                color
            ) {

                const borderWidth =
                    parseFloat(
                        width
                    )
                    ||
                    0;


                if (
                    borderWidth <= 0
                ) {

                    return false;

                }


                if (
                    borderStyle === "none"
                    ||
                    borderStyle === "hidden"
                ) {

                    return false;

                }


                if (
                    !hasVisibleColor(
                        color
                    )
                ) {

                    return false;

                }


                return true;

            }


            // =================================
            // CHECK EACH BUTTON CANDIDATE
            // =================================

            for (
                const button of
                buttons
            ) {

                if (
                    !isVisible(
                        button
                    )
                    ||
                    shouldIgnore(
                        button
                    )
                ) {

                    continue;

                }


                const rect =
                    button.getBoundingClientRect();


                const style =
                    window.getComputedStyle(
                        button
                    );


                const text =
                    cleanText(
                        button.innerText
                        ||
                        button.value
                        ||
                        button.getAttribute(
                            "aria-label"
                        )
                        ||
                        ""
                    );


                // =================================
                // IGNORE EMPTY TECHNICAL ELEMENTS
                // =================================

                if (
                    !text
                    &&
                    rect.width < 10
                    &&
                    rect.height < 10
                ) {

                    continue;

                }


                const tag =
                    button.tagName.toLowerCase();


                // =================================
                // NATIVE BUTTON
                // =================================

                const isNativeButton =
                    (
                        tag === "button"
                        ||
                        (
                            tag === "input"
                            &&
                            (
                                button.type === "submit"
                                ||
                                button.type === "button"
                            )
                        )
                    );


                // =================================
                // BUTTON ROLE
                // =================================

                const hasButtonRole =
                    (
                        button.getAttribute(
                            "role"
                        )
                        ===
                        "button"
                    );


                // =================================
                // CLASS INFORMATION
                // =================================

                const classText =
                    (
                        typeof button.className
                        ===
                        "string"
                            ?
                            button.className
                            :
                            ""
                    )
                    .toLowerCase();


                // =================================
                // PADDING
                // =================================

                const paddingTop =
                    parseFloat(
                        style.paddingTop
                    )
                    ||
                    0;


                const paddingBottom =
                    parseFloat(
                        style.paddingBottom
                    )
                    ||
                    0;


                const paddingLeft =
                    parseFloat(
                        style.paddingLeft
                    )
                    ||
                    0;


                const paddingRight =
                    parseFloat(
                        style.paddingRight
                    )
                    ||
                    0;


                const verticalPadding =
                    paddingTop
                    +
                    paddingBottom;


                const horizontalPadding =
                    paddingLeft
                    +
                    paddingRight;


                // Horizontal padding alone is
                // not enough to call something
                // a button.
                const hasButtonPadding =
                    (
                        verticalPadding >= 8
                    );


                // =================================
                // BACKGROUND
                // =================================

                const hasBackground =
                    hasVisibleColor(
                        style.backgroundColor
                    );


                // =================================
                // BORDER
                // =================================

                const hasBorder =
                    (
                        hasVisibleBorder(
                            style.borderTopWidth,
                            style.borderTopStyle,
                            style.borderTopColor
                        )
                        ||
                        hasVisibleBorder(
                            style.borderRightWidth,
                            style.borderRightStyle,
                            style.borderRightColor
                        )
                        ||
                        hasVisibleBorder(
                            style.borderBottomWidth,
                            style.borderBottomStyle,
                            style.borderBottomColor
                        )
                        ||
                        hasVisibleBorder(
                            style.borderLeftWidth,
                            style.borderLeftStyle,
                            style.borderLeftColor
                        )
                    );


                // =================================
                // REAL CTA CLASSIFICATION
                // =================================
                //
                // Elementor sometimes uses:
                //
                // .elementor-button
                //
                // on links that visually behave
                // like ordinary text links.
                //
                // Therefore class name alone does
                // NOT make an element a CTA.
                // =================================

                const isAnchor =
                    (
                        tag === "a"
                    );


                let isRealCTA =
                    false;


                // Native buttons always count
                if (
                    isNativeButton
                    ||
                    hasButtonRole
                ) {

                    isRealCTA =
                        true;

                }


                // Anchor links must visually
                // behave like buttons
                else if (
                    isAnchor
                ) {

                    isRealCTA =
                        (
                            hasBackground
                            ||
                            hasBorder
                            ||
                            verticalPadding >= 8
                        );

                }


                // Custom non-anchor elements
                else {

                    isRealCTA =
                        (
                            hasButtonPadding
                            ||
                            hasBackground
                            ||
                            hasBorder
                        );

                }


                // =================================
                // SKIP NORMAL TEXT LINKS
                // =================================

                if (
                    !isRealCTA
                ) {

                    continue;

                }


                // =================================
                // SMALL CTA CHECK
                // =================================
                //
                // This module uses 24px as a
                // practical minimum heuristic.
                // Accessibility touch-target checks
                // can use their own threshold later.
                // =================================

                if (
                    rect.width < 24
                    ||
                    rect.height < 24
                ) {

                    result.smallButtons.push({

                        tag:
                            button.tagName,

                        text:
                            text.substring(
                                0,
                                100
                            ),

                        width:
                            Math.round(
                                rect.width
                            ),

                        height:
                            Math.round(
                                rect.height
                            ),

                        className:
                            classText.substring(
                                0,
                                120
                            ),

                        verticalPadding:
                            Math.round(
                                verticalPadding * 10
                            ) / 10,

                        horizontalPadding:
                            Math.round(
                                horizontalPadding * 10
                            ) / 10,

                        background:
                            style.backgroundColor,

                        border:
                            hasBorder

                    });

                }

            }


            return result;

        }
    """)

    # =====================================
    # DISPLAY HELPER
    # =====================================

    def show_issues(
        title,
        issues,
        formatter,
        limit=10
    ):

        if not issues:

            print(
                f"PASS | {title}"
            )

            return


        print(
            f"WARNING | {title} |",
            len(issues),
            "issue(s)"
        )


        for index, issue in enumerate(
            issues[:limit],
            start=1
        ):

            print(
                f"{index}.",
                formatter(
                    issue
                )
            )


        if len(issues) > limit:

            print(
                "   ...",
                len(issues) - limit,
                "more"
            )

    # =====================================
    # SMALL TEXT
    # =====================================

    show_issues(

        "Very Small Text",

        results[
            "smallText"
        ],

        lambda item: (
            f"{item['tag']} | "
            f"{item['fontSize']}px | "
            f"{item['text']}"
        )

    )

    # =====================================
    # TEXT CLIPPING
    # =====================================

    show_issues(

        "Text Clipping",

        results[
            "clippedText"
        ],

        lambda item: (
            f"{item['tag']} | "
            f"{item['direction']} | "
            f"{item['text']}"
        )

    )

    # =====================================
    # LINE HEIGHT
    # =====================================

    show_issues(

        "Line Height",

        results[
            "tightLineHeight"
        ],

        lambda item: (
            f"{item['tag']} | "
            f"font {item['fontSize']}px | "
            f"line-height {item['lineHeight']}px | "
            f"{item['text']}"
        )

    )

    # =====================================
    # WIDE PARAGRAPHS
    # =====================================

    show_issues(

        "Wide Paragraphs",

        results[
            "wideParagraphs"
        ],

        lambda item: (
            f"{item['width']}px | "
            f"{item['text']}"
        )

    )

    # =====================================
    # DISTORTED IMAGES
    # =====================================

    show_issues(

        "Image Distortion",

        results[
            "distortedImages"
        ],

        lambda item: (
            f"{item['displayed']} displayed | "
            f"{item['natural']} original | "
            f"{item['differencePercent']}% ratio difference | "
            f"{item['alt'] or item['src']}"
        )

    )

    # =====================================
    # SMALL BUTTONS / CTAS
    # =====================================

    show_issues(

        "Small Buttons / CTAs",

        results[
            "smallButtons"
        ],

        lambda item: (
            f"{item['width']}x{item['height']}px | "
            f"{item['text']}"
        )

    )

    # =====================================
    # SUMMARY
    # =====================================

    total_issues = (

        len(
            results[
                "smallText"
            ]
        )

        +

        len(
            results[
                "clippedText"
            ]
        )

        +

        len(
            results[
                "tightLineHeight"
            ]
        )

        +

        len(
            results[
                "wideParagraphs"
            ]
        )

        +

        len(
            results[
                "distortedImages"
            ]
        )

        +

        len(
            results[
                "smallButtons"
            ]
        )

    )

    print(
        "\nLayout & Design Summary"
    )

    print(
        "Very Small Text:",
        len(
            results[
                "smallText"
            ]
        )
    )

    print(
        "Clipped Text:",
        len(
            results[
                "clippedText"
            ]
        )
    )

    print(
        "Tight Line Height:",
        len(
            results[
                "tightLineHeight"
            ]
        )
    )

    print(
        "Wide Paragraphs:",
        len(
            results[
                "wideParagraphs"
            ]
        )
    )

    print(
        "Distorted Images:",
        len(
            results[
                "distortedImages"
            ]
        )
    )

    print(
        "Small Buttons / CTAs:",
        len(
            results[
                "smallButtons"
            ]
        )
    )

    # =====================================
    # FINAL RESULT
    # =====================================

    if (
        total_issues == 0
    ):

        print(
            "\nPASS | Layout & Design |",
            "No obvious layout/design issues detected"
        )

    else:

        print(
            "\nWARNING | Layout & Design |",
            total_issues,
            "possible issue(s) require review"
        )

    print(
        "\nLayout & Design Check Complete"
    )

    print(
        "------------------------------"
    )