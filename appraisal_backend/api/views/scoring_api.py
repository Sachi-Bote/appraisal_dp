from rest_framework.views import APIView
from rest_framework.response import Response

from scoring.engine import calculate_full_score


class ScoringAPI(APIView):
    def post(self, request):
        score = calculate_full_score(request.data)
        return Response(score)


