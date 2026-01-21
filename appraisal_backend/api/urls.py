from django.urls import path
from api.views.auth import RegisterAPI, LoginAPI
from api.views.test import WhoAmI
from api.views.faculty import FacultySubmitAPI
from api.views.principal import PrincipalApproveAPI
from api.views.scoring_api import ScoringAPI
from api.views.workflow_api import WorkflowAPI
from api.views.hod import (
    HODAppraisalList,
    HODApproveAppraisal,
    HODReturnAppraisal,
    HODStartReviewAppraisal,   # 👈 ADD THIS
)

urlpatterns = [
    # AUTH
    path("auth/login/", LoginAPI.as_view()),
    path("register/", RegisterAPI.as_view()),
    path("login/", LoginAPI.as_view()),
    path("whoami/", WhoAmI.as_view()),

    # FACULTY
    path("faculty/submit/", FacultySubmitAPI.as_view()),

    # HOD
    path("hod/appraisals/", HODAppraisalList.as_view()),
    path(
        "hod/appraisal/<int:appraisal_id>/start-review/",
        HODStartReviewAppraisal.as_view()
    ),
    path(
        "hod/appraisal/<int:appraisal_id>/approve/",
        HODApproveAppraisal.as_view()
    ),
    path(
        "hod/appraisal/<int:appraisal_id>/return/",
        HODReturnAppraisal.as_view()
    ),

    # PRINCIPAL
    path("principal/approve/", PrincipalApproveAPI.as_view()),

    # OTHER
    path("score/calculate/", ScoringAPI.as_view()),
    path("workflow/transition/", WorkflowAPI.as_view()),
]
