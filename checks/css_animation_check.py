def check_css_animations(page):
    """
    Check CSS animations and transitions on the page.

    Checks:
    - CSS animation properties
    - CSS transitions
    - Browser Web Animations API
    - Long animations
    - Infinite animations
    - Long transitions
    - prefers-reduced-motion support
    """

    print("\nCSS Animation Check")
    print("-------------------")


    # =====================================
    # COLLECT ANIMATION DATA
    # =====================================

    animation_data = page.evaluate("""
        () => {

            const elements = Array.from(
                document.querySelectorAll("body *")
            );

            const cssAnimations = [];
            const cssTransitions = [];
            const browserAnimations = [];


            // =================================
            // CSS ANIMATIONS & TRANSITIONS
            // =================================

            for (const el of elements) {

                const style =
                    window.getComputedStyle(el);

                const rect =
                    el.getBoundingClientRect();


                // Ignore hidden / zero-size elements
                if (
                    style.display === "none" ||
                    style.visibility === "hidden" ||
                    Number(style.opacity) === 0 ||
                    rect.width <= 0 ||
                    rect.height <= 0
                ) {
                    continue;
                }


                // =================================
                // CSS ANIMATION
                // =================================

                if (
                    style.animationName &&
                    style.animationName !== "none"
                ) {

                    cssAnimations.push({
                        tag:
                            el.tagName,

                        className:
                            typeof el.className === "string"
                                ? el.className
                                : "",

                        name:
                            style.animationName,

                        duration:
                            style.animationDuration,

                        delay:
                            style.animationDelay,

                        iteration:
                            style.animationIterationCount,

                        timing:
                            style.animationTimingFunction,

                        playState:
                            style.animationPlayState
                    });
                }


                // =================================
                // CSS TRANSITION
                // =================================

                const transitionDuration =
                    style.transitionDuration;

                if (
                    transitionDuration &&
                    transitionDuration !== "0s"
                ) {

                    cssTransitions.push({
                        tag:
                            el.tagName,

                        className:
                            typeof el.className === "string"
                                ? el.className
                                : "",

                        property:
                            style.transitionProperty,

                        duration:
                            transitionDuration,

                        delay:
                            style.transitionDelay,

                        timing:
                            style.transitionTimingFunction
                    });
                }
            }


            // =================================
            // WEB ANIMATIONS API
            // =================================

            try {

                const detectedAnimations =
                    document.getAnimations();

                for (
                    const animation of
                    detectedAnimations
                ) {

                    const effect =
                        animation.effect;

                    if (!effect) {
                        continue;
                    }


                    const target =
                        effect.target;

                    if (!target) {
                        continue;
                    }


                    let timing = {};

                    try {

                        timing =
                            effect.getComputedTiming();

                    }
                    catch (error) {

                        timing = {};
                    }


                    browserAnimations.push({
                        tag:
                            target.tagName || "",

                        className:
                            typeof target.className === "string"
                                ? target.className
                                : "",

                        playState:
                            animation.playState || "",

                        duration:
                            Number(
                                timing.duration
                            ) || 0,

                        progress:
                            timing.progress === null
                                ? null
                                : timing.progress,

                        currentTime:
                            Number(
                                animation.currentTime
                            ) || 0
                    });
                }

            }
            catch (error) {

                // Browser does not expose
                // animation information.
            }


            return {
                cssAnimations:
                    cssAnimations,

                cssTransitions:
                    cssTransitions,

                browserAnimations:
                    browserAnimations
            };
        }
    """)


    # =====================================
    # GET RESULTS
    # =====================================

    animations = animation_data[
        "cssAnimations"
    ]

    transitions = animation_data[
        "cssTransitions"
    ]

    browser_animations = animation_data[
        "browserAnimations"
    ]


    # =====================================
    # SUMMARY
    # =====================================

    print(
        "CSS Animations Found:",
        len(animations)
    )

    print(
        "CSS Transitions Found:",
        len(transitions)
    )

    print(
        "Browser Animations Detected:",
        len(browser_animations)
    )


    # =====================================
    # HELPER:
    # CONVERT CSS TIME TO SECONDS
    # =====================================

    def time_to_seconds(value):
        """
        Convert CSS duration values such as:
        500ms
        0.5s
        0.3s, 0.5s
        into seconds.
        """

        if not value:
            return 0

        values = value.split(",")

        durations = []

        for item in values:

            item = item.strip()

            try:

                if item.endswith("ms"):

                    durations.append(
                        float(item[:-2]) /
                        1000
                    )

                elif item.endswith("s"):

                    durations.append(
                        float(item[:-1])
                    )

            except ValueError:
                continue


        if not durations:
            return 0

        return max(durations)


    # =====================================
    # ANALYZE CSS ANIMATIONS
    # =====================================

    long_animations = []
    infinite_animations = []


    for animation in animations:

        duration = time_to_seconds(
            animation["duration"]
        )


        # Animation longer than 3 seconds
        if duration > 3:

            long_animations.append(
                animation
            )


        # Infinite / continuous animation
        iteration = (
            animation["iteration"]
            or ""
        ).lower()

        if "infinite" in iteration:

            infinite_animations.append(
                animation
            )


    # =====================================
    # LONG ANIMATION RESULT
    # =====================================

    if long_animations:

        print(
            "WARNING | Long CSS Animations |",
            len(long_animations),
            "animation(s) longer than 3 seconds"
        )

        for animation in long_animations[:10]:

            print(
                "   ",
                animation["tag"],
                "|",
                animation["className"],
                "|",
                animation["name"],
                "| Duration:",
                animation["duration"]
            )

    else:

        print(
            "PASS | Animation Duration |",
            "No excessive animation durations detected"
        )


    # =====================================
    # INFINITE ANIMATION RESULT
    # =====================================

    if infinite_animations:

        print(
            "INFO | Infinite Animations |",
            len(infinite_animations),
            "continuous animation(s) detected"
        )

        for animation in infinite_animations[:10]:

            print(
                "   ",
                animation["tag"],
                "|",
                animation["className"],
                "|",
                animation["name"],
                "| Duration:",
                animation["duration"]
            )

    else:

        print(
            "PASS | Infinite Animations |",
            "No continuous CSS animations detected"
        )


    # =====================================
    # ANALYZE CSS TRANSITIONS
    # =====================================

    long_transitions = []


    for transition in transitions:

        duration = time_to_seconds(
            transition["duration"]
        )

        if duration > 1:

            long_transitions.append(
                transition
            )


    # =====================================
    # LONG TRANSITION RESULT
    # =====================================

    if long_transitions:

        print(
            "WARNING | Long CSS Transitions |",
            len(long_transitions),
            "transition(s) longer than 1 second"
        )

        for transition in long_transitions[:10]:

            print(
                "   ",
                transition["tag"],
                "|",
                transition["className"],
                "|",
                transition["property"],
                "| Duration:",
                transition["duration"]
            )

    else:

        print(
            "PASS | Transition Duration |",
            "No unusually long transitions detected"
        )


    # =====================================
    # BROWSER ANIMATION DETAILS
    # =====================================

    running_browser_animations = []

    for animation in browser_animations:

        if animation[
            "playState"
        ] in [
            "running",
            "pending"
        ]:

            running_browser_animations.append(
                animation
            )


    if running_browser_animations:

        print(
            "INFO | Active Browser Animations |",
            len(running_browser_animations),
            "currently running"
        )

        for animation in (
            running_browser_animations[:10]
        ):

            duration = animation[
                "duration"
            ]

            print(
                "   ",
                animation["tag"],
                "|",
                animation["className"],
                "| State:",
                animation["playState"],
                "| Duration:",
                f"{duration:.0f} ms"
            )

    elif browser_animations:

        print(
            "INFO | Browser Animations |",
            len(browser_animations),
            "animation(s) registered but not currently running"
        )

    else:

        print(
            "INFO | Browser Animations |",
            "No browser animations currently registered"
        )


    # =====================================
    # PREFERS-REDUCED-MOTION CHECK
    # =====================================

    reduced_motion_support = page.evaluate("""
        () => {

            // =================================
            // CHECK ACCESSIBLE CSS RULES
            // =================================

            try {

                for (
                    const sheet of
                    document.styleSheets
                ) {

                    let rules;

                    try {

                        rules =
                            sheet.cssRules;

                    }
                    catch (error) {

                        // Cross-origin stylesheet.
                        // Browser may prevent reading it.
                        continue;
                    }


                    if (!rules) {
                        continue;
                    }


                    for (
                        const rule of rules
                    ) {

                        const cssText =
                            rule.cssText || "";

                        if (
                            cssText.includes(
                                "prefers-reduced-motion"
                            )
                        ) {
                            return true;
                        }


                        if (
                            rule.media &&
                            rule.media.mediaText &&
                            rule.media.mediaText.includes(
                                "prefers-reduced-motion"
                            )
                        ) {
                            return true;
                        }
                    }
                }

            }
            catch (error) {
                // Ignore CSSOM errors
            }


            // =================================
            // CHECK INLINE STYLE TAGS
            // =================================

            const styleTags =
                Array.from(
                    document.querySelectorAll(
                        "style"
                    )
                );

            for (
                const styleTag of
                styleTags
            ) {

                if (
                    (
                        styleTag.textContent ||
                        ""
                    ).includes(
                        "prefers-reduced-motion"
                    )
                ) {
                    return true;
                }
            }


            return false;
        }
    """)


    if reduced_motion_support:

        print(
            "PASS | Reduced Motion |",
            "prefers-reduced-motion support detected"
        )

    else:

        print(
            "WARNING | Reduced Motion |",
            "No detectable prefers-reduced-motion CSS found"
        )


    # =====================================
    # COMPLETE
    # =====================================

    print(
        "\nCSS Animation Check Complete"
    )

    print(
        "----------------------------"
    )