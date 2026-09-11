import re

from spellchecker import SpellChecker


def check_content(page):
    """
    Extract meaningful visible website content and
    perform spelling analysis.

    Current checks:
    1. Trigger lazy / animated content
    2. Extract meaningful visible text
    3. Ignore navigation / translator / system content
    4. Remove duplicate text
    5. Count content blocks and words
    6. Detect likely spelling mistakes
    7. Ignore technical/company terms
    8. Handle valid hyphenated words

    Grammar analysis will be added separately.
    """

    print(
        "\nContent Grammar & Spelling Check"
    )

    print(
        "--------------------------------"
    )

    # =====================================
    # TRIGGER LAZY / ANIMATED CONTENT
    # =====================================
    # Elementor often hides entrance-animation
    # content until it enters the viewport.
    # Scroll through the page first so the
    # complete visible content becomes available.
    # =====================================

    try:

        page.evaluate("""
            async () => {

                const delay = (ms) =>
                    new Promise(
                        resolve =>
                            setTimeout(
                                resolve,
                                ms
                            )
                    );

                const pageHeight =
                    Math.max(
                        document.body.scrollHeight,
                        document.documentElement.scrollHeight
                    );

                const step =
                    Math.max(
                        Math.floor(
                            window.innerHeight * 0.75
                        ),
                        400
                    );

                for (
                    let y = 0;
                    y < pageHeight;
                    y += step
                ) {

                    window.scrollTo(
                        0,
                        y
                    );

                    await delay(
                        120
                    );
                }

                // Scroll completely to bottom
                window.scrollTo(
                    0,
                    pageHeight
                );

                await delay(
                    500
                );

                // Return to top
                window.scrollTo(
                    0,
                    0
                );

                await delay(
                    500
                );
            }
        """)

    except Exception:

        pass

    # =====================================
    # EXTRACT CLEAN PAGE CONTENT
    # =====================================

    content_data = page.evaluate("""
        () => {

            // =================================
            // AREAS TO IGNORE
            // =================================

            const ignoredSelectors = [

                "script",
                "style",
                "noscript",

                "nav",

                ".menu",
                ".menu-item",

                ".elementor-nav-menu",
                ".elementskit-navbar-nav",
                ".elementskit-menu-container",

                ".goog-te-gadget",
                ".goog-te-combo",
                ".skiptranslate",
                ".gtranslate_wrapper",
                ".gt_switcher",

                ".cookie",
                ".cookie-banner",
                ".cookie-notice",
                "[class*='cookie']",

                ".screen-reader-text",
                ".sr-only",

                "[aria-hidden='true']"
            ];


            // =================================
            // IGNORE CHECK
            // =================================

            function isIgnored(element) {

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

                        // Ignore invalid selector errors
                    }
                }

                return false;
            }


            // =================================
            // VISIBILITY CHECK
            // =================================

            function isVisible(element) {

                const rect =
                    element.getBoundingClientRect();

                const style =
                    window.getComputedStyle(
                        element
                    );

                return (
                    style.display !== "none" &&
                    style.visibility !== "hidden" &&
                    Number(style.opacity) !== 0 &&
                    rect.width > 0 &&
                    rect.height > 0
                );
            }


            // =================================
            // CLEAN TEXT
            // =================================

            function cleanText(text) {

                if (!text) {
                    return "";
                }

                return text
                    .replace(
                        /\\s+/g,
                        " "
                    )
                    .replace(
                        /\\u00A0/g,
                        " "
                    )
                    .trim();
            }


            // =================================
            // STORAGE
            // =================================

            const headings = [];

            const paragraphs = [];

            const listItems = [];

            const buttons = [];

            const uniqueText =
                new Set();


            // =================================
            // ADD UNIQUE CONTENT
            // =================================

            function addContent(
                collection,
                text,
                tag
            ) {

                const cleaned =
                    cleanText(
                        text
                    );

                if (!cleaned) {
                    return;
                }


                // Ignore tiny fragments
                if (
                    cleaned.length < 2
                ) {
                    return;
                }


                const key =
                    cleaned.toLowerCase();


                // Ignore duplicate content
                if (
                    uniqueText.has(
                        key
                    )
                ) {
                    return;
                }


                uniqueText.add(
                    key
                );


                collection.push({
                    tag:
                        tag,

                    text:
                        cleaned
                });
            }


            // =================================
            // HEADINGS
            // =================================

            const headingElements =
                Array.from(
                    document.querySelectorAll(
                        "h1, h2, h3, h4, h5, h6"
                    )
                );


            for (
                const element of
                headingElements
            ) {

                if (
                    !isVisible(element)
                    ||
                    isIgnored(element)
                ) {
                    continue;
                }


                addContent(
                    headings,
                    element.innerText,
                    element.tagName
                );
            }


            // =================================
            // PARAGRAPHS
            // =================================

            const paragraphElements =
                Array.from(
                    document.querySelectorAll(
                        "p"
                    )
                );


            for (
                const element of
                paragraphElements
            ) {

                if (
                    !isVisible(element)
                    ||
                    isIgnored(element)
                ) {
                    continue;
                }


                addContent(
                    paragraphs,
                    element.innerText,
                    "P"
                );
            }


            // =================================
            // LIST ITEMS
            // =================================

            const listElements =
                Array.from(
                    document.querySelectorAll(
                        "main li, article li, section li"
                    )
                );


            for (
                const element of
                listElements
            ) {

                if (
                    !isVisible(element)
                    ||
                    isIgnored(element)
                ) {
                    continue;
                }


                addContent(
                    listItems,
                    element.innerText,
                    "LI"
                );
            }


            // =================================
            // BUTTONS
            // =================================

            const buttonElements =
                Array.from(
                    document.querySelectorAll(
                        [
                            "button",
                            "input[type='submit']",
                            "input[type='button']"
                        ].join(",")
                    )
                );


            for (
                const element of
                buttonElements
            ) {

                if (
                    !isVisible(element)
                    ||
                    isIgnored(element)
                ) {
                    continue;
                }


                const buttonText = (
                    element.innerText
                    ||
                    element.value
                    ||
                    element.getAttribute(
                        "aria-label"
                    )
                    ||
                    ""
                );


                addContent(
                    buttons,
                    buttonText,
                    element.tagName
                );
            }


            return {
                headings:
                    headings,

                paragraphs:
                    paragraphs,

                listItems:
                    listItems,

                buttons:
                    buttons
            };
        }
    """)

    # =====================================
    # GET CONTENT GROUPS
    # =====================================

    headings = (
        content_data[
            "headings"
        ]
    )

    paragraphs = (
        content_data[
            "paragraphs"
        ]
    )

    list_items = (
        content_data[
            "listItems"
        ]
    )

    buttons = (
        content_data[
            "buttons"
        ]
    )

    # =====================================
    # BUILD COMPLETE CONTENT
    # =====================================

    all_content = (
        headings
        +
        paragraphs
        +
        list_items
        +
        buttons
    )

    # =====================================
    # CONTENT SUMMARY
    # =====================================

    print(
        "Headings:",
        len(headings)
    )

    print(
        "Paragraphs:",
        len(paragraphs)
    )

    print(
        "List Items:",
        len(list_items)
    )

    print(
        "Buttons:",
        len(buttons)
    )

    print(
        "Total Content Blocks:",
        len(all_content)
    )

    # =====================================
    # COUNT WORDS
    # =====================================

    total_words = 0

    for item in all_content:

        text = (
            item.get(
                "text",
                ""
            )
            or ""
        )

        words = re.findall(
            r"[A-Za-z]+(?:['’-][A-Za-z]+)*",
            text
        )

        total_words += len(
            words
        )

    print(
        "Approximate Words:",
        total_words
    )

    # =====================================
    # EMPTY CONTENT CHECK
    # =====================================

    if not all_content:

        print(
            "FAIL | Content Extraction |",
            "No meaningful visible content extracted"
        )

        print(
            "\nContent Grammar & Spelling Check Complete"
        )

        print(
            "-----------------------------------------"
        )

        return

    print(
        "PASS | Content Extraction |",
        len(all_content),
        "meaningful content block(s)"
    )

    # =====================================
    # CONTENT SAMPLE
    # =====================================

    print(
        "\nContent Sample"
    )

    print(
        "--------------"
    )

    for index, item in enumerate(
        all_content[:20],
        start=1
    ):

        text = (
            item["text"]
        )

        if len(text) > 180:

            text = (
                text[:177]
                + "..."
            )

        print(
            index,
            "|",
            item["tag"],
            "|",
            text
        )

    # =====================================
    # STORE CLEAN CONTENT
    # =====================================

    try:

        page._qa_content_blocks = (
            all_content
        )

    except Exception:

        pass

    # =====================================
    # SPELLING ANALYSIS
    # =====================================

    print(
        "\nSpelling Analysis"
    )

    print(
        "-----------------"
    )

    # =====================================
    # CREATE SPELL CHECKER
    # =====================================

    spell = SpellChecker(
        language="en"
    )

    # =====================================
    # CUSTOM VALID WORDS
    # =====================================
    # Company names, abbreviations and
    # engineering / industrial terminology.
    # =====================================

    custom_words = {

        # -------------------------------------
        # COMPANY / BRAND WORDS
        # -------------------------------------

        "vrishal",
        "vishal",
        "deepit",
        "pvt",
        "ltd",

        # -------------------------------------
        # ABBREVIATIONS
        # -------------------------------------

        "hse",
        "epc",

        # -------------------------------------
        # BUSINESS TERMS
        # -------------------------------------

        "inhouse",
        "in-house",

        "self-reliance",

        "world-class",

        "end-to-end",

        "one-stop",

        # -------------------------------------
        # ENGINEERING TERMS
        # -------------------------------------

        "skids",
        "tankages",

        "turnarounds",
        "shutdowns",

        "fabrication",

        "engineering",

        "industrial",

        "mechanical",

        "piping",

        "rotary",

        "modularization",

        "modularisation",

        "blasting-painting",

        "mega",

        "spools",

        "preventive"
    }

    # =====================================
    # LOAD CUSTOM WORDS
    # =====================================

    spell.word_frequency.load_words(
        custom_words
    )

    # =====================================
    # COLLECT WORD LOCATIONS
    # =====================================

    word_locations = {}

    for block_index, item in enumerate(
        all_content,
        start=1
    ):

        text = (
            item.get(
                "text",
                ""
            )
            or ""
        )

        words = re.findall(
            r"[A-Za-z]+(?:['’\-–—][A-Za-z]+)*",
            text
        )

        for word in words:

            clean_word = (
                word.strip(
                    "'’\\-–—"
                )
            )

            if not clean_word:
                continue

            # =====================================
            # IGNORE VERY SHORT WORDS
            # =====================================

            if (
                len(clean_word) <= 2
            ):
                continue

            # =====================================
            # IGNORE ACRONYMS
            # =====================================
            # HSE
            # API
            # HVAC
            # EPC
            # etc.
            # =====================================

            if (
                clean_word.isupper()
                and
                len(clean_word) <= 8
            ):
                continue

            normalized = (
                clean_word.lower()
            )

            # =====================================
            # CUSTOM WORD WHITELIST
            # =====================================

            normalized_compact = (
                normalized
                .replace(
                    "-",
                    ""
                )
                .replace(
                    "–",
                    ""
                )
                .replace(
                    "—",
                    ""
                )
            )

            if (
                normalized
                in custom_words
                or
                normalized_compact
                in custom_words
            ):
                continue

            # =====================================
            # VALID HYPHENATED WORDS
            # =====================================
            # Examples:
            #
            # self-reliant
            # world-class
            # in-house
            # end-to-end
            #
            # If every part is a recognized
            # English word, ignore the compound.
            # =====================================

            if (
                "-" in normalized
                or
                "–" in normalized
                or
                "—" in normalized
            ):

                word_parts = re.split(
                    r"[-–—]",
                    normalized
                )

                word_parts = [
                    part
                    for part in word_parts
                    if part
                ]

                if word_parts:

                    unknown_parts = (
                        spell.unknown(
                            word_parts
                        )
                    )

                    if not unknown_parts:
                        continue

            # =====================================
            # CREATE WORD LOCATION ENTRY
            # =====================================
            # IMPORTANT:
            # setdefault must happen before
            # append to prevent KeyError.
            # =====================================

            word_locations.setdefault(
                normalized,
                []
            )

            # =====================================
            # STORE WORD LOCATION
            # =====================================

            word_locations[
                normalized
            ].append(
                {
                    "original":
                        clean_word,

                    "block":
                        block_index,

                    "tag":
                        item["tag"],

                    "text":
                        text
                }
            )

    # =====================================
    # FIND UNKNOWN WORDS
    # =====================================

    all_words = set(
        word_locations.keys()
    )

    unknown_words = (
        spell.unknown(
            all_words
        )
    )

    # =====================================
    # BUILD SPELLING ISSUES
    # =====================================

    spelling_issues = []

    for word in sorted(
        unknown_words
    ):

        locations = (
            word_locations.get(
                word,
                []
            )
        )

        if not locations:
            continue

        try:

            suggestion = (
                spell.correction(
                    word
                )
            )

        except Exception:

            suggestion = None

        # =====================================
        # NO USEFUL SUGGESTION
        # =====================================

        if not suggestion:
            continue

        if (
            suggestion.lower()
            ==
            word.lower()
        ):
            continue

        spelling_issues.append(
            {
                "word":
                    locations[0][
                        "original"
                    ],

                "suggestion":
                    suggestion,

                "locations":
                    locations
            }
        )

    # =====================================
    # SPELLING RESULT
    # =====================================

    if spelling_issues:

        print(
            "WARNING | Spelling |",
            len(spelling_issues),
            "possible spelling issue(s)"
        )

        for issue in spelling_issues[
            :20
        ]:

            location = (
                issue[
                    "locations"
                ][0]
            )

            print(
                "\nWord |",
                issue["word"]
            )

            print(
                "Suggestion |",
                issue[
                    "suggestion"
                ]
            )

            print(
                "Location |",
                location[
                    "tag"
                ],
                "| Block",
                location[
                    "block"
                ]
            )

            print(
                "Content |",
                location[
                    "text"
                ][:180]
            )

            occurrence_count = (
                len(
                    issue[
                        "locations"
                    ]
                )
            )

            if (
                occurrence_count > 1
            ):

                print(
                    "Occurrences |",
                    occurrence_count
                )

    else:

        print(
            "PASS | Spelling |",
            "No likely spelling mistakes detected"
        )

    # =====================================
    # SPELLING SUMMARY
    # =====================================

    print(
        "\nSpelling Summary"
    )

    print(
        "Unique Words Checked:",
        len(all_words)
    )

    print(
        "Possible Issues:",
        len(spelling_issues)
    )

    # =====================================
    # GRAMMAR STATUS
    # =====================================

    print(
        "\nINFO | Grammar Analysis |",
        "Grammar engine not added yet"
    )

    # =====================================
    # COMPLETE
    # =====================================

    print(
        "\nContent Grammar & Spelling Check Complete"
    )

    print(
        "-----------------------------------------"
    )