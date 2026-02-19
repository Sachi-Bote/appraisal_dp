from api.serializers import AppraisalSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from validation.master_validator import validate_full_form
from scoring.engine import calculate_full_score
from workflow.engine import perform_action
from api.permissions import IsFaculty
from workflow.states import States
from core.models import FacultyProfile, Appraisal, AppraisalScore

from core.utils.audit import log_action
from scoring.activity_selection import normalize_activity_payload

class FacultySubmitAPI(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    @transaction.atomic
    

    def post(self, request):
        user = request.user
        # 1️⃣ Faculty profile
        try:
            faculty = FacultyProfile.objects.select_related("department").get(user=user)
        except FacultyProfile.DoesNotExist:
            return Response({"error": "Faculty profile not found"}, status=400)

        if not faculty.department:
            return Response(
                {"error": "Faculty is not mapped to any department"},
                status=400
            )

        if not faculty.department.hod:
            return Response(
                {"error": f"No HOD assigned to department '{faculty.department.department_name}'. Please ensure your HOD is registered and assigned."},
                status=400
            )


        meta = request.data
        payload = request.data.get("appraisal_data")

        if not payload:
            return Response(
                {"error": "appraisal_data is required"},
                status=400
            )

        payload["activities"] = normalize_activity_payload(payload.get("activities", {}))

       
        
        # checking if the appraisal is already finalized

        submit_action = payload.get("submit_action", "submit").lower()

        # Full validation is required only for final submit.
        # Draft saves should allow partially filled forms.
        if submit_action == "submit":
            ok, err = validate_full_form(payload, meta)
            if not ok:
                return Response({"error": err}, status=400)


        # 3️⃣ DUPLICATE CHECK / DRAFT UPDATE
        existing_appraisal = Appraisal.objects.filter(
            faculty=faculty,
            academic_year=meta["academic_year"],
            semester=meta["semester"],
            form_type=meta["form_type"]
        ).first()

        if existing_appraisal:
            if existing_appraisal.status != States.DRAFT:
                return Response(
                    {"error": "Appraisal already exists and is submitted/finalized for this period"},
                    status=400
                )
            # Update existing draft
            appraisal = existing_appraisal
            appraisal.appraisal_data = payload
            appraisal.save()
        else:
            # 5️⃣ CREATE APPRAISAL (INITIAL STATE = DRAFT)
            appraisal = Appraisal.objects.create(
                faculty=faculty,
                form_type=meta["form_type"],
                academic_year=meta["academic_year"],
                semester=meta["semester"],
                appraisal_data=payload,
                status=States.DRAFT,
                is_hod_appraisal=False
            )

        if submit_action == "submit":
            # 4️⃣ SCORING (Only for submission)
            scoring_payload = {
                "teaching": payload.get("teaching", {}),
                "activities": payload.get("activities", {}),
                "research": payload.get("research", {}),
                "pbas": payload.get("pbas", {}),
                "acr": {
                    "grade": payload["acr"]["grade"]
                }
            }

            required_sections = ["teaching", "activities", "research", "pbas"]
            acr_data = scoring_payload.get("acr")

            if not acr_data or "grade" not in acr_data:
                return Response({"error": "ACR grade is required"}, status=400)
            
            missing = [s for s in required_sections if s not in scoring_payload]
            if missing:
                return Response({"error": f"Missing appraisal sections: {missing}"}, status=400)

            is_pbas = meta.get("form_type") == "PBAS"
            if is_pbas and "courses" not in scoring_payload["teaching"]:
                return Response({"error": "Teaching courses data is missing"}, status=400)

            score_result = calculate_full_score(scoring_payload)

        if submit_action == "submit":
            # 6️⃣ WORKFLOW: FACULTY SUBMIT
            new_state = perform_action(
                current_state=appraisal.status,
                next_state=States.SUBMITTED
            )
            old_state = {
                "status": appraisal.status
            }
            appraisal.status = new_state

            # 7️⃣ ASSIGN HOD
            appraisal.hod = faculty.department.hod
            appraisal.save()

            # 8️⃣ CREATE SCORE
            AppraisalScore.objects.create(
                appraisal=appraisal,
                teaching_score=score_result["teaching"]["score"],
                research_score=score_result["research"]["total"],
                activity_score=score_result["activities"]["score"],
                feedback_score=score_result["pbas"]["total"],
                total_score=score_result["total_score"],
                acr_score = score_result["acr"]["credit_point"]
            )

            log_action(
                    request=request,
                    action="SUBMIT_APPRAISAL",
                    entity="Appraisal",
                    entity_id=appraisal.appraisal_id,
                    old_value=old_state,
                    new_value={
                        "status": appraisal.status,
                        "faculty_id": faculty.pk
                    }
                )

            return Response(
                {
                    "message": "Appraisal submitted successfully",
                    "appraisal_id": appraisal.appraisal_id,
                    "current_state": appraisal.status,
                    "total_score": score_result["total_score"]
                },
                status=201
            )
        else:
            # DRAFT SAVED
            return Response(
                {
                    "message": "Draft saved successfully",
                    "appraisal_id": appraisal.appraisal_id,
                    "current_state": appraisal.status
                },
                status=201
            )
class FacultyAppraisalListAPI(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def get(self, request):
        faculty = FacultyProfile.objects.get(user=request.user)

        appraisals = Appraisal.objects.filter(
            faculty=faculty
        ).order_by("-updated_at")

        serializer = AppraisalSerializer(appraisals, many=True)

        return Response(serializer.data)
class FacultyResubmitAPI(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    @transaction.atomic
    def post(self, request, appraisal_id):
        faculty = FacultyProfile.objects.get(user=request.user)

        appraisal = Appraisal.objects.get(
            appraisal_id=appraisal_id,
            faculty=faculty
        )

        if appraisal.status not in [States.DRAFT, States.RETURNED_BY_HOD, States.RETURNED_BY_PRINCIPAL]:
            return Response(
                {"error": "Only draft or returned appraisals can be resubmitted"},
                status=400
            )

        # update data
        data = request.data["appraisal_data"]
        data["activities"] = normalize_activity_payload(data.get("activities", {}))
        appraisal.appraisal_data = data

        submit_action = data.get("submit_action", "submit").lower()

        # Calculation for Score (if submitting)
        score_result = None
        if submit_action == "submit":
            ok, err = validate_full_form(data, request.data)
            if not ok:
                return Response({"error": err}, status=400)
            score_result = calculate_full_score(data)

        old_state = {
            "status": appraisal.status
        }
        
        # workflow
        if submit_action == "submit":
            appraisal.status = perform_action(
                current_state=appraisal.status,
                next_state=States.SUBMITTED
            )

        appraisal.save()

        # CREATE/UPDATE SCORE
        if score_result:
            AppraisalScore.objects.update_or_create(
                appraisal=appraisal,
                defaults={
                    "teaching_score": score_result["teaching"]["score"],
                    "research_score": score_result["research"]["total"],
                    "activity_score": score_result["activities"]["score"],
                    "feedback_score": score_result["pbas"]["total"],
                    "total_score": score_result["total_score"],
                    "acr_score": score_result["acr"]["credit_point"]
                }
            )

        log_action(
                request=request,
                action="SUBMIT_APPRAISAL",
                entity="Appraisal",
                entity_id=appraisal.appraisal_id,
                old_value=old_state,
                new_value={
                    "status": appraisal.status,
                    "faculty_id": faculty.pk
                }
            )
        return Response({"message": "Appraisal resubmitted"})
