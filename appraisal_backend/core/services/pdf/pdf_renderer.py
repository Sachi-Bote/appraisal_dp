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

logger = logging.getLogger(__name__)


def _render_with_xhtml2pdf(html: str) -> bytes:
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if pdf.err:
        raise Exception("Error generating PDF with xhtml2pdf")
    return result.getvalue()


def _render_with_playwright(html: str) -> bytes:
    """
    Render PDF using Chromium (Playwright) for browser-accurate output.
    """
    from playwright.sync_api import sync_playwright

    configured_path = getattr(settings, "PLAYWRIGHT_BROWSER_PATH", "") or ""
    browser_paths = [configured_path] if configured_path else []
    browser_paths.extend([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ])

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
                    launch_errors.append(str(e))

        if browser is None:
            try:
                # Use Playwright managed browser when installed at build-time.
                browser = p.chromium.launch(headless=True, args=launch_args)
            except Exception as e:
                launch_errors.append(str(e))

        if browser is None:
            try:
                browser = p.chromium.launch(headless=True, channel="msedge", args=launch_args)
            except Exception as e:
                launch_errors.append(str(e))

        if browser is None:
            raise Exception("Playwright browser launch failed: " + " | ".join(launch_errors))

        try:
            page = browser.new_page()
            page.set_content(html, wait_until="load")
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
            )
            return pdf_bytes
        finally:
            browser.close()


def _render_with_edge_cli(html: str) -> bytes:
    """
    Render PDF using local Microsoft Edge headless CLI.
    This avoids requiring Playwright/Python package in runtime.
    """
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

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if proc.returncode != 0 or not os.path.exists(pdf_path):
            stderr = (proc.stderr or "").strip()
            stdout = (proc.stdout or "").strip()
            raise Exception(f"Edge CLI PDF generation failed. rc={proc.returncode} stderr={stderr} stdout={stdout}")

        with open(pdf_path, "rb") as f:
            return f.read()


def _render_pdf_bytes(html: str) -> tuple[bytes, str]:
    engine = getattr(settings, "PDF_RENDER_ENGINE", "auto").lower()
    allow_fallback = getattr(settings, "PDF_ALLOW_FALLBACK", True)

    if engine == "xhtml2pdf":
        return _render_with_xhtml2pdf(html), "xhtml2pdf"

    if engine == "edge":
        return _render_with_edge_cli(html), "edge-cli"

    if engine == "playwright":
        try:
            return _render_with_playwright(html), "playwright"
        except Exception as e:
            if allow_fallback:
                logger.warning("Playwright render failed; using xhtml2pdf fallback. error=%s", e)
                return _render_with_xhtml2pdf(html), "xhtml2pdf-fallback"
            raise Exception(f"Playwright rendering failed and fallback disabled: {e}")

    if engine in {"playwright", "auto"}:
        # Try Edge CLI first (no Python Playwright dependency)
        try:
            return _render_with_edge_cli(html), "edge-cli"
        except Exception:
            pass

        try:
            return _render_with_playwright(html), "playwright"
        except Exception as e:
            if allow_fallback:
                logger.warning("Playwright render failed in auto mode; using xhtml2pdf fallback. error=%s", e)
                return _render_with_xhtml2pdf(html), "xhtml2pdf-fallback"
            raise Exception(f"Playwright rendering failed and fallback disabled: {e}")

    # Unknown engine -> safe fallback
    return _render_with_xhtml2pdf(html), "xhtml2pdf-fallback"


def render_to_pdf(template_path: str, context: dict) -> HttpResponse:
    template = get_template(template_path)
    html = template.render(context)
    try:
        pdf_bytes, used_engine = _render_pdf_bytes(html)
    except Exception as exc:
        logger.exception("PDF generation failed for template '%s': %s", template_path, exc)
        return HttpResponse(
            "Error generating PDF",
            status=500
        )

    response = HttpResponse(
        pdf_bytes,
        content_type="application/pdf"
    )
    response["X-PDF-Engine"] = used_engine
    return response


def save_pdf_to_disk(template_path: str, context: dict, filename: str) -> tuple[str, str]:
    """
    Render PDF and save to disk, returning (file_path, engine_name).
    """
    template = get_template(template_path)
    html = template.render(context)
    pdf_bytes, used_engine = _render_pdf_bytes(html)
        
    # Define save directory

    # Use MEDIA_ROOT if available, else formatted 'generated_pdfs' in base dir
    if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs')
    else:
        output_dir = os.path.join(settings.BASE_DIR, 'generated_pdfs')
        
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    
    with open(file_path, 'wb') as f:
        f.write(pdf_bytes)

    return file_path, used_engine
