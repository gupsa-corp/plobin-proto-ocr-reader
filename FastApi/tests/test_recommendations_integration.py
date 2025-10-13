#!/usr/bin/env python3
"""
추천 시스템 통합 테스트
"""

import unittest
import requests
import time
import json
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRecommendationsIntegration(unittest.TestCase):
    """추천 시스템 통합 테스트"""

    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        cls.base_url = "http://localhost:6003"
        cls.timeout = 10

        # 서버가 실행 중인지 확인
        try:
            response = requests.get(f"{cls.base_url}/health", timeout=cls.timeout)
            if response.status_code != 200:
                raise Exception("서버가 실행되지 않음")
        except requests.exceptions.RequestException:
            raise unittest.SkipTest("서버가 실행되지 않아 통합 테스트를 건너뜁니다")

    def test_full_recommendation_workflow(self):
        """전체 추천 워크플로우 테스트"""

        # 1. 기본 티켓 추천 요청
        response = requests.get(f"{self.base_url}/recommendations/tickets?count=5", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)

        tickets_data = response.json()
        self.assertEqual(len(tickets_data['data']['tickets']), 5)

        # 2. 집중 영역 조회
        response = requests.get(f"{self.base_url}/recommendations/focus-areas", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)

        focus_areas = response.json()['data']['focus_areas']
        area_names = list(focus_areas.keys())

        # 3. 특정 집중 영역으로 필터링된 티켓 요청
        if area_names:
            area = area_names[0]  # 첫 번째 영역 사용
            response = requests.get(
                f"{self.base_url}/recommendations/tickets?focus_area={area}&count=3",
                timeout=self.timeout
            )
            self.assertEqual(response.status_code, 200)

            filtered_data = response.json()
            self.assertEqual(filtered_data['data']['filters']['focus_area'], area)

        # 4. 스프린트 계획 요청
        response = requests.get(f"{self.base_url}/recommendations/sprint?capacity=30", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)

        sprint_data = response.json()
        self.assertLessEqual(sprint_data['data']['allocated_points'], 30)

        # 5. 제품 백로그 조회
        response = requests.get(f"{self.base_url}/recommendations/backlog", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)

        backlog_data = response.json()
        self.assertIn('statistics', backlog_data['data'])

    def test_cross_endpoint_data_consistency(self):
        """엔드포인트 간 데이터 일관성 테스트"""

        # 백로그에서 전체 통계 가져오기
        response = requests.get(f"{self.base_url}/recommendations/backlog", timeout=self.timeout)
        backlog_stats = response.json()['data']['statistics']

        # 메트릭에서 통계 가져오기
        response = requests.get(f"{self.base_url}/recommendations/metrics", timeout=self.timeout)
        metrics_stats = response.json()['data']['ticket_statistics']

        # 우선순위 분포가 일치하는지 확인 (대략적으로)
        backlog_priorities = backlog_stats['by_priority']
        metrics_priorities = metrics_stats['priority_distribution']

        # 동일한 우선순위 키들이 존재하는지 확인
        for priority in backlog_priorities.keys():
            self.assertIn(priority, metrics_priorities)

    def test_api_response_time_consistency(self):
        """API 응답 시간 일관성 테스트"""

        endpoints = [
            "/recommendations/tickets?count=5",
            "/recommendations/sprint?capacity=25",
            "/recommendations/focus-areas",
            "/recommendations/metrics"
        ]

        response_times = []

        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", timeout=self.timeout)
            end_time = time.time()

            self.assertEqual(response.status_code, 200)
            response_time = end_time - start_time
            response_times.append(response_time)

            # 각 API가 2초 이내에 응답하는지 확인
            self.assertLess(response_time, 2.0, f"Endpoint {endpoint} took {response_time:.2f}s")

        # 평균 응답 시간이 1초 이내인지 확인
        avg_response_time = sum(response_times) / len(response_times)
        self.assertLess(avg_response_time, 1.0, f"Average response time: {avg_response_time:.2f}s")

    def test_concurrent_api_access(self):
        """동시 API 접근 테스트"""

        def make_request(endpoint):
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=self.timeout)
                return {
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_time': response.elapsed.total_seconds()
                }
            except Exception as e:
                return {
                    'endpoint': endpoint,
                    'status_code': None,
                    'success': False,
                    'error': str(e)
                }

        # 다양한 엔드포인트에 동시 요청
        endpoints = [
            "/recommendations/tickets?count=3",
            "/recommendations/tickets?count=5",
            "/recommendations/tickets?focus_area=ocr",
            "/recommendations/sprint?capacity=20",
            "/recommendations/sprint?capacity=40",
            "/recommendations/backlog",
            "/recommendations/focus-areas",
            "/recommendations/metrics"
        ]

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_endpoint = {
                executor.submit(make_request, endpoint): endpoint
                for endpoint in endpoints
            }

            results = []
            for future in as_completed(future_to_endpoint):
                result = future.result()
                results.append(result)

        end_time = time.time()
        total_time = end_time - start_time

        # 결과 검증
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]

        # 최소 80% 성공률
        success_rate = len(successful_requests) / len(results)
        self.assertGreaterEqual(success_rate, 0.8, f"Success rate: {success_rate:.2%}")

        # 전체 시간이 10초 이내
        self.assertLess(total_time, 10.0, f"Total time: {total_time:.2f}s")

        # 실패한 요청이 있으면 로그 출력
        if failed_requests:
            print(f"Failed requests: {failed_requests}")

    def test_data_format_consistency(self):
        """데이터 형식 일관성 테스트"""

        # 티켓 데이터 형식 검증
        response = requests.get(f"{self.base_url}/recommendations/tickets?count=3", timeout=self.timeout)
        tickets = response.json()['data']['tickets']

        for ticket in tickets:
            # 필수 필드 존재 확인
            required_fields = ['ticket_id', 'title', 'description', 'type', 'priority', 'story_points']
            for field in required_fields:
                self.assertIn(field, ticket)

            # 티켓 ID 형식 확인
            self.assertTrue(ticket['ticket_id'].startswith('OCR-'))
            self.assertTrue(ticket['ticket_id'].split('-')[1].isdigit())

            # 스토리 포인트가 양수인지 확인
            self.assertGreater(ticket['story_points'], 0)

            # 유효한 우선순위인지 확인
            valid_priorities = ['critical', 'high', 'medium', 'low']
            self.assertIn(ticket['priority'], valid_priorities)

    def test_parameter_validation_integration(self):
        """파라미터 유효성 검증 통합 테스트"""

        # 잘못된 count 파라미터
        invalid_counts = [-1, 0, 100, 'abc']
        for count in invalid_counts:
            response = requests.get(f"{self.base_url}/recommendations/tickets?count={count}")
            self.assertEqual(response.status_code, 422, f"Count {count} should be invalid")

        # 잘못된 capacity 파라미터
        invalid_capacities = [-10, 0, 200, 'xyz']
        for capacity in invalid_capacities:
            response = requests.get(f"{self.base_url}/recommendations/sprint?capacity={capacity}")
            self.assertEqual(response.status_code, 422, f"Capacity {capacity} should be invalid")

    def test_load_handling(self):
        """부하 처리 테스트"""

        def make_requests(num_requests):
            successful = 0
            for _ in range(num_requests):
                try:
                    response = requests.get(
                        f"{self.base_url}/recommendations/tickets?count=5",
                        timeout=self.timeout
                    )
                    if response.status_code == 200:
                        successful += 1
                except:
                    pass
            return successful

        # 50개 요청 보내기
        num_requests = 50
        start_time = time.time()
        successful = make_requests(num_requests)
        end_time = time.time()

        total_time = end_time - start_time

        # 성공률 90% 이상
        success_rate = successful / num_requests
        self.assertGreaterEqual(success_rate, 0.9, f"Success rate: {success_rate:.2%}")

        # 처리 시간이 합리적인지 확인 (초당 최소 5개 요청 처리)
        requests_per_second = num_requests / total_time
        self.assertGreaterEqual(requests_per_second, 5.0, f"RPS: {requests_per_second:.2f}")

class TestRecommendationsEndToEnd(unittest.TestCase):
    """추천 시스템 End-to-End 테스트"""

    def setUp(self):
        self.base_url = "http://localhost:6003"
        self.timeout = 15

    def test_real_world_scenario(self):
        """실제 사용 시나리오 테스트"""

        # 시나리오: 개발팀 리더가 다음 스프린트를 계획하는 상황

        # 1. 먼저 제품 백로그를 확인하여 전체 상황 파악
        response = requests.get(f"{self.base_url}/recommendations/backlog", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)

        backlog_data = response.json()['data']
        total_tickets = backlog_data['statistics']['total_tickets']
        self.assertGreater(total_tickets, 0)

        # 2. 현재 Critical/High 우선순위 작업 확인
        response = requests.get(
            f"{self.base_url}/recommendations/tickets?priority_filter=critical&count=10",
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 200)

        critical_tickets = response.json()['data']['tickets']

        response = requests.get(
            f"{self.base_url}/recommendations/tickets?priority_filter=high&count=10",
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 200)

        high_tickets = response.json()['data']['tickets']

        # 3. OCR 관련 작업만 별도로 확인
        response = requests.get(
            f"{self.base_url}/recommendations/tickets?focus_area=ocr&count=15",
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 200)

        ocr_tickets = response.json()['data']['tickets']

        # 4. 5명 팀으로 40 SP 용량의 스프린트 계획
        response = requests.get(
            f"{self.base_url}/recommendations/sprint?capacity=40&team_size=5",
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 200)

        sprint_plan = response.json()['data']

        # 검증: 스프린트 계획이 합리적인지 확인
        self.assertLessEqual(sprint_plan['allocated_points'], sprint_plan['capacity'])
        self.assertGreater(len(sprint_plan['tickets']), 0)

        # 5. 스프린트에 포함된 티켓들의 우선순위 분포 확인
        sprint_tickets = sprint_plan['tickets']
        priorities = [ticket['priority'] for ticket in sprint_tickets]

        # Critical이나 High 우선순위 티켓이 포함되어 있는지 확인
        high_priority_count = priorities.count('critical') + priorities.count('high')
        self.assertGreater(high_priority_count, 0, "스프린트에 높은 우선순위 티켓이 포함되어야 함")

    def test_api_documentation_scenario(self):
        """API 문서화 시나리오 테스트"""

        # 시나리오: API 문서 작성을 위해 모든 엔드포인트 확인

        endpoints_to_test = [
            ("/recommendations/tickets", {"count": 3}),
            ("/recommendations/tickets", {"focus_area": "performance", "count": 5}),
            ("/recommendations/sprint", {"capacity": 30}),
            ("/recommendations/backlog", {}),
            ("/recommendations/focus-areas", {}),
            ("/recommendations/metrics", {})
        ]

        for endpoint, params in endpoints_to_test:
            response = requests.get(
                self.base_url + endpoint,
                params=params,
                timeout=self.timeout
            )

            self.assertEqual(response.status_code, 200, f"Endpoint {endpoint} failed")

            # JSON 응답 형식 확인
            try:
                data = response.json()
                self.assertIn('status', data)
                self.assertEqual(data['status'], 'success')
            except json.JSONDecodeError:
                self.fail(f"Invalid JSON response from {endpoint}")

if __name__ == '__main__':
    # 통합 테스트는 실행 중인 서버가 필요함을 알림
    print("=== 추천 시스템 통합 테스트 ===")
    print("주의: 이 테스트는 localhost:6003에서 실행 중인 서버가 필요합니다.")
    print("서버를 먼저 실행한 후 테스트를 수행하세요.")
    print()

    unittest.main()