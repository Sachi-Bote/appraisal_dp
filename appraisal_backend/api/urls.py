from django.urls import path
from api.views.auth import RegisterAPI, LoginAPI, LogoutView
from api.views.test import WhoAmI
from api.views.faculty import FacultyAppraisalListAPI, FacultySubmitAPI, FacultyResubmitAPI
from api.views.principal import PrincipalApproveAPI, PrincipalReturnAPI
from api.views.scoring_api import ScoringAPI
from api.views.workflow_api import WorkflowAPI
from api.views.hod import (
    HODAppraisalList,
    HODApproveAppraisal,
    HODReturnAppraisal,
    HODStartReviewAppraisal,
    HODSubmitAPI,
    HODResubmitAPI,
    HODAppraisalListAPI   # 👈 ADD THIS
)
from api.views.principal import(
    PrincipalApproveAPI,
    PrincipalAppraisalList,
    PrincipalStartReviewAPI,
    PrincipalReturnAPI,
    PrincipalFinalizeAPI,
)
from api.views.me import MeView 


urlpatterns = [
    # AUTH
    path("auth/login/", LoginAPI.as_view()),
    path("register/", RegisterAPI.as_view()),
    path("login/", LoginAPI.as_view()),
    path("whoami/", WhoAmI.as_view()),
    path("logout/", LogoutView.as_view()),

    #API ME
    path("me/", MeView.as_view()),

    # FACULTY
    path("faculty/submit/", FacultySubmitAPI.as_view()),
    path("faculty/appraisals/", FacultyAppraisalListAPI.as_view()),
    path("faculty/appraisal/<int:appraisal_id>/resubmit/", FacultyResubmitAPI.as_view()),


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
    path("hod/submit/", HODSubmitAPI.as_view()),
    path("hod/appraisals/", HODAppraisalListAPI.as_view()),
    path("hod/resubmit/<int:appraisal_id>/", HODResubmitAPI.as_view()),


    # PRINCIPAL   
    path("principal/appraisal/<int:appraisal_id>/approve/",PrincipalApproveAPI.as_view()),
    path("principal/appraisals/", PrincipalAppraisalList.as_view()),
    path("principal/appraisal/<int:appraisal_id>/start-review/",PrincipalStartReviewAPI.as_view()),
    path("principal/appraisal/<int:appraisal_id>/return/", PrincipalReturnAPI.as_view()),
    path("principal/appraisal/<int:appraisal_id>/finalize/", PrincipalFinalizeAPI.as_view()),
    # OTHER
    path("score/calculate/", ScoringAPI.as_view()),
    path("workflow/transition/", WorkflowAPI.as_view()),
]
