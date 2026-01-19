from django.urls import path
from api.views.auth import RegisterAPI
from .views.auth import LoginAPI
from .views.faculty import FacultySubmitAPI
from .views.hod import HODReviewAPI
from .views.principal import PrincipalApproveAPI
from .views.scoring_api import ScoringAPI
from .views.workflow_api import WorkflowAPI
from api.views.auth import RegisterAPI, LoginAPI
#from .views.pdf_api import PDFGenerateAPI

urlpatterns = [
    path("auth/login/", LoginAPI.as_view()),

    path("faculty/submit/", FacultySubmitAPI.as_view()),

    path("hod/review/", HODReviewAPI.as_view()),

    path("principal/approve/", PrincipalApproveAPI.as_view()),

    path("score/calculate/", ScoringAPI.as_view()),

    path("workflow/transition/", WorkflowAPI.as_view()),

    #path("pdf/generate/", PDFGenerateAPI.as_view()),

    path('register/', RegisterAPI.as_view()),

    path('login/', LoginAPI.as_view()),
]
