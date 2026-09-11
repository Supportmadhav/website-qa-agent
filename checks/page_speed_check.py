import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

import requests
from requests.exceptions import SSLError


PAGESPEED_ENDPOINT = (
    "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
)


def _status_for_score(score):
    if score is None:
        return "info"
    if score >= 90:
        return "pass"
    if score >= 50:
        return "warning"
    return "fail"


def _score_label(score):
    if score is None:
        return "Unavailable"
    if score >= 90:
        return "Good"
    if score >= 50:
        return "Needs improvement"
    return "Poor"


def _status_for_metric(metric_id, numeric_value):
    if numeric_value is None:
        return "info"

    limits = {
        "first-contentful-paint": (1800, 3000),
        "largest-contentful-paint": (2500, 4000),
        "cumulative-layout-shift": (0.10, 0.25),
        "total-blocking-time": (200, 600),
        "speed-index": (3400, 5800),
        "interactive": (3800, 7300),
    }

    good, warning = limits.get(
        metric_id,
        (None, None),
    )

    if good is None:
        return "info"

    if numeric_value <= good:
        return "pass"

    if numeric_value <= warning:
        return "warning"

    return "fail"


def _metric_target(metric_id):
    return {
        "first-contentful-paint": "Good <= 1.8 s",
        "largest-contentful-paint": "Good <= 2.5 s",
        "cumulative-layout-shift": "Good <= 0.10",
        "total-blocking-time": "Good <= 200 ms",
        "speed-index": "Good <= 3.4 s",
        "interactive": "Good <= 3.8 s",
    }.get(
        metric_id,
        "",
    )


def _metric_description(metric_id):
    return {
        "first-contentful-paint": (
            "When the browser first renders visible page content."
        ),
        "largest-contentful-paint": (
            "When the largest visible content element finishes rendering."
        ),
        "cumulative-layout-shift": (
            "How visually stable the page is while loading."
        ),
        "total-blocking-time": (
            "Main-thread blocking that can delay interaction."
        ),
        "speed-index": (
            "How quickly visible page content is populated."
        ),
        "interactive": (
            "Approximate time until the page becomes reliably interactive."
        ),
    }.get(
        metric_id,
        "Lighthouse performance metric.",
    )


def _audit_metric(audits, metric_id, label):
    audit = audits.get(
        metric_id,
        {},
    )

    numeric_value = audit.get(
        "numericValue"
    )

    return {
        "id": metric_id,
        "label": label,
        "value": numeric_value,
        "display": audit.get(
            "displayValue"
        ) or "Unavailable",
        "status": _status_for_metric(
            metric_id,
            numeric_value,
        ),
        "target": _metric_target(
            metric_id
        ),
        "description": _metric_description(
            metric_id
        ),
        "score": audit.get(
            "score"
        ),
    }


def _opportunity_status(score):
    if score is None:
        return "info"
    if score >= 0.9:
        return "pass"
    if score >= 0.5:
        return "warning"
    return "fail"


def _extract_opportunities(audits):
    opportunities = []

    for audit_id, audit in audits.items():
        score = audit.get(
            "score"
        )

        display_mode = audit.get(
            "scoreDisplayMode"
        )

        details = audit.get(
            "details"
        ) or {}

        details_type = details.get(
            "type"
        )

        if display_mode in {
            "notApplicable",
            "manual",
        }:
            continue

        if score is None:
            continue

        is_opportunity = (
            details_type == "opportunity"
            or score < 0.90
        )

        if not is_opportunity:
            continue

        savings_ms = details.get(
            "overallSavingsMs"
        )

        savings_bytes = details.get(
            "overallSavingsBytes"
        )

        opportunities.append({
            "id": audit_id,
            "title": audit.get(
                "title"
            ) or audit_id,
            "description": audit.get(
                "description"
            ) or "",
            "display": audit.get(
                "displayValue"
            ) or "",
            "score": score,
            "status": _opportunity_status(
                score
            ),
            "savings_ms": savings_ms,
            "savings_bytes": savings_bytes,
        })

    def ranking(item):
        return (
            item.get("savings_ms") or 0,
            item.get("savings_bytes") or 0,
            1 - (item.get("score") or 0),
        )

    opportunities.sort(
        key=ranking,
        reverse=True,
    )

    return opportunities[:12]


def _extract_diagnostics(audits):
    wanted = [
        "server-response-time",
        "render-blocking-resources",
        "unused-css-rules",
        "unused-javascript",
        "uses-text-compression",
        "modern-image-formats",
        "uses-optimized-images",
        "uses-responsive-images",
        "total-byte-weight",
        "mainthread-work-breakdown",
        "bootup-time",
        "third-party-summary",
    ]

    diagnostics = []

    for audit_id in wanted:
        audit = audits.get(
            audit_id
        )

        if not audit:
            continue

        score = audit.get(
            "score"
        )

        diagnostics.append({
            "id": audit_id,
            "title": audit.get(
                "title"
            ) or audit_id,
            "display": audit.get(
                "displayValue"
            ) or "",
            "score": score,
            "status": _opportunity_status(
                score
            ) if score is not None else "info",
        })

    return diagnostics


def _parse_pagespeed_response(strategy, body):
    lighthouse = body.get(
        "lighthouseResult"
    ) or {}

    categories = lighthouse.get(
        "categories"
    ) or {}

    performance = categories.get(
        "performance"
    ) or {}

    raw_score = performance.get(
        "score"
    )

    score = (
        round(
            raw_score * 100
        )
        if isinstance(
            raw_score,
            (int, float),
        )
        else None
    )

    audits = lighthouse.get(
        "audits"
    ) or {}

    metrics = [
        _audit_metric(
            audits,
            "first-contentful-paint",
            "First Contentful Paint",
        ),
        _audit_metric(
            audits,
            "largest-contentful-paint",
            "Largest Contentful Paint",
        ),
        _audit_metric(
            audits,
            "cumulative-layout-shift",
            "Cumulative Layout Shift",
        ),
        _audit_metric(
            audits,
            "total-blocking-time",
            "Total Blocking Time",
        ),
        _audit_metric(
            audits,
            "speed-index",
            "Speed Index",
        ),
        _audit_metric(
            audits,
            "interactive",
            "Time to Interactive",
        ),
    ]

    loading_experience = body.get(
        "loadingExperience"
    ) or {}

    return {
        "strategy": strategy,
        "score": score,
        "score_label": _score_label(
            score
        ),
        "overall_status": _status_for_score(
            score
        ),
        "requested_url": lighthouse.get(
            "requestedUrl"
        ),
        "final_url": lighthouse.get(
            "finalUrl"
        ),
        "fetch_time": lighthouse.get(
            "fetchTime"
        ),
        "lighthouse_version": lighthouse.get(
            "lighthouseVersion"
        ),
        "user_agent": lighthouse.get(
            "userAgent"
        ),
        "metrics": metrics,
        "opportunities": _extract_opportunities(
            audits
        ),
        "diagnostics": _extract_diagnostics(
            audits
        ),
        "run_warnings": lighthouse.get(
            "runWarnings"
        ) or [],
        "field_data": {
            "available": bool(
                loading_experience.get(
                    "metrics"
                )
            ),
            "overall_category": loading_experience.get(
                "overall_category"
            ),
            "metrics": loading_experience.get(
                "metrics"
            ) or {},
        },
    }


def _ssl_verify_setting():
    flag = os.getenv(
        "PAGESPEED_SSL_VERIFY",
        "",
    ).strip().lower()

    if flag in {
        "0",
        "false",
        "no",
        "off",
    }:
        return False

    return True


def _http_get(url, params, timeout):
    verify = _ssl_verify_setting()

    try:
        return requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={
                "Accept": "application/json",
            },
            verify=verify,
        )

    except SSLError:
        if verify is False:
            raise

        try:
            import urllib3

            urllib3.disable_warnings()

        except Exception:
            pass

        return requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={
                "Accept": "application/json",
            },
            verify=False,
        )


def _pagespeed_error_message(response, body=None):
    payload = body if isinstance(body, dict) else {}

    if not payload:
        try:
            payload = response.json()
        except Exception:
            payload = {}

    error = payload.get("error") or {}

    if isinstance(error, dict):
        message = (
            error.get("message")
            or error.get("status")
            or ""
        ).strip()

        if message:
            return message

    text = (
        getattr(response, "text", "")
        or ""
    ).strip()

    if text:
        return text[-800:]

    return (
        f"HTTP {getattr(response, 'status_code', '?')} "
        "from Google PageSpeed Insights"
    )


def _run_pagespeed(url, strategy):
    api_key = (
        os.getenv("PAGESPEED_API_KEY", "")
        or
        os.getenv("PAGESPEED_API_KEY", "")
        or
        os.getenv("GOOGLE_PAGESPEED_API_KEY", "")
    ).strip()

    params = [
        ("url", url),
        ("strategy", strategy),
        ("category", "performance"),
        ("locale", "en"),
    ]

    if api_key:
        params.append(
            ("key", api_key)
        )

    last_error = None

    for attempt in range(3):
        try:
            response = _http_get(
                PAGESPEED_ENDPOINT,
                params,
                120,
            )

            try:
                body = response.json()
            except Exception:
                body = {}

            if (
                response.status_code >= 400
                or
                body.get("error")
            ):
                raise RuntimeError(
                    _pagespeed_error_message(
                        response,
                        body,
                    )
                )

            if not (
                body.get("lighthouseResult")
                or {}
            ).get("categories"):
                raise RuntimeError(
                    "Google PageSpeed Insights returned no Lighthouse result."
                )

            result = _parse_pagespeed_response(
                strategy,
                body,
            )

            result["source"] = "google_pagespeed_insights"
            result["source_label"] = "Google PageSpeed Insights"

            return result

        except Exception as exc:
            last_error = exc

            message = str(exc).lower()

            if "quota exceeded" in message:
                break

            retryable = (
                "429" in message
                or
                "rate" in message
                or
                "timeout" in message
                or
                "timed out" in message
            )

            if (
                attempt < 2
                and
                retryable
            ):
                time.sleep(
                    4 * (attempt + 1)
                )
                continue

            break

    raise RuntimeError(
        str(last_error)
        or
        "Google PageSpeed Insights request failed"
    )



def _chrome_path_from_page(page):
    env_path = (
        os.getenv("CHROME_PATH", "")
        or
        os.getenv("LIGHTHOUSE_CHROME_PATH", "")
    ).strip()

    if env_path and os.path.exists(env_path):
        return env_path

    try:
        browser = page.context.browser

        browser_type = getattr(
            browser,
            "browser_type",
            None,
        )

        executable = getattr(
            browser_type,
            "executable_path",
            None,
        )

        if executable and os.path.exists(executable):
            return executable

    except Exception:
        pass

    return ""


def _candidate_lighthouse_command():
    """
    Prefer node + lighthouse CLI, then a local binary, then npx.
    Windows .cmd files are executed via shell so they actually start.
    """

    cwd = Path.cwd()

    node = (
        shutil.which("node.exe")
        or
        shutil.which("node")
    )

    cli_files = [
        cwd / "node_modules" / "lighthouse" / "cli" / "index.js",
        cwd / "frontend" / "node_modules" / "lighthouse" / "cli" / "index.js",
    ]

    if node:
        for cli_file in cli_files:
            if cli_file.exists():
                return [
                    node,
                    str(cli_file),
                ]

    names = (
        ("lighthouse.cmd", "lighthouse")
        if os.name == "nt"
        else ("lighthouse", "lighthouse.cmd")
    )

    folders = [
        cwd / "node_modules" / ".bin",
        cwd / "frontend" / "node_modules" / ".bin",
    ]

    for folder in folders:
        for name in names:
            candidate = folder / name

            if candidate.exists():
                return [
                    str(candidate)
                ]

    for name in names:
        found = shutil.which(name)

        if found:
            return [
                found
            ]

    npx = (
        shutil.which("npx.cmd")
        or
        shutil.which("npx")
    )

    if npx:
        return [
            npx,
            "--yes",
            "lighthouse",
        ]

    raise RuntimeError(
        "Local Lighthouse fallback requires Node.js/npm. "
        "The npx command was not found."
    )


def _run_process(command, timeout_seconds, env=None):
    first = str(command[0]).lower()

    use_shell = (
        os.name == "nt"
        and
        first.endswith(
            (
                ".cmd",
                ".bat",
            )
        )
    )

    kwargs = {
        "cwd": str(Path.cwd()),
        "capture_output": True,
        "text": True,
        "timeout": timeout_seconds,
        "check": False,
        "shell": use_shell,
    }

    if env is not None:
        kwargs["env"] = env

    if os.name == "nt":
        kwargs["creationflags"] = getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0,
        )

    if use_shell:
        return subprocess.run(
            subprocess.list2cmdline(command),
            **kwargs,
        )

    return subprocess.run(
        command,
        **kwargs,
    )


def _run_local_lighthouse(url, strategy, chrome_path=""):
    command = _candidate_lighthouse_command()

    timeout_seconds = int(
        os.getenv(
            "LIGHTHOUSE_TIMEOUT_SECONDS",
            "180",
        )
    )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".json",
            delete=False,
        ) as handle:
            temp_path = handle.name

        args = command + [
            url,
            "--only-categories=performance",
            "--output=json",
            f"--output-path={temp_path}",
            "--quiet",
            "--chrome-flags="
            "--headless=new --disable-gpu --no-sandbox --disable-dev-shm-usage",
        ]

        if chrome_path:
            args.append(
                f"--chrome-path={chrome_path}"
            )

        if strategy == "desktop":
            args.append(
                "--preset=desktop"
            )

        lh_tmp = Path.cwd() / ".lighthouse-tmp"
        lh_tmp.mkdir(
            exist_ok=True
        )

        env = os.environ.copy()
        env["TEMP"] = str(lh_tmp)
        env["TMP"] = str(lh_tmp)

        completed = _run_process(
            args,
            timeout_seconds,
            env,
        )

        report_file = Path(
            temp_path
        )

        if (
            completed.returncode != 0
            and
            (
                not report_file.exists()
                or
                report_file.stat().st_size == 0
            )
        ):
            details = (
                completed.stderr
                or
                completed.stdout
                or
                "Unknown Lighthouse CLI error"
            )

            raise RuntimeError(
                "Local Lighthouse failed: "
                +
                details[-1200:].strip()
            )

        if (
            not report_file.exists()
            or
            report_file.stat().st_size == 0
        ):
            raise RuntimeError(
                "Local Lighthouse did not produce a JSON report."
            )

        lighthouse = json.loads(
            report_file.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )

        if (
            isinstance(lighthouse, dict)
            and
            "categories" not in lighthouse
        ):
            lighthouse = (
                lighthouse.get("lighthouseResult")
                or lighthouse.get("lhr")
                or lighthouse
            )

        # Reuse the exact same Lighthouse parser used for Google PSI.
        result = _parse_pagespeed_response(
            strategy,
            {
                "lighthouseResult":
                    lighthouse,

                "loadingExperience":
                    {},
            },
        )

        result["source"] = "local_lighthouse"
        result["source_label"] = "Local Lighthouse"

        return result

    finally:
        if temp_path:
            try:
                Path(
                    temp_path
                ).unlink(
                    missing_ok=True
                )

            except Exception:
                pass


def _local_resource_diagnostics(page):
    performance = page.evaluate(
        """
        () => {
            const navigation =
                performance.getEntriesByType("navigation")[0];

            const resources =
                performance.getEntriesByType("resource")
                .map(
                    item => ({
                        name: item.name,
                        initiatorType: item.initiatorType || "",
                        duration: item.duration || 0,
                        transferSize:
                            item.transferSize ||
                            item.encodedBodySize ||
                            0
                    })
                );

            return {
                htmlSize:
                    navigation
                        ? (
                            navigation.transferSize ||
                            navigation.encodedBodySize ||
                            0
                          )
                        : 0,
                resources
            };
        }
        """
    )

    resources = performance.get(
        "resources",
        []
    )

    resource_summary = {
        "CSS": {"count": 0, "bytes": 0},
        "JavaScript": {"count": 0, "bytes": 0},
        "Images": {"count": 0, "bytes": 0},
        "Fonts": {"count": 0, "bytes": 0},
        "Other": {"count": 0, "bytes": 0},
    }

    image_ext = (
        ".jpg", ".jpeg", ".png", ".gif",
        ".webp", ".avif", ".svg", ".ico",
    )

    font_ext = (
        ".woff", ".woff2", ".ttf", ".otf", ".eot",
    )

    for item in resources:
        path = (
            urlsplit(
                item.get("name") or ""
            ).path.lower()
        )

        initiator = (
            item.get("initiatorType") or ""
        ).lower()

        if initiator == "css" or path.endswith(
            ".css"
        ):
            key = "CSS"

        elif initiator == "script" or path.endswith(
            ".js"
        ):
            key = "JavaScript"

        elif initiator in {
            "img",
            "image",
        } or path.endswith(
            image_ext
        ):
            key = "Images"

        elif initiator == "font" or path.endswith(
            font_ext
        ):
            key = "Fonts"

        else:
            key = "Other"

        resource_summary[key][
            "count"
        ] += 1

        resource_summary[key][
            "bytes"
        ] += item.get(
            "transferSize",
            0,
        ) or 0

    rows = []

    for resource_type, values in resource_summary.items():
        size_kb = round(
            values["bytes"] / 1024,
            2,
        )

        rows.append({
            "type": resource_type,
            "count": values["count"],
            "size_kb": size_kb,
            "size_display": (
                f"{size_kb / 1024:.2f} MB"
                if size_kb >= 1024
                else f"{size_kb:.2f} KB"
            ),
            "status": "info",
        })

    total_bytes = (
        performance.get(
            "htmlSize",
            0,
        )
        + sum(
            item.get(
                "transferSize",
                0,
            ) or 0
            for item in resources
        )
    )

    total_kb = round(
        total_bytes / 1024,
        2,
    )

    return {
        "html_size_kb": round(
            performance.get(
                "htmlSize",
                0,
            ) / 1024,
            2,
        ),
        "total_requests": len(
            resources
        ),
        "total_transfer_kb": total_kb,
        "total_transfer_display": (
            f"{total_kb / 1024:.2f} MB"
            if total_kb >= 1024
            else f"{total_kb:.2f} KB"
        ),
        "resource_summary": rows,
    }


def check_page_speed(page):
    """
    Official Google PageSpeed Insights / Lighthouse performance report.

    Main score source:
    Google PageSpeed Insights API v5, run separately for mobile and desktop.

    Local Playwright data is retained only as a secondary resource diagnostic.
    It is NOT used to invent a PageSpeed/Lighthouse score.
    """

    print(
        "\nPage Speed Check"
    )
    print(
        "----------------"
    )

    url = page.url

    try:
        local = _local_resource_diagnostics(
            page
        )

    except Exception as exc:
        local = {
            "resource_summary": [],
            "total_requests": 0,
            "total_transfer_kb": 0,
            "total_transfer_display": "Unavailable",
            "html_size_kb": 0,
            "error": str(exc),
        }

    strategies = {}
    google_errors = {}
    local_errors = {}
    chrome_path = _chrome_path_from_page(
        page
    )

    # Run Google PSI one strategy at a time. Parallel calls without an
    # API key are a common cause of 429s / empty Page Speed reports.
    for strategy in (
        "mobile",
        "desktop",
    ):
        try:
            strategies[
                strategy
            ] = _run_pagespeed(
                url,
                strategy,
            )

        except Exception as exc:
            google_errors[
                strategy
            ] = str(
                exc
            )

    # =====================================
    # LOCAL LIGHTHOUSE FALLBACK
    # =====================================
    # Run missing strategies sequentially so two local Lighthouse
    # instances do not compete for CPU/RAM and distort each other.
    for strategy in (
        "mobile",
        "desktop",
    ):
        if strategy in strategies:
            continue

        try:
            strategies[
                strategy
            ] = _run_local_lighthouse(
                url,
                strategy,
                chrome_path,
            )

        except Exception as exc:
            local_errors[
                strategy
            ] = str(
                exc
            )

    api_available = bool(
        strategies
    )

    default_strategy = (
        "desktop"
        if "desktop" in strategies
        else "mobile"
        if "mobile" in strategies
        else None
    )

    default = (
        strategies.get(
            default_strategy,
            {}
        )
        if default_strategy
        else {}
    )

    recommendations = []

    for opportunity in default.get(
        "opportunities",
        []
    ):
        if opportunity.get(
            "status"
        ) not in {
            "warning",
            "fail",
        }:
            continue

        recommendations.append({
            "priority": (
                "High"
                if opportunity.get(
                    "status"
                ) == "fail"
                else "Medium"
            ),
            "status": opportunity.get(
                "status"
            ),
            "title": opportunity.get(
                "title"
            ),
            "recommendation": opportunity.get(
                "display"
            ) or opportunity.get(
                "description",
                "",
            ),
        })

    strategy_sources = {
        strategy:
            result.get(
                "source",
                "google_pagespeed_insights",
            )
        for strategy, result in strategies.items()
    }

    source_values = set(
        strategy_sources.values()
    )

    if not api_available:
        source = "unavailable"
        source_label = "Lighthouse unavailable"

    elif len(source_values) == 1:
        source = next(
            iter(
                source_values
            )
        )

        source_label = (
            "Google PageSpeed Insights"
            if source == "google_pagespeed_insights"
            else "Local Lighthouse"
        )

    else:
        source = "mixed"
        source_label = "Google PSI + Local Lighthouse"

    all_errors = {
        **google_errors,
        **{
            f"{strategy}_local":
                message
            for strategy, message in local_errors.items()
        },
    }

    page_speed_data = {
        "source":
            source,

        "source_label":
            source_label,

        "available":
            api_available,

        # Backward compatibility with earlier frontend code.
        "api_available":
            api_available,

        "google_available":
            any(
                value == "google_pagespeed_insights"
                for value in strategy_sources.values()
            ),

        "local_available":
            any(
                value == "local_lighthouse"
                for value in strategy_sources.values()
            ),

        "fallback_used":
            any(
                value == "local_lighthouse"
                for value in strategy_sources.values()
            ),

        "strategy_sources":
            strategy_sources,

        "default_strategy": default_strategy,
        "strategies": strategies,
        "api_errors": all_errors,
        "google_errors": google_errors,
        "local_errors": local_errors,
        "api_key_configured": bool(
            (
                os.getenv("PAGESPEED_API_KEY", "")
                or
                os.getenv("PAGESPEED_API_KEY", "")
                or
                os.getenv("GOOGLE_PAGESPEED_API_KEY", "")
            ).strip()
        ),
        "note": (
            "Google PageSpeed Insights is preferred. If Google is rate-limited "
            "or unavailable, a real Lighthouse run is performed locally. "
            "Local and Google lab scores can differ because they use different "
            "hardware and network environments. No custom score is invented."
        ),

        # Backward-compatible fields used by existing PDF/report code.
        "score": default.get(
            "score"
        ),
        "score_label": default.get(
            "score_label",
            "Unavailable",
        ),
        "overall_status": default.get(
            "overall_status",
            "info",
        ),
        "metrics": default.get(
            "metrics",
            [],
        ),
        "recommendations": recommendations,
        "resource_summary": local.get(
            "resource_summary",
            [],
        ),
        "total_requests": local.get(
            "total_requests",
            0,
        ),
        "total_transfer_kb": local.get(
            "total_transfer_kb",
            0,
        ),
        "total_transfer_display": local.get(
            "total_transfer_display",
            "Unavailable",
        ),
        "html_size_kb": local.get(
            "html_size_kb",
            0,
        ),
        "html_size_display": (
            f"{local.get('html_size_kb', 0):.2f} KB"
        ),
        "slow_resources": [],
        "local_resource_diagnostics": local,
    }

    print(
        "QA_PAGE_SPEED|"
        + json.dumps(
            page_speed_data,
            ensure_ascii=False,
        )
    )

    if not api_available:
        print(
            "WARNING | Google PageSpeed Insights | "
            "Official Lighthouse score could not be retrieved"
        )

        for strategy, message in google_errors.items():
            print(
                f"INFO | Google {strategy.title()} API Error | {message}"
            )

        for strategy, message in local_errors.items():
            print(
                f"INFO | Local {strategy.title()} Lighthouse Error | {message}"
            )

        print(
            "INFO | Local Resource Diagnostics | "
            f"{local.get('total_requests', 0)} requests | "
            f"{local.get('total_transfer_display', 'Unavailable')} transferred"
        )

        print(
            "\nPage Speed Check Complete"
        )

        return

    for strategy in (
        "mobile",
        "desktop",
    ):
        result = strategies.get(
            strategy
        )

        if not result:
            continue

        status = result[
            "overall_status"
        ].upper()

        print(
            f"{status} | {result.get('source_label', 'Lighthouse')} "
            f"{strategy.title()} Score | "
            f"{result['score']} / 100 | {result['score_label']}"
        )

        for metric in result.get(
            "metrics",
            []
        ):
            print(
                f"{metric['status'].upper()} | "
                f"{strategy.title()} - {metric['label']} | "
                f"{metric['display']} | {metric['target']}"
            )

    if google_errors:
        print(
            "INFO | Google PSI Fallback | "
            "Google was unavailable/rate-limited for one or more strategies; "
            "Local Lighthouse was used where possible"
        )

    print(
        "INFO | Local Page Requests |",
        local.get(
            "total_requests",
            0,
        )
    )

    print(
        "INFO | Local Transfer Size |",
        local.get(
            "total_transfer_display",
            "Unavailable",
        )
    )

    print(
        "\nPage Speed Check Complete"
    )
