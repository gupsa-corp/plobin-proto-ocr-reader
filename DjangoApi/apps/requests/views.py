"""
Requests 앱의 API 뷰
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.ocr.models import ProcessingRequest
from apps.ocr.serializers import ProcessingRequestSerializer


class RequestListView(APIView):
    """요청 목록 조회"""

    def get(self, request):
        """모든 요청 목록 조회"""
        requests = ProcessingRequest.objects.all()
        serializer = ProcessingRequestSerializer(requests, many=True)
        return Response(serializer.data)


class RequestDetailView(APIView):
    """요청 상세 조회"""

    def get(self, request, request_id):
        """특정 요청 상세 조회"""
        try:
            req = ProcessingRequest.objects.get(id=request_id)
            serializer = ProcessingRequestSerializer(req)
            return Response(serializer.data)
        except ProcessingRequest.DoesNotExist:
            return Response(
                {"error": "Request not found"},
                status=status.HTTP_404_NOT_FOUND
            )
