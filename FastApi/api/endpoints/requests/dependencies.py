"""
Shared dependencies for requests API endpoints
"""

from services.file.storage import RequestStorage

# 전역 저장소 인스턴스
request_storage = None
extractor = None
pdf_processor = None


def set_dependencies(output_dir: str):
    """의존성 설정"""
    global request_storage
    request_storage = RequestStorage(output_dir)


def set_processing_dependencies(doc_extractor, pdf_proc):
    """처리 관련 의존성 설정"""
    global extractor, pdf_processor
    extractor = doc_extractor
    pdf_processor = pdf_proc


def get_request_storage() -> RequestStorage:
    """RequestStorage 인스턴스 반환"""
    if request_storage is None:
        raise RuntimeError("RequestStorage가 초기화되지 않았습니다")
    return request_storage


def get_extractor():
    """Document extractor 반환"""
    if extractor is None:
        raise RuntimeError("Document extractor가 초기화되지 않았습니다")
    return extractor


def get_pdf_processor():
    """PDF processor 반환"""
    if pdf_processor is None:
        raise RuntimeError("PDF processor가 초기화되지 않았습니다")
    return pdf_processor