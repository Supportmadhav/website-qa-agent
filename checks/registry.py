"""
Maps UI selection IDs to the existing QA check modules.

Keep all existing check modules unchanged.
"""

from checks.page_speed_check import check_page_speed
from checks.link_check import check_links
from checks.page_link_list_check import (
    check_page_link_list,
)
from checks.website_page_list_check import (
    check_website_page_list,
)
from checks.image_check import check_images
from checks.meta_check import check_meta_tags
from checks.sticky_header_check import check_sticky_header
from checks.css_animation_check import check_css_animations
from checks.browser_compatibility_check import (
    check_browser_compatibility,
)
from checks.google_translate_check import (
    check_google_translate,
)
from checks.whatsapp_check import check_whatsapp
from checks.social_media_check import (
    check_social_media,
)
from checks.contact_form_check import (
    check_contact_forms,
)
from checks.blog_check import check_blog_page
from checks.content_check import check_content
from checks.layout_design_check import (
    check_layout_design,
)


def _page_runner(function):
    def runner(
        *,
        page,
        playwright,
        url,
    ):
        return function(page)

    return runner


def _browser_runner(
    *,
    page,
    playwright,
    url,
):
    return check_browser_compatibility(
        playwright,
        url,
    )


CHECK_REGISTRY = {
    "page_speed": {
        "label": "Page Speed",
        "category": "Performance",
        "runner": _page_runner(
            check_page_speed
        ),
    },
    "links": {
        "label": "Broken Links",
        "category": "Site Integrity",
        "runner": _page_runner(
            check_links
        ),
    },
    "page_link_list": {
        "label": "Page Link List",
        "category": "Site Integrity",
        "runner": _page_runner(
            check_page_link_list
        ),
    },
    "website_page_list": {
        "label": "Website Page List",
        "category": "Site Integrity",
        "runner": _page_runner(
            check_website_page_list
        ),
    },
    "images": {
        "label": "Image Optimization",
        "category": "Site Integrity",
        "runner": _page_runner(
            check_images
        ),
    },
    "meta": {
        "label": "Meta & Source Data",
        "category": "SEO",
        "runner": _page_runner(
            check_meta_tags
        ),
    },
    "sticky_header": {
        "label": "Sticky Header",
        "category": "Layout",
        "runner": _page_runner(
            check_sticky_header
        ),
    },
    "css_animation": {
        "label": "CSS Animation",
        "category": "Experience",
        "runner": _page_runner(
            check_css_animations
        ),
    },
    "google_translate": {
        "label": "Google Translate",
        "category": "Functionality",
        "runner": _page_runner(
            check_google_translate
        ),
    },
    "whatsapp": {
        "label": "WhatsApp",
        "category": "Functionality",
        "runner": _page_runner(
            check_whatsapp
        ),
    },
    "social_media": {
        "label": "Social Media",
        "category": "Functionality",
        "runner": _page_runner(
            check_social_media
        ),
    },
    "contact_form": {
        "label": "Contact Form",
        "category": "Functionality",
        "runner": _page_runner(
            check_contact_forms
        ),
    },
    "blog": {
        "label": "Blog Page",
        "category": "Content",
        "runner": _page_runner(
            check_blog_page
        ),
    },
    "content": {
        "label": "Content & Spelling",
        "category": "Content",
        "runner": _page_runner(
            check_content
        ),
    },
    "layout_design": {
        "label": "Layout & Design",
        "category": "Layout",
        "runner": _page_runner(
            check_layout_design
        ),
    },
    "browser_compatibility": {
        "label": "Browser Compatibility",
        "category": "Compatibility",
        "runner": _browser_runner,
    },
}


CHECK_ORDER = [
    "page_speed",
    "links",
    "page_link_list",
    "website_page_list",
    "images",
    "meta",
    "sticky_header",
    "css_animation",
    "google_translate",
    "whatsapp",
    "social_media",
    "contact_form",
    "blog",
    "content",
    "layout_design",
    "browser_compatibility",
]


PUBLIC_CHECKS = [
    {
        "id": check_id,
        "label": (
            CHECK_REGISTRY[
                check_id
            ]["label"]
        ),
        "category": (
            CHECK_REGISTRY[
                check_id
            ]["category"]
        ),
    }
    for check_id in CHECK_ORDER
]
