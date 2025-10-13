#!/usr/bin/env python3
"""
추천 시스템 성능 테스트
"""

import unittest
import time
import statistics
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import memory_profiler
import psutil

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.recommendations.ticket_generator import TicketRecommendationEngine
from fastapi.testclient import TestClient
from api_server import app

class TestRecommendationEnginePerformance(unittest.TestCase):
    """추천 엔진 성능 테스트"""

    def setUp(self):
        self.engine = TicketRecommendationEngine()

    def test_basic_recommendation_performance(self):
        """기본 추천 성능 테스트"""

        # 다양한 개수로 성능 측정
        test_counts = [1, 5, 10, 20, 50]
        results = {}

        for count in test_counts:
            times = []

            # 10회 반복 측정
            for _ in range(10):
                start_time = time.time()
                recommendations = self.engine.generate_recommendations(count=count)
                end_time = time.time()

                self.assertEqual(len(recommendations), min(count, len(self.engine.ocr_tasks) + len(self.engine.general_tasks)))
                times.append(end_time - start_time)

            avg_time = statistics.mean(times)
            max_time = max(times)
            min_time = min(times)

            results[count] = {
                'avg_time': avg_time,
                'max_time': max_time,
                'min_time': min_time,
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0
            }

            # 성능 기준: 평균 100ms 이내
            self.assertLess(avg_time, 0.1, f"Count {count}: Average time {avg_time:.3f}s exceeds 100ms")

            # 최대 시간: 500ms 이내
            self.assertLess(max_time, 0.5, f"Count {count}: Max time {max_time:.3f}s exceeds 500ms")

        # 결과 출력
        print("\n=== 기본 추천 성능 결과 ===")
        for count, result in results.items():
            print(f"Count {count:2d}: Avg={result['avg_time']*1000:.1f}ms, "
                  f"Max={result['max_time']*1000:.1f}ms, "
                  f"Min={result['min_time']*1000:.1f}ms, "
                  f"StdDev={result['std_dev']*1000:.1f}ms")

    def test_sprint_recommendation_performance(self):
        """스프린트 추천 성능 테스트"""

        test_capacities = [20, 40, 60, 80, 100]
        results = {}

        for capacity in test_capacities:
            times = []

            # 5회 반복 측정
            for _ in range(5):
                start_time = time.time()
                sprint_plan = self.engine.generate_sprint_recommendations(sprint_capacity=capacity)
                end_time = time.time()

                # 용량 제약 확인
                self.assertLessEqual(sprint_plan['allocated_points'], capacity)
                times.append(end_time - start_time)

            avg_time = statistics.mean(times)
            max_time = max(times)

            results[capacity] = {
                'avg_time': avg_time,
                'max_time': max_time
            }

            # 성능 기준: 평균 200ms 이내
            self.assertLess(avg_time, 0.2, f"Capacity {capacity}: Average time {avg_time:.3f}s exceeds 200ms")

        print("\n=== 스프린트 추천 성능 결과 ===")
        for capacity, result in results.items():
            print(f"Capacity {capacity:3d}: Avg={result['avg_time']*1000:.1f}ms, "
                  f"Max={result['max_time']*1000:.1f}ms")

    def test_focus_area_filtering_performance(self):
        """집중 영역 필터링 성능 테스트"""

        focus_areas = ['ocr', 'performance', 'security', 'api', 'nonexistent']
        results = {}

        for area in focus_areas:
            times = []

            # 5회 반복 측정
            for _ in range(5):
                start_time = time.time()
                recommendations = self.engine.generate_recommendations(count=20, focus_area=area)
                end_time = time.time()

                times.append(end_time - start_time)

            avg_time = statistics.mean(times)
            result_count = len(recommendations)

            results[area] = {
                'avg_time': avg_time,
                'result_count': result_count
            }

            # 성능 기준: 평균 150ms 이내
            self.assertLess(avg_time, 0.15, f"Focus area {area}: Average time {avg_time:.3f}s exceeds 150ms")

        print("\n=== 집중 영역 필터링 성능 결과 ===")
        for area, result in results.items():
            print(f"Area {area:12s}: Avg={result['avg_time']*1000:.1f}ms, "
                  f"Results={result['result_count']:2d}")

    def test_memory_usage(self):
        """메모리 사용량 테스트"""

        # 메모리 사용량 측정 함수
        def measure_memory():
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB

        initial_memory = measure_memory()

        # 대량 추천 생성
        for _ in range(100):
            self.engine.generate_recommendations(count=10)

        # 스프린트 계획 생성
        for capacity in range(20, 101, 10):
            self.engine.generate_sprint_recommendations(sprint_capacity=capacity)

        final_memory = measure_memory()
        memory_increase = final_memory - initial_memory

        print(f"\n=== 메모리 사용량 결과 ===")
        print(f"초기 메모리: {initial_memory:.1f}MB")
        print(f"최종 메모리: {final_memory:.1f}MB")
        print(f"메모리 증가: {memory_increase:.1f}MB")

        # 메모리 증가가 50MB 이내인지 확인
        self.assertLess(memory_increase, 50, f"Memory increase {memory_increase:.1f}MB exceeds 50MB")

    def test_concurrent_access_performance(self):
        """동시 접근 성능 테스트"""

        def generate_recommendations():
            start_time = time.time()
            recommendations = self.engine.generate_recommendations(count=5)
            end_time = time.time()
            return {
                'duration': end_time - start_time,
                'count': len(recommendations)
            }

        # 10개 스레드로 동시 실행
        num_threads = 10
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(generate_recommendations) for _ in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time

        # 결과 분석
        durations = [result['duration'] for result in results]
        avg_duration = statistics.mean(durations)
        max_duration = max(durations)

        print(f"\n=== 동시 접근 성능 결과 ===")
        print(f"총 스레드: {num_threads}")
        print(f"총 시간: {total_time:.3f}s")
        print(f"평균 개별 시간: {avg_duration:.3f}s")
        print(f"최대 개별 시간: {max_duration:.3f}s")
        print(f"처리량: {num_threads/total_time:.1f} 요청/초")

        # 성능 기준
        self.assertLess(total_time, 5.0, f"Total time {total_time:.3f}s exceeds 5s")
        self.assertLess(avg_duration, 1.0, f"Average duration {avg_duration:.3f}s exceeds 1s")

class TestAPIPerformance(unittest.TestCase):
    """API 성능 테스트"""

    def setUp(self):
        self.client = TestClient(app)

    def test_api_response_times(self):
        """API 응답 시간 테스트"""

        endpoints = [
            ("/recommendations/tickets", {"count": 5}),
            ("/recommendations/tickets", {"focus_area": "ocr", "count": 3}),
            ("/recommendations/sprint", {"capacity": 30}),
            ("/recommendations/backlog", {}),
            ("/recommendations/focus-areas", {}),
            ("/recommendations/metrics", {})
        ]

        results = {}

        for endpoint, params in endpoints:
            times = []

            # 각 엔드포인트를 5회 호출
            for _ in range(5):
                start_time = time.time()
                response = self.client.get(endpoint, params=params)
                end_time = time.time()

                self.assertEqual(response.status_code, 200)
                times.append(end_time - start_time)

            avg_time = statistics.mean(times)
            max_time = max(times)
            min_time = min(times)

            results[endpoint] = {
                'avg_time': avg_time,
                'max_time': max_time,
                'min_time': min_time
            }

            # 성능 기준: 평균 1초 이내
            self.assertLess(avg_time, 1.0, f"Endpoint {endpoint}: Average time {avg_time:.3f}s exceeds 1s")

        print("\n=== API 응답 시간 결과 ===")
        for endpoint, result in results.items():
            print(f"{endpoint:30s}: Avg={result['avg_time']*1000:.0f}ms, "
                  f"Max={result['max_time']*1000:.0f}ms, "
                  f"Min={result['min_time']*1000:.0f}ms")

    def test_api_throughput(self):
        """API 처리량 테스트"""

        def make_request():
            start_time = time.time()
            response = self.client.get("/recommendations/tickets", params={"count": 3})
            end_time = time.time()
            return {
                'success': response.status_code == 200,
                'duration': end_time - start_time
            }

        # 순차적 요청 처리량 측정
        num_requests = 20
        start_time = time.time()

        sequential_results = []
        for _ in range(num_requests):
            result = make_request()
            sequential_results.append(result)

        sequential_time = time.time() - start_time
        sequential_throughput = num_requests / sequential_time

        # 병렬 요청 처리량 측정
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            parallel_futures = [executor.submit(make_request) for _ in range(num_requests)]
            parallel_results = [future.result() for future in as_completed(parallel_futures)]

        parallel_time = time.time() - start_time
        parallel_throughput = num_requests / parallel_time

        print(f"\n=== API 처리량 결과 ===")
        print(f"순차 처리: {sequential_throughput:.1f} 요청/초 ({sequential_time:.3f}s)")
        print(f"병렬 처리: {parallel_throughput:.1f} 요청/초 ({parallel_time:.3f}s)")
        print(f"병렬 처리 향상도: {parallel_throughput/sequential_throughput:.1f}x")

        # 성능 기준
        self.assertGreater(sequential_throughput, 5.0, "Sequential throughput should be > 5 req/s")
        self.assertGreater(parallel_throughput, 10.0, "Parallel throughput should be > 10 req/s")

    def test_large_request_performance(self):
        """대용량 요청 성능 테스트"""

        large_counts = [30, 40, 50]

        for count in large_counts:
            start_time = time.time()
            response = self.client.get("/recommendations/tickets", params={"count": count})
            end_time = time.time()

            duration = end_time - start_time

            self.assertEqual(response.status_code, 200)

            data = response.json()
            actual_count = len(data['data']['tickets'])

            print(f"\n대용량 요청 (count={count}): {duration:.3f}s, 실제 반환={actual_count}")

            # 성능 기준: 2초 이내
            self.assertLess(duration, 2.0, f"Large request (count={count}) took {duration:.3f}s > 2s")

class TestPerformanceBenchmark(unittest.TestCase):
    """성능 벤치마크 테스트"""

    def setUp(self):
        self.engine = TicketRecommendationEngine()
        self.client = TestClient(app)

    def test_comprehensive_benchmark(self):
        """종합 성능 벤치마크"""

        benchmark_results = {}

        # 1. 기본 추천 성능
        start_time = time.time()
        for _ in range(100):
            self.engine.generate_recommendations(count=10)
        benchmark_results['basic_recommendations'] = time.time() - start_time

        # 2. 스프린트 계획 성능
        start_time = time.time()
        for capacity in range(20, 101, 10):
            self.engine.generate_sprint_recommendations(sprint_capacity=capacity)
        benchmark_results['sprint_planning'] = time.time() - start_time

        # 3. API 호출 성능
        start_time = time.time()
        for _ in range(50):
            response = self.client.get("/recommendations/tickets", params={"count": 5})
            self.assertEqual(response.status_code, 200)
        benchmark_results['api_calls'] = time.time() - start_time

        # 4. 복합 시나리오 성능
        start_time = time.time()
        for _ in range(10):
            # 다양한 작업을 순차적으로 수행
            self.engine.generate_recommendations(count=5)
            self.engine.generate_recommendations(count=10, focus_area="ocr")
            self.engine.generate_sprint_recommendations(sprint_capacity=40)
        benchmark_results['complex_scenario'] = time.time() - start_time

        print("\n=== 종합 성능 벤치마크 결과 ===")
        print(f"기본 추천 (100회): {benchmark_results['basic_recommendations']:.3f}s")
        print(f"스프린트 계획 (9회): {benchmark_results['sprint_planning']:.3f}s")
        print(f"API 호출 (50회): {benchmark_results['api_calls']:.3f}s")
        print(f"복합 시나리오 (10회): {benchmark_results['complex_scenario']:.3f}s")

        # 성능 기준
        self.assertLess(benchmark_results['basic_recommendations'], 5.0)
        self.assertLess(benchmark_results['sprint_planning'], 3.0)
        self.assertLess(benchmark_results['api_calls'], 10.0)
        self.assertLess(benchmark_results['complex_scenario'], 5.0)

if __name__ == '__main__':
    print("=== 추천 시스템 성능 테스트 ===")
    print("이 테스트는 성능 메트릭을 측정하고 기준을 검증합니다.")
    print()

    unittest.main(verbosity=2)