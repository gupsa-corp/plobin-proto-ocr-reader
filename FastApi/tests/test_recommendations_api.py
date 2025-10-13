#!/usr/bin/env python3
"""
추천 API 엔드포인트 테스트
"""

import unittest
import asyncio
import sys
import os
from unittest.mock import patch, MagicMock
import json

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api_server import app

class TestRecommendationsAPI(unittest.TestCase):
    """추천 API 테스트"""

    def setUp(self):
        """테스트 클라이언트 설정"""
        self.client = TestClient(app)

    def test_get_tickets_basic(self):
        """기본 티켓 추천 API 테스트"""
        response = self.client.get("/recommendations/tickets")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('tickets', data['data'])
        self.assertIn('meta', data)

        # 기본 10개 티켓 확인
        tickets = data['data']['tickets']
        self.assertEqual(len(tickets), 10)

        # 각 티켓의 필수 필드 확인
        for ticket in tickets:
            self.assertIn('ticket_id', ticket)
            self.assertIn('title', ticket)
            self.assertIn('description', ticket)
            self.assertIn('type', ticket)
            self.assertIn('priority', ticket)
            self.assertIn('story_points', ticket)
            self.assertIn('assignee', ticket)
            self.assertIn('component', ticket)

    def test_get_tickets_with_count(self):
        """개수 지정 티켓 추천 테스트"""
        response = self.client.get("/recommendations/tickets?count=5")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        tickets = data['data']['tickets']
        self.assertEqual(len(tickets), 5)

    def test_get_tickets_with_focus_area(self):
        """집중 영역 필터링 테스트"""
        response = self.client.get("/recommendations/tickets?focus_area=ocr&count=3")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        tickets = data['data']['tickets']
        self.assertGreater(len(tickets), 0)

        # 필터 정보 확인
        filters = data['data']['filters']
        self.assertEqual(filters['focus_area'], 'ocr')
        self.assertEqual(filters['requested_count'], 3)

    def test_get_tickets_with_priority_filter(self):
        """우선순위 필터링 테스트"""
        response = self.client.get("/recommendations/tickets?priority_filter=high&count=20")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        tickets = data['data']['tickets']

        # 모든 티켓이 high 우선순위인지 확인
        for ticket in tickets:
            self.assertEqual(ticket['priority'], 'high')

    def test_get_tickets_invalid_count(self):
        """잘못된 개수 파라미터 테스트"""
        # 너무 큰 개수
        response = self.client.get("/recommendations/tickets?count=100")
        self.assertEqual(response.status_code, 422)  # Validation error

        # 음수
        response = self.client.get("/recommendations/tickets?count=-1")
        self.assertEqual(response.status_code, 422)

        # 0
        response = self.client.get("/recommendations/tickets?count=0")
        self.assertEqual(response.status_code, 422)

    def test_get_sprint_recommendations(self):
        """스프린트 추천 API 테스트"""
        response = self.client.get("/recommendations/sprint?capacity=30")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('planning_info', data)
        self.assertIn('recommendations', data)

        # 스프린트 데이터 확인
        sprint_data = data['data']
        self.assertIn('sprint_name', sprint_data)
        self.assertIn('capacity', sprint_data)
        self.assertIn('allocated_points', sprint_data)
        self.assertIn('tickets', sprint_data)
        self.assertIn('summary', sprint_data)

        # 용량 확인
        self.assertLessEqual(sprint_data['allocated_points'], sprint_data['capacity'])

    def test_get_sprint_with_team_size(self):
        """팀 크기를 고려한 스프린트 추천 테스트"""
        response = self.client.get("/recommendations/sprint?capacity=40&team_size=8")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        planning_info = data['planning_info']

        self.assertEqual(planning_info['original_capacity'], 40)
        self.assertEqual(planning_info['team_size'], 8)
        # 8명 팀이므로 용량이 조정되어야 함 (40 * 8 / 5 = 64)
        self.assertEqual(planning_info['adjusted_capacity'], 64)

    def test_get_sprint_invalid_params(self):
        """잘못된 스프린트 파라미터 테스트"""
        # 용량이 범위를 벗어남
        response = self.client.get("/recommendations/sprint?capacity=200")
        self.assertEqual(response.status_code, 422)

        # 팀 크기가 범위를 벗어남
        response = self.client.get("/recommendations/sprint?team_size=30")
        self.assertEqual(response.status_code, 422)

    def test_get_product_backlog(self):
        """제품 백로그 API 테스트"""
        response = self.client.get("/recommendations/backlog")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('roadmap_suggestions', data)

        # 백로그 데이터 확인
        backlog_data = data['data']
        self.assertIn('backlog', backlog_data)
        self.assertIn('statistics', backlog_data)

        # 우선순위별 백로그 확인
        backlog = backlog_data['backlog']
        self.assertIn('critical', backlog)
        self.assertIn('high', backlog)
        self.assertIn('medium', backlog)
        self.assertIn('low', backlog)

        # 통계 확인
        stats = backlog_data['statistics']
        self.assertIn('total_tickets', stats)
        self.assertIn('total_story_points', stats)
        self.assertIn('estimated_sprints', stats)

    def test_get_focus_areas(self):
        """집중 영역 목록 API 테스트"""
        response = self.client.get("/recommendations/focus-areas")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)

        # 집중 영역 데이터 확인
        focus_areas = data['data']['focus_areas']
        self.assertIn('ocr', focus_areas)
        self.assertIn('performance', focus_areas)
        self.assertIn('security', focus_areas)

        # 각 영역에 설명이 있는지 확인
        for area_name, area_info in focus_areas.items():
            self.assertIn('description', area_info)
            self.assertIn('sample_tasks', area_info)

    def test_get_metrics(self):
        """메트릭 API 테스트"""
        response = self.client.get("/recommendations/metrics")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)

        # 메트릭 데이터 확인
        metrics_data = data['data']
        self.assertIn('algorithm_info', metrics_data)
        self.assertIn('ticket_statistics', metrics_data)
        self.assertIn('performance_metrics', metrics_data)
        self.assertIn('usage_statistics', metrics_data)

class TestRecommendationsAPIError(unittest.TestCase):
    """추천 API 오류 처리 테스트"""

    def setUp(self):
        self.client = TestClient(app)

    @patch('api.endpoints.recommendations.get_recommendations')
    def test_tickets_api_error_handling(self, mock_get_recommendations):
        """티켓 API 오류 처리 테스트"""
        # 예외 발생 시뮬레이션
        mock_get_recommendations.side_effect = Exception("테스트 오류")

        response = self.client.get("/recommendations/tickets")

        self.assertEqual(response.status_code, 500)
        self.assertIn("추천 생성 실패", response.json()['detail'])

    @patch('api.endpoints.recommendations.get_sprint_recommendations')
    def test_sprint_api_error_handling(self, mock_get_sprint):
        """스프린트 API 오류 처리 테스트"""
        # 예외 발생 시뮬레이션
        mock_get_sprint.side_effect = Exception("스프린트 오류")

        response = self.client.get("/recommendations/sprint")

        self.assertEqual(response.status_code, 500)
        self.assertIn("스프린트 계획 생성 실패", response.json()['detail'])

class TestRecommendationsAPIPerformance(unittest.TestCase):
    """추천 API 성능 테스트"""

    def setUp(self):
        self.client = TestClient(app)

    def test_api_response_time(self):
        """API 응답 시간 테스트"""
        import time

        start_time = time.time()
        response = self.client.get("/recommendations/tickets?count=10")
        end_time = time.time()

        response_time = end_time - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 1.0)  # 1초 이내 응답

    def test_large_request_handling(self):
        """대량 요청 처리 테스트"""
        response = self.client.get("/recommendations/tickets?count=50")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        tickets = data['data']['tickets']
        self.assertLessEqual(len(tickets), 50)  # 최대 50개까지

    def test_concurrent_requests(self):
        """동시 요청 처리 테스트"""
        import threading
        import time

        results = []

        def make_request():
            response = self.client.get("/recommendations/tickets?count=5")
            results.append(response.status_code)

        # 10개의 동시 요청
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        start_time = time.time()

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()

        # 모든 요청이 성공했는지 확인
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status == 200 for status in results))

        # 전체 처리 시간이 합리적인지 확인
        total_time = end_time - start_time
        self.assertLess(total_time, 5.0)  # 5초 이내

class TestRecommendationsAPIValidation(unittest.TestCase):
    """추천 API 유효성 검증 테스트"""

    def setUp(self):
        self.client = TestClient(app)

    def test_response_structure_validation(self):
        """응답 구조 유효성 검증"""
        response = self.client.get("/recommendations/tickets?count=3")
        data = response.json()

        # 최상위 구조 확인
        required_top_keys = ['status', 'data', 'meta']
        for key in required_top_keys:
            self.assertIn(key, data)

        # data 구조 확인
        data_section = data['data']
        required_data_keys = ['tickets', 'count', 'filters']
        for key in required_data_keys:
            self.assertIn(key, data_section)

        # meta 구조 확인
        meta_section = data['meta']
        required_meta_keys = ['generated_at', 'algorithm_version', 'data_source']
        for key in required_meta_keys:
            self.assertIn(key, meta_section)

    def test_ticket_structure_validation(self):
        """티켓 구조 유효성 검증"""
        response = self.client.get("/recommendations/tickets?count=1")
        data = response.json()

        ticket = data['data']['tickets'][0]

        required_ticket_keys = [
            'ticket_id', 'title', 'description', 'type', 'priority',
            'status', 'story_points', 'estimated_hours', 'labels',
            'assignee', 'component', 'created_date', 'due_date',
            'reporter', 'sprint', 'epic'
        ]

        for key in required_ticket_keys:
            self.assertIn(key, ticket)

        # 데이터 타입 확인
        self.assertIsInstance(ticket['story_points'], int)
        self.assertIsInstance(ticket['estimated_hours'], int)
        self.assertIsInstance(ticket['labels'], list)

if __name__ == '__main__':
    unittest.main()