import json


RESPONSIVE_AUDIT_VIEWPORTS = [
    {
        "id": "desktop",
        "label": "Desktop",
        "width": 1920,
        "height": 1080,
        "range": "1920px to 1440px",
    },
    {
        "id": "laptop",
        "label": "Laptop",
        "width": 1366,
        "height": 768,
        "range": "1439px to 1024px",
    },
    {
        "id": "tablet",
        "label": "Tablet",
        "width": 768,
        "height": 1024,
        "range": "1023px to 768px",
    },
    {
        "id": "mobile",
        "label": "Mobile",
        "width": 390,
        "height": 844,
        "range": "767px to 324px",
    },
]


IGNORED_LAYOUT_SELECTORS = [
    ".swiper",
    ".swiper-wrapper",
    ".swiper-slide",
    ".slick-list",
    ".slick-track",
    ".slick-slide",
    ".elementskit-menu-container",
    ".elementskit-menu-offcanvas-elements",
    ".elementor-motion-effects-container",
    ".elementor-motion-effects-layer",
    ".elementor-background-video-container",
]


def _snapshot(
    page,
):
    return page.evaluate(
        """
        (ignoredSelectors) => {
            const ignored =
                ignoredSelectors.join(
                    ","
                );

            function visible(
                element
            ) {
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
                    rect.width > 0
                    &&
                    rect.height > 0
                );
            }

            const outside = [];

            for (
                const element of
                document.querySelectorAll(
                    "body *"
                )
            ) {
                if (
                    outside.length >= 20
                ) {
                    break;
                }

                if (
                    ignored
                    &&
                    (
                        element.matches(
                            ignored
                        )
                        ||
                        element.closest(
                            ignored
                        )
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

                const style =
                    getComputedStyle(
                        element
                    );

                if (
                    style.position === "fixed"
                ) {
                    continue;
                }

                const rect =
                    element.getBoundingClientRect();

                if (
                    rect.left < -8
                    ||
                    rect.right >
                        window.innerWidth + 8
                ) {
                    outside.push({
                        tag:
                            element.tagName,

                        text:
                            (
                                element.innerText
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

            const contentSelectors =
                "h1,h2,h3,h4,h5,h6,p,button,"
                + "input,textarea,select,label,img";

            const elements =
                Array.from(
                    document.querySelectorAll(
                        contentSelectors
                    )
                )
                .filter(
                    visible
                )
                .slice(
                    0,
                    350
                );

            let overlapCount = 0;

            for (
                let firstIndex = 0;
                firstIndex < elements.length;
                firstIndex += 1
            ) {
                const first =
                    elements[
                        firstIndex
                    ];

                const firstStyle =
                    getComputedStyle(
                        first
                    );

                if (
                    firstStyle.position ===
                    "fixed"
                    ||
                    firstStyle.position ===
                    "sticky"
                ) {
                    continue;
                }

                const firstRect =
                    first.getBoundingClientRect();

                for (
                    let secondIndex =
                        firstIndex + 1;
                    secondIndex <
                        elements.length;
                    secondIndex += 1
                ) {
                    if (
                        overlapCount >= 20
                    ) {
                        break;
                    }

                    const second =
                        elements[
                            secondIndex
                        ];

                    if (
                        first.contains(
                            second
                        )
                        ||
                        second.contains(
                            first
                        )
                    ) {
                        continue;
                    }

                    const secondStyle =
                        getComputedStyle(
                            second
                        );

                    if (
                        secondStyle.position ===
                        "fixed"
                        ||
                        secondStyle.position ===
                        "sticky"
                    ) {
                        continue;
                    }

                    const secondRect =
                        second.getBoundingClientRect();

                    const overlapWidth =
                        Math.min(
                            firstRect.right,
                            secondRect.right
                        )
                        -
                        Math.max(
                            firstRect.left,
                            secondRect.left
                        );

                    const overlapHeight =
                        Math.min(
                            firstRect.bottom,
                            secondRect.bottom
                        )
                        -
                        Math.max(
                            firstRect.top,
                            secondRect.top
                        );

                    if (
                        overlapWidth > 20
                        &&
                        overlapHeight > 20
                    ) {
                        overlapCount += 1;
                    }
                }
            }

            return {
                viewport_width:
                    window.innerWidth,

                viewport_height:
                    window.innerHeight,

                document_width:
                    document.documentElement.scrollWidth,

                horizontal_overflow:
                    document.documentElement.scrollWidth
                    >
                    window.innerWidth + 2,

                outside_elements:
                    outside,

                overlap_count:
                    overlapCount
            };
        }
        """,
        IGNORED_LAYOUT_SELECTORS,
    )


def check_responsive(
    page,
):
    print(
        "\nResponsive Check"
    )

    print(
        "----------------"
    )

    try:
        original_viewport = (
            page.viewport_size
            or
            {
                "width": 1366,
                "height": 768,
            }
        )

    except Exception:
        original_viewport = {
            "width": 1366,
            "height": 768,
        }

    results = []

    try:
        for viewport in (
            RESPONSIVE_AUDIT_VIEWPORTS
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

            page.evaluate(
                "window.scrollTo(0, 0)"
            )

            page.wait_for_timeout(
                120
            )

            snapshot = (
                _snapshot(
                    page
                )
            )

            issue_count = (
                int(
                    bool(
                        snapshot.get(
                            "horizontal_overflow"
                        )
                    )
                )
                +
                len(
                    snapshot.get(
                        "outside_elements",
                        []
                    )
                )
                +
                snapshot.get(
                    "overlap_count",
                    0,
                )
            )

            if issue_count:
                status = (
                    "warning"
                )

            else:
                status = (
                    "pass"
                )

            record = {
                "id":
                    viewport[
                        "id"
                    ],

                "label":
                    viewport[
                        "label"
                    ],

                "range":
                    viewport[
                        "range"
                    ],

                "width":
                    viewport[
                        "width"
                    ],

                "height":
                    viewport[
                        "height"
                    ],

                "status":
                    status,

                "horizontal_overflow":
                    bool(
                        snapshot.get(
                            "horizontal_overflow"
                        )
                    ),

                "document_width":
                    snapshot.get(
                        "document_width"
                    ),

                "outside_count":
                    len(
                        snapshot.get(
                            "outside_elements",
                            []
                        )
                    ),

                "overlap_count":
                    snapshot.get(
                        "overlap_count",
                        0,
                    ),

                "outside_elements":
                    snapshot.get(
                        "outside_elements",
                        []
                    )[
                        :10
                    ],
            }

            results.append(
                record
            )

            if status == "pass":
                print(
                    (
                        f"PASS | {viewport['label']} "
                        f"{viewport['width']}x{viewport['height']} | "
                        "No obvious horizontal overflow, outside element, "
                        "or major content overlap detected"
                    )
                )

            else:
                print(
                    (
                        f"WARNING | {viewport['label']} "
                        f"{viewport['width']}x{viewport['height']} | "
                        f"Horizontal overflow: "
                        f"{record['horizontal_overflow']} | "
                        f"Outside elements: "
                        f"{record['outside_count']} | "
                        f"Overlaps: "
                        f"{record['overlap_count']}"
                    )
                )

    finally:
        page.set_viewport_size(
            original_viewport
        )

        page.evaluate(
            "window.scrollTo(0, 0)"
        )

    data = {
        "ranges": [
            {
                "id": "desktop",
                "label": "Desktop",
                "min_width": 1440,
                "max_width": 1920,
                "display_range": "1920px to 1440px",
            },
            {
                "id": "laptop",
                "label": "Laptop",
                "min_width": 1024,
                "max_width": 1439,
                "display_range": "1439px to 1024px",
            },
            {
                "id": "tablet",
                "label": "Tablet",
                "min_width": 768,
                "max_width": 1023,
                "display_range": "1023px to 768px",
            },
            {
                "id": "mobile",
                "label": "Mobile",
                "min_width": 324,
                "max_width": 767,
                "display_range": "767px to 324px",
            },
        ],

        "audit_viewports":
            results,
    }

    print(
        "QA_RESPONSIVE_DATA|"
        +
        json.dumps(
            data,
            ensure_ascii=False,
        )
    )

    if any(
        result[
            "status"
        ] ==
        "warning"
        for result in results
    ):
        print(
            "WARNING | Responsive Summary | "
            "One or more representative viewports require review"
        )

    else:
        print(
            "PASS | Responsive Summary | "
            "Representative desktop, laptop, tablet and mobile viewports passed"
        )

    print(
        "\nResponsive Check Complete"
    )
