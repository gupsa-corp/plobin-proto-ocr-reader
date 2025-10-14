"""
Analysis 앱의 URL 설정
"""
from django.urls import path
from .views import AnalysisHealthView

app_name = 'analysis'

urlpatterns = [
    path('analysis/health/', AnalysisHealthView.as_view(), name='health'),
]
