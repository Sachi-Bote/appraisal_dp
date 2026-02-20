from django.shortcuts import get_object_or_404
from core.models import Appraisal, GeneratedPDF
from core.services.pdf.sppu_mapper import get_sppu_pdf_data
from core.services.pdf.pbas_mapper import get_pbas_pdf_data
from core.services.pdf.enhanced_sppu_mapper import get_enhanced_sppu_pdf_data
from core.services.pdf.enhanced_pbas_mapper import get_enhanced_pbas_pdf_data
from core.services.pdf.pdf_renderer import render_to_pdf, save_pdf_to_disk
import os
from django.http import FileResponse
import logging
from time import perf_counter

logger = logging.getLogger(__name__)
perf_logger = logging.getLogger("api.performance")


def _cached_pdf_response(appraisal, filename):
    """
    Return cached PDF when it exists and is newer than appraisal changes.
    """
    started = perf_counter()
    cached_pdf = (
        GeneratedPDF.objects
        .filter(appraisal=appraisal, pdf_path__iendswith=filename)
        .order_by("-generated_at")
        .first()
    )
    if not cached_pdf:
        perf_logger.info(
            "pdf.cache_check appraisal_id=%s filename=%s hit=false reason=not_found duration_ms=%.2f",
            getattr(appraisal, "appraisal_id", None),
            filename,
            (perf_counter() - started) * 1000,
        )
        return None

    if cached_pdf.generated_at and appraisal.updated_at and cached_pdf.generated_at < appraisal.updated_at:
        perf_logger.info(
            "pdf.cache_check appraisal_id=%s filename=%s hit=false reason=stale duration_ms=%.2f",
            getattr(appraisal, "appraisal_id", None),
            filename,
            (perf_counter() - started) * 1000,
        )
        return None

    if not os.path.exists(cached_pdf.pdf_path):
        perf_logger.info(
            "pdf.cache_check appraisal_id=%s filename=%s hit=false reason=missing_file duration_ms=%.2f",
            getattr(appraisal, "appraisal_id", None),
            filename,
            (perf_counter() - started) * 1000,
        )
        return None

    response = FileResponse(open(cached_pdf.pdf_path, "rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-PDF-Cache"] = "HIT"
    perf_logger.info(
        "pdf.cache_check appraisal_id=%s filename=%s hit=true duration_ms=%.2f",
        getattr(appraisal, "appraisal_id", None),
        filename,
        (perf_counter() - started) * 1000,
    )
    return response


def _save_pdf_and_return_response(appraisal, template_path, context, filename):
    """
    Save rendered PDF to disk + GeneratedPDF table, then return file response.
    Falls back to direct render when save fails.
    """
    started = perf_counter()
    try:
        render_started = perf_counter()
        file_path, used_engine = save_pdf_to_disk(template_path, context, filename)
        render_ms = (perf_counter() - render_started) * 1000

        db_started = perf_counter()
        GeneratedPDF.objects.create(
            appraisal=appraisal,
            pdf_path=file_path
        )
        db_ms = (perf_counter() - db_started) * 1000

        response = FileResponse(open(file_path, "rb"), content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['X-PDF-Engine'] = used_engine
        response["X-PDF-Cache"] = "MISS"
        perf_logger.info(
            "pdf.generate_timing appraisal_id=%s filename=%s engine=%s render_save_ms=%.2f db_record_ms=%.2f total_ms=%.2f",
            getattr(appraisal, "appraisal_id", None),
            filename,
            used_engine,
            render_ms,
            db_ms,
            (perf_counter() - started) * 1000,
        )
        return response
    except Exception:
        logger.exception(
            "Failed to save generated PDF '%s' for appraisal %s; falling back to direct response render.",
            filename,
            getattr(appraisal, "appraisal_id", "unknown"),
        )
        return render_to_pdf(template_path, context)


def generate_sppu_pdf(request, appraisal_id):
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    context = get_sppu_pdf_data(appraisal)
    return render_to_pdf("pdf/sppu.html", context)


def generate_pbas_pdf(request, appraisal_id):
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    context = get_pbas_pdf_data(appraisal)
    return render_to_pdf("pdf/pbas.html", context)


def generate_enhanced_sppu_pdf(request, appraisal_id):
    """Generate enhanced SPPU PDF, SAVE to DB, and return"""
    started = perf_counter()
    appraisal = get_object_or_404(Appraisal, appraisal_id=appraisal_id)
    filename = f"SPPU_Enhanced_appraisal_{appraisal_id}.pdf"
    cached = _cached_pdf_response(appraisal, filename)
    if cached:
        perf_logger.info(
            "pdf.endpoint_timing endpoint=sppu appraisal_id=%s total_ms=%.2f cache=hit",
            appraisal_id,
            (perf_counter() - started) * 1000,
        )
        return cached
    context_started = perf_counter()
    context = get_enhanced_sppu_pdf_data(appraisal)
    context_ms = (perf_counter() - context_started) * 1000
    perf_logger.info(
        "pdf.endpoint_timing endpoint=sppu appraisal_id=%s context_ms=%.2f cache=miss",
        appraisal_id,
        context_ms,
    )
    return _save_pdf_and_return_response(
        appraisal=appraisal,
        template_path="pdf/enhanced_sppu.html",
        context=context,
        filename=filename
    )


def generate_enhanced_pbas_pdf(request, appraisal_id):
    """Generate enhanced AICTE PBAS PDF, save to DB/disk, and return"""
    started = perf_counter()
    appraisal = get_object_or_404(Appraisal, appraisal_id=appraisal_id)
    filename = f"PBAS_Enhanced_appraisal_{appraisal_id}.pdf"
    cached = _cached_pdf_response(appraisal, filename)
    if cached:
        perf_logger.info(
            "pdf.endpoint_timing endpoint=pbas appraisal_id=%s total_ms=%.2f cache=hit",
            appraisal_id,
            (perf_counter() - started) * 1000,
        )
        return cached
    context_started = perf_counter()
    context = get_enhanced_pbas_pdf_data(appraisal)
    context_ms = (perf_counter() - context_started) * 1000
    perf_logger.info(
        "pdf.endpoint_timing endpoint=pbas appraisal_id=%s context_ms=%.2f cache=miss",
        appraisal_id,
        context_ms,
    )
    return _save_pdf_and_return_response(
        appraisal=appraisal,
        template_path="pdf/enhanced_pbas.html",
        context=context,
        filename=filename
    )
