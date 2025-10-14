from django.apps import AppConfig


class OcrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ocr'
    verbose_name = 'OCR Processing'

    def ready(self):
        """앱 초기화 시 실행"""
        # OCR 엔진 초기화는 뷰에서 필요 시 수행
        pass
