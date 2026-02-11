from dbm import error
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.permissions import IsHOD
from core.models import Appraisal, ApprovalHistory, Department
from workflow.engine import perform_action
from workflow.states import States
from scoring.engine import calculate_full_score
from validation.master_validator import validate_full_form
from django.db import transaction
from api.serializers import AppraisalSerializer
from core.models import FacultyProfile, Appraisal, AppraisalScore, User
from core.utils.audit import log_action


class HODSubmitAPI(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    @transaction.atomic
    def post(self, request):
        user = request.user

        try:
            faculty = FacultyProfile.objects.select_related("department").get(user=user)
        except FacultyProfile.DoesNotExist:
            return Response({"error": "Faculty profile not found for HOD"}, status=400)

        meta = request.data
        payload = request.data.get("appraisal_data")

        if not payload:
            return Response({"error": "appraisal_data is required"}, status=400)

        # ✅ USE CENTRAL VALIDATOR
        ok, err = validate_full_form(payload, meta)
        if not ok:
            return Response({"error": err}, status=400)

        # 3️⃣ DUPLICATE CHECK / DRAFT UPDATE
        existing_appraisal = Appraisal.objects.filter(
            faculty=faculty,
            academic_year=meta["academic_year"],
            semester=meta["semester"],
            form_type=meta["form_type"],
            is_hod_appraisal=True
        ).first()

        if existing_appraisal:
            if existing_appraisal.status != States.DRAFT:
                return Response(
                    {"error": "HOD appraisal already exists and is submitted/finalized for this period"},
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
                is_hod_appraisal=True,
                principal=User.objects.filter(role="PRINCIPAL").first()
            )

        submit_action = payload.get("submit_action", "submit").lower()

        if submit_action == "submit":
            old_state = {"status": appraisal.status}
            score_result = calculate_full_score(payload)

            appraisal.status = perform_action(
                current_state=appraisal.status,
                next_state=States.SUBMITTED,
                appraisal=appraisal
            )
            appraisal.save()

            AppraisalScore.objects.create(
                appraisal=appraisal,
                teaching_score=score_result["teaching"]["score"],
                research_score=score_result["research"]["total"],
                activity_score=score_result["activities"]["score"],
                feedback_score=score_result["pbas"]["total"],
                total_score=score_result["total_score"]
            )

            log_action(
                request=request,
                action="SUBMIT_APPRAISAL",
                entity="Appraisal",
                entity_id=appraisal.appraisal_id,
                old_value=old_state,
                new_value={"status": appraisal.status}
            )

            return Response(
                {
                    "message": "HOD appraisal submitted successfully",
                    "appraisal_id": appraisal.appraisal_id,
                    "current_state": appraisal.status,
                    "total_score": score_result["total_score"]
                },
                status=201
            )
        else:
            return Response(
                {
                    "message": "Draft saved successfully",
                    "appraisal_id": appraisal.appraisal_id,
                    "current_state": appraisal.status
                },
                status=201
            )

    


class HODAppraisalListAPI(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    def get(self, request):
        faculty = FacultyProfile.objects.get(user=request.user)

        appraisals = Appraisal.objects.filter(
            faculty=faculty,
            is_hod_appraisal=True
        ).order_by("-updated_at")


        return Response(
            AppraisalSerializer(appraisals, many=True).data
        )


class HODResubmitAPI(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    @transaction.atomic
    def post(self, request, appraisal_id):
        faculty = FacultyProfile.objects.get(user=request.user)

        appraisal = Appraisal.objects.get(
            appraisal_id=appraisal_id,
            faculty=faculty,
            is_hod_appraisal=True
        )

        if appraisal.status not in [States.DRAFT, States.RETURNED_BY_PRINCIPAL]:
            return Response(
                {"error": "Only draft or returned appraisals can be resubmitted"},
                status=400
            )

        old_state = {
            "status": appraisal.status
        }

        # update data
        data = request.data["appraisal_data"]
        appraisal.appraisal_data = data

        submit_action = data.get("submit_action", "submit").lower()

        # Calculation for Score (if submitting)
        score_result = None
        if submit_action == "submit":
            score_result = calculate_full_score(data)

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
                    "faculty_id": appraisal.faculty.pk
                }
            )

        return Response({"message": "HOD appraisal resubmitted"})
    

# =========================
# START HOD REVIEW
# =========================
class HODStartReviewAppraisal(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    def post(self, request, appraisal_id):
        # 1️⃣ Fetch appraisal
        
        try:
            appraisal = Appraisal.objects.select_related(
                "faculty__department"
            ).get(appraisal_id=appraisal_id)
            
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        # 2️⃣ Fetch HOD department
        try:
            department = Department.objects.get(hod=request.user)
        except Department.DoesNotExist:
            return Response(
                {"error": "HOD is not assigned to any department"},
                status=400
            )

        
        # 3️⃣ Ownership check
        if appraisal.faculty.department != department:
            return Response(
                {"error": "You cannot review appraisals outside your department"},
                status=403
            )

        # 4️⃣ Workflow transition
        try:
            new_state = perform_action(
                current_state=appraisal.status,
                next_state=States.REVIEWED_BY_HOD
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

        # 5️⃣ Save
        appraisal.status = new_state
  
        appraisal.save()

        
        return Response({
            "message": "Appraisal moved to HOD review",
            "current_state": new_state
        })


# =========================
# LIST FOR HOD
# =========================
class HODAppraisalList(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    def get(self, request):
        try:
            department = Department.objects.get(hod=request.user)
            print(f"DEBUG: HOD {request.user.username} found for department {department.department_name}")
        except Department.DoesNotExist:
            print(f"DEBUG: HOD {request.user.username} NOT linked to any department")
            return Response(
                {"error": "HOD is not assigned to any department"},
                status=400
            )

        appraisals = Appraisal.objects.select_related(
            "faculty", "faculty__department"
        ).filter(
            faculty__department=department,
            is_hod_appraisal=False,
            status__in=[
                States.SUBMITTED, 
                States.REVIEWED_BY_HOD, 
                States.HOD_APPROVED,
                States.REVIEWED_BY_PRINCIPAL,
                States.PRINCIPAL_APPROVED,
                States.FINALIZED,
                States.RETURNED_BY_HOD,
                States.RETURNED_BY_PRINCIPAL,
            ]
        ).order_by("-updated_at")
        
        print(f"DEBUG: Found {appraisals.count()} faculty appraisals for department {department.department_name}")

        return Response([
            {
                "appraisal_id": a.appraisal_id,          # ✅ REQUIRED
                "academic_year": a.academic_year,
                "semester": a.semester,
                "status": a.status,

                # ✅ REQUIRED FOR UI
                "faculty_name": a.faculty.full_name,
                "designation": a.faculty.designation,
                "department": a.faculty.department.department_name,
            }
            for a in appraisals
        ])




# =========================
# HOD APPROVE
# =========================
class HODApproveAppraisal(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    def post(self, request, appraisal_id):
        try:
            appraisal = Appraisal.objects.select_related(
                "faculty__department"
            ).get(appraisal_id=appraisal_id)


        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        # 🔒 Department check
        try:
            department = Department.objects.get(hod=request.user)
        except Department.DoesNotExist:
            return Response(
                {"error": "HOD is not assigned to any department"},
                status=400
            )

        if appraisal.faculty.department != department:
            return Response(
                {"error": "You cannot act on appraisals outside your department"},
                status=403
            )

        # ❌ Invalid state
        if appraisal.status != States.REVIEWED_BY_HOD:
            return Response(
                {"error": "Appraisal not in HOD review state"},
                status=400
            )

        # ✅ Approve
        new_state = perform_action(
            current_state=appraisal.status,
            next_state=States.HOD_APPROVED
        )

        appraisal.status = new_state
        appraisal.save()

        ApprovalHistory.objects.update_or_create(
            appraisal=appraisal,
            role="HOD",
            defaults={
                "approved_by": request.user,
                "action": "APPROVED",
                "from_state": States.REVIEWED_BY_HOD,
                "to_state": new_state,
                "remarks": None
            }
        )

        return Response({
            "message": "Approved by HOD",
            "new_state": new_state
        })


# =========================
# HOD RETURN
# =========================
class HODReturnAppraisal(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    def post(self, request, appraisal_id):
        remarks = request.data.get("remarks", "")

        try:
            appraisal = Appraisal.objects.select_related(
                "faculty__department"
            ).get(appraisal_id=appraisal_id)

        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        try:
            department = Department.objects.get(hod=request.user)
        except Department.DoesNotExist:
            return Response(
                {"error": "HOD is not assigned to any department"},
                status=400
            )

        if appraisal.faculty.department != department:
            return Response(
                {"error": "You cannot act on appraisals outside your department"},
                status=403
            )

        if appraisal.status not in [States.SUBMITTED, States.REVIEWED_BY_HOD]:
            return Response(
                {"error": "Appraisal not in a state that can be returned by HOD"},
                status=400
            )


        
        new_state = perform_action(
            current_state=appraisal.status,
            next_state=States.RETURNED_BY_HOD
        )


        appraisal.status = new_state

        appraisal.remarks = remarks
        appraisal.save()

        ApprovalHistory.objects.update_or_create(
            appraisal=appraisal,
            role="HOD",
            defaults={
                "approved_by": request.user,
                "action": "SENT_BACK",
                "from_state": appraisal.status, # Use dynamic state
                "to_state": new_state,
                "remarks": remarks
            }
        )

        return Response({
            "message": "Returned to faculty",
            "new_state": new_state
        })


