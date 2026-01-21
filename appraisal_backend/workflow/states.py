
class States:
    DRAFT = "draft"
    SUBMITTED = "submitted"
    HOD_REVIEW = "hod_review"
    HOD_APPROVED = "hod_approved"
    PRINCIPAL_REVIEW = "principal_review"
    PRINCIPAL_APPROVED = "principal_approved"
    FINALIZED = "finalized"


VALID_TRANSITIONS = {
    States.DRAFT: [States.SUBMITTED],
    States.SUBMITTED: [States.HOD_REVIEW],
    States.HOD_REVIEW: [States.HOD_APPROVED, States.DRAFT],  # reject back to draft
    States.HOD_APPROVED: [States.PRINCIPAL_REVIEW],
    States.PRINCIPAL_REVIEW: [States.PRINCIPAL_APPROVED, States.DRAFT],
    States.PRINCIPAL_APPROVED: [States.FINALIZED]
}
