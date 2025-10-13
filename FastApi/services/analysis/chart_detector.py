#!/usr/bin/env python3
"""
경량 차트/그래프 감지 - OpenCV 기반
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
import math


class LightweightChartDetector:
    """OpenCV를 사용한 경량 차트 감지기"""

    def __init__(self):
        """차트 감지기 초기화"""
        self.min_chart_area = 5000  # 최소 차트 영역 (픽셀)
        self.min_line_length = 50   # 최소 라인 길이
        self.line_threshold = 10    # 라인 감지 임계값

    def detect_charts(self, image_path: str, existing_blocks: List[Dict] = None) -> List[Dict[str, Any]]:
        """
        이미지에서 차트/그래프 영역 감지

        Args:
            image_path: 이미지 파일 경로
            existing_blocks: 기존 OCR 블록들 (겹침 방지용)

        Returns:
            감지된 차트 정보 리스트
        """
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                return []

            height, width = image.shape[:2]

            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            charts = []

            # 1. 바차트 감지
            bar_charts = self._detect_bar_charts(gray, width, height)
            charts.extend(bar_charts)

            # 2. 라인차트 감지
            line_charts = self._detect_line_charts(gray, width, height)
            charts.extend(line_charts)

            # 3. 파이차트 감지
            pie_charts = self._detect_pie_charts(gray, width, height)
            charts.extend(pie_charts)

            # 4. 기하학적 도형 기반 차트 감지
            geometric_charts = self._detect_geometric_charts(gray, width, height)
            charts.extend(geometric_charts)

            # 5. 기존 OCR 블록과 겹치는 차트 필터링
            if existing_blocks:
                charts = self._filter_overlapping_charts(charts, existing_blocks)

            # 6. 차트 신뢰도 계산 및 정렬
            charts = self._calculate_chart_confidence(charts, gray)

            print(f"경량 차트 감지 완료: {len(charts)}개")
            return charts

        except Exception as e:
            print(f"차트 감지 중 오류: {e}")
            return []

    def _detect_bar_charts(self, gray: np.ndarray, width: int, height: int) -> List[Dict]:
        """바차트 감지"""
        charts = []

        try:
            # 수직 바차트 감지
            vertical_bars = self._find_vertical_bars(gray)
            if len(vertical_bars) >= 2:  # 최소 2개 이상의 바
                chart_bbox = self._get_bounding_box(vertical_bars)
                if self._is_valid_chart_area(chart_bbox, width, height):
                    charts.append({
                        'type': 'bar_chart',
                        'subtype': 'vertical',
                        'bbox': chart_bbox,
                        'bars_count': len(vertical_bars),
                        'bars': vertical_bars
                    })

            # 수평 바차트 감지
            horizontal_bars = self._find_horizontal_bars(gray)
            if len(horizontal_bars) >= 2:
                chart_bbox = self._get_bounding_box(horizontal_bars)
                if self._is_valid_chart_area(chart_bbox, width, height):
                    charts.append({
                        'type': 'bar_chart',
                        'subtype': 'horizontal',
                        'bbox': chart_bbox,
                        'bars_count': len(horizontal_bars),
                        'bars': horizontal_bars
                    })

        except Exception as e:
            print(f"바차트 감지 오류: {e}")

        return charts

    def _detect_line_charts(self, gray: np.ndarray, width: int, height: int) -> List[Dict]:
        """라인차트 감지"""
        charts = []

        try:
            # Hough 라인 변환으로 라인 감지
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=self.line_threshold,
                                   minLineLength=self.min_line_length, maxLineGap=10)

            if lines is not None and len(lines) >= 3:
                # 연결된 라인 그룹 찾기
                line_groups = self._group_connected_lines(lines)

                for group in line_groups:
                    if len(group) >= 3:  # 최소 3개 라인
                        chart_bbox = self._get_lines_bounding_box(group)
                        if self._is_valid_chart_area(chart_bbox, width, height):
                            charts.append({
                                'type': 'line_chart',
                                'bbox': chart_bbox,
                                'lines_count': len(group),
                                'lines': group.tolist()
                            })

        except Exception as e:
            print(f"라인차트 감지 오류: {e}")

        return charts

    def _detect_pie_charts(self, gray: np.ndarray, width: int, height: int) -> List[Dict]:
        """파이차트 감지"""
        charts = []

        try:
            # 원형 모양 감지
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=100,
                                     param1=50, param2=30, minRadius=30, maxRadius=200)

            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")

                for (x, y, r) in circles:
                    # 원 내부의 라인 수로 파이차트 판단
                    roi = gray[max(0, y-r):min(height, y+r), max(0, x-r):min(width, x+r)]
                    edges = cv2.Canny(roi, 50, 150)
                    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=5, minLineLength=10)

                    if lines is not None and len(lines) >= 2:  # 파이 조각 라인들
                        bbox = [x-r, y-r, x+r, y+r]
                        if self._is_valid_chart_area(bbox, width, height):
                            charts.append({
                                'type': 'pie_chart',
                                'bbox': bbox,
                                'center': [x, y],
                                'radius': r,
                                'segments': len(lines)
                            })

        except Exception as e:
            print(f"파이차트 감지 오류: {e}")

        return charts

    def _detect_geometric_charts(self, gray: np.ndarray, width: int, height: int) -> List[Dict]:
        """기하학적 도형 기반 차트 감지"""
        charts = []

        try:
            # 컨투어 감지
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            rectangular_regions = []

            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.min_chart_area:
                    # 사각형 근사
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if len(approx) == 4:  # 사각형
                        x, y, w, h = cv2.boundingRect(contour)
                        aspect_ratio = w / h

                        # 차트 같은 비율 (너무 길거나 높지 않음)
                        if 0.3 < aspect_ratio < 3.0 and area > self.min_chart_area:
                            rectangular_regions.append({
                                'type': 'chart_region',
                                'bbox': [x, y, x+w, y+h],
                                'area': area,
                                'aspect_ratio': aspect_ratio
                            })

            # 큰 사각형 영역들을 잠재적 차트로 분류
            for region in sorted(rectangular_regions, key=lambda x: x['area'], reverse=True)[:3]:
                charts.append(region)

        except Exception as e:
            print(f"기하학적 차트 감지 오류: {e}")

        return charts

    def _find_vertical_bars(self, gray: np.ndarray) -> List[List[int]]:
        """수직 바 감지"""
        bars = []

        try:
            # 수직 구조 요소로 모폴로지 연산
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
            vertical = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            # 이진화
            _, binary = cv2.threshold(vertical, 127, 255, cv2.THRESH_BINARY_INV)

            # 컨투어 찾기
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # 수직 바 조건: 높이가 너비보다 크고 충분한 크기
                if h > w * 2 and h > 30 and w > 5:
                    bars.append([x, y, x+w, y+h])

        except Exception as e:
            print(f"수직 바 감지 오류: {e}")

        return bars

    def _find_horizontal_bars(self, gray: np.ndarray) -> List[List[int]]:
        """수평 바 감지"""
        bars = []

        try:
            # 수평 구조 요소로 모폴로지 연산
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
            horizontal = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            # 이진화
            _, binary = cv2.threshold(horizontal, 127, 255, cv2.THRESH_BINARY_INV)

            # 컨투어 찾기
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # 수평 바 조건: 너비가 높이보다 크고 충분한 크기
                if w > h * 2 and w > 30 and h > 5:
                    bars.append([x, y, x+w, y+h])

        except Exception as e:
            print(f"수평 바 감지 오류: {e}")

        return bars

    def _group_connected_lines(self, lines: np.ndarray) -> List[np.ndarray]:
        """연결된 라인들을 그룹화"""
        if lines is None or len(lines) == 0:
            return []

        groups = []
        used = set()

        for i, line1 in enumerate(lines):
            if i in used:
                continue

            group = [line1[0]]
            used.add(i)

            for j, line2 in enumerate(lines):
                if j in used:
                    continue

                # 라인 간 거리 계산
                if self._are_lines_connected(line1[0], line2[0]):
                    group.append(line2[0])
                    used.add(j)

            if len(group) >= 2:
                groups.append(np.array(group))

        return groups

    def _are_lines_connected(self, line1: List[int], line2: List[int], threshold: int = 20) -> bool:
        """두 라인이 연결되어 있는지 확인"""
        x1, y1, x2, y2 = line1
        x3, y3, x4, y4 = line2

        # 라인 끝점들 간의 최소 거리
        distances = [
            math.sqrt((x1-x3)**2 + (y1-y3)**2),
            math.sqrt((x1-x4)**2 + (y1-y4)**2),
            math.sqrt((x2-x3)**2 + (y2-y3)**2),
            math.sqrt((x2-x4)**2 + (y2-y4)**2)
        ]

        return min(distances) < threshold

    def _get_bounding_box(self, elements: List[List[int]]) -> List[int]:
        """요소들의 바운딩 박스 계산"""
        if not elements:
            return [0, 0, 0, 0]

        x_coords = []
        y_coords = []

        for element in elements:
            x_coords.extend([element[0], element[2]])
            y_coords.extend([element[1], element[3]])

        return [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]

    def _get_lines_bounding_box(self, lines: np.ndarray) -> List[int]:
        """라인들의 바운딩 박스 계산"""
        if len(lines) == 0:
            return [0, 0, 0, 0]

        x_coords = lines[:, [0, 2]].flatten()
        y_coords = lines[:, [1, 3]].flatten()

        return [int(min(x_coords)), int(min(y_coords)), int(max(x_coords)), int(max(y_coords))]

    def _is_valid_chart_area(self, bbox: List[int], img_width: int, img_height: int) -> bool:
        """유효한 차트 영역인지 확인"""
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        area = width * height

        # 면적, 비율, 위치 확인
        return (area > self.min_chart_area and
                0.1 < width/height < 10 and  # 극단적 비율 제외
                x1 >= 0 and y1 >= 0 and x2 <= img_width and y2 <= img_height)

    def _filter_overlapping_charts(self, charts: List[Dict], ocr_blocks: List[Dict]) -> List[Dict]:
        """OCR 블록과 겹치는 차트 필터링"""
        filtered_charts = []

        for chart in charts:
            chart_bbox = chart['bbox']
            overlaps_significantly = False

            for block in ocr_blocks:
                block_bbox = block.get('bbox', {})
                if self._calculate_overlap(chart_bbox, [
                    block_bbox.get('x_min', 0), block_bbox.get('y_min', 0),
                    block_bbox.get('x_max', 0), block_bbox.get('y_max', 0)
                ]) > 0.5:  # 50% 이상 겹침
                    overlaps_significantly = True
                    break

            if not overlaps_significantly:
                filtered_charts.append(chart)

        return filtered_charts

    def _calculate_overlap(self, bbox1: List[int], bbox2: List[int]) -> float:
        """두 바운딩 박스의 겹침 비율 계산"""
        try:
            x1_min, y1_min, x1_max, y1_max = bbox1
            x2_min, y2_min, x2_max, y2_max = bbox2

            overlap_x_min = max(x1_min, x2_min)
            overlap_y_min = max(y1_min, y2_min)
            overlap_x_max = min(x1_max, x2_max)
            overlap_y_max = min(y1_max, y2_max)

            if overlap_x_min >= overlap_x_max or overlap_y_min >= overlap_y_max:
                return 0.0

            overlap_area = (overlap_x_max - overlap_x_min) * (overlap_y_max - overlap_y_min)
            bbox1_area = (x1_max - x1_min) * (y1_max - y1_min)

            return overlap_area / bbox1_area if bbox1_area > 0 else 0.0
        except Exception:
            return 0.0

    def _calculate_chart_confidence(self, charts: List[Dict], gray: np.ndarray) -> List[Dict]:
        """차트 신뢰도 계산"""
        for chart in charts:
            try:
                bbox = chart['bbox']
                x1, y1, x2, y2 = bbox

                # 기본 신뢰도
                confidence = 0.5

                # 크기 기반 가중치
                area = (x2 - x1) * (y2 - y1)
                if area > 20000:
                    confidence += 0.2

                # 타입별 가중치
                if chart['type'] == 'bar_chart':
                    confidence += 0.1 + min(chart.get('bars_count', 0) * 0.05, 0.2)
                elif chart['type'] == 'line_chart':
                    confidence += 0.1 + min(chart.get('lines_count', 0) * 0.03, 0.15)
                elif chart['type'] == 'pie_chart':
                    confidence += 0.15 + min(chart.get('segments', 0) * 0.02, 0.1)

                chart['confidence'] = min(confidence, 0.95)  # 최대 95%

            except Exception:
                chart['confidence'] = 0.3  # 기본값

        # 신뢰도 순 정렬
        return sorted(charts, key=lambda x: x.get('confidence', 0), reverse=True)


def create_chart_detector() -> LightweightChartDetector:
    """차트 감지기 인스턴스 생성"""
    return LightweightChartDetector()


__all__ = ['LightweightChartDetector', 'create_chart_detector']