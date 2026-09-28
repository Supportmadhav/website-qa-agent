from __future__ import annotations

import io
import json
import re
import time
import traceback
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from datetime import datetime, timezone
from html import unescape
from pathlib import PurePosixPath
from urllib.parse import urldefrag, urljoin, urlparse
import warnings

import requests
from urllib3.exceptions import InsecureRequestWarning

from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from checks.registry import (
    CHECK_ORDER,
    CHECK_REGISTRY,
)
from checks.report_enrichment import (
    collect_design_overview,
    collect_seo_overview,
    collect_social_profiles,
    design_metric_findings,
    seo_metric_findings,
)


STATUS_MAP = {
    "pass": "pass",
    "fail": "fail",
    "warning": "warning",
    "warn": "warning",
    "info": "info",
    "error": "fail",
}


PAGE_LIST_LIMIT = 100

HTML_PAGE_EXTENSIONS = {
    "",
    ".asp",
    ".aspx",
    ".cfm",
    ".cgi",
    ".htm",
    ".html",
    ".jsp",
    ".jspx",
    ".php",
}


def _site_hostname(url: str) -> str:
    return (
        urlparse(url).hostname
        or
        ""
    ).lower().removeprefix("www.")


def _is_html_page_url(
    url: str,
    website_url: str,
) -> bool:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return False

    if _site_hostname(url) != _site_hostname(website_url):
        return False

    suffix = PurePosixPath(parsed.path).suffix.lower()
    return suffix in HTML_PAGE_EXTENSIONS


def _clean_page_title(value: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        unescape(value or ""),
    ).strip()


def _page_list_get(
    url: str,
    *,
    accept: str,
    timeout: int = 8,
):
    request_options = {
        "headers": {
            "User-Agent": (
                "Mozilla/5.0 (compatible; WebsiteQAAgent/2.1)"
            ),
            "Accept": accept,
        },
        "timeout": timeout,
        "allow_redirects": True,
    }

    try:
        return requests.get(
            url,
            verify=True,
            **request_options,
        )
    except requests.exceptions.SSLError:
        # Match the browser's existing ignore_https_errors behavior so sites
        # with an incomplete certificate chain can still be inventoried.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InsecureRequestWarning)
            return requests.get(
                url,
                verify=False,
                **request_options,
            )


def _discover_sitemap_page_items(
    website_url: str,
) -> list[dict]:
    parsed = urlparse(website_url)
    origin = f"{parsed.scheme}://{parsed.netloc}/"
    sitemap_queue = []

    try:
        robots = _page_list_get(
            urljoin(origin, "robots.txt"),
            accept="text/plain,*/*;q=0.5",
        )

        for sitemap_url in re.findall(
            r"^\s*Sitemap:\s*(\S+)",
            robots.text or "",
            flags=re.I | re.M,
        ):
            sitemap_queue.append(
                unescape(sitemap_url.strip())
            )
    except requests.RequestException:
        pass

    for path in (
        "sitemap_index.xml",
        "wp-sitemap.xml",
        "sitemap.xml",
    ):
        sitemap_queue.append(
            urljoin(origin, path)
        )

    processed_sitemaps = set()
    page_urls = []
    page_seen = set()

    while (
        sitemap_queue
        and
        len(processed_sitemaps) < 20
        and
        len(page_urls) < PAGE_LIST_LIMIT - 1
    ):
        sitemap_url = sitemap_queue.pop(0)
        sitemap_key = urldefrag(sitemap_url).url

        if (
            sitemap_key in processed_sitemaps
            or
            _site_hostname(sitemap_key) != _site_hostname(website_url)
        ):
            continue

        processed_sitemaps.add(sitemap_key)

        try:
            response = _page_list_get(
                sitemap_key,
                accept="application/xml,text/xml,*/*;q=0.5",
            )

            if response.status_code >= 400:
                continue

            locations = re.findall(
                r"<loc[^>]*>(.*?)</loc>",
                response.text or "",
                flags=re.I | re.S,
            )

        except requests.RequestException:
            continue

        for location in locations:
            clean_url = urldefrag(
                _clean_page_title(location)
            ).url

            if _site_hostname(clean_url) != _site_hostname(website_url):
                continue

            path = urlparse(clean_url).path.lower()

            if path.endswith(".xml"):
                if clean_url not in processed_sitemaps:
                    sitemap_queue.append(clean_url)
                continue

            key = clean_url.rstrip("/")

            if (
                key in page_seen
                or
                not _is_html_page_url(clean_url, website_url)
            ):
                continue

            page_seen.add(key)
            page_urls.append(
                {
                    "url": clean_url,
                    "title": "",
                }
            )

            if len(page_urls) >= PAGE_LIST_LIMIT - 1:
                break

    return page_urls


def _discover_404_page_item(
    website_url: str,
) -> dict | None:
    parsed = urlparse(website_url)
    probe_url = f"{parsed.scheme}://{parsed.netloc}/404/"

    try:
        response = _page_list_get(
            probe_url,
            accept="text/html,application/xhtml+xml",
        )

        if response.status_code != 404:
            return None

        title_match = re.search(
            r"<title[^>]*>(.*?)</title>",
            response.text[:250_000],
            flags=re.I | re.S,
        )

        return {
            "title": _clean_page_title(
                title_match.group(1)
                if title_match
                else "404 Page"
            ) or "404 Page",
            "url": probe_url,
        }

    except requests.RequestException:
        return None


def _fetch_page_list_item(
    item: dict,
    website_url: str,
) -> dict | None:
    url = item["url"]

    try:
        response = _page_list_get(
            url,
            accept="text/html,application/xhtml+xml",
        )

        final_url = urldefrag(response.url).url

        if not _is_html_page_url(final_url, website_url):
            return None

        content_type = (
            response.headers.get("content-type")
            or
            ""
        ).lower()

        html = response.text[:250_000]
        looks_like_html = bool(
            re.search(
                r"<!doctype\s+html|<html(?:\s|>)|<title(?:\s|>)",
                html,
                flags=re.I,
            )
        )

        if (
            content_type
            and
            "text/html" not in content_type
            and
            "application/xhtml+xml" not in content_type
            and
            not looks_like_html
        ):
            return None

        title_match = re.search(
            r"<title[^>]*>(.*?)</title>",
            html,
            flags=re.I | re.S,
        )

        title = _clean_page_title(
            title_match.group(1)
            if title_match
            else item.get("title")
        )

        return {
            "title": title or "Untitled page",
            "url": final_url,
        }

    except requests.RequestException:
        # Keep page-shaped links when a direct metadata request is blocked.
        # Asset extensions have already been rejected before this call.
        return {
            "title": (
                _clean_page_title(item.get("title"))
                or
                "Untitled page"
            ),
            "url": url,
        }


def _collect_website_pages(
    page,
    page_info: dict,
) -> list[dict]:
    website_url = page_info.get("final_url") or page_info.get("requested_url")
    homepage_url = urldefrag(website_url).url

    page_items = [
        {
            "title": page_info.get("title") or "Home",
            "url": homepage_url,
        }
    ]

    try:
        links = page.eval_on_selector_all(
            "a[href]",
            """
            (anchors) => anchors.map((anchor) => ({
                url: anchor.href || "",
                title:
                    (anchor.textContent || "").replace(/\\s+/g, " ").trim()
                    || anchor.getAttribute("aria-label")
                    || anchor.getAttribute("title")
                    || ""
            }))
            """,
        )
    except Exception:
        links = []

    seen = {homepage_url.rstrip("/")}
    candidates = []

    for item in _discover_sitemap_page_items(website_url):
        clean_url = urldefrag(item.get("url") or "").url
        key = clean_url.rstrip("/")

        if not clean_url or key in seen:
            continue

        seen.add(key)
        candidates.append(item)

        if len(candidates) >= PAGE_LIST_LIMIT - 1:
            break

    for link in links:
        clean_url = urldefrag(link.get("url") or "").url
        key = clean_url.rstrip("/")

        if (
            not clean_url
            or
            key in seen
            or
            not _is_html_page_url(clean_url, website_url)
        ):
            continue

        seen.add(key)
        candidates.append(
            {
                "url": clean_url,
                "title": link.get("title") or "",
            }
        )

        if len(candidates) >= PAGE_LIST_LIMIT - 1:
            break

    not_found_item = _discover_404_page_item(website_url)

    if not_found_item and len(candidates) < PAGE_LIST_LIMIT - 1:
        not_found_key = not_found_item["url"].rstrip("/")

        if not_found_key not in seen:
            seen.add(not_found_key)
            candidates.append(not_found_item)

    if candidates:
        with ThreadPoolExecutor(max_workers=8) as executor:
            fetched = executor.map(
                lambda item: _fetch_page_list_item(item, website_url),
                candidates,
            )

            final_seen = {homepage_url.rstrip("/")}

            for item in fetched:
                if not item:
                    continue

                key = item["url"].rstrip("/")
                if key in final_seen:
                    continue

                final_seen.add(key)
                page_items.append(item)

    return [
        {
            "page_no": index,
            "title": item["title"],
            "url": item["url"],
        }
        for index, item in enumerate(page_items, start=1)
    ]


def normalize_url(
    url: str,
) -> str:
    url = (
        url
        or
        ""
    ).strip()

    if not url:
        raise ValueError(
            "Website URL is required."
        )

    if not url.startswith(
        (
            "http://",
            "https://",
        )
    ):
        url = (
            "https://"
            +
            url
        )

    parsed = urlparse(
        url
    )

    if not parsed.netloc:
        raise ValueError(
            "Please enter a valid website URL."
        )

    return url


def _ordered_selection(
    selected_checks: list[str],
) -> list[str]:
    selected = set(
        selected_checks
    )

    unknown = (
        selected.difference(
            CHECK_REGISTRY.keys()
        )
    )

    if unknown:
        raise ValueError(
            "Unknown QA check(s): "
            +
            ", ".join(
                sorted(
                    unknown
                )
            )
        )

    return [
        check_id
        for check_id in CHECK_ORDER
        if check_id in selected
    ]


def _extract_structured_records(
    output: str,
):
    """
    Pull machine-readable rows out of QA module output.

    Supported:
        QA_IMAGE_ASSET|{json}
        QA_PAGE_SPEED|{json}
        QA_PAGE_LINK|{json}
        QA_BLOG_DATA|{json}
        QA_BROWSER_COMPAT|{json}
    """

    clean_lines = []

    image_assets = []
    page_speed_data = None
    page_links = []
    blog_data = None
    browser_compatibility_data = None

    for line in (
        output
        or
        ""
    ).splitlines():

        if line.startswith(
            "QA_IMAGE_ASSET|"
        ):
            payload = (
                line.split(
                    "|",
                    1,
                )[1]
            )

            try:
                image_assets.append(
                    json.loads(
                        payload
                    )
                )

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                pass

            continue

        if line.startswith(
            "QA_PAGE_SPEED|"
        ):
            payload = (
                line.split(
                    "|",
                    1,
                )[1]
            )

            try:
                page_speed_data = (
                    json.loads(
                        payload
                    )
                )

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                page_speed_data = None

            continue

        if line.startswith(
            "QA_PAGE_LINK|"
        ):
            payload = (
                line.split(
                    "|",
                    1,
                )[1]
            )

            try:
                page_links.append(
                    json.loads(
                        payload
                    )
                )

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                pass

            continue

        if line.startswith(
            "QA_BLOG_DATA|"
        ):
            payload = (
                line.split(
                    "|",
                    1,
                )[1]
            )

            try:
                blog_data = (
                    json.loads(
                        payload
                    )
                )

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                blog_data = None

            continue

        if line.startswith(
            "QA_BROWSER_COMPAT|"
        ):
            payload = (
                line.split(
                    "|",
                    1,
                )[1]
            )

            try:
                browser_compatibility_data = (
                    json.loads(
                        payload
                    )
                )

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                browser_compatibility_data = None

            continue

        clean_lines.append(
            line
        )

    return {
        "output":
            "\n".join(
                clean_lines
            ).strip(),

        "image_assets":
            image_assets,

        "page_speed_data":
            page_speed_data,

        "page_links":
            page_links,

        "blog_data":
            blog_data,

        "browser_compatibility_data":
            browser_compatibility_data,
    }


def _clean_console_line(
    line: str,
) -> str:
    line = (
        line
        or
        ""
    ).strip()

    return re.sub(
        r"^[#>*\-\s]+",
        "",
        line,
    ).strip()


def _finding_from_line(
    line: str,
    check_label: str,
):
    clean = (
        _clean_console_line(
            line
        )
    )

    if not clean:
        return None

    status_match = re.match(
        r"^STATUS\s*:\s*"
        r"(PASS|FAIL|WARNING|WARN|INFO|ERROR)"
        r"\b\s*(.*)$",
        clean,
        flags=re.IGNORECASE,
    )

    if status_match:
        raw_status = (
            status_match
            .group(1)
            .lower()
        )

        trailing = (
            status_match
            .group(2)
            .strip(
                " |-:"
            )
        )

        return {
            "status":
                STATUS_MAP[
                    raw_status
                ],

            "title":
                check_label,

            "message":
                trailing
                or
                "Status reported by check.",

            "raw":
                clean,
        }

    explicit_match = re.match(
        r"^(PASS|FAIL|WARNING|WARN|INFO|ERROR)"
        r"\b\s*(?:\||:|-)?\s*(.*)$",
        clean,
        flags=re.IGNORECASE,
    )

    if not explicit_match:
        return None

    raw_status = (
        explicit_match
        .group(1)
        .lower()
    )

    remainder = (
        explicit_match
        .group(2)
        .strip()
    )

    parts = [
        part.strip()
        for part in remainder.split(
            "|"
        )
        if part.strip()
    ]

    if not parts:
        title = check_label
        message = ""

    elif len(
        parts
    ) == 1:
        title = parts[0]
        message = ""

    else:
        title = parts[0]
        message = " | ".join(
            parts[1:]
        )

    return {
        "status":
            STATUS_MAP[
                raw_status
            ],

        "title":
            title
            or
            check_label,

        "message":
            message,

        "raw":
            clean,
    }


def _parse_findings(
    output: str,
    check_label: str,
    execution_error: str | None,
):
    findings = []
    seen = set()

    for line in (
        output
        or
        ""
    ).splitlines():
        finding = (
            _finding_from_line(
                line,
                check_label,
            )
        )

        if not finding:
            continue

        key = (
            finding[
                "status"
            ],
            finding[
                "title"
            ],
            finding[
                "message"
            ],
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        findings.append(
            finding
        )

    if execution_error:
        findings.insert(
            0,
            {
                "status":
                    "fail",

                "title":
                    "Check execution error",

                "message":
                    execution_error,

                "raw":
                    execution_error,
            },
        )

    if not findings:
        findings.append(
            {
                "status":
                    "pass",

                "title":
                    check_label,

                "message":
                    (
                        "Check completed without an explicit "
                        "FAIL or WARNING status."
                    ),

                "raw":
                    "",
            }
        )

    return findings


def _module_status(
    findings,
):
    failed_findings = [
        finding
        for finding in findings
        if finding.get(
            "status"
        ) == "fail"
    ]

    # A module that could not execute is a real failed check regardless of
    # how many findings were produced.
    if any(
        finding.get(
            "title",
            "",
        ).strip().lower()
        == "check execution error"
        for finding in failed_findings
    ):
        return "fail"

    # Keep an isolated failed finding visible as "needs attention" without
    # making the whole report tab look like the entire check failed.
    if len(
        failed_findings
    ) >= 2:
        return "fail"

    if failed_findings or any(
        finding.get(
            "status"
        ) == "warning"
        for finding in findings
    ):
        return "warning"

    return "pass"


def _page_speed_module_status(
    page_speed_data,
):
    """Return the worst overall Lighthouse status across device strategies.

    Individual Lighthouse metrics can fail while the weighted performance
    score remains in the "needs improvement" range. The report tab represents
    the check's overall score, so it must use the mobile/desktop score statuses
    instead of the worst diagnostic row.
    """
    strategies = (
        (page_speed_data or {}).get(
            "strategies",
            {},
        )
        or
        {}
    )

    statuses = {
        strategy.get(
            "overall_status"
        )
        for strategy in strategies.values()
        if isinstance(
            strategy,
            dict,
        )
    }

    for status in (
        "fail",
        "warning",
        "pass",
        "info",
    ):
        if status in statuses:
            return status

    return None


def _check_status(
    check_id,
    findings,
    page_speed_data=None,
):
    status = _module_status(
        findings
    )

    if check_id == "page_speed":
        page_speed_status = (
            _page_speed_module_status(
                page_speed_data
            )
        )

        if page_speed_status:
            return page_speed_status

    return status


def _finding_counts(
    findings,
):
    counts = {
        "pass": 0,
        "warning": 0,
        "fail": 0,
        "info": 0,
    }

    for finding in findings:
        status = (
            finding.get(
                "status"
            )
        )

        if status in counts:
            counts[
                status
            ] += 1

    return counts


# ============================================================
# CONTENT DETAILS
# ============================================================

def _parse_spelling_issues_from_output(
    output,
):
    issues = []
    current = None

    for raw_line in (
        output
        or
        ""
    ).splitlines():
        line = (
            raw_line.strip()
        )

        if line.startswith(
            "Word |"
        ):
            if current:
                issues.append(
                    current
                )

            current = {
                "type":
                    "spelling",

                "status":
                    "warning",

                "incorrect":
                    (
                        line.split(
                            "|",
                            1,
                        )[1]
                        .strip()
                    ),

                "suggestion":
                    "",

                "location":
                    "",

                "context":
                    "",

                "rule":
                    "Possible spelling error",
            }

            continue

        if not current:
            continue

        if line.startswith(
            "Suggestion |"
        ):
            current[
                "suggestion"
            ] = (
                line.split(
                    "|",
                    1,
                )[1]
                .strip()
            )

        elif line.startswith(
            "Location |"
        ):
            current[
                "location"
            ] = (
                line.split(
                    "|",
                    1,
                )[1]
                .strip()
            )

        elif line.startswith(
            "Content |"
        ):
            current[
                "context"
            ] = (
                line.split(
                    "|",
                    1,
                )[1]
                .strip()
            )

    if current:
        issues.append(
            current
        )

    unique = []
    seen = set()

    for issue in issues:
        key = (
            issue.get(
                "incorrect",
                "",
            ).lower(),

            issue.get(
                "location",
                "",
            ),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique.append(
            issue
        )

    return unique



# ============================================================
# SPELLING CONFIDENCE FILTER
# ============================================================

_PROTECTED_SITE_WORDS = {
    "clientele",
    "fertilisers",
    "fertiliser",
    "modularization",
    "modularisation",
    "self-reliant",
    "self-reliance",
    "in-house",
    "tankages",
    "skids",
    "petrochemicals",
    "petrochemical",
    "phenolics",
    "fluorine",
    "turnarounds",
    "scaffolding",
    "refractory",
    "vrishal",
    "vishal",
    "deepit",
}


_COMPANY_CONTEXT_WORDS = re.compile(
    r"\b("
    r"limited|ltd|pvt|private|industries|industry|"
    r"chemicals|chemical|energy|energies|enterprise|"
    r"engineering|petrochemicals|petrochemical|"
    r"phenolics|fluorine|corporation|group|company|"
    r"technologies|technology|projects|international"
    r")\b",
    flags=re.IGNORECASE,
)


def _ascii_word(value):
    normalized = unicodedata.normalize(
        "NFKD",
        str(
            value
            or
            ""
        )
        .replace(
            "’",
            "'",
        )
        .replace(
            "‘",
            "'",
        ),
    )

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )


def _edit_distance(
    left,
    right,
):
    left = left or ""
    right = right or ""

    previous = list(
        range(
            len(
                right
            )
            +
            1
        )
    )

    for (
        left_index,
        left_char,
    ) in enumerate(
        left,
        start=1,
    ):
        current = [
            left_index
        ]

        for (
            right_index,
            right_char,
        ) in enumerate(
            right,
            start=1,
        ):
            current.append(
                min(
                    current[
                        right_index
                        -
                        1
                    ]
                    +
                    1,

                    previous[
                        right_index
                    ]
                    +
                    1,

                    previous[
                        right_index
                        -
                        1
                    ]
                    +
                    (
                        0
                        if left_char ==
                        right_char
                        else
                        1
                    ),
                )
            )

        previous = current

    return previous[
        -1
    ]


def _keep_spelling_issue(
    issue,
):
    incorrect = (
        issue.get(
            "incorrect",
            "",
        )
        .strip()
    )

    suggestion = (
        issue.get(
            "suggestion",
            "",
        )
        .strip()
    )

    context = (
        issue.get(
            "context",
            "",
        )
        .strip()
    )

    location = (
        issue.get(
            "location",
            "",
        )
        .strip()
    )

    if not incorrect:
        return False

    incorrect_ascii = (
        _ascii_word(
            incorrect
        )
        .lower()
        .strip()
    )

    suggestion_ascii = (
        _ascii_word(
            suggestion
        )
        .lower()
        .strip()
    )

    # Curly apostrophe, accents or capitalization alone are not spelling errors.
    if (
        suggestion_ascii
        and
        incorrect_ascii ==
        suggestion_ascii
    ):
        return False

    if (
        incorrect_ascii in
        _PROTECTED_SITE_WORDS
    ):
        return False

    valid_variant_pairs = {
        frozenset(
            (
                "fertilisers",
                "fertilizers",
            )
        ),
        frozenset(
            (
                "fertiliser",
                "fertilizer",
            )
        ),
    }

    if (
        suggestion_ascii
        and
        frozenset(
            (
                incorrect_ascii,
                suggestion_ascii,
            )
        )
        in
        valid_variant_pairs
    ):
        return False

    is_small_company_heading = bool(
        re.match(
            r"^H[4-6]\b",
            location,
            flags=re.IGNORECASE,
        )
    )

    starts_capitalized = (
        incorrect[
            :1
        ].isupper()
    )

    company_context = bool(
        _COMPANY_CONTEXT_WORDS.search(
            context
        )
    )

    context_word_count = len(
        re.findall(
            r"[A-Za-z][A-Za-z'’-]*",
            context,
        )
    )

    distance = (
        _edit_distance(
            incorrect_ascii,
            suggestion_ascii,
        )
        if suggestion_ascii
        else
        999
    )

    # Client/company card headings are commonly proper nouns.
    # Keep only a very high-confidence typo in a longer word.
    if (
        starts_capitalized
        and
        (
            company_context
            or
            (
                is_small_company_heading
                and
                context_word_count <= 8
            )
        )
    ):
        if not (
            distance == 1
            and
            len(
                incorrect_ascii
            )
            >=
            8
        ):
            return False

    if (
        starts_capitalized
        and
        is_small_company_heading
        and
        len(
            incorrect_ascii
        )
        <=
        7
    ):
        return False

    # Real high-confidence typos such as Maintenanace -> maintenance remain.
    return True


def _filter_spelling_issues(
    issues,
):
    filtered = []
    seen = set()

    for issue in (
        issues
        or
        []
    ):
        if not _keep_spelling_issue(
            issue
        ):
            continue

        key = (
            _ascii_word(
                issue.get(
                    "incorrect",
                    "",
                )
            ).lower(),

            issue.get(
                "location",
                "",
            ),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        filtered.append(
            issue
        )

    return filtered


def _basic_grammar_issues(
    page,
):
    try:
        blocks = page.evaluate(
            """
            () => {
                const selector =
                    "h1,h2,h3,h4,h5,h6,p,li,label,button";

                const ignored =
                    ".skiptranslate,.goog-te-gadget,"
                    + ".goog-te-menu-frame,.screen-reader-text,"
                    + ".sr-only,.swiper-slide-duplicate,"
                    + "[aria-hidden='true']";

                const output = [];
                const seen = new Set();

                document
                    .querySelectorAll(
                        selector
                    )
                    .forEach(
                        (element) => {
                            if (
                                element.closest(
                                    ignored
                                )
                            ) {
                                return;
                            }

                            const style =
                                getComputedStyle(
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
                                ||
                                rect.width <= 0
                                ||
                                rect.height <= 0
                            ) {
                                return;
                            }

                            const text =
                                (
                                    element.innerText
                                    ||
                                    element.textContent
                                    ||
                                    ""
                                )
                                .replace(
                                    /\\s+/g,
                                    " "
                                )
                                .trim();

                            if (
                                text.length < 3
                                ||
                                seen.has(
                                    text
                                )
                            ) {
                                return;
                            }

                            seen.add(
                                text
                            );

                            output.push({
                                tag:
                                    element.tagName,

                                text:
                                    text
                            });
                        }
                    );

                return output;
            }
            """
        )

    except Exception:
        blocks = []

    issues = []
    seen = set()

    phrase_rules = [
        (
            r"\bthese is\b",
            "these are",
            "Subject-verb agreement",
        ),
        (
            r"\bthose is\b",
            "those are",
            "Subject-verb agreement",
        ),
        (
            r"\bthis are\b",
            "this is",
            "Subject-verb agreement",
        ),
        (
            r"\bit are\b",
            "it is",
            "Subject-verb agreement",
        ),
        (
            r"\bwe is\b",
            "we are",
            "Subject-verb agreement",
        ),
        (
            r"\bthey is\b",
            "they are",
            "Subject-verb agreement",
        ),
        (
            r"\byou is\b",
            "you are",
            "Subject-verb agreement",
        ),
        (
            r"\bdoes not shows\b",
            "does not show",
            "Verb form after auxiliary",
        ),
        (
            r"\bdo not shows\b",
            "do not show",
            "Verb form after auxiliary",
        ),
        (
            r"\bdid not showed\b",
            "did not show",
            "Verb form after auxiliary",
        ),
        (
            r"\bmore better\b",
            "better",
            "Double comparative",
        ),
        (
            r"\bmore easier\b",
            "easier",
            "Double comparative",
        ),
        (
            r"\bwe are provide\b",
            "we provide / we are providing",
            "Verb construction",
        ),
        (
            r"\bwe provides\b",
            "we provide",
            "Subject-verb agreement",
        ),
    ]

    for index, block in enumerate(
        blocks,
        start=1,
    ):
        text = (
            block.get(
                "text",
                "",
            )
        )

        tag = (
            block.get(
                "tag",
                "",
            )
        )

        location = (
            f"{tag} | Block {index}"
        )

        for match in re.finditer(
            r"\b([A-Za-z][A-Za-z'-]{1,})\s+\1\b",
            text,
            flags=re.IGNORECASE,
        ):
            incorrect = (
                match.group(
                    0
                )
            )

            key = (
                "Repeated word",
                incorrect.lower(),
                location,
            )

            if key not in seen:
                seen.add(
                    key
                )

                issues.append(
                    {
                        "type":
                            "grammar",

                        "status":
                            "warning",

                        "incorrect":
                            incorrect,

                        "suggestion":
                            match.group(
                                1
                            ),

                        "location":
                            location,

                        "context":
                            text[
                                :320
                            ],

                        "rule":
                            "Repeated word",
                    }
                )

        for match in re.finditer(
            r"\b([A-Za-z0-9]+)\s+([,.;:!?])",
            text,
        ):
            incorrect = (
                match.group(
                    0
                )
            )

            suggestion = (
                match.group(
                    1
                )
                +
                match.group(
                    2
                )
            )

            key = (
                "Space before punctuation",
                incorrect,
                location,
            )

            if key not in seen:
                seen.add(
                    key
                )

                issues.append(
                    {
                        "type":
                            "grammar",

                        "status":
                            "warning",

                        "incorrect":
                            incorrect,

                        "suggestion":
                            suggestion,

                        "location":
                            location,

                        "context":
                            text[
                                :320
                            ],

                        "rule":
                            "Space before punctuation",
                    }
                )

        for match in re.finditer(
            r"([A-Za-z])([,;:])([A-Za-z])",
            text,
        ):
            incorrect = (
                match.group(
                    0
                )
            )

            suggestion = (
                match.group(
                    1
                )
                +
                match.group(
                    2
                )
                +
                " "
                +
                match.group(
                    3
                )
            )

            key = (
                "Missing space after punctuation",
                incorrect,
                location,
            )

            if key not in seen:
                seen.add(
                    key
                )

                issues.append(
                    {
                        "type":
                            "grammar",

                        "status":
                            "warning",

                        "incorrect":
                            incorrect,

                        "suggestion":
                            suggestion,

                        "location":
                            location,

                        "context":
                            text[
                                :320
                            ],

                        "rule":
                            "Missing space after punctuation",
                    }
                )

        for (
            pattern,
            suggestion,
            rule,
        ) in phrase_rules:
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            incorrect = (
                match.group(
                    0
                )
            )

            key = (
                rule,
                incorrect.lower(),
                location,
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            issues.append(
                {
                    "type":
                        "grammar",

                    "status":
                        "warning",

                    "incorrect":
                        incorrect,

                    "suggestion":
                        suggestion,

                    "location":
                        location,

                    "context":
                        text[
                            :320
                        ],

                    "rule":
                        rule,
                }
            )

    return issues


def _run_one_check(
    check_id,
    page,
    playwright,
    url,
):
    check = (
        CHECK_REGISTRY[
            check_id
        ]
    )

    output = io.StringIO()

    execution_status = (
        "completed"
    )

    error = None

    started = (
        time.perf_counter()
    )

    try:
        with redirect_stdout(
            output
        ):
            check[
                "runner"
            ](
                page=page,
                playwright=playwright,
                url=url,
            )

    except Exception as exc:
        execution_status = (
            "error"
        )

        error = str(
            exc
        )

        with redirect_stdout(
            output
        ):
            print(
                f"ERROR | "
                f"{check['label']} | "
                f"{exc}"
            )

            traceback.print_exc()

    duration_seconds = round(
        time.perf_counter()
        -
        started,
        2,
    )

    raw_output = (
        output
        .getvalue()
        .strip()
    )

    structured = (
        _extract_structured_records(
            raw_output
        )
    )

    display_output = (
        structured[
            "output"
        ]
    )

    findings = (
        _parse_findings(
            display_output,
            check[
                "label"
            ],
            error,
        )
    )

    content_issues = []

    if check_id == "content":
        spelling_issues = (
            _filter_spelling_issues(
                _parse_spelling_issues_from_output(
                    display_output
                )
            )
        )

        grammar_issues = (
            _basic_grammar_issues(
                page
            )
        )

        content_issues = (
            spelling_issues
            +
            grammar_issues
        )

        findings = [
            finding
            for finding in findings
            if (
                finding.get(
                    "title",
                    "",
                )
                .strip()
                .lower()
                not in {
                    "spelling",
                    "grammar analysis",
                }
            )
        ]

        if spelling_issues:
            for issue in spelling_issues:
                findings.append(
                    {
                        "status":
                            "warning",

                        "title":
                            (
                                "Spelling: "
                                +
                                issue.get(
                                    "incorrect",
                                    "",
                                )
                            ),

                        "message":
                            (
                                "Suggestion: "
                                +
                                (
                                    issue.get(
                                        "suggestion"
                                    )
                                    or
                                    "Review manually"
                                )
                                +
                                " | "
                                +
                                issue.get(
                                    "location",
                                    "",
                                )
                            ),

                        "raw":
                            "",
                    }
                )

        else:
            findings.append(
                {
                    "status":
                        "pass",

                    "title":
                        "Spelling",

                    "message":
                        "No detailed spelling issues were detected.",

                    "raw":
                        "",
                }
            )

        if grammar_issues:
            for issue in grammar_issues:
                findings.append(
                    {
                        "status":
                            "warning",

                        "title":
                            (
                                "Grammar: "
                                +
                                issue.get(
                                    "rule",
                                    "Possible grammar issue",
                                )
                            ),

                        "message":
                            (
                                issue.get(
                                    "incorrect",
                                    "",
                                )
                                +
                                " -> "
                                +
                                issue.get(
                                    "suggestion",
                                    "",
                                )
                                +
                                " | "
                                +
                                issue.get(
                                    "location",
                                    "",
                                )
                            ),

                        "raw":
                            "",
                    }
                )

        else:
            findings.append(
                {
                    "status":
                        "info",

                    "title":
                        "Basic Grammar Analysis",

                    "message":
                        (
                            "No obvious issue found by the local "
                            "high-confidence grammar rules. "
                            "Full LanguageTool analysis remains disabled."
                        ),

                    "raw":
                        "",
                }
            )

    status = _check_status(
        check_id,
        findings,
        structured[
            "page_speed_data"
        ],
    )

    return {
        "id":
            check_id,

        "label":
            check[
                "label"
            ],

        "category":
            check[
                "category"
            ],

        "status":
            status,

        "execution_status":
            execution_status,

        "error":
            error,

        "duration_seconds":
            duration_seconds,

        "counts":
            _finding_counts(
                findings
            ),

        "findings":
            findings,

        "image_assets":
            structured[
                "image_assets"
            ],

        "page_speed_data":
            structured[
                "page_speed_data"
            ],

        "content_issues":
            content_issues,

        "page_links":
            structured[
                "page_links"
            ],

        "blog_data":
            structured[
                "blog_data"
            ],

        "browser_compatibility_data":
            structured[
                "browser_compatibility_data"
            ],

        "output":
            display_output,
    }


def _report_summary(
    results,
):
    check_summary = {
        "total":
            len(
                results
            ),

        "pass":
            0,

        "warning":
            0,

        "fail":
            0,
    }

    finding_summary = {
        "total":
            0,

        "pass":
            0,

        "warning":
            0,

        "fail":
            0,

        "info":
            0,
    }

    for result in results:
        status = (
            result.get(
                "status"
            )
        )

        if status in check_summary:
            check_summary[
                status
            ] += 1

        counts = (
            result.get(
                "counts",
                {},
            )
        )

        for key in (
            "pass",
            "warning",
            "fail",
            "info",
        ):
            value = (
                counts.get(
                    key,
                    0,
                )
            )

            finding_summary[
                key
            ] += value

            finding_summary[
                "total"
            ] += value

    return (
        check_summary,
        finding_summary,
    )


def _install_performance_observers(
    page,
):
    page.add_init_script(
        """
        (() => {
            window.__qaPerf = {
                lcp: [],
                layoutShifts: [],
                longTasks: []
            };

            try {
                new PerformanceObserver(
                    (list) => {
                        window.__qaPerf.lcp.push(
                            ...list.getEntries().map(
                                entry => ({
                                    startTime:
                                        entry.startTime,
                                    size:
                                        entry.size || 0
                                })
                            )
                        );
                    }
                ).observe({
                    type:
                        "largest-contentful-paint",
                    buffered:
                        true
                });
            } catch (error) {}

            try {
                new PerformanceObserver(
                    (list) => {
                        window.__qaPerf.layoutShifts.push(
                            ...list.getEntries().map(
                                entry => ({
                                    value:
                                        entry.value || 0,
                                    hadRecentInput:
                                        !!entry.hadRecentInput
                                })
                            )
                        );
                    }
                ).observe({
                    type:
                        "layout-shift",
                    buffered:
                        true
                });
            } catch (error) {}

            try {
                new PerformanceObserver(
                    (list) => {
                        window.__qaPerf.longTasks.push(
                            ...list.getEntries().map(
                                entry => ({
                                    duration:
                                        entry.duration || 0,
                                    startTime:
                                        entry.startTime || 0
                                })
                            )
                        );
                    }
                ).observe({
                    type:
                        "longtask",
                    buffered:
                        true
                });
            } catch (error) {}
        })();
        """
    )


def run_scan(
    url: str,
    selected_checks: list[str],
):
    scan_started = (
        time.perf_counter()
    )

    url = normalize_url(
        url
    )

    ordered_checks = (
        _ordered_selection(
            selected_checks
        )
    )

    if not ordered_checks:
        raise ValueError(
            "Select at least one QA check."
        )

    results = []

    with sync_playwright() as p:
        browser = (
            p.chromium.launch(
                headless=True
            )
        )

        context = (
            browser.new_context(
                viewport={
                    "width": 1366,
                    "height": 768,
                },

                ignore_https_errors=True,
            )
        )

        page = (
            context.new_page()
        )

        # Page Speed needs its observers installed before navigation.
        if (
            "page_speed"
            in
            ordered_checks
        ):
            _install_performance_observers(
                page
            )

        # =====================================
        # FASTER NAVIGATION
        # =====================================
        # DOMContentLoaded is enough for most QA modules and prevents
        # one slow ad/tracker/media request from blocking the whole scan.
        # =====================================

        try:
            response = (
                page.goto(
                    url,
                    wait_until=
                        "domcontentloaded",
                    timeout=
                        30_000,
                )
            )

        except PlaywrightTimeoutError:
            # A partially loaded page can still be testable.
            response = None

        # Page Speed needs load timing if it becomes available,
        # but do not let it block the scan indefinitely.
        if (
            "page_speed"
            in
            ordered_checks
        ):
            try:
                page.wait_for_load_state(
                    "load",
                    timeout=
                        12_000,
                )

            except PlaywrightTimeoutError:
                pass

        else:
            # Short stabilization only.
            page.wait_for_timeout(
                250
            )

        page_info = {
            "requested_url":
                url,

            "final_url":
                page.url,

            "title":
                page.title(),

            "http_status":
                (
                    response.status
                    if response
                    else None
                ),
        }

        website_pages = (
            _collect_website_pages(
                page,
                page_info,
            )
            if "website_page_list" in ordered_checks
            else []
        )

        for check_id in ordered_checks:
            result = _run_one_check(
                check_id=check_id,
                page=page,
                playwright=p,
                url=url,
            )

            try:
                if check_id == "social_media":
                    result["social_profiles"] = collect_social_profiles(page)
                elif check_id == "meta":
                    overview = collect_seo_overview(page)
                    result["seo_overview"] = overview
                    result["findings"].extend(seo_metric_findings(overview))
                elif check_id == "layout_design":
                    overview = collect_design_overview(page)
                    usability_checks = (
                        "Very Small Text", "Text Clipping", "Line Height",
                        "Wide Paragraphs", "Image Distortion",
                        "Small Buttons / CTAs",
                    )
                    by_title = {
                        finding.get("title"): finding
                        for finding in result.get("findings", [])
                    }
                    passed = sum(
                        by_title.get(title, {}).get("status") == "pass"
                        for title in usability_checks
                    )
                    overview["design_score"] = min(
                        100,
                        overview["design_score"] + round(20 * passed / 6),
                    )
                    result["design_overview"] = overview
                    result["findings"].extend(design_metric_findings(overview))

                result["status"] = _check_status(
                    check_id,
                    result["findings"],
                    result.get("page_speed_data"),
                )
                result["counts"] = _finding_counts(result["findings"])
            except Exception as exc:
                # An optional report preview must never invalidate the
                # underlying QA check or the rest of the scan.
                result["report_enrichment_error"] = str(exc)

            results.append(result)

        context.close()
        browser.close()

    (
        check_summary,
        finding_summary,
    ) = _report_summary(
        results
    )

    total_duration = round(
        time.perf_counter()
        -
        scan_started,
        2,
    )

    return {
        "generated_at":
            (
                datetime
                .now(
                    timezone.utc
                )
                .isoformat()
            ),

        "page":
            page_info,

        "website_pages":
            website_pages,

        "selected_checks":
            ordered_checks,

        "total_selected":
            len(
                ordered_checks
            ),

        "scan_duration_seconds":
            total_duration,

        "check_summary":
            check_summary,

        "finding_summary":
            finding_summary,

        "summary":
            check_summary,

        "results":
            results,
    }


if __name__ == "__main__":
    print(
        "Website QA Agent"
    )

    print(
        "----------------"
    )

    entered_url = input(
        "Enter website URL: "
    )

    print(
        "\nAvailable checks:"
    )

    for index, check_id in enumerate(
        CHECK_ORDER,
        start=1,
    ):
        print(
            f"{index}. "
            f"{CHECK_REGISTRY[check_id]['label']} "
            f"[{check_id}]"
        )

    raw = input(
        "\nEnter check IDs separated by commas, "
        "or type ALL: "
    ).strip()

    selected = (
        CHECK_ORDER.copy()
        if raw.upper()
        ==
        "ALL"
        else [
            value.strip()
            for value in raw.split(
                ","
            )
            if value.strip()
        ]
    )

    report = run_scan(
        entered_url,
        selected,
    )

    print(
        "\nScanning:",
        report[
            "page"
        ][
            "final_url"
        ],
    )

    print(
        "Total scan time:",
        report[
            "scan_duration_seconds"
        ],
        "seconds",
    )

    for result in report[
        "results"
    ]:
        print(
            "\n"
            +
            "=" * 70
        )

        print(
            result[
                "label"
            ],
            "|",
            result[
                "status"
            ].upper(),
            "|",
            result[
                "duration_seconds"
            ],
            "s",
        )

        print(
            "=" * 70
        )

        print(
            result[
                "output"
            ]
            or
            "No console output."
        )
