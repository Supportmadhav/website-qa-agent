from difflib import SequenceMatcher

def check_google_translate(page):
    """
    Check whether a Google/GTranslate language
    translator is present and basically configured.

    Checks:
    1. Translator container/widget detection
    2. Google Translate / GTranslate scripts
    3. Language selector detection
    4. Available language options
    5. Translator visibility
    6. Broken translator resources
    """

    print("\nGoogle Language Translator Check")
    print("--------------------------------")

    # =====================================
    # WAIT FOR TRANSLATOR INITIALIZATION
    # =====================================

    try:

        page.wait_for_function(
            """
            () => {

                const combo =
                    document.querySelector(
                        ".goog-te-combo"
                    );

                const translateElements =
                    document.querySelectorAll(
                        [
                            ".goog-te-combo",
                            ".gtranslate_wrapper",
                            ".gt_switcher",
                            ".glink",
                            "#google_translate_element"
                        ].join(",")
                    );

                // Continue once translator UI exists.
                // The Google combo may remain empty when
                // a custom translation interface is used.
                return (
                    combo !== null ||
                    translateElements.length > 0
                );
            }
            """,
            timeout=5000
        )

    except Exception:

        # Do not stop the QA scan if Google
        # Translate initializes slowly.
        pass


    # Give Google's script a little more time
    # to populate dynamic controls.
    page.wait_for_timeout(
        1500
    )    


    # =====================================
    # DETECT TRANSLATOR
    # =====================================

    translator_data = page.evaluate("""
        () => {

            const result = {
                containers: [],
                selectors: [],
                scripts: [],
                links: [],
                languageOptions: [],
                visible: false
            };


            // =================================
            // COMMON TRANSLATOR CONTAINERS
            // =================================

            const containerSelectors = [
                "#google_translate_element",
                ".google_translate_element",
                ".goog-te-gadget",
                ".goog-te-combo",
                ".gtranslate_wrapper",
                ".gt_switcher",
                ".gt_selector",
                ".glink",
                "[class*='gtranslate']",
                "[id*='google_translate']"
            ];


            for (
                const selector of
                containerSelectors
            ) {

                const elements =
                    document.querySelectorAll(
                        selector
                    );

                for (
                    const element of
                    elements
                ) {

                    const rect =
                        element.getBoundingClientRect();

                    const style =
                        window.getComputedStyle(
                            element
                        );


                    const isVisible = (
                        style.display !== "none" &&
                        style.visibility !== "hidden" &&
                        Number(style.opacity) !== 0 &&
                        rect.width > 0 &&
                        rect.height > 0
                    );


                    result.containers.push({
                        selector:
                            selector,

                        tag:
                            element.tagName,

                        className:
                            typeof element.className === "string"
                                ? element.className
                                : "",

                        visible:
                            isVisible
                    });


                    if (isVisible) {
                        result.visible = true;
                    }
                }
            }


            // =================================
            // SELECT LANGUAGE ELEMENTS
            // =================================

            const selects =
                Array.from(
                    document.querySelectorAll(
                        "select"
                    )
                );


            for (
                const select of
                selects
            ) {

                const text =
                    (
                        select.innerText ||
                        ""
                    ).toLowerCase();

                const classText =
                    (
                        typeof select.className ===
                        "string"
                            ? select.className
                            : ""
                    ).toLowerCase();

                const idText =
                    (
                        select.id ||
                        ""
                    ).toLowerCase();


                const looksLikeTranslator = (
                    classText.includes(
                        "goog-te"
                    ) ||
                    classText.includes(
                        "gtranslate"
                    ) ||
                    idText.includes(
                        "translate"
                    ) ||
                    text.includes(
                        "english"
                    ) ||
                    text.includes(
                        "language"
                    )
                );


                if (!looksLikeTranslator) {
                    continue;
                }


                const options =
                    Array.from(
                        select.options
                    );


                result.selectors.push({
                    tag:
                        select.tagName,

                    id:
                        select.id || "",

                    className:
                        typeof select.className ===
                        "string"
                            ? select.className
                            : "",

                    optionCount:
                        options.length
                });


                for (
                    const option of
                    options
                ) {

                    const name =
                        (
                            option.textContent ||
                            ""
                        ).trim();

                    const value =
                        option.value || "";


                    if (name) {

                        result.languageOptions.push({
                            name:
                                name,

                            value:
                                value
                        });
                    }
                }
            }


            // =================================
            // TRANSLATOR LINKS
            // =================================

            const links =
                Array.from(
                    document.querySelectorAll(
                        "a"
                    )
                );


            for (
                const link of
                links
            ) {

                const href =
                    (
                        link.href ||
                        ""
                    ).toLowerCase();

                const className =
                    (
                        typeof link.className ===
                        "string"
                            ? link.className
                            : ""
                    ).toLowerCase();

                const onclick =
                    (
                        link.getAttribute(
                            "onclick"
                        ) ||
                        ""
                    ).toLowerCase();


                if (
                    href.includes(
                        "translate.google"
                    ) ||
                    className.includes(
                        "gtranslate"
                    ) ||
                    className.includes(
                        "glink"
                    ) ||
                    onclick.includes(
                        "dotranslate"
                    ) ||
                    onclick.includes(
                        "gtranslate"
                    )
                ) {

                    const rect =
                        link.getBoundingClientRect();

                    const style =
                        window.getComputedStyle(
                            link
                        );

                    const isVisible = (
                        style.display !== "none" &&
                        style.visibility !== "hidden" &&
                        Number(style.opacity) !== 0 &&
                        rect.width > 0 &&
                        rect.height > 0
                    );


                    result.links.push({
                        text:
                            (
                                link.innerText ||
                                link.getAttribute(
                                    "title"
                                ) ||
                                ""
                            )
                            .trim()
                            .slice(
                                0,
                                80
                            ),

                        href:
                            link.href || "",

                        visible:
                            isVisible
                    });


                    if (isVisible) {
                        result.visible = true;
                    }
                }
            }


            // =================================
            // TRANSLATOR SCRIPTS
            // =================================

            const scripts =
                Array.from(
                    document.querySelectorAll(
                        "script[src]"
                    )
                );


            for (
                const script of
                scripts
            ) {

                const src =
                    script.src || "";

                const srcLower =
                    src.toLowerCase();


                if (
                    srcLower.includes(
                        "translate.google"
                    ) ||
                    srcLower.includes(
                        "translate.googleapis"
                    ) ||
                    srcLower.includes(
                        "gtranslate"
                    )
                ) {

                    result.scripts.push(
                        src
                    );
                }
            }


            return result;
        }
    """)


    # =====================================
    # BASIC DETECTION
    # =====================================

    detected = (
        len(
            translator_data[
                "containers"
            ]
        ) > 0
        or
        len(
            translator_data[
                "selectors"
            ]
        ) > 0
        or
        len(
            translator_data[
                "scripts"
            ]
        ) > 0
        or
        len(
            translator_data[
                "links"
            ]
        ) > 0
    )


    if detected:

        print(
            "PASS | Translator Detection |",
            "Language translator detected"
        )

    else:

        print(
            "FAIL | Translator Detection |",
            "No Google/GTranslate translator detected"
        )

        print(
            "\nGoogle Language Translator Check Complete"
        )

        print(
            "-----------------------------------------"
        )

        return


    # =====================================
    # TRANSLATOR CONTAINER
    # =====================================

    containers = translator_data[
        "containers"
    ]


    if containers:

        print(
            "PASS | Translator Container |",
            len(containers),
            "translator-related element(s) detected"
        )

    else:

        print(
            "INFO | Translator Container |",
            "No standard translator container found"
        )


    # =====================================
    # VISIBILITY
    # =====================================

    if translator_data[
        "visible"
    ]:

        print(
            "PASS | Translator Visibility |",
            "Visible translator element detected"
        )

    else:

        print(
            "WARNING | Translator Visibility |",
            "Translator detected but no standard visible container found"
        )


    # =====================================
    # LANGUAGE SELECTOR
    # =====================================

    selectors = translator_data[
        "selectors"
    ]


    if selectors:

        print(
            "PASS | Language Selector |",
            len(selectors),
            "selector(s) detected"
        )

        for selector in selectors[:5]:

            print(
                "   ",
                selector["tag"],
                "| ID:",
                selector["id"],
                "| Class:",
                selector["className"],
                "| Options:",
                selector["optionCount"]
            )

    else:

        print(
            "INFO | Language Selector |",
            "No standard <select> language selector detected"
        )


    # =====================================
    # LANGUAGE OPTIONS
    # =====================================

    language_options = (
        translator_data[
            "languageOptions"
        ]
    )


    # Remove duplicate languages
    unique_languages = []

    seen_languages = set()


    for language in language_options:

        name = language[
            "name"
        ]

        key = name.lower()

        if key in seen_languages:
            continue

        seen_languages.add(
            key
        )

        unique_languages.append(
            language
        )


    if unique_languages:

        print(
            "PASS | Language Options |",
            len(unique_languages),
            "language option(s)"
        )

        language_names = [
            item["name"]
            for item in
            unique_languages[:15]
        ]

        print(
            "   ",
            ", ".join(
                language_names
            )
        )

    else:

        print(
            "INFO | Language Options |",
            "Languages may be loaded through a custom translator interface"
        )


    # =====================================
    # TRANSLATOR SCRIPTS
    # =====================================

    scripts = translator_data[
        "scripts"
    ]


    if scripts:

        print(
            "PASS | Translator Scripts |",
            len(scripts),
            "translator script(s) detected"
        )

        for script in scripts[:5]:

            print(
                "   ",
                script[:160]
            )

    else:

        print(
            "INFO | Translator Scripts |",
            "No external Google/GTranslate script URL detected"
        )


    # =====================================
    # TRANSLATOR LINKS
    # =====================================

    translator_links = (
        translator_data[
            "links"
        ]
    )


    if translator_links:

        print(
            "PASS | Translator Links |",
            len(translator_links),
            "translator-related link(s) detected"
        )

    else:

        print(
            "INFO | Translator Links |",
            "No translator links detected"
        )


    # =====================================
    # CHECK TRANSLATOR RESOURCES
    # =====================================

    translator_resource_errors = (
        page.evaluate("""
            () => {

                return performance
                    .getEntriesByType(
                        "resource"
                    )
                    .filter((resource) => {

                        const url =
                            (
                                resource.name ||
                                ""
                            ).toLowerCase();

                        return (
                            url.includes(
                                "translate.google"
                            ) ||
                            url.includes(
                                "translate.googleapis"
                            ) ||
                            url.includes(
                                "gtranslate"
                            )
                        );
                    })
                    .map((resource) => ({
                        url:
                            resource.name,

                        duration:
                            Math.round(
                                resource.duration
                            ),

                        size:
                            resource.transferSize || 0
                    }));
            }
        """)
    )


    if translator_resource_errors:

        print(
            "PASS | Translator Resources |",
            len(
                translator_resource_errors
            ),
            "translator resource(s) loaded"
        )

    else:

        print(
            "INFO | Translator Resources |",
            "No translator network resources found in performance data"
        )


    # =====================================
    # FUNCTIONAL TRANSLATION TEST
    # =====================================

    print(
        "\nTranslation Function Test"
    )

    original_url = page.url


    # -------------------------------------
    # GET PAGE CONTENT BEFORE TRANSLATION
    # -------------------------------------

    def get_main_page_text():
        """
        Get visible page content while excluding
        Google Translate interface elements.
        """

        return page.evaluate("""
            () => {

                const source =
                    document.querySelector("main")
                    || document.body;

                if (!source) {
                    return "";
                }

                const clone =
                    source.cloneNode(true);


                // Remove elements that could change
                // independently of page translation.
                const removeSelectors = [
                    "script",
                    "style",
                    "noscript",
                    ".goog-te-gadget",
                    ".goog-te-combo",
                    ".goog-te-banner-frame",
                    ".skiptranslate",
                    ".gtranslate_wrapper",
                    ".gt_switcher"
                ];


                for (
                    const selector of
                    removeSelectors
                ) {

                    clone
                        .querySelectorAll(
                            selector
                        )
                        .forEach(
                            element =>
                                element.remove()
                        );
                }


                return (
                    clone.innerText || ""
                )
                .replace(
                    /\\s+/g,
                    " "
                )
                .trim();
            }
        """)


    before_translation = (
        get_main_page_text()
    )


    # =====================================
    # FIND GOOGLE TRANSLATE SELECTOR
    # =====================================

    translate_combo = page.locator(
        ".goog-te-combo"
    ).first


    if translate_combo.count() == 0:

        print(
            "WARNING | Translation Function |",
            "Google Translate selector not available"
        )

    else:

        # =====================================
        # CHECK SPANISH OPTION
        # =====================================

        spanish_available = page.evaluate("""
            () => {

                const combo =
                    document.querySelector(
                        ".goog-te-combo"
                    );

                if (!combo) {
                    return false;
                }

                return Array.from(
                    combo.options
                ).some(
                    option =>
                        option.value === "es"
                );
            }
        """)


        if not spanish_available:

            print(
                "WARNING | Translation Function |",
                "Spanish test language is not available"
            )

        else:

            try:

                # =====================================
                # SWITCH TO SPANISH
                # =====================================

                translate_combo.select_option(
                    "es"
                )

                print(
                    "INFO | Translation Test |",
                    "Selected Spanish (es)"
                )


                # Google Translate works
                # asynchronously, so allow it time
                # to change page content.
                page.wait_for_timeout(
                    5000
                )


                # =====================================
                # CHECK SELECTED LANGUAGE
                # =====================================

                selected_language = (
                    translate_combo
                    .input_value()
                )


                if selected_language == "es":

                    print(
                        "PASS | Language Selection |",
                        "Spanish selected successfully"
                    )

                else:

                    print(
                        "WARNING | Language Selection |",
                        "Expected es but found:",
                        selected_language
                    )


                # =====================================
                # GET CONTENT AFTER TRANSLATION
                # =====================================

                after_translation = (
                    get_main_page_text()
                )


                # =====================================
                # COMPARE PAGE CONTENT
                # =====================================

                if (
                    before_translation
                    and
                    after_translation
                ):

                    similarity = (
                        SequenceMatcher(
                            None,
                            before_translation[:10000],
                            after_translation[:10000]
                        )
                        .ratio()
                    )

                    changed_percent = (
                        100
                        -
                        similarity * 100
                    )


                    if changed_percent >= 10:

                        print(
                            "PASS | Translation Function |",
                            "Page content changed after translation",
                            "| Change:",
                            f"{changed_percent:.1f}%"
                        )

                    elif (
                        before_translation
                        !=
                        after_translation
                    ):

                        print(
                            "WARNING | Translation Function |",
                            "Only a small amount of page content changed",
                            "| Change:",
                            f"{changed_percent:.1f}%"
                        )

                    else:

                        print(
                            "FAIL | Translation Function |",
                            "Page content did not change after selecting Spanish"
                        )

                else:

                    print(
                        "WARNING | Translation Function |",
                        "Unable to compare page text"
                    )


            except Exception as error:

                print(
                    "FAIL | Translation Function |",
                    str(error)[:250]
                )


    # =====================================
    # RESTORE ORIGINAL PAGE
    # =====================================

    try:

        # Remove Google Translate cookie
        # so later QA checks are not performed
        # on the translated version.
        page.context.clear_cookies(
            name="googtrans"
        )

    except Exception:

        pass


    try:

        page.goto(
            original_url,
            wait_until="load",
            timeout=30000
        )

        page.wait_for_timeout(
            1000
        )

    except Exception:

        pass

    # =====================================
    # COMPLETE
    # =====================================

    print(
        "\nGoogle Language Translator Check Complete"
    )

    print(
        "-----------------------------------------"
    )