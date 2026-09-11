import json
from urllib.parse import urlparse


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


def check_page_link_list(page):
    """
    List every HTTP/HTTPS anchor found in the current HTML page.

    Output fields:
    - No
    - URL
    - Link Name
    - Internal / External

    Notes:
    - Relative URLs are resolved to absolute URLs by the browser.
    - mailto:, tel:, javascript: and other non-HTTP links are excluded.
    - Duplicate anchors are intentionally kept because the user asked
      for all HTML links present on the page.
    """

    print(
        "\nPage Link List Check"
    )

    print(
        "--------------------"
    )

    current_host = (
        _normalize_host(
            urlparse(
                page.url
            ).hostname
        )
    )

    links = page.evaluate(
        """
        () => {
            return Array
                .from(
                    document.querySelectorAll(
                        "a[href]"
                    )
                )
                .map(
                    (anchor, index) => {
                        const rawHref =
                            anchor.getAttribute(
                                "href"
                            )
                            ||
                            "";

                        const resolvedHref =
                            anchor.href
                            ||
                            "";

                        const text =
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
                            .trim();

                        const ariaLabel =
                            (
                                anchor.getAttribute(
                                    "aria-label"
                                )
                                ||
                                ""
                            ).trim();

                        const title =
                            (
                                anchor.getAttribute(
                                    "title"
                                )
                                ||
                                ""
                            ).trim();

                        const imageAlt =
                            (
                                anchor.querySelector(
                                    "img[alt]"
                                )
                                ?.getAttribute(
                                    "alt"
                                )
                                ||
                                ""
                            ).trim();

                        return {
                            dom_index:
                                index + 1,

                            raw_href:
                                rawHref,

                            url:
                                resolvedHref,

                            text:
                                text,

                            aria_label:
                                ariaLabel,

                            title:
                                title,

                            image_alt:
                                imageAlt
                        };
                    }
                );
        }
        """
    )

    records = []

    internal_count = 0
    external_count = 0

    for link in links:
        resolved_url = (
            link.get(
                "url"
            )
            or
            ""
        ).strip()

        if not resolved_url:
            continue

        parsed = urlparse(
            resolved_url
        )

        if parsed.scheme.lower() not in (
            "http",
            "https",
        ):
            continue

        link_host = (
            _normalize_host(
                parsed.hostname
            )
        )

        link_type = (
            "Internal"
            if link_host == current_host
            else "External"
        )

        if link_type == "Internal":
            internal_count += 1

        else:
            external_count += 1

        link_name = (
            link.get(
                "text"
            )
            or
            link.get(
                "aria_label"
            )
            or
            link.get(
                "title"
            )
            or
            link.get(
                "image_alt"
            )
            or
            "(No link name)"
        )

        record = {
            "no":
                len(
                    records
                )
                +
                1,

            "url":
                resolved_url,

            "link_name":
                link_name,

            "link_type":
                link_type,

            "raw_href":
                link.get(
                    "raw_href"
                )
                or
                "",
        }

        records.append(
            record
        )

        print(
            "QA_PAGE_LINK|"
            +
            json.dumps(
                record,
                ensure_ascii=False,
            )
        )

    total = len(
        records
    )

    print(
        "INFO | Page Link List |",
        f"{total} HTML link(s) found"
    )

    print(
        "INFO | Internal Links |",
        internal_count
    )

    print(
        "INFO | External Links |",
        external_count
    )

    print(
        "\nPage Link List Check Complete"
    )
