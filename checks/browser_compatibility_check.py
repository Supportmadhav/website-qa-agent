import json
import time
from urllib.parse import urlparse


DESKTOP_VIEWPORT = {
    "width": 1366,
    "height": 768,
}

RESPONSIVE_VIEWPORTS = [
    {
        "label": "Mobile",
        "width": 390,
        "height": 844,
    },
    {
        "label": "Tablet",
        "width": 768,
        "height": 1024,
    },
    {
        "label": "Desktop",
        "width": 1366,
        "height": 768,
    },
]


CRITERIA = [
    # =====================================
    # 2. VISUAL / LAYOUT CONSISTENCY
    # =====================================
    {
        "group": "2. Visual / Layout Consistency",
        "id": "layout_render",
        "label": "Page layout renders correctly",
    },
    {
        "group": "2. Visual / Layout Consistency",
        "id": "fonts",
        "label": "Fonts render consistently",
    },
    {
        "group": "2. Visual / Layout Consistency",
        "id": "images_icons_svg",
        "label": "Images, icons and SVGs display properly",
    },
    {
        "group": "2. Visual / Layout Consistency",
        "id": "animations",
        "label": "CSS animations / transitions",
    },
    {
        "group": "2. Visual / Layout Consistency",
        "id": "responsive",
        "label": "Responsive breakpoints",
    },
    {
        "group": "2. Visual / Layout Consistency",
        "id": "print_styles",
        "label": "Print styles",
    },

    # =====================================
    # 3. FUNCTIONALITY TESTING
    # =====================================
    {
        "group": "3. Functionality Testing",
        "id": "javascript_features",
        "label": "JavaScript features execute",
    },
    {
        "group": "3. Functionality Testing",
        "id": "forms",
        "label": "Forms: validation / submission / autofill",
    },
    {
        "group": "3. Functionality Testing",
        "id": "interactive_elements",
        "label": "Interactive elements",
    },
    {
        "group": "3. Functionality Testing",
        "id": "third_party_embeds",
        "label": "Third-party embeds",
    },
    {
        "group": "3. Functionality Testing",
        "id": "storage",
        "label": "Local storage / cookies / session",
    },
    {
        "group": "3. Functionality Testing",
        "id": "uploads_downloads",
        "label": "File uploads / downloads",
    },

    # =====================================
    # 4. PERFORMANCE
    # =====================================
    {
        "group": "4. Performance",
        "id": "page_load_time",
        "label": "Page load time",
    },
    {
        "group": "4. Performance",
        "id": "js_execution_speed",
        "label": "JavaScript execution speed",
    },
    {
        "group": "4. Performance",
        "id": "memory_usage",
        "label": "Memory usage",
    },
    {
        "group": "4. Performance",
        "id": "slow_3g",
        "label": "Slow 3G simulation",
    },

    # =====================================
    # 5. CSS / HTML FEATURE SUPPORT
    # =====================================
    {
        "group": "5. CSS / HTML Feature Support",
        "id": "caniuse_runtime",
        "label": "Detected features / Can I Use review",
    },
    {
        "group": "5. CSS / HTML Feature Support",
        "id": "vendor_prefixes",
        "label": "Vendor prefixes",
    },
    {
        "group": "5. CSS / HTML Feature Support",
        "id": "grid_flex",
        "label": "CSS Grid / Flexbox support",
    },
    {
        "group": "5. CSS / HTML Feature Support",
        "id": "css_variables",
        "label": "CSS custom properties (variables)",
    },

    # =====================================
    # 6. JAVASCRIPT API SUPPORT
    # =====================================
    {
        "group": "6. JavaScript API Support",
        "id": "fetch_api",
        "label": "Fetch API",
    },
    {
        "group": "6. JavaScript API Support",
        "id": "promise_async",
        "label": "Promises / async-await",
    },
    {
        "group": "6. JavaScript API Support",
        "id": "dom_apis",
        "label": "DOM APIs: closest / IntersectionObserver",
    },
    {
        "group": "6. JavaScript API Support",
        "id": "polyfill_needs",
        "label": "Polyfill needs",
    },

    # =====================================
    # 7. ACCESSIBILITY
    # =====================================
    {
        "group": "7. Accessibility Across Browsers",
        "id": "screen_reader",
        "label": "Screen reader behavior",
    },
    {
        "group": "7. Accessibility Across Browsers",
        "id": "keyboard_navigation",
        "label": "Keyboard navigation",
    },
    {
        "group": "7. Accessibility Across Browsers",
        "id": "focus_states",
        "label": "Focus states",
    },

    # =====================================
    # 8. ERROR HANDLING
    # =====================================
    {
        "group": "8. Error Handling",
        "id": "console_errors_warnings",
        "label": "Console errors / warnings",
    },
    {
        "group": "8. Error Handling",
        "id": "graceful_degradation",
        "label": "Graceful degradation",
    },
    {
        "group": "8. Error Handling",
        "id": "feature_detection",
        "label": "Feature detection / Modernizr",
    },
]


def _cell(
    status,
    detail,
    value=None,
):
    return {
        "status": status,
        "detail": str(
            detail
            or
            ""
        ),
        "value": value,
    }


def _status_label(
    status,
):
    return {
        "pass": "PASS",
        "warning": "WARNING",
        "fail": "FAIL",
        "info": "INFO",
        "manual": "MANUAL",
    }.get(
        status,
        "INFO",
    )


def _http_cell(
    status_code,
):
    if status_code is None:
        return _cell(
            "warning",
            "No main document HTTP response was captured.",
        )

    if 200 <= status_code < 400:
        return _cell(
            "pass",
            f"HTTP {status_code}",
            status_code,
        )

    return _cell(
        "fail",
        f"HTTP {status_code}",
        status_code,
    )


def _layout_snapshot(
    page,
):
    return page.evaluate(
        """
        () => {
            const ignoredSelector = [
                "svg",
                "path",
                "g",
                "canvas",
                "noscript",
                "template",
                "script",
                "style",
                "iframe",
                "[aria-hidden='true']",
                ".sr-only",
                ".screen-reader-text",
                ".visually-hidden",
                ".swiper",
                ".swiper-wrapper",
                ".swiper-slide",
                ".slick-list",
                ".slick-track",
                ".slick-slide",
                ".elementskit-menu-container",
                ".elementskit-menu-offcanvas-elements",
                ".elementor-motion-effects-container",
                ".elementor-motion-effects-layer"
            ].join(",");

            const root =
                document.documentElement;

            const clientWidth =
                root.clientWidth
                ||
                window.innerWidth;

            const scrollWidth =
                Math.max(
                    root.scrollWidth || 0,
                    document.body
                        ? document.body.scrollWidth
                        : 0
                );

            const pageOverflowPx =
                scrollWidth - clientWidth;

            const pageHasHorizontalScroll =
                pageOverflowPx > 24;

            function visible(element) {
                const style =
                    getComputedStyle(
                        element
                    );

                const rect =
                    element.getBoundingClientRect();

                return (
                    style.display !== "none"
                    &&
                    style.visibility !== "hidden"
                    &&
                    Number(
                        style.opacity
                    ) !== 0
                    &&
                    rect.width > 1
                    &&
                    rect.height > 1
                );
            }

            function clippedByAncestor(element) {
                let current =
                    element.parentElement;

                while (
                    current
                    &&
                    current !== document.body
                ) {
                    const style =
                        getComputedStyle(
                            current
                        );

                    const overflowX =
                        style.overflowX
                        ||
                        style.overflow;

                    if (
                        overflowX === "hidden"
                        ||
                        overflowX === "clip"
                    ) {
                        return true;
                    }

                    current =
                        current.parentElement;
                }

                return false;
            }

            const offenders = [];

            if (pageHasHorizontalScroll) {
                for (
                    const element of document.querySelectorAll(
                        "body *"
                    )
                ) {
                    if (
                        offenders.length >= 8
                    ) {
                        break;
                    }

                    if (
                        element.matches(
                            ignoredSelector
                        )
                        ||
                        element.closest(
                            ignoredSelector
                        )
                    ) {
                        continue;
                    }

                    if (
                        !visible(
                            element
                        )
                    ) {
                        continue;
                    }

                    if (
                        clippedByAncestor(
                            element
                        )
                    ) {
                        continue;
                    }

                    const style =
                        getComputedStyle(
                            element
                        );

                    if (
                        style.position === "fixed"
                        ||
                        style.position === "sticky"
                    ) {
                        continue;
                    }

                    const rect =
                        element.getBoundingClientRect();

                    if (
                        rect.right <= 0
                        ||
                        rect.left >= clientWidth
                    ) {
                        continue;
                    }

                    const overflowRight =
                        rect.right - clientWidth;

                    if (
                        overflowRight <= 24
                    ) {
                        continue;
                    }

                    const alreadyCounted =
                        offenders.some(
                            (item) =>
                                item.element.contains(
                                    element
                                )
                        );

                    if (alreadyCounted) {
                        continue;
                    }

                    offenders.push({
                        element,

                        tag:
                            element.tagName,

                        className:
                            String(
                                element.className
                                ||
                                ""
                            ).slice(
                                0,
                                100
                            ),

                        left:
                            Math.round(
                                rect.left
                            ),

                        right:
                            Math.round(
                                rect.right
                            )
                    });
                }
            }

            return {
                viewport_width:
                    clientWidth,

                scroll_width:
                    scrollWidth,

                page_overflow_px:
                    pageOverflowPx,

                body_text_chars:
                    (
                        document.body?.innerText
                        ||
                        ""
                    ).trim().length,

                visible_overflow_elements:
                    offenders.map(
                        (item) => ({
                            tag:
                                item.tag,

                            className:
                                item.className,

                            left:
                                item.left,

                            right:
                                item.right
                        })
                    )
            };
        }
        """
    )


def _collect_base_metrics(
    page,
):
    return page.evaluate(
        """
        async () => {
            try {
                if (
                    document.fonts
                    &&
                    document.fonts.ready
                ) {
                    await document.fonts.ready;
                }
            }
            catch (error) {}

            const nav =
                performance.getEntriesByType(
                    "navigation"
                )[0];

            const loadMs =
                nav
                ? (
                    (
                        nav.loadEventEnd
                        ||
                        performance.now()
                    )
                    -
                    nav.startTime
                )
                : performance.now();

            const domContentMs =
                nav
                ? (
                    (
                        nav.domContentLoadedEventEnd
                        ||
                        performance.now()
                    )
                    -
                    nav.startTime
                )
                : null;

            // ---------------------------------
            // IMAGES / SVG
            // ---------------------------------

            const images =
                Array.from(
                    document.images
                );

            const brokenImages =
                images.filter(
                    image =>
                        image.complete
                        &&
                        image.naturalWidth === 0
                ).length;

            const visibleZeroSvg =
                Array.from(
                    document.querySelectorAll(
                        "svg"
                    )
                )
                .filter(
                    svg => {
                        const rect =
                            svg.getBoundingClientRect();

                        const style =
                            getComputedStyle(
                                svg
                            );

                        const visible =
                            (
                                style.display !== "none"
                                &&
                                style.visibility !== "hidden"
                                &&
                                rect.width > 0
                                &&
                                rect.height > 0
                            );

                        return (
                            visible
                            &&
                            (
                                rect.width < 1
                                ||
                                rect.height < 1
                            )
                        );
                    }
                ).length;

            // ---------------------------------
            // FONTS
            // ---------------------------------

            let fontFaces = [];

            try {
                fontFaces =
                    document.fonts
                        ? Array.from(
                            document.fonts
                        ).map(
                            face => ({
                                family:
                                    face.family,

                                status:
                                    face.status
                            })
                        )
                        : [];
            }
            catch (error) {
                fontFaces = [];
            }

            const unloadedFonts =
                fontFaces.filter(
                    face =>
                        face.status !==
                        "loaded"
                ).length;

            // ---------------------------------
            // ANIMATION / TRANSITIONS
            // ---------------------------------

            let animationCount = null;

            try {
                animationCount =
                    document.getAnimations
                        ? document.getAnimations().length
                        : null;
            }
            catch (error) {
                animationCount = null;
            }

            let transitionCount = 0;

            const transitionSample =
                Array.from(
                    document.querySelectorAll(
                        "body *"
                    )
                ).slice(
                    0,
                    900
                );

            for (
                const element of transitionSample
            ) {
                const style =
                    getComputedStyle(
                        element
                    );

                const durations =
                    (
                        style.transitionDuration
                        ||
                        ""
                    )
                    .split(
                        ","
                    )
                    .map(
                        value =>
                            value.trim()
                    );

                if (
                    durations.some(
                        value =>
                            value
                            &&
                            value !== "0s"
                            &&
                            value !== "0ms"
                    )
                ) {
                    transitionCount += 1;
                }
            }

            // ---------------------------------
            // FORMS / INTERACTIVE / EMBEDS
            // ---------------------------------

            const forms =
                Array.from(
                    document.forms
                );

            const requiredFields =
                document.querySelectorAll(
                    "input[required],"
                    + "textarea[required],"
                    + "select[required]"
                ).length;

            const labelledFields =
                Array.from(
                    document.querySelectorAll(
                        "input:not([type='hidden']),"
                        + "textarea,"
                        + "select"
                    )
                )
                .filter(
                    field => {
                        if (
                            field.labels
                            &&
                            field.labels.length
                        ) {
                            return true;
                        }

                        return Boolean(
                            field.getAttribute(
                                "aria-label"
                            )
                            ||
                            field.getAttribute(
                                "aria-labelledby"
                            )
                            ||
                            field.getAttribute(
                                "placeholder"
                            )
                        );
                    }
                ).length;

            const totalFields =
                document.querySelectorAll(
                    "input:not([type='hidden']),"
                    + "textarea,"
                    + "select"
                ).length;

            const interactiveCount =
                document.querySelectorAll(
                    "button,"
                    + "select,"
                    + "details,"
                    + "dialog,"
                    + "[role='button'],"
                    + "[aria-expanded]"
                ).length;

            const currentHost =
                location.hostname
                    .replace(
                        /^www\\./,
                        ""
                    )
                    .toLowerCase();

            const thirdPartyIframes =
                Array.from(
                    document.querySelectorAll(
                        "iframe[src]"
                    )
                )
                .map(
                    iframe =>
                        iframe.src
                )
                .filter(
                    src => {
                        try {
                            const host =
                                new URL(
                                    src,
                                    location.href
                                ).hostname
                                .replace(
                                    /^www\\./,
                                    ""
                                )
                                .toLowerCase();

                            return (
                                host
                                &&
                                host !==
                                currentHost
                            );
                        }
                        catch (error) {
                            return false;
                        }
                    }
                );

            const fileInputs =
                document.querySelectorAll(
                    "input[type='file']"
                ).length;

            const downloadLinks =
                document.querySelectorAll(
                    "a[download]"
                ).length;

            // ---------------------------------
            // STORAGE
            // ---------------------------------

            let localStorageOk = false;
            let sessionStorageOk = false;

            try {
                const key =
                    "__qa_test_local__";

                localStorage.setItem(
                    key,
                    "1"
                );

                localStorage.removeItem(
                    key
                );

                localStorageOk = true;
            }
            catch (error) {}

            try {
                const key =
                    "__qa_test_session__";

                sessionStorage.setItem(
                    key,
                    "1"
                );

                sessionStorage.removeItem(
                    key
                );

                sessionStorageOk = true;
            }
            catch (error) {}

            // ---------------------------------
            // CSS FEATURE USAGE + SUPPORT
            // ---------------------------------

            let cssText =
                Array.from(
                    document.querySelectorAll(
                        "style"
                    )
                )
                .map(
                    style =>
                        style.textContent
                        ||
                        ""
                )
                .join(
                    "\\n"
                );

            cssText +=
                "\\n"
                +
                Array.from(
                    document.querySelectorAll(
                        "[style]"
                    )
                )
                .map(
                    element =>
                        element.getAttribute(
                            "style"
                        )
                        ||
                        ""
                )
                .join(
                    "\\n"
                );

            const sampleElements =
                Array.from(
                    document.querySelectorAll(
                        "body *"
                    )
                ).slice(
                    0,
                    800
                );

            let computedGrid = false;
            let computedFlex = false;
            let computedSticky = false;

            for (
                const element of sampleElements
            ) {
                const style =
                    getComputedStyle(
                        element
                    );

                if (
                    style.display === "grid"
                    ||
                    style.display ===
                    "inline-grid"
                ) {
                    computedGrid = true;
                }

                if (
                    style.display === "flex"
                    ||
                    style.display ===
                    "inline-flex"
                ) {
                    computedFlex = true;
                }

                if (
                    style.position ===
                    "sticky"
                ) {
                    computedSticky = true;
                }
            }

            const cssUsage = {
                grid:
                    computedGrid
                    ||
                    /display\\s*:\\s*(grid|inline-grid)/i.test(
                        cssText
                    ),

                flex:
                    computedFlex
                    ||
                    /display\\s*:\\s*(flex|inline-flex)/i.test(
                        cssText
                    ),

                custom_properties:
                    /var\\s*\\(\\s*--/i.test(
                        cssText
                    )
                    ||
                    /--[a-z0-9_-]+\\s*:/i.test(
                        cssText
                    ),

                backdrop_filter:
                    /backdrop-filter\\s*:/i.test(
                        cssText
                    ),

                aspect_ratio:
                    /aspect-ratio\\s*:/i.test(
                        cssText
                    ),

                sticky:
                    computedSticky
                    ||
                    /position\\s*:\\s*sticky/i.test(
                        cssText
                    )
            };

            const cssSupport = {
                grid:
                    CSS.supports(
                        "display",
                        "grid"
                    ),

                flex:
                    CSS.supports(
                        "display",
                        "flex"
                    ),

                custom_properties:
                    CSS.supports(
                        "--qa-variable",
                        "1"
                    ),

                backdrop_filter:
                    (
                        CSS.supports(
                            "backdrop-filter",
                            "blur(1px)"
                        )
                        ||
                        CSS.supports(
                            "-webkit-backdrop-filter",
                            "blur(1px)"
                        )
                    ),

                aspect_ratio:
                    CSS.supports(
                        "aspect-ratio",
                        "1 / 1"
                    ),

                sticky:
                    (
                        CSS.supports(
                            "position",
                            "sticky"
                        )
                        ||
                        CSS.supports(
                            "position",
                            "-webkit-sticky"
                        )
                    )
            };

            const prefixOnlyPatterns = [
                {
                    prefixed:
                        /-webkit-backdrop-filter\\s*:/i,

                    standard:
                        /(^|[^-])backdrop-filter\\s*:/i,

                    name:
                        "backdrop-filter"
                },
                {
                    prefixed:
                        /-webkit-appearance\\s*:/i,

                    standard:
                        /(^|[^-])appearance\\s*:/i,

                    name:
                        "appearance"
                }
            ];

            const prefixOnly = [];

            for (
                const pattern of prefixOnlyPatterns
            ) {
                if (
                    pattern.prefixed.test(
                        cssText
                    )
                    &&
                    !pattern.standard.test(
                        cssText
                    )
                ) {
                    prefixOnly.push(
                        pattern.name
                    );
                }
            }

            const vendorPrefixCount =
                (
                    cssText.match(
                        /-(webkit|moz|ms|o)-[a-z-]+\\s*:/gi
                    )
                    ||
                    []
                ).length;

            // ---------------------------------
            // JAVASCRIPT API SUPPORT
            // ---------------------------------

            let asyncAwait = false;

            try {
                new Function(
                    "async function qaAsync(){ await Promise.resolve(1); }"
                );

                asyncAwait = true;
            }
            catch (error) {}

            const jsSupport = {
                fetch:
                    typeof window.fetch ===
                    "function",

                promise:
                    typeof window.Promise ===
                    "function",

                async_await:
                    asyncAwait,

                closest:
                    typeof Element !==
                    "undefined"
                    &&
                    typeof Element.prototype.closest ===
                    "function",

                intersection_observer:
                    typeof window.IntersectionObserver ===
                    "function"
            };

            // ---------------------------------
            // PRINT CSS
            // ---------------------------------

            let printRuleCount = 0;

            for (
                const sheet of Array.from(
                    document.styleSheets
                )
            ) {
                try {
                    for (
                        const rule of Array.from(
                            sheet.cssRules
                            ||
                            []
                        )
                    ) {
                        if (
                            rule.media
                            &&
                            String(
                                rule.media.mediaText
                                ||
                                ""
                            ).toLowerCase().includes(
                                "print"
                            )
                        ) {
                            printRuleCount += 1;
                        }
                    }
                }
                catch (error) {
                    // Cross-origin stylesheet: ignore safely.
                }
            }

            // ---------------------------------
            // FEATURE DETECTION / BROWSER DETECTION
            // ---------------------------------

            const inlineScripts =
                Array.from(
                    document.querySelectorAll(
                        "script:not([src])"
                    )
                )
                .map(
                    script =>
                        script.textContent
                        ||
                        ""
                )
                .join(
                    "\\n"
                )
                .slice(
                    0,
                    250000
                );

            const featureDetectionFound =
                (
                    /\\bModernizr\\b/.test(
                        inlineScripts
                    )
                    ||
                    /CSS\\.supports\\s*\\(/.test(
                        inlineScripts
                    )
                    ||
                    /typeof\\s+[A-Za-z_$]/.test(
                        inlineScripts
                    )
                    ||
                    /\\bin\\s+window\\b/.test(
                        inlineScripts
                    )
                );

            const userAgentDetectionFound =
                /navigator\\.userAgent|navigator\\.vendor|navigator\\.platform/.test(
                    inlineScripts
                );

            // ---------------------------------
            // JS MICRO BENCHMARK
            // ---------------------------------

            const benchmarkStart =
                performance.now();

            let benchmarkAccumulator = 0;

            for (
                let index = 1;
                index <= 120000;
                index += 1
            ) {
                benchmarkAccumulator +=
                    Math.sqrt(
                        index
                    );
            }

            const benchmarkMs =
                performance.now()
                -
                benchmarkStart;

            const memory =
                performance.memory
                    ? {
                        used:
                            performance.memory.usedJSHeapSize,

                        total:
                            performance.memory.totalJSHeapSize,

                        limit:
                            performance.memory.jsHeapSizeLimit
                    }
                    : null;

            return {
                load_ms:
                    loadMs,

                dom_content_ms:
                    domContentMs,

                images_total:
                    images.length,

                broken_images:
                    brokenImages,

                svg_total:
                    document.querySelectorAll(
                        "svg"
                    ).length,

                zero_size_svg:
                    visibleZeroSvg,

                font_faces:
                    fontFaces.length,

                unloaded_fonts:
                    unloadedFonts,

                font_status:
                    document.fonts
                        ? document.fonts.status
                        : "unsupported",

                animation_count:
                    animationCount,

                transition_count:
                    transitionCount,

                forms:
                    forms.length,

                fields:
                    totalFields,

                required_fields:
                    requiredFields,

                labelled_fields:
                    labelledFields,

                interactive_count:
                    interactiveCount,

                third_party_iframes:
                    thirdPartyIframes,

                local_storage:
                    localStorageOk,

                session_storage:
                    sessionStorageOk,

                cookies_enabled:
                    navigator.cookieEnabled,

                file_inputs:
                    fileInputs,

                download_links:
                    downloadLinks,

                css_usage:
                    cssUsage,

                css_support:
                    cssSupport,

                vendor_prefix_count:
                    vendorPrefixCount,

                prefix_only:
                    prefixOnly,

                js_support:
                    jsSupport,

                print_rule_count:
                    printRuleCount,

                feature_detection_found:
                    featureDetectionFound,

                user_agent_detection_found:
                    userAgentDetectionFound,

                benchmark_ms:
                    benchmarkMs,

                memory:
                    memory,

                benchmark_accumulator:
                    benchmarkAccumulator
            };
        }
        """
    )


def _responsive_cell(
    page,
):
    results = []

    try:
        for viewport in (
            RESPONSIVE_VIEWPORTS
        ):
            page.set_viewport_size(
                {
                    "width":
                        viewport[
                            "width"
                        ],

                    "height":
                        viewport[
                            "height"
                        ],
                }
            )

            page.wait_for_timeout(
                80
            )

            snapshot = (
                _layout_snapshot(
                    page
                )
            )

            results.append(
                {
                    "label":
                        viewport[
                            "label"
                        ],

                    "width":
                        viewport[
                            "width"
                        ],

                    "overflow":
                        len(
                            snapshot.get(
                                "visible_overflow_elements",
                                [],
                            )
                        ),
                }
            )

    finally:
        page.set_viewport_size(
            DESKTOP_VIEWPORT
        )

        page.wait_for_timeout(
            80
        )

    failing = [
        item
        for item in results
        if item[
            "overflow"
        ] > 0
    ]

    if failing:
        detail = "; ".join(
            (
                f"{item['label']} "
                f"({item['width']}px): "
                f"{item['overflow']} overflow element(s)"
            )
            for item in failing
        )

        return _cell(
            "warning",
            detail,
            results,
        )

    detail = ", ".join(
        (
            f"{item['label']} {item['width']}px"
        )
        for item in results
    )

    return _cell(
        "pass",
        f"No obvious horizontal layout break at {detail}.",
        results,
    )


def _print_cell(
    page,
    print_rule_count,
):
    if not print_rule_count:
        return _cell(
            "info",
            "No explicit @media print rule detected; print-specific styling is not present or is in an inaccessible cross-origin stylesheet.",
        )

    try:
        page.emulate_media(
            media="print"
        )

        page.wait_for_timeout(
            80
        )

        snapshot = (
            _layout_snapshot(
                page
            )
        )

        offenders = len(
            snapshot.get(
                "visible_overflow_elements",
                [],
            )
        )

        if offenders:
            return _cell(
                "warning",
                f"Print mode detected {offenders} visible overflow element(s).",
            )

        return _cell(
            "pass",
            f"{print_rule_count} print media rule(s) detected and no obvious print overflow found.",
        )

    except Exception as exc:
        return _cell(
            "warning",
            f"Print emulation could not be completed: {exc}",
        )

    finally:
        try:
            page.emulate_media(
                media="screen"
            )

        except Exception:
            pass


def _keyboard_and_focus_cells(
    page,
):
    focus_sequence = []
    focus_style = None

    try:
        page.evaluate(
            """
            () => {
                try {
                    document.activeElement?.blur();
                }
                catch (error) {}

                window.scrollTo(
                    0,
                    0
                );
            }
            """
        )

        for index in range(
            4
        ):
            page.keyboard.press(
                "Tab"
            )

            page.wait_for_timeout(
                40
            )

            active = page.evaluate(
                """
                () => {
                    const element =
                        document.activeElement;

                    if (
                        !element
                        ||
                        element ===
                        document.body
                        ||
                        element ===
                        document.documentElement
                    ) {
                        return null;
                    }

                    const style =
                        getComputedStyle(
                            element
                        );

                    return {
                        tag:
                            element.tagName,

                        id:
                            element.id
                            ||
                            "",

                        text:
                            (
                                element.innerText
                                ||
                                element.getAttribute(
                                    "aria-label"
                                )
                                ||
                                element.getAttribute(
                                    "title"
                                )
                                ||
                                ""
                            )
                            .replace(
                                /\\s+/g,
                                " "
                            )
                            .trim()
                            .slice(
                                0,
                                80
                            ),

                        outline_style:
                            style.outlineStyle,

                        outline_width:
                            style.outlineWidth,

                        box_shadow:
                            style.boxShadow
                    };
                }
                """
            )

            if active:
                focus_sequence.append(
                    active
                )

                if (
                    focus_style is None
                ):
                    focus_style = (
                        active
                    )

        unique_focus = {
            (
                item.get(
                    "tag"
                ),
                item.get(
                    "id"
                ),
                item.get(
                    "text"
                ),
            )
            for item in focus_sequence
        }

        if len(
            unique_focus
        ) >= 2:
            keyboard = _cell(
                "pass",
                f"Tab navigation reached {len(unique_focus)} distinct focus targets in the smoke test.",
            )

        elif len(
            unique_focus
        ) == 1:
            keyboard = _cell(
                "warning",
                "Tab navigation reached only one distinct focus target in the smoke test.",
            )

        else:
            keyboard = _cell(
                "warning",
                "No obvious keyboard-focusable element was reached with Tab.",
            )

        if not focus_style:
            focus = _cell(
                "info",
                "Focus styling could not be evaluated because no focus target was reached.",
            )

        else:
            outline_visible = (
                focus_style.get(
                    "outline_style"
                )
                not in (
                    "none",
                    "",
                )
                and
                focus_style.get(
                    "outline_width"
                )
                not in (
                    "0px",
                    "",
                )
            )

            box_shadow = (
                focus_style.get(
                    "box_shadow"
                )
                not in (
                    "none",
                    "",
                )
            )

            if (
                outline_visible
                or
                box_shadow
            ):
                focus = _cell(
                    "pass",
                    "The first keyboard focus target has an obvious outline or box-shadow focus indicator.",
                )

            else:
                focus = _cell(
                    "warning",
                    "The first keyboard focus target has no obvious outline or box-shadow focus indicator.",
                )

        return (
            keyboard,
            focus,
        )

    except Exception as exc:
        return (
            _cell(
                "warning",
                f"Keyboard navigation smoke test could not complete: {exc}",
            ),
            _cell(
                "info",
                "Focus styling was not evaluated because the keyboard test failed.",
            ),
        )

    finally:
        try:
            page.evaluate(
                "() => document.activeElement?.blur()"
            )

        except Exception:
            pass


def _criteria_from_metrics(
    *,
    page,
    base,
    layout,
    js_errors,
    console_errors,
    console_warnings,
    failed_requests,
    http_resource_errors,
    browser_id,
):
    criteria = {}

    # =====================================
    # 2. VISUAL / LAYOUT
    # =====================================

    overflow_count = len(
        layout.get(
            "visible_overflow_elements",
            [],
        )
    )

    if (
        layout.get(
            "body_text_chars",
            0,
        ) < 20
    ):
        criteria[
            "layout_render"
        ] = _cell(
            "fail",
            "Very little visible page content rendered.",
        )

    elif overflow_count:
        criteria[
            "layout_render"
        ] = _cell(
            "warning",
            f"{overflow_count} visible element(s) extend outside the desktop viewport.",
        )

    else:
        criteria[
            "layout_render"
        ] = _cell(
            "pass",
            "No obvious broken desktop layout or visible horizontal overflow detected.",
        )

    font_extensions = (
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
    )

    font_failures = []

    for item in (
        failed_requests
        +
        http_resource_errors
    ):
        item_url = (
            item.get(
                "url"
            )
            or
            ""
        ).lower()

        clean_url = (
            item_url
            .split(
                "?",
                1,
            )[0]
            .split(
                "#",
                1,
            )[0]
        )

        if clean_url.endswith(
            font_extensions
        ):
            font_failures.append(
                item_url
            )

    if (
        base.get(
            "font_status"
        ) ==
        "unsupported"
    ):
        criteria[
            "fonts"
        ] = _cell(
            "info",
            "Font Loading API is not available in this browser.",
        )

    elif font_failures:
        criteria[
            "fonts"
        ] = _cell(
            "warning",
            f"{len(font_failures)} font resource request(s) failed.",
        )

    elif (
        base.get(
            "font_status"
        )
        !=
        "loaded"
    ):
        criteria[
            "fonts"
        ] = _cell(
            "warning",
            (
                f"document.fonts status is "
                f"{base.get('font_status')}; "
                "font loading may still be incomplete."
            ),
        )

    else:
        criteria[
            "fonts"
        ] = _cell(
            "pass",
            (
                f"Font loading state is ready; "
                f"{base.get('font_faces', 0)} font face(s) registered. "
                "Unused font faces are not treated as failures."
            ),
        )

    media_issues = (
        base.get(
            "broken_images",
            0,
        )
        +
        base.get(
            "zero_size_svg",
            0,
        )
    )

    if media_issues:
        criteria[
            "images_icons_svg"
        ] = _cell(
            "warning",
            (
                f"{base.get('broken_images', 0)} broken image(s); "
                f"{base.get('zero_size_svg', 0)} visible zero-size SVG(s)."
            ),
        )

    else:
        criteria[
            "images_icons_svg"
        ] = _cell(
            "pass",
            (
                f"{base.get('images_total', 0)} image(s) and "
                f"{base.get('svg_total', 0)} SVG element(s) checked; "
                "no obvious rendering failure detected."
            ),
        )

    animation_count = (
        base.get(
            "animation_count"
        )
    )

    transition_count = (
        base.get(
            "transition_count",
            0,
        )
    )

    if (
        animation_count is None
    ):
        criteria[
            "animations"
        ] = _cell(
            "warning",
            "Web Animations API is not available, so active CSS animations could not be inspected.",
        )

    elif (
        animation_count
        or
        transition_count
    ):
        criteria[
            "animations"
        ] = _cell(
            "pass",
            (
                f"{animation_count} active/browser animation(s), "
                f"{transition_count} element(s) with transitions detected."
            ),
        )

    else:
        criteria[
            "animations"
        ] = _cell(
            "info",
            "No active animations or non-zero transitions detected during the snapshot.",
        )

    criteria[
        "responsive"
    ] = _responsive_cell(
        page
    )

    criteria[
        "print_styles"
    ] = _print_cell(
        page,
        base.get(
            "print_rule_count",
            0,
        ),
    )

    # =====================================
    # 3. FUNCTIONALITY
    # =====================================

    if js_errors:
        criteria[
            "javascript_features"
        ] = _cell(
            "fail",
            f"{len(js_errors)} JavaScript runtime error(s) occurred.",
        )

    else:
        criteria[
            "javascript_features"
        ] = _cell(
            "pass",
            "No JavaScript pageerror event occurred during the compatibility smoke test.",
        )

    if base.get(
        "forms",
        0,
    ):
        criteria[
            "forms"
        ] = _cell(
            "manual",
            (
                f"{base.get('forms')} form(s), "
                f"{base.get('fields')} visible field(s), "
                f"{base.get('required_fields')} required field(s), "
                f"{base.get('labelled_fields')} labelled/accessible-name field(s). "
                "Real submission and autofill are intentionally not performed."
            ),
        )

    else:
        criteria[
            "forms"
        ] = _cell(
            "info",
            "No forms detected on this page.",
        )

    if base.get(
        "interactive_count",
        0,
    ):
        criteria[
            "interactive_elements"
        ] = _cell(
            "manual",
            (
                f"{base.get('interactive_count')} interactive element(s) detected. "
                "Unsafe clicks that could submit forms, change state, or navigate are not automated."
            ),
        )

    else:
        criteria[
            "interactive_elements"
        ] = _cell(
            "info",
            "No obvious buttons, selects, dialogs, details or ARIA-expanded controls detected.",
        )

    iframe_urls = (
        base.get(
            "third_party_iframes",
            []
        )
        or
        []
    )

    iframe_failed = []

    for iframe_url in iframe_urls:
        for failed in (
            failed_requests
            +
            http_resource_errors
        ):
            failed_url = (
                failed.get(
                    "url"
                )
                or
                ""
            )

            if (
                iframe_url
                and
                failed_url.startswith(
                    iframe_url
                )
            ):
                iframe_failed.append(
                    failed_url
                )

    if iframe_failed:
        criteria[
            "third_party_embeds"
        ] = _cell(
            "warning",
            f"{len(iframe_failed)} third-party embed request(s) failed.",
        )

    elif iframe_urls:
        criteria[
            "third_party_embeds"
        ] = _cell(
            "pass",
            f"{len(iframe_urls)} third-party iframe/embed(s) detected with no direct failed request captured.",
        )

    else:
        criteria[
            "third_party_embeds"
        ] = _cell(
            "info",
            "No third-party iframe embed detected.",
        )

    storage_ok = (
        base.get(
            "local_storage"
        )
        and
        base.get(
            "session_storage"
        )
    )

    if storage_ok:
        criteria[
            "storage"
        ] = _cell(
            "pass",
            (
                "localStorage and sessionStorage read/write smoke tests passed; "
                f"cookies enabled: {bool(base.get('cookies_enabled'))}."
            ),
        )

    else:
        criteria[
            "storage"
        ] = _cell(
            "warning",
            (
                f"localStorage: {bool(base.get('local_storage'))}; "
                f"sessionStorage: {bool(base.get('session_storage'))}; "
                f"cookies enabled: {bool(base.get('cookies_enabled'))}."
            ),
        )

    if (
        base.get(
            "file_inputs",
            0,
        )
        or
        base.get(
            "download_links",
            0,
        )
    ):
        criteria[
            "uploads_downloads"
        ] = _cell(
            "manual",
            (
                f"{base.get('file_inputs', 0)} file input(s), "
                f"{base.get('download_links', 0)} download link(s) detected. "
                "Real file upload/download is not executed without a test fixture."
            ),
        )

    else:
        criteria[
            "uploads_downloads"
        ] = _cell(
            "info",
            "No explicit file upload input or HTML download link detected.",
        )

    # =====================================
    # 4. PERFORMANCE
    # =====================================

    load_ms = float(
        base.get(
            "load_ms"
        )
        or
        0
    )

    if load_ms <= 5000:
        load_status = (
            "pass"
        )

    elif load_ms <= 10000:
        load_status = (
            "warning"
        )

    else:
        load_status = (
            "fail"
        )

    criteria[
        "page_load_time"
    ] = _cell(
        load_status,
        f"{load_ms / 1000:.2f} s browser load timing.",
        round(
            load_ms,
            2,
        ),
    )

    benchmark_ms = float(
        base.get(
            "benchmark_ms"
        )
        or
        0
    )

    if benchmark_ms <= 50:
        benchmark_status = (
            "pass"
        )

    elif benchmark_ms <= 150:
        benchmark_status = (
            "warning"
        )

    else:
        benchmark_status = (
            "fail"
        )

    criteria[
        "js_execution_speed"
    ] = _cell(
        benchmark_status,
        f"Synthetic 120k-operation JavaScript benchmark: {benchmark_ms:.2f} ms.",
        round(
            benchmark_ms,
            2,
        ),
    )

    memory = (
        base.get(
            "memory"
        )
    )

    if memory:
        used_mb = (
            memory.get(
                "used",
                0,
            )
            /
            1024
            /
            1024
        )

        criteria[
            "memory_usage"
        ] = _cell(
            "info",
            f"Approximate JS heap used: {used_mb:.2f} MB. performance.memory is Chromium-specific and is not a full process-memory measurement.",
            round(
                used_mb,
                2,
            ),
        )

    else:
        criteria[
            "memory_usage"
        ] = _cell(
            "info",
            "This engine does not expose performance.memory; cross-browser process memory is not available through the standard page API.",
        )

    criteria[
        "slow_3g"
    ] = _cell(
        "manual",
        (
            "Slow 3G reload is not run in the standard compatibility scan because it would materially increase scan time. "
            + (
                "Chromium network emulation can be added as an optional stress mode."
                if browser_id in (
                    "chrome",
                    "edge",
                )
                else
                "Equivalent network emulation is not uniformly available through Playwright for this engine."
            )
        ),
    )

    # =====================================
    # 5. CSS / HTML SUPPORT
    # =====================================

    usage = (
        base.get(
            "css_usage",
            {}
        )
    )

    support = (
        base.get(
            "css_support",
            {}
        )
    )

    used_features = [
        key
        for (
            key,
            used,
        ) in usage.items()
        if used
    ]

    unsupported_used = [
        key
        for key in used_features
        if not support.get(
            key,
            False,
        )
    ]

    if unsupported_used:
        criteria[
            "caniuse_runtime"
        ] = _cell(
            "warning",
            (
                "Detected CSS feature(s) not supported at runtime: "
                +
                ", ".join(
                    unsupported_used
                )
                +
                ". Runtime support is tested in the actual engine; live caniuse.com lookup is not bundled."
            ),
        )

    elif used_features:
        criteria[
            "caniuse_runtime"
        ] = _cell(
            "pass",
            (
                "Runtime support passed for detected features: "
                +
                ", ".join(
                    used_features
                )
                +
                ". This tests the exact browser engine; caniuse.com remains a reference for older/version-range support."
            ),
        )

    else:
        criteria[
            "caniuse_runtime"
        ] = _cell(
            "info",
            "No selected modern CSS feature from the built-in risk set was detected in accessible style rules.",
        )

    prefix_only = (
        base.get(
            "prefix_only",
            []
        )
        or
        []
    )

    if prefix_only:
        criteria[
            "vendor_prefixes"
        ] = _cell(
            "warning",
            (
                "Prefix-only declaration(s) detected without the standard form: "
                +
                ", ".join(
                    prefix_only
                )
            ),
        )

    elif base.get(
        "vendor_prefix_count",
        0,
    ):
        criteria[
            "vendor_prefixes"
        ] = _cell(
            "pass",
            f"{base.get('vendor_prefix_count')} vendor-prefixed declaration(s) detected; no built-in prefix-only risk found.",
        )

    else:
        criteria[
            "vendor_prefixes"
        ] = _cell(
            "info",
            "No vendor-prefixed declaration detected in accessible inline/style rules.",
        )

    grid_or_flex_used = (
        usage.get(
            "grid"
        )
        or
        usage.get(
            "flex"
        )
    )

    if grid_or_flex_used:
        missing = []

        if (
            usage.get(
                "grid"
            )
            and
            not support.get(
                "grid"
            )
        ):
            missing.append(
                "Grid"
            )

        if (
            usage.get(
                "flex"
            )
            and
            not support.get(
                "flex"
            )
        ):
            missing.append(
                "Flexbox"
            )

        if missing:
            criteria[
                "grid_flex"
            ] = _cell(
                "fail",
                "Unsupported layout feature(s): "
                +
                ", ".join(
                    missing
                ),
            )

        else:
            criteria[
                "grid_flex"
            ] = _cell(
                "pass",
                "Detected Grid/Flexbox usage is supported by this browser engine. Legacy-browser fallback design is not simulated.",
            )

    else:
        criteria[
            "grid_flex"
        ] = _cell(
            "info",
            "No Grid/Flexbox usage detected in the accessible style sample.",
        )

    if usage.get(
        "custom_properties"
    ):
        if support.get(
            "custom_properties"
        ):
            criteria[
                "css_variables"
            ] = _cell(
                "pass",
                "CSS custom properties are used and supported.",
            )

        else:
            criteria[
                "css_variables"
            ] = _cell(
                "fail",
                "CSS custom properties are used but not supported.",
            )

    else:
        criteria[
            "css_variables"
        ] = _cell(
            "info",
            "No CSS custom property usage detected in the accessible style sample.",
        )

    # =====================================
    # 6. JS API SUPPORT
    # =====================================

    js_support = (
        base.get(
            "js_support",
            {}
        )
    )

    criteria[
        "fetch_api"
    ] = _cell(
        (
            "pass"
            if js_support.get(
                "fetch"
            )
            else "fail"
        ),
        (
            "Fetch API supported."
            if js_support.get(
                "fetch"
            )
            else "Fetch API is not supported; XMLHttpRequest/polyfill fallback would be required."
        ),
    )

    promise_async_ok = (
        js_support.get(
            "promise"
        )
        and
        js_support.get(
            "async_await"
        )
    )

    criteria[
        "promise_async"
    ] = _cell(
        (
            "pass"
            if promise_async_ok
            else "fail"
        ),
        (
            "Promise and async-await syntax supported."
            if promise_async_ok
            else (
                f"Promise: {bool(js_support.get('promise'))}; "
                f"async-await: {bool(js_support.get('async_await'))}."
            )
        ),
    )

    dom_missing = []

    if not js_support.get(
        "closest"
    ):
        dom_missing.append(
            "Element.closest"
        )

    if not js_support.get(
        "intersection_observer"
    ):
        dom_missing.append(
            "IntersectionObserver"
        )

    criteria[
        "dom_apis"
    ] = _cell(
        (
            "pass"
            if not dom_missing
            else "warning"
        ),
        (
            "Element.closest and IntersectionObserver supported."
            if not dom_missing
            else (
                "Missing API(s): "
                +
                ", ".join(
                    dom_missing
                )
            )
        ),
    )

    missing_polyfills = []

    if not js_support.get(
        "fetch"
    ):
        missing_polyfills.append(
            "fetch"
        )

    if not js_support.get(
        "promise"
    ):
        missing_polyfills.append(
            "Promise"
        )

    if not js_support.get(
        "closest"
    ):
        missing_polyfills.append(
            "Element.closest"
        )

    if not js_support.get(
        "intersection_observer"
    ):
        missing_polyfills.append(
            "IntersectionObserver"
        )

    if missing_polyfills:
        criteria[
            "polyfill_needs"
        ] = _cell(
            "warning",
            "Potential polyfill need: "
            +
            ", ".join(
                missing_polyfills
            ),
        )

    else:
        criteria[
            "polyfill_needs"
        ] = _cell(
            "pass",
            "No polyfill need detected for the built-in API support set.",
        )

    # =====================================
    # 7. ACCESSIBILITY
    # =====================================

    criteria[
        "screen_reader"
    ] = _cell(
        "manual",
        (
            "Real screen-reader behavior cannot be verified by Playwright alone. "
            "Use NVDA/JAWS on Windows and VoiceOver on macOS/Safari for final accessibility sign-off."
        ),
    )

    keyboard_cell, focus_cell = (
        _keyboard_and_focus_cells(
            page
        )
    )

    criteria[
        "keyboard_navigation"
    ] = keyboard_cell

    criteria[
        "focus_states"
    ] = focus_cell

    # =====================================
    # 8. ERROR HANDLING
    # =====================================

    if (
        console_errors
        or
        console_warnings
    ):
        criteria[
            "console_errors_warnings"
        ] = _cell(
            "warning",
            (
                f"{len(console_errors)} console error(s), "
                f"{len(console_warnings)} console warning(s)."
            ),
        )

    else:
        criteria[
            "console_errors_warnings"
        ] = _cell(
            "pass",
            "No console error/warning event captured.",
        )

    missing_api_count = len(
        missing_polyfills
    )

    if (
        missing_api_count
        and
        js_errors
    ):
        criteria[
            "graceful_degradation"
        ] = _cell(
            "warning",
            (
                f"{missing_api_count} missing built-in API(s) and "
                f"{len(js_errors)} runtime error(s) were observed; graceful degradation may be incomplete."
            ),
        )

    elif missing_api_count:
        criteria[
            "graceful_degradation"
        ] = _cell(
            "info",
            (
                f"{missing_api_count} built-in API(s) missing, "
                "but no pageerror was captured during the smoke test."
            ),
        )

    else:
        criteria[
            "graceful_degradation"
        ] = _cell(
            "pass",
            "No missing API from the built-in compatibility set and no runtime pageerror was captured.",
        )

    if base.get(
        "user_agent_detection_found"
    ):
        criteria[
            "feature_detection"
        ] = _cell(
            "warning",
            (
                "Inline script contains navigator.userAgent/vendor/platform detection. "
                "Prefer feature detection where possible."
            ),
        )

    elif base.get(
        "feature_detection_found"
    ):
        criteria[
            "feature_detection"
        ] = _cell(
            "pass",
            "Feature-detection pattern (Modernizr/CSS.supports/typeof/etc.) detected in inline scripts.",
        )

    else:
        criteria[
            "feature_detection"
        ] = _cell(
            "info",
            (
                "No obvious feature-detection or user-agent detection pattern found in inline scripts. "
                "External script source is not fully inspected."
            ),
        )

    return criteria


def _summary_from_browser(
    *,
    launch_status,
    launch_detail,
    http_status,
    criteria,
    js_errors,
    console_errors,
    failed_requests,
    http_resource_errors,
):
    summary = {
        "browser_launch":
            _cell(
                launch_status,
                launch_detail,
            ),

        "http_status":
            _http_cell(
                http_status
            ),

        "layout":
            criteria.get(
                "layout_render",
                _cell(
                    "info",
                    "Layout not evaluated.",
                ),
            ),

        "javascript_errors":
            _cell(
                (
                    "fail"
                    if js_errors
                    else "pass"
                ),
                (
                    f"{len(js_errors)} JavaScript runtime error(s)."
                    if js_errors
                    else "No JavaScript runtime error captured."
                ),
                len(
                    js_errors
                ),
            ),

        "console_errors":
            _cell(
                (
                    "warning"
                    if console_errors
                    else "pass"
                ),
                (
                    f"{len(console_errors)} console error(s)."
                    if console_errors
                    else "No console error captured."
                ),
                len(
                    console_errors
                ),
            ),

        "failed_requests":
            _cell(
                (
                    "warning"
                    if (
                        failed_requests
                        or
                        http_resource_errors
                    )
                    else "pass"
                ),
                (
                    (
                        f"{len(failed_requests)} network failure(s); "
                        f"{len(http_resource_errors)} HTTP resource error(s)."
                    )
                    if (
                        failed_requests
                        or
                        http_resource_errors
                    )
                    else "No failed request or HTTP resource error captured."
                ),
                (
                    len(
                        failed_requests
                    )
                    +
                    len(
                        http_resource_errors
                    )
                ),
            ),
    }

    return summary


def _unavailable_browser_record(
    spec,
    error,
):
    criteria = {
        item[
            "id"
        ]:
            _cell(
                "info",
                "Not tested because the browser could not launch.",
            )
        for item in CRITERIA
    }

    summary = {
        "browser_launch":
            _cell(
                "fail",
                error,
            ),

        "http_status":
            _cell(
                "info",
                "Not tested.",
            ),

        "layout":
            _cell(
                "info",
                "Not tested.",
            ),

        "javascript_errors":
            _cell(
                "info",
                "Not tested.",
            ),

        "console_errors":
            _cell(
                "info",
                "Not tested.",
            ),

        "failed_requests":
            _cell(
                "info",
                "Not tested.",
            ),
    }

    return {
        "id":
            spec[
                "id"
            ],

        "name":
            spec[
                "name"
            ],

        "engine":
            spec[
                "engine_label"
            ],

        "version":
            "",

        "launched":
            False,

        "launch_error":
            error,

        "http_status":
            None,

        "final_url":
            None,

        "summary":
            summary,

        "criteria":
            criteria,

        "errors":
            {
                "javascript":
                    [],

                "console":
                    [],

                "console_warnings":
                    [],

                "failed_requests":
                    [],

                "http_resource_errors":
                    [],
            },
    }


def _test_browser(
    playwright,
    spec,
    url,
):
    browser = None

    try:
        browser_type = getattr(
            playwright,
            spec[
                "playwright_type"
            ],
        )

        launch_args = {
            "headless":
                True,
        }

        if spec.get(
            "channel"
        ):
            launch_args[
                "channel"
            ] = spec[
                "channel"
            ]

        browser = browser_type.launch(
            **launch_args
        )

    except Exception as exc:
        return _unavailable_browser_record(
            spec,
            f"Browser launch failed: {exc}",
        )

    version = (
        browser.version
        or
        ""
    )

    context = browser.new_context(
        viewport=(
            DESKTOP_VIEWPORT
        ),
        ignore_https_errors=True,
    )

    page = context.new_page()

    js_errors = []
    console_errors = []
    console_warnings = []
    failed_requests = []
    http_resource_errors = []

    page.on(
        "pageerror",
        lambda error:
            js_errors.append(
                str(
                    error
                )
            ),
    )

    def on_console(
        message,
    ):
        item = {
            "type":
                message.type,

            "text":
                message.text,
        }

        if message.type == "error":
            console_errors.append(
                item
            )

        elif message.type == "warning":
            console_warnings.append(
                item
            )

    page.on(
        "console",
        on_console,
    )

    page.on(
        "requestfailed",
        lambda request:
            failed_requests.append(
                {
                    "url":
                        request.url,

                    "failure":
                        request.failure
                        or
                        "Unknown request failure",
                }
            ),
    )

    def on_response(
        response,
    ):
        if (
            response.status >= 400
        ):
            http_resource_errors.append(
                {
                    "url":
                        response.url,

                    "status":
                        response.status,
                }
            )

    page.on(
        "response",
        on_response,
    )

    response = None
    http_status = None
    final_url = url

    try:
        response = page.goto(
            url,
            wait_until=
                "domcontentloaded",
            timeout=
                30_000,
        )

        if response:
            http_status = (
                response.status
            )

        try:
            page.wait_for_load_state(
                "load",
                timeout=
                    8_000,
            )

        except Exception:
            pass

        page.wait_for_timeout(
            450
        )

        final_url = (
            page.url
        )

        layout = (
            _layout_snapshot(
                page
            )
        )

        base = (
            _collect_base_metrics(
                page
            )
        )

        criteria = (
            _criteria_from_metrics(
                page=
                    page,

                base=
                    base,

                layout=
                    layout,

                js_errors=
                    js_errors,

                console_errors=
                    console_errors,

                console_warnings=
                    console_warnings,

                failed_requests=
                    failed_requests,

                http_resource_errors=
                    http_resource_errors,

                browser_id=
                    spec[
                        "id"
                    ],
            )
        )

        summary = (
            _summary_from_browser(
                launch_status=
                    "pass",

                launch_detail=
                    (
                        f"Launched successfully"
                        +
                        (
                            f" | Version {version}"
                            if version
                            else ""
                        )
                    ),

                http_status=
                    http_status,

                criteria=
                    criteria,

                js_errors=
                    js_errors,

                console_errors=
                    console_errors,

                failed_requests=
                    failed_requests,

                http_resource_errors=
                    http_resource_errors,
            )
        )

        return {
            "id":
                spec[
                    "id"
                ],

            "name":
                spec[
                    "name"
                ],

            "engine":
                spec[
                    "engine_label"
                ],

            "version":
                version,

            "launched":
                True,

            "launch_error":
                None,

            "http_status":
                http_status,

            "final_url":
                final_url,

            "summary":
                summary,

            "criteria":
                criteria,

            "metrics":
                {
                    "page_load_ms":
                        base.get(
                            "load_ms"
                        ),

                    "dom_content_ms":
                        base.get(
                            "dom_content_ms"
                        ),

                    "js_benchmark_ms":
                        base.get(
                            "benchmark_ms"
                        ),

                    "memory":
                        base.get(
                            "memory"
                        ),
                },

            "errors":
                {
                    "javascript":
                        js_errors[
                            :25
                        ],

                    "console":
                        console_errors[
                            :25
                        ],

                    "console_warnings":
                        console_warnings[
                            :25
                        ],

                    "failed_requests":
                        failed_requests[
                            :25
                        ],

                    "http_resource_errors":
                        http_resource_errors[
                            :25
                        ],
                },
        }

    except Exception as exc:
        criteria = {
            item[
                "id"
            ]:
                _cell(
                    "info",
                    "Not tested because page navigation failed.",
                )
            for item in CRITERIA
        }

        summary = {
            "browser_launch":
                _cell(
                    "pass",
                    (
                        "Browser launched successfully"
                        +
                        (
                            f" | Version {version}"
                            if version
                            else ""
                        )
                    ),
                ),

            "http_status":
                _cell(
                    "fail",
                    f"Navigation failed: {exc}",
                ),

            "layout":
                _cell(
                    "info",
                    "Not tested.",
                ),

            "javascript_errors":
                _cell(
                    "info",
                    "Not tested.",
                ),

            "console_errors":
                _cell(
                    "info",
                    "Not tested.",
                ),

            "failed_requests":
                _cell(
                    "warning",
                    f"{len(failed_requests)} request failure(s) captured before navigation stopped.",
                ),
        }

        return {
            "id":
                spec[
                    "id"
                ],

            "name":
                spec[
                    "name"
                ],

            "engine":
                spec[
                    "engine_label"
                ],

            "version":
                version,

            "launched":
                True,

            "launch_error":
                None,

            "http_status":
                http_status,

            "final_url":
                final_url,

            "summary":
                summary,

            "criteria":
                criteria,

            "errors":
                {
                    "javascript":
                        js_errors[
                            :25
                        ],

                    "console":
                        console_errors[
                            :25
                        ],

                    "console_warnings":
                        console_warnings[
                            :25
                        ],

                    "failed_requests":
                        failed_requests[
                            :25
                        ],

                    "http_resource_errors":
                        http_resource_errors[
                            :25
                        ],
                },

            "navigation_error":
                str(
                    exc
                ),
        }

    finally:
        try:
            context.close()

        except Exception:
            pass

        try:
            browser.close()

        except Exception:
            pass


def check_browser_compatibility(
    playwright,
    url,
):
    """
    Cross-browser compatibility report.

    Browser columns:
    - Chrome
    - Edge
    - Firefox
    - Safari* (Playwright WebKit on Windows)

    IMPORTANT:
    WebKit on Windows is an engine-level approximation of Safari.
    It is not a real macOS Safari application.
    """

    print(
        "\nBrowser Compatibility Check"
    )

    print(
        "---------------------------"
    )

    specs = [
        {
            "id":
                "chrome",

            "name":
                "Chrome",

            "playwright_type":
                "chromium",

            "channel":
                "chrome",

            "engine_label":
                "Chromium / Google Chrome",
        },
        {
            "id":
                "edge",

            "name":
                "Edge",

            "playwright_type":
                "chromium",

            "channel":
                "msedge",

            "engine_label":
                "Chromium / Microsoft Edge",
        },
        {
            "id":
                "firefox",

            "name":
                "Firefox",

            "playwright_type":
                "firefox",

            "channel":
                None,

            "engine_label":
                "Mozilla Firefox",
        },
        {
            "id":
                "safari",

            "name":
                "Safari*",

            "playwright_type":
                "webkit",

            "channel":
                None,

            "engine_label":
                "Playwright WebKit (Safari engine approximation)",
        },
    ]

    browser_results = []

    for spec in specs:
        print(
            f"\nTesting {spec['name']}..."
        )

        started = (
            time.perf_counter()
        )

        result = (
            _test_browser(
                playwright,
                spec,
                url,
            )
        )

        result[
            "duration_seconds"
        ] = round(
            time.perf_counter()
            -
            started,
            2,
        )

        browser_results.append(
            result
        )

        for summary_id, label in (
            (
                "browser_launch",
                "Browser Launch",
            ),
            (
                "http_status",
                "HTTP Status",
            ),
            (
                "layout",
                "Layout",
            ),
            (
                "javascript_errors",
                "JavaScript Errors",
            ),
            (
                "console_errors",
                "Console Errors",
            ),
            (
                "failed_requests",
                "Failed Requests",
            ),
        ):
            cell = (
                result.get(
                    "summary",
                    {}
                ).get(
                    summary_id,
                    _cell(
                        "info",
                        "Not available.",
                    ),
                )
            )

            print(
                (
                    f"{_status_label(cell['status'])} | "
                    f"{spec['name']} - {label} | "
                    f"{cell['detail']}"
                )
            )

    data = {
        "browsers":
            browser_results,

        "criteria":
            CRITERIA,

        "overview_rows":
            [
                {
                    "id":
                        "browser_launch",

                    "label":
                        "Browser Launch",
                },
                {
                    "id":
                        "http_status",

                    "label":
                        "HTTP Status",
                },
                {
                    "id":
                        "layout",

                    "label":
                        "Layout",
                },
                {
                    "id":
                        "javascript_errors",

                    "label":
                        "JavaScript Errors",
                },
                {
                    "id":
                        "console_errors",

                    "label":
                        "Console Errors",
                },
                {
                    "id":
                        "failed_requests",

                    "label":
                        "Failed Requests",
                },
            ],

        "notes":
            [
                (
                    "Safari* is tested with Playwright WebKit on Windows. "
                    "Final Safari sign-off should be performed on macOS Safari."
                ),
                (
                    "Real screen-reader verification (NVDA/JAWS/VoiceOver), "
                    "real form submission/autofill, file transfer, and Slow 3G "
                    "stress testing are reported as MANUAL where applicable."
                ),
                (
                    "The Can I Use row performs runtime feature support checks "
                    "in each actual test engine. A live caniuse.com lookup is not "
                    "bundled; use caniuse.com when deciding support for older browser versions."
                ),
            ],
    }

    print(
        "QA_BROWSER_COMPAT|"
        +
        json.dumps(
            data,
            ensure_ascii=False,
        )
    )

    print(
        "\nBrowser Compatibility Check Complete"
    )
