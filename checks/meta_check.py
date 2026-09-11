from urllib.parse import urlsplit, urlunsplit
import requests
import json

def get_meta_content(page, selector):
    locator = page.locator(selector)

    if locator.count() > 0:
        return locator.first.get_attribute("content")

    return None


def get_link_href(page, selector):
    locator = page.locator(selector)

    if locator.count() > 0:
        return locator.first.get_attribute("href")

    return None


def check_meta_tags(page):

    print("\nMeta Tags Check")
    print("---------------")

    pass_count = 0
    fail_count = 0
    warning_count = 0


    # -------------------------------------
    # PAGE TITLE
    # -------------------------------------

    page_title = page.title().strip()

    if not page_title:

        print(
            "FAIL | Page Title | MISSING"
        )
        fail_count += 1
    else:

        title_length = len(page_title)

        if title_length < 30:

            print(
                "WARNING | Page Title |",
                page_title,
                "| Length:",
                title_length,
                "| Too short"
            )
            warning_count += 1

        elif title_length > 60:

            print(
                "WARNING | Page Title |",
                page_title,
                "| Length:",
                title_length,
                "| Too long"
            )

            warning_count += 1

        else:

            print(
                "PASS | Page Title |",
                page_title,
                "| Length:",
                title_length
            )

            pass_count += 1

      # -------------------------------------
    # CANONICAL URL
    # -------------------------------------

    canonical = get_link_href(
        page,
        'link[rel="canonical"]'
    )

    current_url = page.url

    if not canonical:

        print(
            "FAIL | Canonical | MISSING"
        )

        fail_count += 1

    else:

        normalized_canonical = normalize_url(canonical)
        normalized_current = normalize_url(current_url)

        if normalized_canonical == normalized_current:

            print(
                "PASS | Canonical |",
                canonical
            )

            pass_count += 1

        else:

            print(
                "WARNING | Canonical |",
                canonical,
                "| Does not match current page:",
                current_url
            )

            warning_count += 1


    # -------------------------------------
    # ROBOTS
    # -------------------------------------

    robots = get_meta_content(
        page,
        'meta[name="robots"]'
    )

    if not robots:

        print(
            "WARNING | Robots | MISSING"
        )

        warning_count += 1

    else:

        robots_lower = robots.lower()

        if "noindex" in robots_lower:

            print(
                "WARNING | Robots |",
                robots,
                "| Page is set to NOINDEX"
            )

            warning_count += 1

        elif "nofollow" in robots_lower:

            print(
                "WARNING | Robots |",
                robots,
                "| Links are set to NOFOLLOW"
            )

            warning_count += 1

        else:

            print(
                "PASS | Robots |",
                robots
            )

            pass_count += 1

    # -------------------------------------
    # OPEN GRAPH URL
    # -------------------------------------

    og_url = get_meta_content(
        page,
        'meta[property="og:url"]'
    )

    if not og_url:

        print(
            "FAIL | OG URL | MISSING"
        )

        fail_count += 1

    else:

        normalized_og_url = normalize_url(og_url)
        normalized_current = normalize_url(page.url)

        if normalized_og_url == normalized_current:

            print(
                "PASS | OG URL |",
                og_url
            )

            pass_count += 1

        else:

            print(
                "WARNING | OG URL |",
                og_url,
                "| Does not match current page:",
                page.url
            )

            warning_count += 1

    # -------------------------------------
    # OPEN GRAPH TYPE
    # -------------------------------------

    og_type = get_meta_content(
        page,
        'meta[property="og:type"]'
    )

    if not og_type:

        print(
            "FAIL | OG Type | MISSING"
        )

        fail_count += 1

    else:

        og_type = og_type.strip().lower()

        print(
            "PASS | OG Type |",
            og_type
        )

        pass_count += 1
        
        # -------------------------------------
        # OPEN GRAPH TITLE
        # -------------------------------------

        og_title = get_meta_content(
            page,
            'meta[property="og:title"]'
        )

        if not og_title:

            print(
                "FAIL | OG Title | MISSING"
            )

            fail_count += 1

        else:

            og_title = og_title.strip()

            if og_title == page_title:

                print(
                    "PASS | OG Title |",
                    og_title
                )

                pass_count += 1

            else:

                print(
                    "WARNING | OG Title |",
                    og_title,
                    "| Different from Page Title"
                )

                warning_count += 1

    # -------------------------------------
    # VIEWPORT META
    # -------------------------------------

    viewport = get_meta_content(
        page,
        'meta[name="viewport"]'
    )

    if not viewport:

        print(
            "FAIL | Viewport | MISSING"
        )

        fail_count += 1

    else:

        viewport_lower = viewport.lower()

        if "width=device-width" in viewport_lower:

            print(
                "PASS | Viewport |",
                viewport
            )

            pass_count += 1

        else:

            print(
                "WARNING | Viewport |",
                viewport,
                "| width=device-width is missing"
            )

            warning_count += 1

        # -------------------------------------
        # OPEN GRAPH DESCRIPTION
        # -------------------------------------

        og_description = get_meta_content(
            page,
            'meta[property="og:description"]'
        )

        if not og_description:

            print(
                "FAIL | OG Description | MISSING"
            )

            fail_count += 1

        else:

            og_description = og_description.strip()
            og_description_length = len(og_description)

            if og_description_length < 50:

                print(
                    "WARNING | OG Description |",
                    og_description,
                    "| Length:",
                    og_description_length,
                    "| Too short"
                )

                warning_count += 1

            elif og_description_length > 200:

                print(
                    "WARNING | OG Description |",
                    og_description,
                    "| Length:",
                    og_description_length,
                    "| Too long"
                )

                warning_count += 1

            else:

                print(
                    "PASS | OG Description |",
                    og_description,
                    "| Length:",
                    og_description_length
                )

                pass_count += 1


    # -------------------------------------
    # OPEN GRAPH IMAGE
    # -------------------------------------

    og_image = get_meta_content(
        page,
        'meta[property="og:image"]'
    )

    if not og_image:

        print(
            "FAIL | OG Image | MISSING"
        )

        fail_count += 1

    elif not og_image.startswith("http"):

        print(
            "WARNING | OG Image |",
            og_image,
            "| Invalid or relative URL"
        )

        warning_count += 1

    else:

        try:
            response = requests.get(
                og_image,
                timeout=10,
                allow_redirects=True
            )

            if response.status_code < 400:

                print(
                    "PASS | OG Image |",
                    og_image,
                    "| Status:",
                    response.status_code
                )

                pass_count += 1

            else:

                print(
                    "FAIL | OG Image |",
                    og_image,
                    "| HTTP Status:",
                    response.status_code
                )

                fail_count += 1

        except requests.RequestException as error:

            print(
                "FAIL | OG Image |",
                og_image,
                "| Could not load image:",
                error
            )

            fail_count += 1


    # -------------------------------------
    # TWITTER CARD
    # -------------------------------------

    twitter_card = get_meta_content(
        page,
        'meta[name="twitter:card"]'
    )

    valid_twitter_cards = [
        "summary",
        "summary_large_image",
        "app",
        "player"
    ]

    if not twitter_card:

        print(
            "WARNING | Twitter Card | MISSING"
        )

        warning_count += 1

    else:

        twitter_card = twitter_card.strip().lower()

        if twitter_card in valid_twitter_cards:

            print(
                "PASS | Twitter Card |",
                twitter_card
            )

            pass_count += 1

        else:

            print(
                "WARNING | Twitter Card |",
                twitter_card,
                "| Unknown card type"
            )

            warning_count += 1

    # -------------------------------------
        # HTML LANGUAGE
        # -------------------------------------
    
        html_lang = page.locator("html").get_attribute("lang")
    
        if not html_lang:
    
            print(
                "WARNING | HTML Language | MISSING"
            )
    
            warning_count += 1
    
        else:
    
            html_lang = html_lang.strip()
    
            print(
                "PASS | HTML Language |",
                html_lang
            )
    
            pass_count += 1

    # -------------------------------------
    # FAVICON
    # -------------------------------------

    favicon_locator = page.locator(
        'link[rel*="icon"]'
    )

    if favicon_locator.count() == 0:

        print(
            "WARNING | Favicon | MISSING"
        )

        warning_count += 1

    else:

        favicon_href = favicon_locator.first.get_attribute(
            "href"
        )

        if favicon_href:

            print(
                "PASS | Favicon |",
                favicon_href
            )

            pass_count += 1

        else:

            print(
                "WARNING | Favicon | Empty href"
            )

            warning_count += 1

    # -------------------------------------
    # CHARACTER ENCODING
    # -------------------------------------

    charset_locator = page.locator(
        'meta[charset]'
    )

    if charset_locator.count() == 0:

        print(
            "WARNING | Charset | MISSING"
        )

        warning_count += 1

    else:

        charset = charset_locator.first.get_attribute(
            "charset"
        )

        if charset and charset.lower() == "utf-8":

            print(
                "PASS | Charset |",
                charset
            )

            pass_count += 1

        else:

            print(
                "WARNING | Charset |",
                charset or "EMPTY",
                "| Recommended: UTF-8"
            )

            warning_count += 1

    # -------------------------------------
    # STRUCTURED DATA / JSON-LD
    # -------------------------------------

    schema_locators = page.locator(
        'script[type="application/ld+json"]'
    )

    schema_count = schema_locators.count()

    if schema_count == 0:

        print(
            "WARNING | Structured Data | MISSING"
        )

        warning_count += 1

    else:

        valid_schema_count = 0
        invalid_schema_count = 0

        for i in range(schema_count):

            schema_text = schema_locators.nth(
                i
            ).text_content()

            if not schema_text:
                continue

            try:

                json.loads(schema_text)

                valid_schema_count += 1

            except json.JSONDecodeError:

                invalid_schema_count += 1

        if invalid_schema_count > 0:

            print(
                "WARNING | Structured Data |",
                schema_count,
                "found |",
                invalid_schema_count,
                "invalid JSON-LD"
            )

            warning_count += 1

        else:

            print(
                "PASS | Structured Data |",
                valid_schema_count,
                "valid JSON-LD block(s)"
            )

            pass_count += 1

    # -------------------------------------
    # HEADING HIERARCHY CHECK
    # -------------------------------------

    heading_locator = page.locator(
        "h1, h2, h3, h4, h5, h6"
    )

    heading_count = heading_locator.count()

    previous_level = 0
    heading_issues = 0

    for i in range(heading_count):

        heading = heading_locator.nth(i)

        tag_name = heading.evaluate(
            "(el) => el.tagName.toLowerCase()"
        )

        heading_text = heading.inner_text().strip()

        level = int(
            tag_name.replace("h", "")
        )

        # Detect skipped heading levels
        # Example: H2 followed directly by H4
        if (
            previous_level > 0
            and level > previous_level + 1
        ):

            heading_issues += 1

            print(
                "WARNING | Heading Hierarchy |",
                f"H{previous_level} → H{level}",
                "|",
                heading_text
            )

        previous_level = level


    if heading_issues == 0:

        print(
            "PASS | Heading Hierarchy |",
            heading_count,
            "headings checked"
        )

        pass_count += 1

    else:

        print(
            "WARNING | Heading Hierarchy |",
            heading_issues,
            "issue(s) found"
        )

        warning_count += 1

    # -------------------------------------
    # META TAG SUMMARY
    # -------------------------------------

    print("\nMeta Tag Summary")
    print("----------------")
    print("Passed:", pass_count)
    print("Failed:", fail_count)
    print("Warnings:", warning_count)

    

def normalize_url(url):
    parts = urlsplit(url)

    path = parts.path.rstrip("/")

    if not path:
        path = "/"

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            "",
            ""
        )
    )