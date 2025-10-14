"""
Templates 앱의 API 뷰
"""
from rest_framework.views import APIView
from rest_framework.response import Response


class TemplateListView(APIView):
    """템플릿 목록 조회"""

    def get(self, request):
        # TODO: 템플릿 목록 조회 구현
        return Response({"templates": []})
