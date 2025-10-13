"""
Template visualization service using PaddleOCR.
"""

import os
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import logging
from .font_manager import get_korean_fonts, font_manager

logger = logging.getLogger(__name__)


class TemplateVisualizer:
    """PaddleOCR 기반 템플릿 시각화 서비스"""

    def __init__(self):
        self.default_colors = {
            'text': '#FF6B6B',      # 빨간색
            'number': '#4ECDC4',    # 청록색
            'currency': '#45B7D1',  # 파란색
            'date': '#96CEB4',      # 초록색
            'email': '#FFEAA7',     # 노란색
            'phone': '#DDA0DD',     # 보라색
            'table': '#FF8C42',     # 주황색
            'checkbox': '#A8E6CF'   # 연초록색
        }

        self.field_type_colors = {
            'text': (255, 107, 107),      # 빨간색
            'number': (78, 205, 196),     # 청록색
            'currency': (69, 183, 209),   # 파란색
            'date': (150, 206, 180),      # 초록색
            'email': (255, 234, 167),     # 노란색
            'phone': (221, 160, 221),     # 보라색
            'table': (255, 140, 66),      # 주황색
            'checkbox': (168, 230, 207)   # 연초록색
        }

    def create_template_preview(self,
                              template_data: Dict,
                              width: Optional[int] = None,
                              height: Optional[int] = None,
                              background_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
        """
        템플릿 미리보기 이미지 생성

        Args:
            template_data: 템플릿 정의 데이터
            width: 이미지 너비 (None이면 템플릿에서 가져옴)
            height: 이미지 높이 (None이면 템플릿에서 가져옴)
            background_color: 배경색 (R, G, B)

        Returns:
            PIL Image 객체
        """
        try:
            # 페이지 레이아웃에서 크기 정보 가져오기
            page_layout = template_data.get('page_layout', {})
            img_width = width or page_layout.get('width', 1024)
            img_height = height or page_layout.get('height', 1448)

            # 빈 이미지 생성
            image = Image.new('RGB', (img_width, img_height), background_color)
            draw = ImageDraw.Draw(image)

            # 한글 폰트 설정 (폰트 매니저 사용)
            font, title_font = get_korean_fonts(regular_size=12, title_size=16)

            # 템플릿 제목 그리기
            template_name = template_data.get('name', 'Template')
            title_bbox = draw.textbbox((0, 0), template_name, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (img_width - title_width) // 2
            draw.text((title_x, 10), template_name, fill=(0, 0, 0), font=title_font)

            # 필드들 그리기
            fields = template_data.get('fields', [])
            for field in fields:
                self._draw_field(draw, field, font)

            # 범례 추가
            self._draw_legend(draw, fields, font, img_width, img_height)

            logger.info(f"Template preview created: {img_width}x{img_height}")
            return image

        except Exception as e:
            logger.error(f"Error creating template preview: {str(e)}")
            # 에러 발생 시 기본 이미지 반환
            error_image = Image.new('RGB', (800, 600), (240, 240, 240))
            error_draw = ImageDraw.Draw(error_image)
            error_draw.text((10, 10), f"Error: {str(e)}", fill=(255, 0, 0))
            return error_image

    def _draw_field(self, draw: ImageDraw.Draw, field: Dict, font):
        """개별 필드 그리기"""
        bbox = field.get('bbox', {})
        field_type = field.get('type', 'text')
        field_name = field.get('name', field.get('field_id', ''))
        required = field.get('required', False)

        # 바운딩 박스 좌표
        x1 = bbox.get('x1', 0)
        y1 = bbox.get('y1', 0)
        x2 = bbox.get('x2', 100)
        y2 = bbox.get('y2', 50)

        # 색상 선택
        color = self.field_type_colors.get(field_type, (128, 128, 128))

        # 바운딩 박스 그리기
        line_width = 3 if required else 2
        for i in range(line_width):
            draw.rectangle([x1-i, y1-i, x2+i, y2+i], outline=color, fill=None)

        # 필드 타입별 패턴 추가
        if field_type == 'table':
            self._draw_table_pattern(draw, x1, y1, x2, y2, color)
        elif field_type == 'checkbox':
            self._draw_checkbox_pattern(draw, x1, y1, x2, y2, color)

        # 필드 라벨 그리기
        label_text = f"{field_name} ({field_type})"
        if required:
            label_text += " *"

        # 라벨 위치 계산
        label_bbox = draw.textbbox((0, 0), label_text, font=font)
        label_width = label_bbox[2] - label_bbox[0]
        label_height = label_bbox[3] - label_bbox[1]

        label_x = x1
        label_y = y1 - label_height - 5

        # 라벨이 이미지 밖으로 나가지 않도록 조정
        if label_y < 0:
            label_y = y2 + 5

        # 라벨 배경 그리기
        bg_padding = 2
        draw.rectangle([
            label_x - bg_padding,
            label_y - bg_padding,
            label_x + label_width + bg_padding,
            label_y + label_height + bg_padding
        ], fill=(255, 255, 255, 220), outline=color)

        # 라벨 텍스트 그리기
        draw.text((label_x, label_y), label_text, fill=color, font=font)

    def _draw_table_pattern(self, draw: ImageDraw.Draw, x1: int, y1: int, x2: int, y2: int, color: Tuple[int, int, int]):
        """테이블 필드에 격자 패턴 그리기"""
        # 세로 선들
        width = x2 - x1
        for i in range(1, 4):
            x = x1 + (width * i // 4)
            draw.line([x, y1, x, y2], fill=color, width=1)

        # 가로 선들
        height = y2 - y1
        for i in range(1, 3):
            y = y1 + (height * i // 3)
            draw.line([x1, y, x2, y], fill=color, width=1)

    def _draw_checkbox_pattern(self, draw: ImageDraw.Draw, x1: int, y1: int, x2: int, y2: int, color: Tuple[int, int, int]):
        """체크박스 필드에 체크 패턴 그리기"""
        # 작은 사각형들 그리기
        box_size = min(20, (x2-x1)//3, (y2-y1)//2)
        start_x = x1 + 10
        start_y = y1 + (y2-y1)//2 - box_size//2

        for i in range(min(3, (x2-x1-20)//30)):
            box_x = start_x + i * 30
            draw.rectangle([box_x, start_y, box_x + box_size, start_y + box_size],
                         outline=color, width=2)

    def _draw_legend(self, draw: ImageDraw.Draw, fields: List[Dict], font, img_width: int, img_height: int):
        """범례 그리기"""
        # 사용된 필드 타입들 수집
        used_types = set()
        for field in fields:
            used_types.add(field.get('type', 'text'))

        if not used_types:
            return

        # 범례 영역 설정
        legend_x = img_width - 200
        legend_y = 50
        legend_item_height = 25

        # 범례 배경
        legend_height = len(used_types) * legend_item_height + 20
        draw.rectangle([legend_x - 10, legend_y - 10,
                       img_width - 10, legend_y + legend_height],
                      fill=(250, 250, 250), outline=(200, 200, 200))

        # 범례 제목
        draw.text((legend_x, legend_y), "Field Types:", fill=(0, 0, 0), font=font)

        # 각 타입별 범례 항목
        for i, field_type in enumerate(sorted(used_types)):
            y = legend_y + 20 + i * legend_item_height
            color = self.field_type_colors.get(field_type, (128, 128, 128))

            # 색상 샘플
            draw.rectangle([legend_x, y, legend_x + 15, y + 10], fill=color)

            # 타입 이름
            draw.text((legend_x + 20, y - 2), field_type, fill=(0, 0, 0), font=font)

    def save_template_preview(self, template_data: Dict, output_path: str) -> bool:
        """
        템플릿 미리보기를 파일로 저장

        Args:
            template_data: 템플릿 정의 데이터
            output_path: 저장할 파일 경로

        Returns:
            저장 성공 여부
        """
        try:
            # 출력 디렉토리 생성
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # 미리보기 이미지 생성
            preview_image = self.create_template_preview(template_data)

            # 이미지 저장
            preview_image.save(output_path, 'PNG', quality=95)

            logger.info(f"Template preview saved: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving template preview: {str(e)}")
            return False

    def create_overlay_visualization(self, template_data: Dict, document_image_path: str) -> Optional[Image.Image]:
        """
        문서 이미지 위에 템플릿 필드를 오버레이

        Args:
            template_data: 템플릿 정의 데이터
            document_image_path: 문서 이미지 경로

        Returns:
            오버레이된 PIL Image 객체 또는 None
        """
        try:
            if not os.path.exists(document_image_path):
                logger.error(f"Document image not found: {document_image_path}")
                return None

            # 원본 문서 이미지 열기
            base_image = Image.open(document_image_path).convert('RGB')
            overlay = Image.new('RGBA', base_image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)

            # 한글 폰트 설정 (폰트 매니저 사용)
            font = font_manager.get_korean_font(size=10, bold=False)

            # 템플릿 필드들을 오버레이로 그리기
            fields = template_data.get('fields', [])
            for field in fields:
                bbox = field.get('bbox', {})
                field_type = field.get('type', 'text')
                field_name = field.get('name', field.get('field_id', ''))

                x1 = bbox.get('x1', 0)
                y1 = bbox.get('y1', 0)
                x2 = bbox.get('x2', 100)
                y2 = bbox.get('y2', 50)

                color = self.field_type_colors.get(field_type, (128, 128, 128))
                alpha_color = (*color, 100)  # 반투명

                # 반투명 바운딩 박스
                draw.rectangle([x1, y1, x2, y2], fill=alpha_color, outline=(*color, 255), width=2)

                # 필드 라벨
                draw.text((x1, y1-15), f"{field_name}", fill=(*color, 255), font=font)

            # 원본 이미지와 오버레이 합성
            result = Image.alpha_composite(base_image.convert('RGBA'), overlay)
            return result.convert('RGB')

        except Exception as e:
            logger.error(f"Error creating overlay visualization: {str(e)}")
            return None