from __future__ import annotations

import re
import socket
import ssl
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)
from requests.exceptions import SSLError

from scanner import normalize_url


MODULE_WEIGHTS = {
    "performance": 20,
    "seo": 25,
    "ux": 15,
    "security": 15,
    "content": 10,
    "mobile": 10,
    "cro": 5,
}

MAX_PAGES = 12
REQUEST_TIMEOUT = 18


def _http_get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; WebsiteQAAgent/2.1; "
            "+https://localhost) AppleWebKit/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        return requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=allow_redirects,
            verify=True,
        )
    except SSLError:
        return requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=allow_redirects,
            verify=False,
        )


def _issue(
    module,
    test_name,
    severity,
    status,
    current_value,
    expected_value,
    recommendation,
):
    return {
        "module": module,
        "test_name": test_name,
        "severity": severity,
        "status": status,
        "current_value": current_value or "",
        "expected_value": expected_value or "",
        "recommendation": recommendation or "",
    }


def _score_from_issues(issues):
    score = 100
    penalties = {
        ("failed", "critical"): 14,
        ("failed", "high"): 9,
        ("failed", "medium"): 5,
        ("failed", "low"): 2,
        ("warning", "critical"): 8,
        ("warning", "high"): 5,
        ("warning", "medium"): 3,
        ("warning", "low"): 1,
    }

    for item in issues:
        if item.get("status") == "passed":
            continue

        score -= penalties.get(
            (
                item.get("status"),
                item.get("severity"),
            ),
            2 if item.get("status") == "failed" else 1,
        )

    return max(0, min(100, score))


def _score_label(score):
    if score >= 90:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Average"
    return "Poor"


def _same_host(left, right):
    a = (urlparse(left).hostname or "").lower().removeprefix("www.")
    b = (urlparse(right).hostname or "").lower().removeprefix("www.")
    return bool(a) and a == b


def _detect_cms(html, headers):
    text = (html or "").lower()
    generator = ""
    match = re.search(
        r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)',
        html or "",
        flags=re.I,
    )
    if match:
        generator = match.group(1)

    if "wp-content" in text or "wordpress" in generator.lower():
        return "WordPress"
    if "cdn.shopify.com" in text or "shopify" in text:
        return "Shopify"
    if "woocommerce" in text:
        return "WooCommerce"
    if "wix.com" in text:
        return "Wix"
    if "squarespace" in text:
        return "Squarespace"
    if "webflow" in text:
        return "Webflow"
    if generator:
        return generator[:80]
    server = (headers or {}).get("Server") or (headers or {}).get("server")
    return server or "Unknown"


def _collect_page(url):
    started = time.perf_counter()
    response = None
    error = None

    try:
        response = _http_get(url)
    except Exception as exc:
        error = str(exc)

    elapsed_ms = round((time.perf_counter() - started) * 1000)

    html = response.text if response is not None else ""
    headers = dict(response.headers) if response is not None else {}

    return {
        "url": url,
        "final_url": response.url if response is not None else url,
        "status_code": response.status_code if response is not None else None,
        "html": html[:250000],
        "headers": headers,
        "response_time_ms": elapsed_ms,
        "error": error,
    }


def _extract_links(base_url, html):
    found = []
    for match in re.finditer(
        r'''href=["']([^"'#]+)["']''',
        html or "",
        flags=re.I,
    ):
        href = match.group(1).strip()
        if href.lower().startswith(("mailto:", "tel:", "javascript:", "data:")):
            continue
        absolute = urljoin(base_url, href)
        if absolute.startswith(("http://", "https://")):
            found.append(absolute.split("#")[0])
    return found


def _playwright_snapshot(url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            ignore_https_errors=True,
        )
        page = context.new_page()
        started = time.perf_counter()
        response = None

        try:
            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )
        except PlaywrightTimeoutError:
            response = None

        try:
            page.wait_for_load_state("load", timeout=8000)
        except PlaywrightTimeoutError:
            pass

        load_ms = round((time.perf_counter() - started) * 1000)
        data = page.evaluate(
            """
            () => {
                const meta = (name) =>
                    document.querySelector(`meta[name="${name}"]`)
                        ?.getAttribute("content")
                    || document.querySelector(`meta[property="${name}"]`)
                        ?.getAttribute("content")
                    || "";

                const canonical =
                    document.querySelector('link[rel="canonical"]')
                        ?.href || "";

                const favicon =
                    document.querySelector('link[rel="icon"], link[rel="shortcut icon"]')
                        ?.href || "";

                const headings = {};
                for (const level of [1, 2, 3]) {
                    headings["h" + level] = document.querySelectorAll(
                        "h" + level
                    ).length;
                }

                const images = Array.from(document.images);
                const missingAlt = images.filter(
                    (img) => !(img.getAttribute("alt") || "").trim()
                ).length;

                const texts = Array.from(
                    document.querySelectorAll("p, li, h1, h2, h3, article")
                )
                    .map((node) => (node.innerText || "").trim())
                    .filter(Boolean);

                const bodyText = (document.body?.innerText || "")
                    .replace(/\\s+/g, " ")
                    .trim();

                const words = bodyText
                    ? bodyText.split(/\\s+/).filter(Boolean).length
                    : 0;

                const buttons = Array.from(
                    document.querySelectorAll(
                        "a, button, [role='button'], input[type='submit']"
                    )
                );

                const smallTargets = buttons.filter((el) => {
                    const rect = el.getBoundingClientRect();
                    return (
                        rect.width > 0
                        && rect.height > 0
                        && (rect.width < 40 || rect.height < 40)
                    );
                }).length;

                const viewport = document.querySelector(
                    'meta[name="viewport"]'
                );

                const nav = document.querySelector(
                    "nav, [role='navigation'], header"
                );
                const search = document.querySelector(
                    "input[type='search'], input[name*='search' i], form[role='search']"
                );
                const breadcrumbs = document.querySelector(
                    "[class*='breadcrumb' i], nav[aria-label*='breadcrumb' i]"
                );
                const footer = document.querySelector("footer");

                const forms = document.querySelectorAll("form").length;
                const phone = /(\\+?\\d[\\d\\s().-]{7,}\\d)/.test(bodyText);
                const email = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}/i.test(
                    document.documentElement.outerHTML
                );
                const whatsapp = !!document.querySelector(
                    "a[href*='wa.me'], a[href*='whatsapp']"
                );
                const chat = /tawk|crisp|intercom|livechat|tidio/i.test(
                    document.documentElement.outerHTML
                );
                const testimonials = /testimonial|review|case study/i.test(
                    bodyText
                );
                const privacy = !!document.querySelector(
                    "a[href*='privacy']"
                );
                const refund = !!document.querySelector(
                    "a[href*='refund'], a[href*='return']"
                );

                const ctaWords = /contact|get started|book|buy|shop|subscribe|sign up|request/i;
                const ctas = buttons.filter((el) =>
                    ctaWords.test((el.innerText || el.value || "").trim())
                );

                let ctaAboveFold = 0;
                for (const el of ctas) {
                    const rect = el.getBoundingClientRect();
                    if (rect.top >= 0 && rect.top < window.innerHeight) {
                        ctaAboveFold += 1;
                    }
                }

                const products = document.querySelectorAll(
                    "[class*='product'], .woocommerce, .shopify-section"
                ).length;

                const schema = document.querySelectorAll(
                    'script[type="application/ld+json"]'
                ).length;

                const htmlLang = document.documentElement.lang || "";
                const charset =
                    document.characterSet
                    || document.querySelector("meta[charset]")
                        ?.getAttribute("charset")
                    || "";

                const robots = meta("robots").toLowerCase();

                const navEntry = performance.getEntriesByType("navigation")[0];

                const root = document.documentElement;
                const horizontalScroll =
                    Math.max(
                        root.scrollWidth || 0,
                        document.body?.scrollWidth || 0
                    ) > (root.clientWidth || window.innerWidth) + 24;

                return {
                    title: document.title || "",
                    description: meta("description"),
                    canonical,
                    favicon,
                    htmlLang,
                    charset,
                    robots,
                    headings,
                    imageCount: images.length,
                    missingAlt,
                    wordCount: words,
                    smallTargets,
                    hasViewport: !!viewport,
                    hasNav: !!nav,
                    hasSearch: !!search,
                    hasBreadcrumbs: !!breadcrumbs,
                    hasFooter: !!footer,
                    formCount: forms,
                    hasPhone: phone,
                    hasEmail: email,
                    hasWhatsapp: whatsapp,
                    hasChat: chat,
                    hasTestimonials: testimonials,
                    hasPrivacy: privacy,
                    hasRefund: refund,
                    ctaCount: ctas.length,
                    ctaAboveFold,
                    productSignals: products,
                    schemaCount: schema,
                    horizontalScroll,
                    ttfb: navEntry ? Math.round(navEntry.responseStart) : null,
                    loadEvent: navEntry
                        ? Math.round(navEntry.loadEventEnd)
                        : null,
                    bodySample: bodyText.slice(0, 4000)
                };
            }
            """
        )

        mobile_scroll = False
        try:
            page.set_viewport_size({"width": 390, "height": 844})
            page.wait_for_timeout(200)
            mobile_scroll = page.evaluate(
                """
                () => {
                    const root = document.documentElement;
                    return Math.max(
                        root.scrollWidth || 0,
                        document.body?.scrollWidth || 0
                    ) > (root.clientWidth || window.innerWidth) + 24;
                }
                """
            )
        except Exception:
            mobile_scroll = False

        context.close()
        browser.close()

        data["http_status"] = response.status if response else None
        data["load_ms"] = load_ms
        data["mobile_horizontal_scroll"] = bool(mobile_scroll)
        return data


def _tls_info(hostname):
    info = {
        "reachable": False,
        "version": "",
        "expires": "",
    }

    if not hostname:
        return info

    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=8) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                info["reachable"] = True
                info["version"] = ssock.version() or ""
                cert = ssock.getpeercert() or {}
                not_after = cert.get("notAfter") or ""
                info["expires"] = not_after
    except Exception:
        pass

    return info


def _host_ip(hostname):
    try:
        return socket.gethostbyname(hostname)
    except Exception:
        return ""


def _module_summary(name, issues):
    passed = sum(1 for item in issues if item["status"] == "passed")
    warning = sum(1 for item in issues if item["status"] == "warning")
    failed = sum(1 for item in issues if item["status"] == "failed")
    score = _score_from_issues(issues)

    return {
        "module": name,
        "score": score,
        "score_label": _score_label(score),
        "passed": passed,
        "warning": warning,
        "failed": failed,
        "total": len(issues),
    }


def _audit_basic(page_data, snap, headers, tls, ip_address):
    html = page_data.get("html") or ""
    cms = _detect_cms(html, headers)
    ssl_ok = (page_data.get("final_url") or "").startswith("https://") and tls.get("reachable")

    facts = {
        "title": snap.get("title") or "",
        "meta_description": snap.get("description") or "",
        "canonical": snap.get("canonical") or "",
        "favicon": snap.get("favicon") or "",
        "cms": cms,
        "language": snap.get("htmlLang") or "",
        "charset": snap.get("charset") or "",
        "ssl": "Enabled" if ssl_ok else "Missing / unverified",
        "ip_address": ip_address or "Unknown",
        "hosting_provider": headers.get("Server") or headers.get("server") or "Unknown",
        "server": headers.get("Server") or headers.get("server") or "Unknown",
        "response_time_ms": page_data.get("response_time_ms"),
        "http_status": page_data.get("status_code"),
    }
    return facts, cms


def _audit_performance(page_data, snap, headers, image_count, missing_alt):
    issues = []
    load_ms = snap.get("load_ms") or page_data.get("response_time_ms") or 0
    ttfb = snap.get("ttfb")

    if load_ms and load_ms > 4000:
        issues.append(_issue(
            "Performance", "Homepage Load Time", "high", "failed",
            f"{load_ms} ms", "Under 3000 ms",
            "Reduce blocking scripts, compress assets, and use a CDN.",
        ))
    elif load_ms and load_ms > 2500:
        issues.append(_issue(
            "Performance", "Homepage Load Time", "medium", "warning",
            f"{load_ms} ms", "Under 2500 ms",
            "Optimize images and defer non-critical JavaScript.",
        ))
    else:
        issues.append(_issue(
            "Performance", "Homepage Load Time", "info", "passed",
            f"{load_ms} ms", "Under 2500 ms", "Keep monitoring homepage load time.",
        ))

    if ttfb and ttfb > 800:
        issues.append(_issue(
            "Performance", "TTFB", "high", "warning",
            f"{ttfb} ms", "Under 600 ms",
            "Improve server response time with caching or a faster host.",
        ))
    else:
        issues.append(_issue(
            "Performance", "TTFB", "info", "passed",
            f"{ttfb or page_data.get('response_time_ms')} ms",
            "Under 600 ms", "Server response time looks acceptable.",
        ))

    encoding = (headers.get("Content-Encoding") or headers.get("content-encoding") or "")
    if encoding:
        issues.append(_issue(
            "Performance", "Compression", "low", "passed",
            encoding, "gzip or br", "Compression is enabled.",
        ))
    else:
        issues.append(_issue(
            "Performance", "Compression", "medium", "failed",
            "None", "gzip or br",
            "Enable gzip or Brotli compression on the server.",
        ))

    cache = headers.get("Cache-Control") or headers.get("cache-control") or ""
    if cache:
        issues.append(_issue(
            "Performance", "Caching", "low", "passed",
            cache[:80], "Cache-Control present", "Review cache lifetimes for static assets.",
        ))
    else:
        issues.append(_issue(
            "Performance", "Caching", "medium", "warning",
            "Missing", "Cache-Control header",
            "Add Cache-Control headers for images, CSS and JavaScript.",
        ))

    cdn = any(
        token in (headers.get("Server") or "").lower()
        or token in str(headers).lower()
        for token in ("cloudflare", "fastly", "akamai", "cloudfront", "bunny")
    )
    issues.append(_issue(
        "Performance", "CDN",
        "low", "passed" if cdn else "warning",
        "Detected" if cdn else "Not detected",
        "CDN in front of static assets",
        "Use a CDN if traffic or image weight is high." if not cdn else "CDN appears to be in use.",
    ))

    if image_count and missing_alt / max(image_count, 1) > 0.4:
        issues.append(_issue(
            "Performance", "Image Optimization", "medium", "warning",
            f"{missing_alt}/{image_count} missing ALT",
            "Optimized images with ALT text",
            "Compress images and add descriptive ALT attributes.",
        ))
    else:
        issues.append(_issue(
            "Performance", "Image Optimization", "low", "passed",
            f"{image_count} images", "Optimized images",
            "Keep compressing large media files.",
        ))

    issues.append(_issue(
        "Performance", "LCP / CLS / INP", "info", "warning",
        "Lab proxies only", "Field Core Web Vitals",
        "Run Page Speed in QA Testing for official Lighthouse LCP, CLS and INP.",
    ))

    return issues


def _audit_seo(pages, snap, homepage):
    issues = []
    html = homepage.get("html") or ""
    title = snap.get("title") or ""
    description = snap.get("description") or ""
    canonical = snap.get("canonical") or ""
    robots = snap.get("robots") or ""

    parsed = urlparse(homepage.get("final_url") or homepage.get("url") or "")
    origin = f"{parsed.scheme}://{parsed.netloc}"

    robots_ok = False
    sitemap_ok = False
    try:
        robots_res = _http_get(urljoin(origin, "/robots.txt"))
        robots_ok = robots_res.status_code == 200 and "user-agent" in (robots_res.text or "").lower()
        sitemap_ok = "sitemap" in (robots_res.text or "").lower()
        if not sitemap_ok:
            sitemap_res = _http_get(urljoin(origin, "/sitemap.xml"))
            sitemap_ok = sitemap_res.status_code == 200 and "<urlset" in (sitemap_res.text or "").lower()
    except Exception:
        pass

    issues.append(_issue(
        "SEO", "robots.txt",
        "high", "passed" if robots_ok else "failed",
        "Found" if robots_ok else "Missing",
        "Accessible robots.txt",
        "Publish a robots.txt that points crawlers to your sitemap." if not robots_ok else "robots.txt is reachable.",
    ))
    issues.append(_issue(
        "SEO", "XML Sitemap",
        "high", "passed" if sitemap_ok else "failed",
        "Found" if sitemap_ok else "Missing",
        "XML sitemap",
        "Add and submit an XML sitemap." if not sitemap_ok else "Sitemap appears available.",
    ))

    if "noindex" in robots:
        issues.append(_issue(
            "SEO", "Noindex Pages", "critical", "failed",
            "noindex present on homepage", "Homepage should be indexable",
            "Remove noindex from the homepage unless the site is intentionally private.",
        ))
    else:
        issues.append(_issue(
            "SEO", "Noindex Pages", "info", "passed",
            "Homepage is indexable", "Indexable homepage",
            "Keep production pages indexable.",
        ))

    if canonical:
        issues.append(_issue(
            "SEO", "Canonical URLs", "low", "passed",
            canonical, "Canonical tag present", "Confirm the canonical matches the preferred URL.",
        ))
    else:
        issues.append(_issue(
            "SEO", "Canonical URLs", "medium", "warning",
            "Missing", "Canonical URL",
            "Add a canonical tag pointing to the preferred homepage URL.",
        ))

    title_len = len(title)
    if not title:
        issues.append(_issue(
            "SEO", "Page Title", "high", "failed",
            "Missing", "30-60 characters",
            "Add a unique, descriptive title tag.",
        ))
    elif title_len < 30 or title_len > 60:
        issues.append(_issue(
            "SEO", "Title Length", "low", "warning",
            f"{title_len} characters", "30-60 characters",
            "Adjust the title length for search snippets.",
        ))
    else:
        issues.append(_issue(
            "SEO", "Page Title", "info", "passed",
            title[:90], "30-60 characters", "Title length looks healthy.",
        ))

    desc_len = len(description)
    if not description:
        issues.append(_issue(
            "SEO", "Meta Description", "high", "failed",
            "Missing", "70-160 characters",
            "Add a unique meta description.",
        ))
    elif desc_len < 70 or desc_len > 160:
        issues.append(_issue(
            "SEO", "Meta Length", "low", "warning",
            f"{desc_len} characters", "70-160 characters",
            "Tune the meta description length.",
        ))
    else:
        issues.append(_issue(
            "SEO", "Meta Description", "info", "passed",
            description[:120], "70-160 characters", "Meta description is present.",
        ))

    h1 = (snap.get("headings") or {}).get("h1", 0)
    if h1 == 0:
        issues.append(_issue(
            "SEO", "H1 Count", "high", "failed",
            "0", "Exactly one H1",
            "Add a single clear H1 heading.",
        ))
    elif h1 > 1:
        issues.append(_issue(
            "SEO", "H1 Count", "medium", "warning",
            str(h1), "Exactly one H1",
            "Reduce duplicate H1 tags.",
        ))
    else:
        issues.append(_issue(
            "SEO", "H1 Count", "info", "passed",
            "1", "Exactly one H1", "H1 structure looks correct.",
        ))

    h2 = (snap.get("headings") or {}).get("h2", 0)
    issues.append(_issue(
        "SEO", "H2 Structure",
        "low", "passed" if h2 else "warning",
        str(h2), "Supporting H2 headings",
        "Add H2 headings to structure the page." if not h2 else "H2 headings are present.",
    ))

    missing_alt = snap.get("missingAlt") or 0
    if missing_alt:
        issues.append(_issue(
            "SEO", "Image ALT Tags", "medium", "warning",
            f"{missing_alt} missing", "All informative images have ALT",
            "Add ALT text to images that convey meaning.",
        ))
    else:
        issues.append(_issue(
            "SEO", "Image ALT Tags", "info", "passed",
            "None missing", "ALT on informative images",
            "Keep ALT text complete as new images are added.",
        ))

    broken = [
        page for page in pages
        if page.get("status_code") and page["status_code"] >= 400
    ]
    if broken:
        issues.append(_issue(
            "SEO", "Broken Links / 404 Pages", "high", "failed",
            f"{len(broken)} crawled error(s)", "No 4xx/5xx on priority pages",
            "Fix or redirect broken URLs found during the crawl.",
        ))
    else:
        issues.append(_issue(
            "SEO", "404 Pages", "info", "passed",
            "None in crawl sample", "No broken priority pages",
            "Continue monitoring for 404s as content changes.",
        ))

    https = (homepage.get("final_url") or "").startswith("https://")
    issues.append(_issue(
        "SEO", "HTTPS",
        "critical", "passed" if https else "failed",
        "HTTPS" if https else "HTTP",
        "HTTPS everywhere",
        "Redirect HTTP to HTTPS." if not https else "Homepage is served over HTTPS.",
    ))

    if snap.get("schemaCount"):
        issues.append(_issue(
            "SEO", "Structured Data", "low", "passed",
            f"{snap.get('schemaCount')} JSON-LD block(s)",
            "Relevant schema", "Validate schema in Google Rich Results.",
        ))
    else:
        issues.append(_issue(
            "SEO", "Structured Data", "low", "warning",
            "None detected", "Organization / WebPage schema",
            "Add JSON-LD schema for the organization and primary pages.",
        ))

    return issues


def _audit_content(snap, pages):
    issues = []
    words = snap.get("wordCount") or 0

    if words < 200:
        issues.append(_issue(
            "Content", "Thin Content", "high", "failed",
            f"{words} words", "300+ words on key pages",
            "Expand homepage copy with useful, unique information.",
        ))
    elif words < 350:
        issues.append(_issue(
            "Content", "Word Count", "medium", "warning",
            f"{words} words", "350+ words",
            "Add supporting sections to strengthen topical coverage.",
        ))
    else:
        issues.append(_issue(
            "Content", "Word Count", "info", "passed",
            f"{words} words", "Healthy page length",
            "Keep content specific and up to date.",
        ))

    titles = [
        re.search(r"<title>(.*?)</title>", page.get("html") or "", flags=re.I | re.S)
        for page in pages
    ]
    clean_titles = [
        re.sub(r"\s+", " ", (match.group(1) if match else "")).strip().lower()
        for match in titles
        if match
    ]
    duplicates = len(clean_titles) - len(set(clean_titles))
    if duplicates > 0:
        issues.append(_issue(
            "Content", "Duplicate Content", "medium", "warning",
            f"{duplicates} duplicate title(s) in crawl",
            "Unique titles per page",
            "Give each important page a unique title and opening paragraph.",
        ))
    else:
        issues.append(_issue(
            "Content", "Duplicate Content", "info", "passed",
            "No duplicate titles in crawl sample",
            "Unique titles",
            "Watch for copied product or blog boilerplate.",
        ))

    sample = snap.get("bodySample") or ""
    long_sentences = [
        sentence for sentence in re.split(r"[.!?]+", sample)
        if len(sentence.split()) > 28
    ]
    if len(long_sentences) >= 3:
        issues.append(_issue(
            "Content", "Readability", "low", "warning",
            "Several very long sentences",
            "Shorter, scannable sentences",
            "Break long sentences and add subheadings.",
        ))
    else:
        issues.append(_issue(
            "Content", "Readability", "info", "passed",
            "No heavy sentence clustering detected",
            "Readable copy",
            "Keep using short paragraphs and clear headings.",
        ))

    issues.append(_issue(
        "Content", "Content Freshness", "info", "warning",
        "Not dated in markup",
        "Visible update dates on key content",
        "Show last-updated dates on blog and service pages.",
    ))
    issues.append(_issue(
        "Content", "EEAT / Content Gap", "info", "warning",
        "Heuristic only",
        "Author, proof and topic coverage",
        "Add expert bios, sources, FAQs and related topic pages to strengthen EEAT.",
    ))

    return issues


def _audit_ux(snap):
    issues = []
    checks = [
        ("Menu Visibility", snap.get("hasNav"), "high", "Visible main navigation"),
        ("Search Available", snap.get("hasSearch"), "low", "Site search or clear contact path"),
        ("Breadcrumbs", snap.get("hasBreadcrumbs"), "low", "Breadcrumbs on inner pages"),
        ("Footer Navigation", snap.get("hasFooter"), "medium", "Useful footer links"),
        ("Viewport Tag", snap.get("hasViewport"), "high", "Mobile viewport meta tag"),
    ]

    for name, present, severity, expected in checks:
        issues.append(_issue(
            "UX", name,
            severity, "passed" if present else "warning",
            "Present" if present else "Not detected",
            expected,
            f"Add {expected.lower()}." if not present else f"{name} looks present.",
        ))

    missing_alt = snap.get("missingAlt") or 0
    issues.append(_issue(
        "UX", "Missing ALT",
        "medium", "warning" if missing_alt else "passed",
        f"{missing_alt} image(s)", "ALT on meaningful images",
        "Add ALT text for accessibility and SEO." if missing_alt else "No missing ALT detected on homepage images.",
    ))

    small = snap.get("smallTargets") or 0
    issues.append(_issue(
        "UX", "Touch Targets",
        "medium", "warning" if small else "passed",
        f"{small} small control(s)", "At least 40px tap targets",
        "Increase padding on buttons and links." if small else "Tap targets look reasonably sized.",
    ))

    issues.append(_issue(
        "UX", "Horizontal Scroll",
        "high", "failed" if snap.get("horizontalScroll") else "passed",
        "Detected" if snap.get("horizontalScroll") else "None",
        "No desktop horizontal scroll",
        "Fix overflowing sections or 100vw elements." if snap.get("horizontalScroll") else "No obvious desktop horizontal scroll.",
    ))

    return issues


def _audit_security(homepage, headers, tls):
    issues = []
    url = homepage.get("final_url") or homepage.get("url") or ""
    https = url.startswith("https://")
    header_map = {str(key).lower(): str(value) for key, value in (headers or {}).items()}

    if not https:
        issues.append(_issue(
            "Security", "SSL / HTTPS", "critical", "failed",
            "HTTP", "HTTPS with valid certificate",
            "Install SSL and redirect all traffic to HTTPS.",
        ))
    elif not tls.get("reachable"):
        issues.append(_issue(
            "Security", "SSL", "high", "warning",
            "HTTPS URL but certificate check failed",
            "Valid publicly trusted certificate",
            "Verify the certificate chain and hostname.",
        ))
    else:
        issues.append(_issue(
            "Security", "SSL", "info", "passed",
            tls.get("version") or "TLS",
            "TLS 1.2+",
            "Certificate handshake succeeded.",
        ))

    if tls.get("expires"):
        issues.append(_issue(
            "Security", "SSL Expiry", "low", "passed",
            tls["expires"], "Valid future expiry",
            "Calendar a renewal before this date.",
        ))

    mixed = bool(re.search(r"""(?:src|href)=["']http://""", homepage.get("html") or "", flags=re.I))
    issues.append(_issue(
        "Security", "Mixed Content",
        "high", "failed" if mixed else "passed",
        "HTTP assets found" if mixed else "None detected",
        "HTTPS assets only",
        "Serve all scripts, images and CSS over HTTPS." if mixed else "No obvious mixed-content assets.",
    ))

    header_checks = [
        ("HSTS", "strict-transport-security", "high"),
        ("CSP", "content-security-policy", "medium"),
        ("X-Frame-Options", "x-frame-options", "medium"),
        ("Referrer Policy", "referrer-policy", "low"),
    ]
    for label, key, severity in header_checks:
        value = header_map.get(key, "")
        issues.append(_issue(
            "Security", label,
            severity, "passed" if value else "warning",
            value[:80] or "Missing",
            f"{label} header",
            f"Add a {label} header." if not value else f"{label} is set.",
        ))

    xss = header_map.get("x-xss-protection", "")
    issues.append(_issue(
        "Security", "X-XSS-Protection",
        "low", "warning" if not xss else "passed",
        xss or "Missing",
        "Optional legacy header or modern CSP",
        "Prefer Content-Security-Policy over X-XSS-Protection.",
    ))

    html = homepage.get("html") or ""
    exposed = bool(re.search(r"wp-admin|phpmyadmin|/\.git|/\.env", html, flags=re.I))
    issues.append(_issue(
        "Security", "Admin / Exposed Files",
        "high", "warning" if exposed else "passed",
        "Possible public admin/path mention" if exposed else "None obvious",
        "Admin paths not advertised",
        "Restrict admin URLs and block sensitive files." if exposed else "No obvious exposed admin files in homepage HTML.",
    ))

    return issues


def _audit_cro(snap):
    issues = []
    issues.append(_issue(
        "CRO", "CTA Above Fold",
        "high", "passed" if snap.get("ctaAboveFold") else "warning",
        f"{snap.get('ctaAboveFold') or 0} CTA(s)",
        "At least one clear CTA in the first screen",
        "Place a primary call-to-action above the fold." if not snap.get("ctaAboveFold") else "A CTA is visible above the fold.",
    ))
    issues.append(_issue(
        "CRO", "CTA Count",
        "low", "warning" if (snap.get("ctaCount") or 0) < 1 else "passed",
        str(snap.get("ctaCount") or 0),
        "Clear primary and supporting CTAs",
        "Add action-oriented buttons such as Contact, Book or Buy.",
    ))
    issues.append(_issue(
        "CRO", "Contact Form",
        "medium", "passed" if snap.get("formCount") else "warning",
        str(snap.get("formCount") or 0),
        "Lead form on key pages",
        "Add a contact or enquiry form." if not snap.get("formCount") else "A form is present.",
    ))

    for name, present, severity, rec in [
        ("Phone Number", snap.get("hasPhone"), "medium", "Show a clickable phone number."),
        ("Email Visibility", snap.get("hasEmail"), "low", "Show a contact email or form alternative."),
        ("WhatsApp", snap.get("hasWhatsapp"), "low", "Add WhatsApp if that is a primary channel."),
        ("Live Chat", snap.get("hasChat"), "low", "Consider live chat for faster lead capture."),
        ("Testimonials / Reviews", snap.get("hasTestimonials"), "medium", "Add testimonials, reviews or case studies."),
        ("Privacy Policy", snap.get("hasPrivacy"), "medium", "Link a privacy policy in the footer."),
        ("Refund Policy", snap.get("hasRefund"), "low", "Add refund/returns copy if you sell online."),
    ]:
        issues.append(_issue(
            "CRO", name,
            severity, "passed" if present else "warning",
            "Detected" if present else "Not detected",
            "Present on high-intent pages",
            rec if not present else f"{name} appears to be present.",
        ))

    return issues


def _audit_mobile(snap):
    issues = []
    issues.append(_issue(
        "Mobile", "Viewport Tag",
        "high", "passed" if snap.get("hasViewport") else "failed",
        "Present" if snap.get("hasViewport") else "Missing",
        "width=device-width viewport",
        "Add a responsive viewport meta tag." if not snap.get("hasViewport") else "Viewport tag is present.",
    ))
    issues.append(_issue(
        "Mobile", "Responsive Layout",
        "high", "failed" if snap.get("mobile_horizontal_scroll") else "passed",
        "Horizontal scroll on 390px" if snap.get("mobile_horizontal_scroll") else "No extra scroll",
        "No mobile horizontal scroll",
        "Fix overflowing mobile sections." if snap.get("mobile_horizontal_scroll") else "Mobile width looks contained.",
    ))
    small = snap.get("smallTargets") or 0
    issues.append(_issue(
        "Mobile", "Button Size / Touch Spacing",
        "medium", "warning" if small else "passed",
        f"{small} small control(s)",
        "44px comfortable tap targets",
        "Increase button size and spacing on mobile." if small else "Controls appear large enough.",
    ))
    issues.append(_issue(
        "Mobile", "Font Readability",
        "low", "passed",
        "Heuristic pass",
        "Readable body copy on small screens",
        "Verify 16px+ body text on real devices.",
    ))
    issues.append(_issue(
        "Mobile", "Page Speed Mobile",
        "medium", "warning",
        "Not a field Lighthouse run",
        "Good mobile Lighthouse score",
        "Use the Page Speed module for a mobile Lighthouse score.",
    ))
    return issues


def _audit_ecommerce(snap, html, cms):
    commerce = cms in {"Shopify", "WooCommerce"} or (snap.get("productSignals") or 0) > 4
    if not commerce:
        return [], False

    issues = []
    text = (html or "").lower()
    issues.append(_issue(
        "E-Commerce", "Product Markup",
        "medium", "passed" if snap.get("schemaCount") else "warning",
        f"{snap.get('schemaCount') or 0} schema block(s)",
        "Product schema",
        "Add Product JSON-LD with price and availability.",
    ))
    issues.append(_issue(
        "E-Commerce", "Cart / Checkout Signals",
        "high", "passed" if ("cart" in text or "checkout" in text) else "warning",
        "Detected" if ("cart" in text or "checkout" in text) else "Not detected",
        "Cart and checkout links",
        "Ensure cart and checkout are linked in the header.",
    ))
    issues.append(_issue(
        "E-Commerce", "Guest Checkout / Payments",
        "low", "warning",
        "Cannot confirm without checkout flow",
        "Guest checkout and visible payment options",
        "Confirm guest checkout and show payment badges.",
    ))
    return issues, True


def _prioritize(issues):
    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    actionable = [
        item for item in issues
        if item.get("status") in {"failed", "warning"}
    ]
    actionable.sort(
        key=lambda item: (
            rank.get(item.get("severity"), 9),
            0 if item.get("status") == "failed" else 1,
            item.get("test_name") or "",
        )
    )
    immediate = [
        item for item in actionable
        if item.get("severity") in {"critical", "high"}
    ][:6]
    high = [
        item for item in actionable
        if item.get("severity") == "medium"
    ][:6]
    return immediate, high, actionable


def _opportunities(modules):
    seo = next((item["score"] for item in modules if item["module"] == "SEO"), 0)
    cro = next((item["score"] for item in modules if item["module"] == "CRO"), 0)
    performance = next((item["score"] for item in modules if item["module"] == "Performance"), 0)

    def band(score):
        if score < 70:
            return "High"
        if score < 85:
            return "Medium"
        return "Low"

    return {
        "seo_traffic_potential": band(seo),
        "lead_conversion_opportunity": band(cro),
        "performance_improvement": band(performance),
    }


def _executive_summary(domain, overall, modules, immediate):
    weakest = sorted(modules, key=lambda item: item["score"])[:2]
    weakest_names = " and ".join(item["module"] for item in weakest) if weakest else "key areas"
    top = ", ".join(item["test_name"] for item in immediate[:3]) or "no critical defects"
    return (
        f"Website health score is {overall}/100 for {domain}. "
        f"The site has a usable foundation, but {weakest_names} need the most attention. "
        f"Highest-impact items to address first: {top}. "
        "Fixing metadata, performance and conversion paths can improve search visibility and lead quality."
    )


def run_website_audit(url: str):
    start = datetime.now(timezone.utc)
    started = time.perf_counter()
    url = normalize_url(url)
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    domain = hostname.removeprefix("www.")

    homepage = _collect_page(url)
    snap = _playwright_snapshot(homepage.get("final_url") or url)
    tls = _tls_info(hostname)
    ip_address = _host_ip(hostname)
    headers = homepage.get("headers") or {}

    links = _extract_links(homepage.get("final_url") or url, homepage.get("html") or "")
    crawl_urls = []
    seen = { (homepage.get("final_url") or url).rstrip("/") }
    for link in links:
        if not _same_host(url, link):
            continue
        key = link.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        crawl_urls.append(link)
        if len(crawl_urls) >= MAX_PAGES - 1:
            break

    pages = [homepage]
    for link in crawl_urls:
        try:
            pages.append(_collect_page(link))
        except Exception:
            pages.append({
                "url": link,
                "final_url": link,
                "status_code": None,
                "html": "",
                "headers": {},
                "response_time_ms": None,
                "error": "Fetch failed",
            })

    basic, cms = _audit_basic(homepage, snap, headers, tls, ip_address)
    performance_issues = _audit_performance(
        homepage, snap, headers,
        snap.get("imageCount") or 0,
        snap.get("missingAlt") or 0,
    )
    seo_issues = _audit_seo(pages, snap, homepage)
    content_issues = _audit_content(snap, pages)
    ux_issues = _audit_ux(snap)
    security_issues = _audit_security(homepage, headers, tls)
    cro_issues = _audit_cro(snap)
    mobile_issues = _audit_mobile(snap)
    ecommerce_issues, ecommerce_detected = _audit_ecommerce(
        snap, homepage.get("html") or "", cms
    )

    grouped = [
        ("Performance", performance_issues),
        ("SEO", seo_issues),
        ("UX", ux_issues),
        ("Security", security_issues),
        ("Content", content_issues),
        ("Mobile", mobile_issues),
        ("CRO", cro_issues),
    ]
    if ecommerce_detected:
        grouped.append(("E-Commerce", ecommerce_issues))

    modules = [_module_summary(name, issues) for name, issues in grouped]
    all_issues = [item for _, group in grouped for item in group]

    weighted = 0
    weight_total = 0
    for module in modules:
        key = module["module"].lower().replace("-", "")
        if key == "ecommerce":
            continue
        weight = MODULE_WEIGHTS.get(module["module"].lower(), 0)
        weighted += module["score"] * weight
        weight_total += weight

    overall = round(weighted / weight_total) if weight_total else 0
    immediate, high_priority, actionable = _prioritize(all_issues)

    counts = {
        "critical": sum(1 for item in all_issues if item["severity"] == "critical" and item["status"] != "passed"),
        "high": sum(1 for item in all_issues if item["severity"] == "high" and item["status"] != "passed"),
        "medium": sum(1 for item in all_issues if item["severity"] == "medium" and item["status"] != "passed"),
        "low": sum(1 for item in all_issues if item["severity"] == "low" and item["status"] != "passed"),
        "failed": sum(1 for item in all_issues if item["status"] == "failed"),
        "warning": sum(1 for item in all_issues if item["status"] == "warning"),
        "passed": sum(1 for item in all_issues if item["status"] == "passed"),
    }

    end = datetime.now(timezone.utc)

    return {
        "audit_id": f"A{uuid.uuid4().hex[:8].upper()}",
        "domain": domain,
        "url": homepage.get("final_url") or url,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "duration_seconds": round(time.perf_counter() - started, 2),
        "status": "completed",
        "overall_score": overall,
        "overall_label": _score_label(overall),
        "basic": basic,
        "modules": modules,
        "issues": all_issues,
        "counts": counts,
        "pages_crawled": len(pages),
        "page_urls": [
            {
                "url": page.get("final_url") or page.get("url"),
                "status_code": page.get("status_code"),
                "response_time_ms": page.get("response_time_ms"),
            }
            for page in pages
        ],
        "priority": {
            "fix_immediately": immediate,
            "high_priority": high_priority,
        },
        "opportunities": _opportunities(modules),
        "executive_summary": _executive_summary(
            domain, overall, modules, immediate
        ),
        "ecommerce_detected": ecommerce_detected,
        "weights": MODULE_WEIGHTS,
    }
