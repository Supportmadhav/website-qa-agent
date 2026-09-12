"""Structured data for the report-specific QA views.

These snapshots supplement the existing checks; they do not change their
pass/warning/fail findings or the tests that produced them.
"""


def collect_social_profiles(page):
    links = page.evaluate(
        """() => Array.from(document.querySelectorAll('a[href]')).map(a => ({
            url: a.href || '',
            target: a.getAttribute('target') || '',
            visible: !!(a.getClientRects().length),
        }))"""
    )

    domains = {
        "Instagram": ("instagram.com",),
        "LinkedIn": ("linkedin.com",),
        "Facebook": ("facebook.com", "fb.com"),
        "YouTube": ("youtube.com", "youtu.be"),
        "X / Twitter": ("x.com", "twitter.com"),
        "Pinterest": ("pinterest.com",),
        "TikTok": ("tiktok.com",),
        "Threads": ("threads.net",),
        "WhatsApp": ("wa.me", "whatsapp.com"),
    }

    from urllib.parse import urlparse

    profiles = []
    for link in links:
        url = link.get("url") or ""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            continue
        host = (parsed.hostname or "").lower().removeprefix("www.")
        platform = next(
            (
                name
                for name, candidates in domains.items()
                if any(host == domain or host.endswith("." + domain) for domain in candidates)
            ),
            None,
        )
        if not platform:
            continue
        profiles.append({
            "platform": platform,
            "url": url,
            "opens_new_tab": link.get("target") == "_blank",
            "visible": bool(link.get("visible")),
        })

    url_counts = {}
    platform_urls = {}
    for profile in profiles:
        url_counts[profile["url"]] = url_counts.get(profile["url"], 0) + 1
        platform_urls.setdefault(profile["platform"], set()).add(profile["url"])

    for profile in profiles:
        profile["is_duplicate"] = url_counts[profile["url"]] > 1
        profile["is_consistent"] = len(platform_urls[profile["platform"]]) == 1
        profile["issues"] = []
        if not profile["opens_new_tab"]:
            profile["issues"].append("Does not open in a new tab")
        if profile["is_duplicate"]:
            profile["issues"].append("Duplicate link on this page")
        if not profile["is_consistent"]:
            profile["issues"].append("Multiple URLs found for this platform")
        if not profile["visible"]:
            profile["issues"].append("Link is hidden on the page")

    return profiles


def collect_seo_overview(page):
    data = page.evaluate(
        """() => {
            const meta = (selector) => document.querySelector(selector)?.getAttribute('content') || '';
            const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'))
                .map(el => ({level: Number(el.tagName.slice(1)), text: (el.textContent || '').trim().slice(0, 160)}));
            const images = Array.from(document.images);
            const tags = {
                canonical: !!document.querySelector('link[rel="canonical"][href]'),
                og_title: !!meta('meta[property="og:title"]'),
                og_description: !!meta('meta[property="og:description"]'),
                og_image: !!meta('meta[property="og:image"]'),
                og_type: !!meta('meta[property="og:type"]'),
                og_url: !!meta('meta[property="og:url"]'),
                twitter_card: !!meta('meta[name="twitter:card"]'),
                robots: !!meta('meta[name="robots"]'),
                structured_data: !!document.querySelector('script[type="application/ld+json"]'),
                favicon: !!document.querySelector('link[rel*="icon"][href]'),
                charset: !!document.querySelector('meta[charset]'),
                html_lang: !!document.documentElement.lang,
            };
            return {
                title_text: document.title || '',
                description_text: meta('meta[name="description"]'),
                heading_sequence: headings,
                alt_present_count: images.filter(img => img.hasAttribute('alt') && img.getAttribute('alt').trim()).length,
                alt_empty_count: images.filter(img => img.hasAttribute('alt') && !img.getAttribute('alt').trim()).length,
                alt_missing_count: images.filter(img => !img.hasAttribute('alt')).length,
                meta_tags_present: tags,
            };
        }"""
    )

    title_length = len(data["title_text"])
    description_length = len(data["description_text"])
    headings = data["heading_sequence"]
    heading_skips = []
    for previous, current in zip(headings, headings[1:]):
        if current["level"] > previous["level"] + 1:
            heading_skips.append(
                f"H{previous['level']} to H{current['level']}"
            )

    alt_total = sum(data[key] for key in (
        "alt_present_count", "alt_empty_count", "alt_missing_count"
    ))
    core_tags = (
        "canonical", "og_title", "og_description", "og_image",
        "og_type", "og_url", "robots", "structured_data",
    )
    tags = data["meta_tags_present"]

    # A page with no images is not penalized for missing image alt text.
    score = (
        (20 if 50 <= title_length <= 60 else 0)
        + (20 if 155 <= description_length <= 160 else 0)
        + (20 if headings and not heading_skips else 0)
        + (round(20 * data["alt_present_count"] / alt_total) if alt_total else 20)
        + round(20 * sum(bool(tags.get(key)) for key in core_tags) / len(core_tags))
    )

    data.update({
        "title_length": title_length,
        "description_length": description_length,
        "heading_skips": heading_skips,
        "seo_score": min(100, score),
    })
    return data


def seo_metric_findings(data):
    findings = []
    for title, length, minimum, maximum in (
        ("SEO Title Length", data["title_length"], 50, 60),
        ("Meta Description Length", data["description_length"], 155, 160),
    ):
        in_range = minimum <= length <= maximum
        findings.append({
            "status": "pass" if in_range else "warning",
            "title": title,
            "message": (
                f"{length} characters; ideal range is {minimum}-{maximum}."
            ),
            "raw": "",
        })

    missing = data["alt_missing_count"]
    findings.append({
        "status": "warning" if missing else "pass",
        "title": "Image ALT Attributes",
        "message": (
            f"{data['alt_present_count']} present, "
            f"{data['alt_empty_count']} empty, {missing} missing."
        ),
        "raw": "",
    })
    return findings


def collect_design_overview(page):
    data = page.evaluate(
        """() => {
            const rgb = value => {
                const m = String(value).match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/i);
                return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
            };
            const opaque = value => !String(value).startsWith('rgba(')
                || Number(String(value).split(',').pop().replace(')', '')) >= .99;
            const hex = c => '#' + c.map(v => Math.max(0, Math.min(255, v)).toString(16).padStart(2, '0')).join('').toUpperCase();
            const luminance = c => {
                const x = c.map(v => { const s = v / 255; return s <= .04045 ? s / 12.92 : Math.pow((s + .055) / 1.055, 2.4); });
                return .2126 * x[0] + .7152 * x[1] + .0722 * x[2];
            };
            const contrast = (a, b) => { const x = luminance(a), y = luminance(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
            const visible = Array.from(document.querySelectorAll('body *')).filter(el => {
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
            }).slice(0, 1200);
            const colorCounts = new Map(), fonts = new Set(), contrastPairs = [];
            let padding = 0, content = 0, samples = 0;
            for (const el of visible) {
                const style = getComputedStyle(el);
                const fg = rgb(style.color), bg = rgb(style.backgroundColor);
                if (fg) colorCounts.set(hex(fg), (colorCounts.get(hex(fg)) || 0) + 1);
                if (bg && opaque(style.backgroundColor)) colorCounts.set(hex(bg), (colorCounts.get(hex(bg)) || 0) + 2);
                if (el.textContent?.trim() && el.children.length === 0) {
                    const font = style.fontFamily.split(',')[0].replace(/[\"']/g, '').trim();
                    if (font) fonts.add(font);
                    if (fg && contrastPairs.length < 35) {
                        let ancestor = el, effectiveBg = null;
                        while (ancestor && !effectiveBg) {
                            const s = getComputedStyle(ancestor);
                            if (Number(s.opacity) < 1) break;
                            const value = rgb(s.backgroundColor);
                            if (value && opaque(s.backgroundColor)) effectiveBg = value;
                            ancestor = ancestor.parentElement;
                        }
                        effectiveBg ||= [255, 255, 255];
                        if (effectiveBg) {
                            const size = parseFloat(style.fontSize) || 16;
                            const large = size >= 24 || (size >= 18.66 && Number(style.fontWeight) >= 700);
                            const ratio = contrast(fg, effectiveBg);
                            contrastPairs.push({
                                text: el.textContent.trim().slice(0, 80),
                                fg: hex(fg), bg: hex(effectiveBg),
                                ratio: Math.round(ratio * 100) / 100,
                                passes_aa: ratio >= (large ? 3 : 4.5),
                                large_text: large,
                            });
                        }
                    }
                    if (samples < 120) {
                        padding += ['paddingTop','paddingBottom','paddingLeft','paddingRight'].reduce((n,k) => n + (parseFloat(style[k]) || 0), 0);
                        content += Math.max(1, el.getBoundingClientRect().width + el.getBoundingClientRect().height);
                        samples++;
                    }
                }
            }
            const levels = [1,2,3,4].map(n => {
                const h = document.querySelector('h' + n);
                return h ? {level: n, size: parseFloat(getComputedStyle(h).fontSize) || 0} : null;
            }).filter(Boolean);
            const typeScaleConsistent = levels.length > 0 && levels.every((h, i) => i === 0 || levels[i-1].size >= h.size);
            const density = content ? Math.round(100 * padding / content) : 0;
            return {
                dominant_colors: Array.from(colorCounts.entries()).sort((a,b) => b[1]-a[1]).slice(0,6).map(x => x[0]),
                contrast_pairs: contrastPairs,
                font_families: Array.from(fonts).slice(0,12),
                type_scale_consistent: typeScaleConsistent,
                whitespace_density_score: Math.min(100, density),
            };
        }"""
    )
    contrast_pairs = data.get("contrast_pairs") or []
    checked = len(contrast_pairs)
    passed = sum(bool(item.get("passes_aa")) for item in contrast_pairs)
    font_count = len(data.get("font_families") or [])
    data["design_score"] = (
        (round(40 * passed / checked) if checked else 0)
        + (20 if 0 < font_count <= 3 else 0)
        + (20 if data.get("type_scale_consistent") else 0)
    )
    data["score_basis"] = (
        "Sampled WCAG AA contrast, font-family count, type-scale consistency "
        "and existing usability checks. "
        "Whitespace is experimental and excluded from the score."
    )
    return data


def design_metric_findings(data):
    pairs = data.get("contrast_pairs") or []
    failing = [item for item in pairs if not item.get("passes_aa")]
    fonts = data.get("font_families") or []
    return [
        {
            "status": "info" if not pairs else "warning" if failing else "pass",
            "title": "WCAG AA Color Contrast",
            "message": (
                "No text/background pairs could be sampled."
                if not pairs else
                f"{len(failing)} of {len(pairs)} sampled text/background "
                "pairs are below the applicable AA threshold."
            ),
            "raw": "",
        },
        {
            "status": "info" if not fonts else "warning" if len(fonts) > 3 else "pass",
            "title": "Font Family Consistency",
            "message": f"{len(fonts)} distinct font families detected.",
            "raw": "",
        },
        {
            "status": "pass" if data.get("type_scale_consistent") else "warning",
            "title": "Heading Type Scale",
            "message": (
                "Heading sizes descend consistently."
                if data.get("type_scale_consistent")
                else "Heading sizes are inconsistent or headings are absent."
            ),
            "raw": "",
        },
    ]
