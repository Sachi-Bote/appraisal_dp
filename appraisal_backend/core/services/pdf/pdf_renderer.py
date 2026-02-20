from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings
from xhtml2pdf import pisa
from io import BytesIO
import os
import subprocess
import tempfile
from pathlib import Path
import logging
from glob import glob
from time import perf_counter

logger = logging.getLogger(__name__)
perf_logger = logging.getLogger("api.performance")


def _discover_playwright_binaries() -> list[str]:
    """
    Discover Chromium/headless-shell binaries installed by Playwright.
    """
    roots = []
    env_root = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if env_root:
        roots.append(env_root)
    roots.append(str(Path.cwd() / ".playwright"))

    candidates: list[str] = []
    for root in roots:
        if not root or not os.path.exists(root):
            continue
        patterns = [
            os.path.join(root, "chromium-*", "**", "chrome"),
            os.path.join(root, "chromium_headless_shell-*", "**", "headless_shell"),
        ]
        for pattern in patterns:
            for match in glob(pattern, recursive=True):
                if os.path.exists(match):
                    candidates.append(match)

    # Preserve order and remove duplicates.
    seen = set()
    ordered = []
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        ordered.append(c)
    return ordered


def _render_with_xhtml2pdf(html: str) -> bytes:
    started = perf_counter()
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if pdf.err:
        raise Exception("Error generating PDF with xhtml2pdf")
    perf_logger.info(
        "pdf.engine_timing engine=xhtml2pdf html_size=%s duration_ms=%.2f",
        len(html),
        (perf_counter() - started) * 1000,
    )
    return result.getvalue()


def _render_with_playwright(html: str) -> bytes:
    """
    Render PDF using Chromium (Playwright) for browser-accurate output.
    """
    from playwright.sync_api import sync_playwright

    configured_path = getattr(settings, "PLAYWRIGHT_BROWSER_PATH", "") or ""
    browser_paths = [configured_path] if configured_path else []
    browser_paths.extend(_discover_playwright_binaries())
    browser_paths.extend([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ])

    started = perf_counter()
    launch_started = perf_counter()
    with sync_playwright() as p:
        browser = None
        launch_errors = []
        launch_args = ["--no-sandbox", "--disable-dev-shm-usage"]

        for candidate in browser_paths:
            if candidate and os.path.exists(candidate):
                try:
                    browser = p.chromium.launch(
                        headless=True,
                        executable_path=candidate,
                        args=launch_args,
                    )
                    break
                except Exception as e:
                    launch_errors.append(f"{candidate}: {e}")

        if browser is None:
            try:
                # Use Playwright managed browser when installed at build-time.
                browser = p.chromium.launch(headless=True, args=launch_args)
            except Exception as e:
                launch_errors.append(f"managed-browser: {e}")

        if browser is None:
            try:
                browser = p.chromium.launch(headless=True, channel="msedge", args=launch_args)
            except Exception as e:
                launch_errors.append(f"channel-msedge: {e}")

        if browser is None:
            logger.error(
                "Playwright launch failed. PLAYWRIGHT_BROWSERS_PATH=%s candidates=%s errors=%s",
                os.getenv("PLAYWRIGHT_BROWSERS_PATH", ""),
                browser_paths,
                launch_errors,
            )
            raise Exception("Playwright browser launch failed: " + " | ".join(launch_errors))
        launch_ms = (perf_counter() - launch_started) * 1000

        try:
            pdf_started = perf_counter()
            page = browser.new_page()
            page.set_content(html, wait_until="load")
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
            )
            pdf_ms = (perf_counter() - pdf_started) * 1000
            perf_logger.info(
                "pdf.engine_timing engine=playwright html_size=%s launch_ms=%.2f pdf_ms=%.2f total_ms=%.2f",
                len(html),
                launch_ms,
                pdf_ms,
                (perf_counter() - started) * 1000,
            )
            return pdf_bytes
        finally:
            browser.close()


def _render_with_edge_cli(html: str) -> bytes:
    """
    Render PDF using local Microsoft Edge headless CLI.
    This avoids requiring Playwright/Python package in runtime.
    """
    started = perf_counter()
    edge_path = getattr(settings, "EDGE_BROWSER_PATH", "") or r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        raise Exception(f"Edge executable not found at: {edge_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = os.path.join(tmpdir, "render.html")
        pdf_path = os.path.join(tmpdir, "render.pdf")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        file_uri = Path(html_path).as_uri()

        cmd = [
            edge_path,
            "--headless=new",
            "--disable-gpu",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=10000",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={pdf_path}",
            file_uri,
        ]

        render_started = perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        render_ms = (perf_counter() - render_started) * 1000

        if proc.returncode != 0 or not os.path.exists(pdf_path):
            stderr = (proc.stderr or "").strip()
            stdout = (proc.stdout or "").strip()
            raise Exception(f"Edge CLI PDF generation failed. rc={proc.returncode} stderr={stderr} stdout={stdout}")

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        perf_logger.info(
            "pdf.engine_timing engine=edge-cli html_size=%s cli_ms=%.2f total_ms=%.2f",
            len(html),
            render_ms,
            (perf_counter() - started) * 1000,
        )
        return pdf_bytes


def _render_pdf_bytes(html: str) -> tuple[bytes, str]:
    started = perf_counter()
    engine = getattr(settings, "PDF_RENDER_ENGINE", "auto").lower()
    allow_fallback = getattr(settings, "PDF_ALLOW_FALLBACK", True)

    if engine == "xhtml2pdf":
        out = _render_with_xhtml2pdf(html), "xhtml2pdf"
        perf_logger.info(
            "pdf.render_pipeline_timing engine_config=%s selected=%s total_ms=%.2f",
            engine,
            out[1],
            (perf_counter() - started) * 1000,
        )
        return out

    if engine == "edge":
        out = _render_with_edge_cli(html), "edge-cli"
        perf_logger.info(
            "pdf.render_pipeline_timing engine_config=%s selected=%s total_ms=%.2f",
            engine,
            out[1],
            (perf_counter() - started) * 1000,
        )
        return out

    if engine == "playwright":
        try:
            out = _render_with_playwright(html), "playwright"
            perf_logger.info(
                "pdf.render_pipeline_timing engine_config=%s selected=%s total_ms=%.2f",
                engine,
                out[1],
                (perf_counter() - started) * 1000,
            )
            return out
        except Exception as e:
            if allow_fallback:
                logger.warning("Playwright render failed; using xhtml2pdf fallback. error=%s", e)
                out = _render_with_xhtml2pdf(html), "xhtml2pdf-fallback"
                perf_logger.info(
                    "pdf.render_pipeline_timing engine_config=%s selected=%s fallback=true total_ms=%.2f",
                    engine,
                    out[1],
                    (perf_counter() - started) * 1000,
                )
                return out
            raise Exception(f"Playwright rendering failed and fallback disabled: {e}")

    if engine in {"playwright", "auto"}:
        # Try Edge CLI first (no Python Playwright dependency)
        try:
            out = _render_with_edge_cli(html), "edge-cli"
            perf_logger.info(
                "pdf.render_pipeline_timing engine_config=%s selected=%s total_ms=%.2f",
                engine,
                out[1],
                (perf_counter() - started) * 1000,
            )
            return out
        except Exception:
            pass

        try:
            out = _render_with_playwright(html), "playwright"
            perf_logger.info(
                "pdf.render_pipeline_timing engine_config=%s selected=%s total_ms=%.2f",
                engine,
                out[1],
                (perf_counter() - started) * 1000,
            )
            return out
        except Exception as e:
            if allow_fallback:
                logger.warning("Playwright render failed in auto mode; using xhtml2pdf fallback. error=%s", e)
                out = _render_with_xhtml2pdf(html), "xhtml2pdf-fallback"
                perf_logger.info(
                    "pdf.render_pipeline_timing engine_config=%s selected=%s fallback=true total_ms=%.2f",
                    engine,
                    out[1],
                    (perf_counter() - started) * 1000,
                )
                return out
            raise Exception(f"Playwright rendering failed and fallback disabled: {e}")

    # Unknown engine -> safe fallback
    out = _render_with_xhtml2pdf(html), "xhtml2pdf-fallback"
    perf_logger.info(
        "pdf.render_pipeline_timing engine_config=%s selected=%s fallback=true total_ms=%.2f",
        engine,
        out[1],
        (perf_counter() - started) * 1000,
    )
    return out


def render_to_pdf(template_path: str, context: dict) -> HttpResponse:
    started = perf_counter()
    template_started = perf_counter()
    template = get_template(template_path)
    html = template.render(context)
    template_ms = (perf_counter() - template_started) * 1000
    render_started = perf_counter()
    try:
        pdf_bytes, used_engine = _render_pdf_bytes(html)
    except Exception as exc:
        logger.exception("PDF generation failed for template '%s': %s", template_path, exc)
        return HttpResponse(
            "Error generating PDF",
            status=500
        )
    render_ms = (perf_counter() - render_started) * 1000

    response = HttpResponse(
        pdf_bytes,
        content_type="application/pdf"
    )
    response["X-PDF-Engine"] = used_engine
    perf_logger.info(
        "pdf.response_timing template=%s engine=%s template_ms=%.2f render_ms=%.2f total_ms=%.2f bytes=%s",
        template_path,
        used_engine,
        template_ms,
        render_ms,
        (perf_counter() - started) * 1000,
        len(pdf_bytes),
    )
    return response


def save_pdf_to_disk(template_path: str, context: dict, filename: str) -> tuple[str, str]:
    """
    Render PDF and save to disk, returning (file_path, engine_name).
    """
    started = perf_counter()
    template_started = perf_counter()
    template = get_template(template_path)
    html = template.render(context)
    template_ms = (perf_counter() - template_started) * 1000
    render_started = perf_counter()
    pdf_bytes, used_engine = _render_pdf_bytes(html)
    render_ms = (perf_counter() - render_started) * 1000
        
    # Define save directory

    # Use MEDIA_ROOT if available, else formatted 'generated_pdfs' in base dir
    if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs')
    else:
        output_dir = os.path.join(settings.BASE_DIR, 'generated_pdfs')
        
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    write_started = perf_counter()
    with open(file_path, 'wb') as f:
        f.write(pdf_bytes)
    write_ms = (perf_counter() - write_started) * 1000
    perf_logger.info(
        "pdf.save_timing template=%s filename=%s engine=%s template_ms=%.2f render_ms=%.2f write_ms=%.2f total_ms=%.2f bytes=%s",
        template_path,
        filename,
        used_engine,
        template_ms,
        render_ms,
        write_ms,
        (perf_counter() - started) * 1000,
        len(pdf_bytes),
    )

    return file_path, used_engine
