#!/usr/bin/env python3
"""
Table recognition service using PaddleOCR's structure analysis
"""

from paddleocr import PaddleOCR
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class TableRecognizer:
    """PaddleOCR의 구조 분석을 사용한 표 인식기"""

    def __init__(self, lang: str = 'korean', use_gpu: bool = False):
        """
        표 인식기 초기화

        Args:
            lang: 언어 설정 (OCR용, 레이아웃은 영어 모델 사용)
            use_gpu: GPU 사용 여부
        """
        self.lang = lang
        self.use_gpu = use_gpu

        # 구조 분석용 PaddleOCR 초기화
        try:
            # PaddleStructure는 별도 import 필요
            from paddleocr import PPStructure

            # 레이아웃 분석은 영어 모델 사용 (한국어 미지원)
            layout_lang = 'en' if lang == 'korean' else lang

            self.structure_engine = PPStructure(
                table=True,              # 표 인식 활성화
                ocr=True,               # OCR 활성화
                show_log=False,         # 로그 최소화
                lang=layout_lang,       # 레이아웃용 언어 설정 (영어)
                layout=True,            # 레이아웃 분석 활성화
                recovery=False          # 복구 기능 비활성화 (속도 향상)
            )
            print(f"PaddleStructure 초기화 완료 - OCR 언어: {lang}, 레이아웃 언어: {layout_lang}")

        except ImportError:
            print("PaddleStructure를 사용할 수 없습니다. 기본 OCR로 대체합니다.")
            self.structure_engine = PaddleOCR(
                lang=lang,
                use_angle_cls=True,
                show_log=False
            )

        except Exception as e:
            print(f"PaddleStructure 초기화 실패: {e}")
            # 기본 OCR로 폴백
            self.structure_engine = PaddleOCR(
                lang=lang,
                use_angle_cls=True,
                show_log=False
            )

    def detect_tables(self, image_path: str) -> List[Dict[str, Any]]:
        """
        이미지에서 표를 감지하고 인식

        Args:
            image_path: 이미지 파일 경로

        Returns:
            표 정보 리스트 (위치, 구조, 내용 포함)
        """
        try:
            # 이미지 로드
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")

            # 구조 분석 실행
            result = self.structure_engine(img)

            tables = []
            table_count = 0

            for item in result:
                if item.get('type') == 'table':
                    table_count += 1

                    # 표 영역 정보
                    bbox = item.get('bbox', [0, 0, img.shape[1], img.shape[0]])

                    # HTML 구조 정보 (가능한 경우)
                    html_content = item.get('res', {}).get('html', '')

                    # 표 셀 정보 추출
                    cells = self._extract_table_cells(item)

                    table_info = {
                        'table_id': table_count,
                        'type': 'table',
                        'bbox': bbox,
                        'bbox_points': self._bbox_to_points(bbox),
                        'html_structure': html_content,
                        'cells': cells,
                        'rows': len(set(cell.get('row', 0) for cell in cells)),
                        'columns': len(set(cell.get('col', 0) for cell in cells)),
                        'confidence': item.get('score', 0.0)
                    }

                    tables.append(table_info)

            print(f"표 {len(tables)}개 감지됨")
            return tables

        except Exception as e:
            print(f"표 감지 중 오류: {e}")
            return []

    def _extract_table_cells(self, table_item: Dict) -> List[Dict[str, Any]]:
        """표 아이템에서 셀 정보 추출"""
        cells = []

        try:
            # 구조 분석 결과에서 셀 정보 추출
            if 'res' in table_item:
                res = table_item['res']

                # HTML 테이블 구조 파싱 (간단한 버전)
                if 'html' in res:
                    cells = self._parse_html_table(res['html'])

                # 또는 직접 셀 정보가 있는 경우
                elif 'cell_bbox' in res:
                    for i, cell_bbox in enumerate(res['cell_bbox']):
                        cell = {
                            'cell_id': i + 1,
                            'text': res.get('texts', [''])[i] if i < len(res.get('texts', [])) else '',
                            'bbox': cell_bbox,
                            'bbox_points': self._bbox_to_points(cell_bbox),
                            'row': res.get('rows', [0])[i] if i < len(res.get('rows', [])) else 0,
                            'col': res.get('cols', [0])[i] if i < len(res.get('cols', [])) else 0,
                            'confidence': res.get('scores', [0.0])[i] if i < len(res.get('scores', [])) else 0.0
                        }
                        cells.append(cell)

        except Exception as e:
            print(f"셀 정보 추출 중 오류: {e}")

        return cells

    def _parse_html_table(self, html: str) -> List[Dict[str, Any]]:
        """HTML 테이블 구조에서 셀 정보 추출 (간단한 파서)"""
        cells = []

        try:
            # 간단한 HTML 파싱 (BeautifulSoup 없이)
            import re

            # <td> 태그에서 텍스트 추출
            td_pattern = r'<td[^>]*>(.*?)</td>'
            matches = re.findall(td_pattern, html, re.DOTALL | re.IGNORECASE)

            for i, match in enumerate(matches):
                # HTML 태그 제거
                text = re.sub(r'<[^>]+>', '', match).strip()

                cell = {
                    'cell_id': i + 1,
                    'text': text,
                    'row': i // 10,  # 임시적인 행 계산
                    'col': i % 10,   # 임시적인 열 계산
                    'confidence': 0.9
                }
                cells.append(cell)

        except Exception as e:
            print(f"HTML 파싱 중 오류: {e}")

        return cells

    def _bbox_to_points(self, bbox: List[float]) -> List[List[float]]:
        """바운딩 박스를 포인트 형태로 변환"""
        if len(bbox) >= 4:
            x1, y1, x2, y2 = bbox[:4]
            return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
        return [[0, 0], [100, 0], [100, 100], [0, 100]]

    def analyze_layout(self, image_path: str) -> Dict[str, Any]:
        """
        이미지의 전체 레이아웃 분석 (표, 제목, 단락 등)

        Args:
            image_path: 이미지 파일 경로

        Returns:
            레이아웃 분석 결과
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")

            # 구조 분석 실행
            result = self.structure_engine(img)

            layout_elements = {
                'tables': [],
                'titles': [],
                'paragraphs': [],
                'figures': [],
                'others': []
            }

            for item in result:
                element_type = item.get('type', 'other')

                element = {
                    'type': element_type,
                    'bbox': item.get('bbox', []),
                    'bbox_points': self._bbox_to_points(item.get('bbox', [])),
                    'confidence': item.get('score', 0.0)
                }

                # 타입별로 분류
                if element_type == 'table':
                    # 표 세부 정보 추가
                    element.update({
                        'cells': self._extract_table_cells(item),
                        'html_structure': item.get('res', {}).get('html', '')
                    })
                    layout_elements['tables'].append(element)

                elif element_type in ['title', 'heading']:
                    layout_elements['titles'].append(element)

                elif element_type in ['text', 'paragraph']:
                    layout_elements['paragraphs'].append(element)

                elif element_type in ['figure', 'image']:
                    layout_elements['figures'].append(element)

                else:
                    layout_elements['others'].append(element)

            return {
                'layout_elements': layout_elements,
                'summary': {
                    'total_tables': len(layout_elements['tables']),
                    'total_titles': len(layout_elements['titles']),
                    'total_paragraphs': len(layout_elements['paragraphs']),
                    'total_figures': len(layout_elements['figures']),
                    'total_others': len(layout_elements['others'])
                }
            }

        except Exception as e:
            print(f"레이아웃 분석 중 오류: {e}")
            return {'layout_elements': {}, 'summary': {}}


def create_table_recognizer(lang: str = 'korean', use_gpu: bool = False) -> TableRecognizer:
    """표 인식기 인스턴스 생성"""
    return TableRecognizer(lang=lang, use_gpu=use_gpu)


__all__ = ['TableRecognizer', 'create_table_recognizer']