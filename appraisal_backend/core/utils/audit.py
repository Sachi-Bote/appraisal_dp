from django.db import transaction
from core.models import AuditLog


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(
    *,
    request,
    action,
    entity,
    entity_id,
    old_value=None,
    new_value=None,
):
    """
    MUST be called inside transaction.atomic()
    """

    user = request.user if request.user.is_authenticated else None

    AuditLog.objects.create(
        user_id_snapshot=user.id if user else None,
        username_snapshot=user.username if user else "SYSTEM",
        role_snapshot=getattr(user, "role", "UNKNOWN"),
        action=action,
        entity=entity,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT"),
    )