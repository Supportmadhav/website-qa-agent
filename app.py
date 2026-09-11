import asyncio
import base64
import re
import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from playwright.async_api import (
    TimeoutError as PlaywrightAsyncTimeoutError,
    async_playwright,
)

from checks.registry import PUBLIC_CHECKS
from scanner import run_scan
from audit import run_website_audit



app = FastAPI(
    title="Website QA Agent API",
    version="2.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResponsiveBrowserSessionRequest(
    BaseModel
):
    url: str = Field(
        min_length=3
    )

    width: int = Field(
        ge=324,
        le=1920
    )

    height: int = Field(
        ge=480,
        le=2160
    )


class ResponsiveBrowserActionRequest(
    BaseModel
):
    session_id: str = Field(
        min_length=8
    )

    action: str = Field(
        min_length=1
    )

    x: float | None = None
    y: float | None = None

    delta_x: float = 0
    delta_y: float = 0

    text: str | None = None
    key: str | None = None
    url: str | None = None


class ResponsiveBrowserScreenshotRequest(
    BaseModel
):
    session_id: str = Field(
        min_length=8
    )

    full_page: bool = True


class ScanRequest(BaseModel):
    url: str = Field(
        min_length=3
    )

    checks: list[str] = Field(
        default_factory=list
    )


class AuditRequest(BaseModel):
    url: str = Field(
        min_length=3
    )


@app.get("/")
def root():
    return {
        "name": "Website QA Agent",
        "status": "ready",
        "selection_limit": None,
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
    }


@app.get("/api/checks")
def get_checks():
    return PUBLIC_CHECKS




# ============================================================
# RESPONSIVE STUDIO - LIVE BROWSER
# ============================================================

_LIVE_PLAYWRIGHT = None
_LIVE_BROWSER = None
_LIVE_BROWSER_LOCK = asyncio.Lock()
_LIVE_SESSIONS = {}

_LIVE_SESSION_TTL_SECONDS = 30 * 60


def _normalize_live_url(
    url: str
) -> str:
    normalized = (
        url
        or
        ""
    ).strip()

    if not normalized.startswith(
        (
            "http://",
            "https://",
        )
    ):
        normalized = (
            "https://"
            +
            normalized
        )

    return normalized


async def _ensure_live_browser():
    global _LIVE_PLAYWRIGHT
    global _LIVE_BROWSER

    async with _LIVE_BROWSER_LOCK:
        if (
            _LIVE_BROWSER is not None
            and
            _LIVE_BROWSER.is_connected()
        ):
            return _LIVE_BROWSER

        if _LIVE_PLAYWRIGHT is None:
            _LIVE_PLAYWRIGHT = (
                await async_playwright()
                .start()
            )

        _LIVE_BROWSER = (
            await _LIVE_PLAYWRIGHT
            .chromium
            .launch(
                headless=True
            )
        )

        return _LIVE_BROWSER


async def _close_live_session(
    session_id: str
):
    session = (
        _LIVE_SESSIONS.pop(
            session_id,
            None,
        )
    )

    if not session:
        return

    try:
        await session[
            "context"
        ].close()

    except Exception:
        pass


async def _cleanup_live_sessions():
    now = (
        time.time()
    )

    stale_ids = [
        session_id
        for (
            session_id,
            session,
        ) in (
            _LIVE_SESSIONS.items()
        )
        if (
            now
            -
            session.get(
                "last_access",
                now,
            )
        )
        >
        _LIVE_SESSION_TTL_SECONDS
    ]

    for session_id in stale_ids:
        await _close_live_session(
            session_id
        )


async def _get_live_session(
    session_id: str
):
    session = (
        _LIVE_SESSIONS.get(
            session_id
        )
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail=(
                "Responsive browser session was not found "
                "or has expired. Start the live browser again."
            ),
        )

    session[
        "last_access"
    ] = time.time()

    return session


def _safe_download_name(
    value: str
) -> str:
    cleaned = (
        value
        or
        "website"
    ).lower()

    cleaned = re.sub(
        r"^www\.",
        "",
        cleaned,
    )

    cleaned = re.sub(
        r"[^a-z0-9.-]+",
        "-",
        cleaned,
    )

    cleaned = (
        cleaned.strip(
            "-"
        )
        or
        "website"
    )

    return cleaned


async def _active_live_page(
    session
):
    context = (
        session[
            "context"
        ]
    )

    pages = [
        page
        for page in context.pages
        if not page.is_closed()
    ]

    if not pages:
        page = (
            await context.new_page()
        )

        session[
            "page"
        ] = page

        return page

    current = (
        session.get(
            "page"
        )
    )

    if (
        current is None
        or
        current.is_closed()
    ):
        current = pages[
            -1
        ]

    # If a click opened a new tab/window, make the newest page active.
    if (
        pages[
            -1
        ]
        is not current
    ):
        current = pages[
            -1
        ]

    session[
        "page"
    ] = current

    return current


async def _live_browser_state(
    session_id: str,
    session,
    *,
    quality: int = 72,
):
    page = (
        await _active_live_page(
            session
        )
    )

    try:
        metadata = (
            await page.evaluate(
                """
                () => ({
                    scroll_x:
                        window.scrollX,

                    scroll_y:
                        window.scrollY,

                    document_width:
                        document.documentElement.scrollWidth,

                    document_height:
                        Math.max(
                            document.body?.scrollHeight || 0,
                            document.documentElement.scrollHeight
                        ),

                    viewport_width:
                        window.innerWidth,

                    viewport_height:
                        window.innerHeight
                })
                """
            )
        )

    except Exception:
        metadata = {
            "scroll_x": 0,
            "scroll_y": 0,
            "document_width":
                session[
                    "width"
                ],
            "document_height":
                session[
                    "height"
                ],
            "viewport_width":
                session[
                    "width"
                ],
            "viewport_height":
                session[
                    "height"
                ],
        }

    try:
        image = (
            await page.screenshot(
                full_page=False,
                type="jpeg",
                quality=quality,
                animations="allow",
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not capture the live browser frame: "
                +
                str(
                    exc
                )
            ),
        ) from exc

    try:
        title = (
            await page.title()
        )

    except Exception:
        title = ""

    try:
        hostname = (
            await page.evaluate(
                "() => location.hostname"
            )
        )

    except Exception:
        hostname = "website"

    return {
        "session_id":
            session_id,

        "url":
            page.url,

        "title":
            title,

        "hostname":
            hostname,

        "http_status":
            session.get(
                "http_status"
            ),

        "viewport": {
            "width":
                session[
                    "width"
                ],

            "height":
                session[
                    "height"
                ],
        },

        "scroll_x":
            metadata.get(
                "scroll_x",
                0,
            ),

        "scroll_y":
            metadata.get(
                "scroll_y",
                0,
            ),

        "document_width":
            metadata.get(
                "document_width"
            ),

        "document_height":
            metadata.get(
                "document_height"
            ),

        "image_mime":
            "image/jpeg",

        "image_base64":
            base64.b64encode(
                image
            ).decode(
                "ascii"
            ),

        "live":
            True,
    }


async def _goto_live_page(
    session,
    url: str
):
    page = (
        await _active_live_page(
            session
        )
    )

    normalized = (
        _normalize_live_url(
            url
        )
    )

    response = None

    try:
        response = (
            await page.goto(
                normalized,
                wait_until=
                    "domcontentloaded",
                timeout=
                    30_000,
            )
        )

    except PlaywrightAsyncTimeoutError:
        pass

    try:
        await page.wait_for_load_state(
            "load",
            timeout=
                5_000,
        )

    except PlaywrightAsyncTimeoutError:
        pass

    await page.wait_for_timeout(
        180
    )

    if response:
        session[
            "http_status"
        ] = response.status

    return page


async def _prepare_full_page(
    page
):
    """
    Trigger lazy-loaded sections before a full-page PNG capture,
    while preserving the user's current scroll position.
    """

    try:
        position = (
            await page.evaluate(
                """
                () => ({
                    x: window.scrollX,
                    y: window.scrollY
                })
                """
            )
        )

    except Exception:
        position = {
            "x": 0,
            "y": 0,
        }

    try:
        await page.evaluate(
            """
            async () => {
                const wait = (ms) =>
                    new Promise(
                        resolve =>
                            setTimeout(
                                resolve,
                                ms
                            )
                    );

                let lastHeight = 0;

                for (
                    let pass = 0;
                    pass < 3;
                    pass += 1
                ) {
                    const total =
                        Math.max(
                            document.body?.scrollHeight || 0,
                            document.documentElement.scrollHeight
                        );

                    if (
                        total === lastHeight
                        &&
                        pass > 0
                    ) {
                        break;
                    }

                    lastHeight =
                        total;

                    const viewport =
                        Math.max(
                            window.innerHeight,
                            500
                        );

                    const step =
                        Math.max(
                            300,
                            Math.floor(
                                viewport
                                *
                                0.75
                            )
                        );

                    for (
                        let y = 0;
                        y < total;
                        y += step
                    ) {
                        window.scrollTo(
                            0,
                            y
                        );

                        await wait(
                            90
                        );
                    }

                    window.scrollTo(
                        0,
                        Math.max(
                            0,
                            total
                            -
                            viewport
                        )
                    );

                    await wait(
                        250
                    );
                }
            }
            """
        )

    finally:
        try:
            await page.evaluate(
                """
                ({x, y}) => {
                    window.scrollTo(
                        x,
                        y
                    );
                }
                """,
                position,
            )

            await page.wait_for_timeout(
                180
            )

        except Exception:
            pass


@app.post(
    "/api/responsive-browser/session"
)
async def responsive_browser_session(
    payload:
        ResponsiveBrowserSessionRequest
):
    await _cleanup_live_sessions()

    browser = (
        await _ensure_live_browser()
    )

    context = (
        await browser.new_context(
            viewport={
                "width":
                    payload.width,

                "height":
                    payload.height,
            },

            device_scale_factor=
                1,

            ignore_https_errors=
                True,

            accept_downloads=
                True,
        )
    )

    page = (
        await context.new_page()
    )

    session_id = (
        uuid.uuid4().hex
    )

    session = {
        "context":
            context,

        "page":
            page,

        "width":
            payload.width,

        "height":
            payload.height,

        "http_status":
            None,

        "last_access":
            time.time(),

        "lock":
            asyncio.Lock(),
    }

    _LIVE_SESSIONS[
        session_id
    ] = session

    try:
        async with session[
            "lock"
        ]:
            await _goto_live_page(
                session,
                payload.url,
            )

            return await _live_browser_state(
                session_id,
                session,
            )

    except Exception:
        await _close_live_session(
            session_id
        )

        raise


@app.get(
    "/api/responsive-browser/frame/{session_id}"
)
async def responsive_browser_frame(
    session_id: str
):
    session = (
        await _get_live_session(
            session_id
        )
    )

    async with session[
        "lock"
    ]:
        return await _live_browser_state(
            session_id,
            session,
            quality=68,
        )


@app.post(
    "/api/responsive-browser/action"
)
async def responsive_browser_action(
    payload:
        ResponsiveBrowserActionRequest
):
    session = (
        await _get_live_session(
            payload.session_id
        )
    )

    async with session[
        "lock"
    ]:
        page = (
            await _active_live_page(
                session
            )
        )

        action = (
            payload.action
            .strip()
            .lower()
        )

        try:
            if action == "click":
                if (
                    payload.x is None
                    or
                    payload.y is None
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Click action requires x and y coordinates."
                        ),
                    )

                await page.mouse.click(
                    payload.x,
                    payload.y,
                )

                await page.wait_for_timeout(
                    160
                )

            elif action == "scroll":
                await page.mouse.wheel(
                    payload.delta_x,
                    payload.delta_y,
                )

                await page.wait_for_timeout(
                    110
                )

            elif action == "text":
                if payload.text:
                    await page.keyboard.insert_text(
                        payload.text
                    )

                    await page.wait_for_timeout(
                        70
                    )

            elif action == "key":
                if not payload.key:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Key action requires a key value."
                        ),
                    )

                await page.keyboard.press(
                    payload.key
                )

                await page.wait_for_timeout(
                    90
                )

            elif action == "reload":
                response = None

                try:
                    response = (
                        await page.reload(
                            wait_until=
                                "domcontentloaded",
                            timeout=
                                30_000,
                        )
                    )

                except PlaywrightAsyncTimeoutError:
                    pass

                if response:
                    session[
                        "http_status"
                    ] = response.status

            elif action == "back":
                response = None

                try:
                    response = (
                        await page.go_back(
                            wait_until=
                                "domcontentloaded",
                            timeout=
                                15_000,
                        )
                    )

                except PlaywrightAsyncTimeoutError:
                    pass

                if response:
                    session[
                        "http_status"
                    ] = response.status

            elif action == "forward":
                response = None

                try:
                    response = (
                        await page.go_forward(
                            wait_until=
                                "domcontentloaded",
                            timeout=
                                15_000,
                        )
                    )

                except PlaywrightAsyncTimeoutError:
                    pass

                if response:
                    session[
                        "http_status"
                    ] = response.status

            elif action == "navigate":
                if not payload.url:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Navigate action requires a URL."
                        ),
                    )

                await _goto_live_page(
                    session,
                    payload.url,
                )

            else:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unsupported live browser action: {payload.action}"
                    ),
                )

            # A click may open a new tab/window.
            await _active_live_page(
                session
            )

            return await _live_browser_state(
                payload.session_id,
                session,
            )

        except HTTPException:
            raise

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Live browser interaction failed: "
                    +
                    str(
                        exc
                    )
                ),
            ) from exc


@app.post(
    "/api/responsive-browser/screenshot"
)
async def responsive_browser_screenshot(
    payload:
        ResponsiveBrowserScreenshotRequest
):
    session = (
        await _get_live_session(
            payload.session_id
        )
    )

    async with session[
        "lock"
    ]:
        page = (
            await _active_live_page(
                session
            )
        )

        if payload.full_page:
            await _prepare_full_page(
                page
            )

        try:
            image = (
                await page.screenshot(
                    full_page=
                        payload.full_page,

                    type=
                        "png",

                    animations=
                        "disabled",
                )
            )

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not generate the screenshot: "
                    +
                    str(
                        exc
                    )
                ),
            ) from exc

        try:
            hostname = (
                await page.evaluate(
                    "() => location.hostname"
                )
            )

        except Exception:
            hostname = "website"

        safe_host = (
            re.sub(
                r"[^a-z0-9.-]+",
                "-",
                (
                    hostname
                    or
                    "website"
                ).lower(),
            )
            .strip(
                "-"
            )
            or
            "website"
        )

        scope = (
            "full-page"
            if payload.full_page
            else
            "viewport"
        )

        return {
            "image_mime":
                "image/png",

            "image_extension":
                "png",

            "image_base64":
                base64.b64encode(
                    image
                ).decode(
                    "ascii"
                ),

            "filename":
                (
                    f"{safe_host}-"
                    f"{session['width']}x{session['height']}-"
                    f"{scope}.png"
                ),
        }


@app.delete(
    "/api/responsive-browser/session/{session_id}"
)
async def responsive_browser_close(
    session_id: str
):
    await _close_live_session(
        session_id
    )

    return {
        "status":
            "closed",

        "session_id":
            session_id,
    }


@app.on_event(
    "shutdown"
)
async def responsive_browser_shutdown():
    global _LIVE_PLAYWRIGHT
    global _LIVE_BROWSER

    session_ids = list(
        _LIVE_SESSIONS.keys()
    )

    for session_id in session_ids:
        await _close_live_session(
            session_id
        )

    if _LIVE_BROWSER is not None:
        try:
            await _LIVE_BROWSER.close()

        except Exception:
            pass

        _LIVE_BROWSER = None

    if _LIVE_PLAYWRIGHT is not None:
        try:
            await _LIVE_PLAYWRIGHT.stop()

        except Exception:
            pass

        _LIVE_PLAYWRIGHT = None


@app.post("/api/scan")
def scan_website(
    payload: ScanRequest
):
    if not payload.checks:
        raise HTTPException(
            status_code=400,
            detail=(
                "Select at least one QA check."
            ),
        )

    try:
        return run_scan(
            payload.url,
            payload.checks,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Scan failed: {exc}"
            ),
        ) from exc


@app.post("/api/audit")
def audit_website(
    payload: AuditRequest
):
    try:
        return run_website_audit(
            payload.url
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Website audit failed: {exc}"
            ),
        ) from exc
