"""
Request processing endpoints - creation and deletion
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import shutil
import time
from datetime import datetime

from .dependencies import get_request_storage, get_extractor, get_pdf_processor

router = APIRouter()


@router.post("/process-request", summary="UUID 기반 문서 처리 요청 생성")
async def process_request(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    merge_blocks: Optional[bool] = Form(True),
    merge_threshold: Optional[int] = Form(30),
    create_sections: Optional[bool] = Form(False),
    build_hierarchy_tree: Optional[bool] = Form(False),
    request_storage = Depends(get_request_storage),
    extractor = Depends(get_extractor),
    pdf_processor = Depends(get_pdf_processor)
) -> Dict[str, Any]:
    """
    UUID v7 기반 문서 처리 요청 생성

    - 파일 업로드 및 시간 기반 UUID v7 생성
    - 이미지/PDF 파일의 OCR 처리
    - 계층적 디렉토리 구조로 결과 저장
    - 블록별 개별 접근 가능한 구조 생성
    """
    start_time = time.time()

    try:
        # 파일 정보 수집
        file_content = await file.read()
        file_size = len(file_content)
        file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'

        # 지원되는 파일 타입 확인
        supported_image_types = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp']
        supported_doc_types = ['pdf']

        if file_type not in supported_image_types + supported_doc_types:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 파일 타입: {file_type}")

        # 요청 생성
        request_id = request_storage.create_request(
            original_filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            total_pages=1  # PDF의 경우 실제 처리에서 업데이트
        )

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name

        try:
            if file_type in supported_image_types:
                # 이미지 처리
                await process_image_request(request_id, tmp_path, file.filename,
                                          merge_blocks, merge_threshold, start_time,
                                          request_storage, extractor,
                                          create_sections, build_hierarchy_tree)
                total_pages = 1

            elif file_type == 'pdf':
                # PDF 처리
                total_pages = await process_pdf_request(request_id, tmp_path, file.filename,
                                                      merge_blocks, merge_threshold, start_time,
                                                      request_storage, extractor, pdf_processor,
                                                      create_sections, build_hierarchy_tree)

            # 메타데이터 업데이트
            metadata = request_storage.get_request_metadata(request_id)
            metadata['total_pages'] = total_pages
            metadata_file = Path(request_storage.base_output_dir) / request_id / 'metadata.json'
            from services.file.metadata import save_metadata
            save_metadata(metadata, metadata_file)

            # 요청 완료 처리
            processing_time = time.time() - start_time
            request_storage.complete_request(request_id, {
                'completed_at': datetime.now().isoformat(),
                'description': description,
                'status': 'completed',
                'total_processing_time': round(processing_time, 3),
                'total_pages': total_pages
            })

            return {
                "request_id": request_id,
                "status": "completed",
                "original_filename": file.filename,
                "file_type": file_type,
                "file_size": file_size,
                "total_pages": total_pages,
                "processing_time": round(processing_time, 3),
                "processing_url": f"/requests/{request_id}"
            }

        finally:
            # 임시 파일 정리
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")


async def process_image_request(request_id: str, image_path: str, original_filename: str,
                               merge_blocks: bool, merge_threshold: int, start_time: float,
                               request_storage, extractor,
                               create_sections: bool = False, build_hierarchy_tree: bool = False) -> None:
    """이미지 요청 처리"""
    try:
        # OCR 처리 (단순 블록 추출 - 레이아웃 분석은 텍스트를 누락시킴)
        # 병합 비활성화 - 모든 텍스트 블록을 개별적으로 유지
        result = extractor.extract_blocks(
            image_path,
            confidence_threshold=0.5,
            merge_blocks=False,  # 병합 비활성화
            merge_threshold=merge_threshold,
            enable_table_recognition=False,
            create_sections=create_sections,
            build_hierarchy_tree=build_hierarchy_tree
        )
        blocks = result.get('blocks', [])

        # 레이아웃 정보 추가 (표, 차트 등)
        layout_info = result.get('layout_info', {})

        # 블록 데이터 변환 (계층 정보 포함)
        processed_blocks = []
        for i, block in enumerate(blocks):
            processed_blocks.append({
                'text': block['text'],
                'confidence': block['confidence'],
                'bbox': block['bbox_points'],
                'block_type': block['type'],
                'block_id': block.get('block_id'),
                'parent_id': block.get('parent_id'),
                'children': block.get('children', []),
                'level': block.get('level', 0)
            })

        # 시각화 이미지 생성
        visualization_data = None
        if blocks:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as viz_tmp:
                viz_path = viz_tmp.name

            try:
                # 시각화 생성
                extractor.visualize_blocks(image_path, result, viz_path)

                # 시각화 파일 읽기
                if Path(viz_path).exists():
                    with open(viz_path, 'rb') as f:
                        visualization_data = f.read()

            except Exception as e:
                print(f"시각화 생성 실패: {e}")
                visualization_data = None
            finally:
                # 임시 시각화 파일 정리
                if Path(viz_path).exists():
                    Path(viz_path).unlink()

        # 원본 이미지 데이터 읽기
        original_image_data = None
        try:
            with open(image_path, 'rb') as f:
                original_image_data = f.read()
        except Exception:
            original_image_data = None

        # 처리 시간 계산
        processing_time = time.time() - start_time

        # 콘텐츠 요약 생성
        from services.analysis import ContentSummarizer
        summarizer = ContentSummarizer()
        content_summary = summarizer.create_comprehensive_summary(processed_blocks)

        # 메타데이터 준비 (섹션/계층 정보 포함)
        ocr_metadata = {}
        if create_sections and 'sections' in result:
            ocr_metadata['sections'] = result['sections']
            ocr_metadata['section_summary'] = result.get('section_summary', {})

        if build_hierarchy_tree and 'hierarchical_blocks' in result:
            ocr_metadata['hierarchical_blocks'] = result['hierarchical_blocks']
            ocr_metadata['hierarchy_statistics'] = result.get('hierarchy_statistics', {})

        # 결과 저장 (메타데이터 포함)
        request_storage.save_page_result(
            request_id=request_id,
            page_number=1,
            blocks=processed_blocks,
            processing_time=processing_time,
            visualization_data=visualization_data,
            original_image_data=original_image_data,
            content_summary=content_summary,
            metadata=ocr_metadata if ocr_metadata else result.get('metadata', {})
        )

        # 섹션 시각화 및 저장 (create_sections가 활성화된 경우)
        if create_sections and 'sections' in result and result['sections']:
            from services.visualization.sections import create_section_visualization_with_crops
            from PIL import Image
            import io

            try:
                # 원본 이미지 로드
                original_image = Image.open(image_path)

                # 섹션 시각화 및 크롭 생성
                with tempfile.TemporaryDirectory() as temp_sections_dir:
                    sections_vis_image, cropped_paths = create_section_visualization_with_crops(
                        original_image,
                        result['sections'],
                        temp_sections_dir,
                        line_thickness=3,
                        padding=5
                    )

                    # 섹션 시각화 이미지를 bytes로 변환
                    sections_vis_buffer = io.BytesIO()
                    sections_vis_image.save(sections_vis_buffer, format='PNG')
                    sections_visualization_data = sections_vis_buffer.getvalue()

                    # 섹션 데이터 및 시각화 저장
                    request_storage.save_sections(
                        request_id=request_id,
                        page_number=1,
                        sections=result['sections'],
                        sections_visualization_data=sections_visualization_data
                    )

                    # 섹션 크롭 이미지들을 sections/ 폴더로 복사
                    if cropped_paths:
                        request_storage.save_section_images(
                            request_id=request_id,
                            page_number=1,
                            section_image_paths=cropped_paths
                        )

            except Exception as e:
                print(f"섹션 시각화 생성 실패: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        raise Exception(f"이미지 처리 중 오류: {str(e)}")


async def process_pdf_request(request_id: str, pdf_path: str, original_filename: str,
                             merge_blocks: bool, merge_threshold: int, start_time: float,
                             request_storage, extractor, pdf_processor,
                             create_sections: bool = False, build_hierarchy_tree: bool = False) -> int:
    """PDF 요청 처리"""
    try:
        # PDF를 이미지로 변환
        image_paths = pdf_processor.convert_pdf_to_images(pdf_path, '/tmp')
        total_pages = len(image_paths)

        for page_num, image_path in enumerate(image_paths, 1):
            page_start_time = time.time()

            # 각 페이지 OCR 처리 (단순 블록 추출 - 레이아웃 분석은 텍스트를 누락시킴)
            # 병합 비활성화 - 모든 텍스트 블록을 개별적으로 유지
            result = extractor.extract_blocks(
                image_path,
                confidence_threshold=0.5,
                merge_blocks=False,  # 병합 비활성화
                merge_threshold=merge_threshold,
                enable_table_recognition=False,
                create_sections=create_sections,
                build_hierarchy_tree=build_hierarchy_tree
            )
            blocks = result.get('blocks', [])

            # 레이아웃 정보 추가 (표, 차트 등)
            layout_info = result.get('layout_info', {})

            # 블록 데이터 변환 (계층 정보 포함)
            processed_blocks = []
            for i, block in enumerate(blocks):
                processed_blocks.append({
                    'text': block['text'],
                    'confidence': block['confidence'],
                    'bbox': block['bbox_points'],
                    'block_type': block['type'],
                    'block_id': block.get('block_id'),
                    'parent_id': block.get('parent_id'),
                    'children': block.get('children', []),
                    'level': block.get('level', 0)
                })

            # 시각화 이미지 생성
            visualization_data = None
            if blocks:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as viz_tmp:
                    viz_path = viz_tmp.name

                try:
                    # 시각화 생성
                    extractor.visualize_blocks(image_path, result, viz_path)

                    # 시각화 파일 읽기
                    if Path(viz_path).exists():
                        with open(viz_path, 'rb') as f:
                            visualization_data = f.read()

                except Exception as e:
                    print(f"페이지 {page_num} 시각화 생성 실패: {e}")
                    visualization_data = None
                finally:
                    # 임시 시각화 파일 정리
                    if Path(viz_path).exists():
                        Path(viz_path).unlink()

            # 원본 페이지 이미지 데이터 읽기
            original_image_data = None
            try:
                with open(image_path, 'rb') as f:
                    original_image_data = f.read()
            except Exception:
                original_image_data = None

            # 페이지 처리 시간 계산
            page_processing_time = time.time() - page_start_time

            # 콘텐츠 요약 생성
            from services.analysis import ContentSummarizer
            summarizer = ContentSummarizer()
            content_summary = summarizer.create_comprehensive_summary(processed_blocks)

            # 메타데이터 준비 (섹션/계층 정보 포함)
            ocr_metadata = {}
            if create_sections and 'sections' in result:
                ocr_metadata['sections'] = result['sections']
                ocr_metadata['section_summary'] = result.get('section_summary', {})

            if build_hierarchy_tree and 'hierarchical_blocks' in result:
                ocr_metadata['hierarchical_blocks'] = result['hierarchical_blocks']
                ocr_metadata['hierarchy_statistics'] = result.get('hierarchy_statistics', {})

            # 페이지 결과 저장 (메타데이터 포함)
            request_storage.save_page_result(
                request_id=request_id,
                page_number=page_num,
                blocks=processed_blocks,
                processing_time=page_processing_time,
                visualization_data=visualization_data,
                original_image_data=original_image_data,
                content_summary=content_summary,
                metadata=ocr_metadata if ocr_metadata else result.get('metadata', {})
            )

            # 섹션 시각화 및 저장 (create_sections가 활성화된 경우)
            if create_sections and 'sections' in result and result['sections']:
                from services.visualization.sections import create_section_visualization_with_crops
                from PIL import Image
                import io

                try:
                    # 원본 이미지 로드
                    original_image = Image.open(image_path)

                    # 섹션 시각화 및 크롭 생성
                    with tempfile.TemporaryDirectory() as temp_sections_dir:
                        sections_vis_image, cropped_paths = create_section_visualization_with_crops(
                            original_image,
                            result['sections'],
                            temp_sections_dir,
                            line_thickness=3,
                            padding=5
                        )

                        # 섹션 시각화 이미지를 bytes로 변환
                        sections_vis_buffer = io.BytesIO()
                        sections_vis_image.save(sections_vis_buffer, format='PNG')
                        sections_visualization_data = sections_vis_buffer.getvalue()

                        # 섹션 데이터 및 시각화 저장
                        request_storage.save_sections(
                            request_id=request_id,
                            page_number=page_num,
                            sections=result['sections'],
                            sections_visualization_data=sections_visualization_data
                        )

                        # 섹션 크롭 이미지들을 sections/ 폴더로 복사
                        if cropped_paths:
                            request_storage.save_section_images(
                                request_id=request_id,
                                page_number=page_num,
                                section_image_paths=cropped_paths
                            )

                except Exception as e:
                    print(f"페이지 {page_num} 섹션 시각화 생성 실패: {e}")
                    import traceback
                    traceback.print_exc()

            # 임시 이미지 파일 정리
            if Path(image_path).exists():
                Path(image_path).unlink()

        return total_pages

    except Exception as e:
        raise Exception(f"PDF 처리 중 오류: {str(e)}")


@router.delete("/requests/{request_id}", summary="UUID 요청 및 관련 데이터 완전 삭제")
async def delete_request(
    request_id: str,
    request_storage = Depends(get_request_storage)
) -> Dict[str, Any]:
    """
    UUID 요청 및 관련 데이터 완전 삭제

    - 요청 메타데이터 삭제
    - 모든 페이지 데이터 삭제
    - 원본/시각화 이미지 삭제
    - 블록별 데이터 삭제
    """
    from services.file.request_manager import validate_request_id

    try:
        # UUID 형식 검증
        if not validate_request_id(request_id):
            raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID 형식")

        # 요청 존재 확인
        if not request_storage.request_exists(request_id):
            raise HTTPException(status_code=404, detail="요청을 찾을 수 없습니다")

        # 요청 삭제
        deleted_files = request_storage.delete_request(request_id)

        return {
            "success": True,
            "message": f"요청 {request_id}이(가) 성공적으로 삭제되었습니다",
            "deleted_files_count": deleted_files,
            "request_id": request_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 중 오류 발생: {str(e)}")