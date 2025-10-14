"""
OCR 앱의 URL 설정
"""
from django.urls import path
from .views import (
    ProcessImageView,
    ProcessPDFView,
    HealthCheckView,
    ServerStatusView,
)

app_name = 'ocr'

urlpatterns = [
    # 헬스 체크
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('status/', ServerStatusView.as_view(), name='server-status'),

    # OCR 처리
    path('process-image/', ProcessImageView.as_view(), name='process-image'),
    path('process-pdf/', ProcessPDFView.as_view(), name='process-pdf'),
]
