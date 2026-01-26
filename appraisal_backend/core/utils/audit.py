from core.models import AuditLog


def log_action(user, action, entity, entity_id):
    AuditLog.objects.create(
        user=user,
        action=action,
        entity=entity,
        entity_id=entity_id
    )