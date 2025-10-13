#!/usr/bin/env python3
"""
추천 시스템 단위 테스트
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.recommendations.ticket_generator import (
    TicketRecommendationEngine,
    TicketType,
    Priority,
    get_recommendations,
    get_sprint_recommendations
)

class TestTicketRecommendationEngine(unittest.TestCase):
    """티켓 추천 엔진 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.engine = TicketRecommendationEngine()

    def test_engine_initialization(self):
        """엔진 초기화 테스트"""
        self.assertIsInstance(self.engine, TicketRecommendationEngine)
        self.assertGreater(len(self.engine.ocr_tasks), 0)
        self.assertGreater(len(self.engine.general_tasks), 0)
        self.assertEqual(self.engine.counter, 1000)

    def test_generate_recommendations_basic(self):
        """기본 추천 생성 테스트"""
        recommendations = self.engine.generate_recommendations(count=5)

        self.assertEqual(len(recommendations), 5)

        for ticket in recommendations:
            self.assertIn('ticket_id', ticket)
            self.assertIn('title', ticket)
            self.assertIn('description', ticket)
            self.assertIn('type', ticket)
            self.assertIn('priority', ticket)
            self.assertIn('story_points', ticket)

            # 티켓 ID 형식 확인
            self.assertTrue(ticket['ticket_id'].startswith('OCR-'))

            # 유효한 타입인지 확인
            self.assertIn(ticket['type'], [t.value for t in TicketType])

            # 유효한 우선순위인지 확인
            self.assertIn(ticket['priority'], [p.value for p in Priority])

            # 스토리 포인트가 양수인지 확인
            self.assertGreater(ticket['story_points'], 0)

    def test_generate_recommendations_count_limit(self):
        """개수 제한 테스트"""
        # 최대 가능한 개수보다 많이 요청
        total_tasks = len(self.engine.ocr_tasks) + len(self.engine.general_tasks)
        recommendations = self.engine.generate_recommendations(count=total_tasks + 10)

        # 실제 가능한 개수만큼만 반환되어야 함
        self.assertLessEqual(len(recommendations), total_tasks)

    def test_generate_recommendations_with_focus_area(self):
        """집중 영역 필터링 테스트"""
        recommendations = self.engine.generate_recommendations(count=10, focus_area="ocr")

        self.assertGreater(len(recommendations), 0)

        # 모든 티켓이 OCR 관련인지 확인
        for ticket in recommendations:
            labels = ticket.get('labels', [])
            self.assertTrue(
                any('ocr' in str(label).lower() for label in labels) or
                'ocr' in ticket['title'].lower() or
                'ocr' in ticket['description'].lower()
            )

    def test_create_ticket(self):
        """티켓 생성 테스트"""
        task_template = {
            "title": "테스트 티켓",
            "description": "테스트용 티켓 설명",
            "type": TicketType.FEATURE,
            "priority": Priority.HIGH,
            "story_points": 5,
            "labels": ["test", "unit"],
            "assignee": "Test Engineer",
            "component": "Testing"
        }

        ticket = self.engine._create_ticket(task_template)

        self.assertEqual(ticket['title'], "테스트 티켓")
        self.assertEqual(ticket['type'], "feature")
        self.assertEqual(ticket['priority'], "high")
        self.assertEqual(ticket['story_points'], 5)
        self.assertEqual(ticket['estimated_hours'], 20)  # 5 * 4
        self.assertEqual(ticket['assignee'], "Test Engineer")
        self.assertEqual(ticket['status'], "TO DO")
        self.assertIn('ticket_id', ticket)
        self.assertIn('created_date', ticket)
        self.assertIn('due_date', ticket)

    def test_generate_sprint_recommendations(self):
        """스프린트 추천 테스트"""
        sprint_plan = self.engine.generate_sprint_recommendations(sprint_capacity=30)

        self.assertIn('sprint_name', sprint_plan)
        self.assertIn('capacity', sprint_plan)
        self.assertIn('allocated_points', sprint_plan)
        self.assertIn('remaining_capacity', sprint_plan)
        self.assertIn('tickets', sprint_plan)
        self.assertIn('summary', sprint_plan)

        # 용량 확인
        self.assertEqual(sprint_plan['capacity'], 30)
        self.assertLessEqual(sprint_plan['allocated_points'], 30)
        self.assertGreaterEqual(sprint_plan['remaining_capacity'], 0)

        # 할당된 포인트 검증
        total_points = sum(ticket['story_points'] for ticket in sprint_plan['tickets'])
        self.assertEqual(sprint_plan['allocated_points'], total_points)

    def test_priority_sorting_in_sprint(self):
        """스프린트에서 우선순위 정렬 테스트"""
        sprint_plan = self.engine.generate_sprint_recommendations(sprint_capacity=40)
        tickets = sprint_plan['tickets']

        if len(tickets) > 1:
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}

            for i in range(len(tickets) - 1):
                current_priority = priority_order.get(tickets[i]['priority'], 4)
                next_priority = priority_order.get(tickets[i + 1]['priority'], 4)
                self.assertLessEqual(current_priority, next_priority)

    def test_count_methods(self):
        """집계 메서드 테스트"""
        sample_tickets = [
            {'priority': 'high', 'type': 'bug', 'assignee': 'Dev A'},
            {'priority': 'high', 'type': 'feature', 'assignee': 'Dev A'},
            {'priority': 'medium', 'type': 'bug', 'assignee': 'Dev B'}
        ]

        priority_counts = self.engine._count_by_priority(sample_tickets)
        type_counts = self.engine._count_by_type(sample_tickets)
        assignee_counts = self.engine._count_by_assignee(sample_tickets)

        self.assertEqual(priority_counts['high'], 2)
        self.assertEqual(priority_counts['medium'], 1)

        self.assertEqual(type_counts['bug'], 2)
        self.assertEqual(type_counts['feature'], 1)

        self.assertEqual(assignee_counts['Dev A'], 2)
        self.assertEqual(assignee_counts['Dev B'], 1)

    def test_convenience_functions(self):
        """편의 함수 테스트"""
        # get_recommendations 함수 테스트
        recommendations = get_recommendations(count=3)
        self.assertEqual(len(recommendations), 3)

        # get_sprint_recommendations 함수 테스트
        sprint_plan = get_sprint_recommendations(capacity=25)
        self.assertIn('tickets', sprint_plan)
        self.assertEqual(sprint_plan['capacity'], 25)

    def test_ticket_id_increment(self):
        """티켓 ID 증분 테스트"""
        initial_counter = self.engine.counter

        recommendations = self.engine.generate_recommendations(count=3)

        # 카운터가 증가했는지 확인
        self.assertEqual(self.engine.counter, initial_counter + 3)

        # 티켓 ID가 순차적인지 확인
        ticket_ids = [int(ticket['ticket_id'].split('-')[1]) for ticket in recommendations]
        for i in range(len(ticket_ids) - 1):
            self.assertEqual(ticket_ids[i + 1], ticket_ids[i] + 1)

    def test_invalid_focus_area(self):
        """존재하지 않는 집중 영역 테스트"""
        recommendations = self.engine.generate_recommendations(count=10, focus_area="nonexistent")

        # 해당하는 티켓이 없으면 빈 리스트 반환
        self.assertEqual(len(recommendations), 0)

    def test_zero_capacity_sprint(self):
        """용량 0인 스프린트 테스트"""
        sprint_plan = self.engine.generate_sprint_recommendations(sprint_capacity=0)

        self.assertEqual(sprint_plan['capacity'], 0)
        self.assertEqual(sprint_plan['allocated_points'], 0)
        self.assertEqual(len(sprint_plan['tickets']), 0)

class TestTicketValidation(unittest.TestCase):
    """티켓 유효성 검증 테스트"""

    def setUp(self):
        self.engine = TicketRecommendationEngine()

    def test_all_ocr_tasks_valid(self):
        """모든 OCR 작업의 유효성 테스트"""
        for task in self.engine.ocr_tasks:
            self.assertIn('title', task)
            self.assertIn('description', task)
            self.assertIn('type', task)
            self.assertIn('priority', task)
            self.assertIn('story_points', task)
            self.assertIn('labels', task)
            self.assertIn('assignee', task)
            self.assertIn('component', task)

            # 타입과 우선순위가 유효한 Enum 값인지 확인
            self.assertIsInstance(task['type'], TicketType)
            self.assertIsInstance(task['priority'], Priority)

            # 스토리 포인트가 양수인지 확인
            self.assertGreater(task['story_points'], 0)

            # 라벨이 리스트인지 확인
            self.assertIsInstance(task['labels'], list)

    def test_all_general_tasks_valid(self):
        """모든 일반 작업의 유효성 테스트"""
        for task in self.engine.general_tasks:
            self.assertIn('title', task)
            self.assertIn('description', task)
            self.assertIn('type', task)
            self.assertIn('priority', task)
            self.assertIn('story_points', task)
            self.assertIn('labels', task)
            self.assertIn('assignee', task)
            self.assertIn('component', task)

            # 타입과 우선순위가 유효한 Enum 값인지 확인
            self.assertIsInstance(task['type'], TicketType)
            self.assertIsInstance(task['priority'], Priority)

    def test_task_diversity(self):
        """작업 다양성 테스트"""
        all_tasks = self.engine.ocr_tasks + self.engine.general_tasks

        # 다양한 타입이 있는지 확인
        types = set(task['type'] for task in all_tasks)
        self.assertGreaterEqual(len(types), 3)

        # 다양한 우선순위가 있는지 확인
        priorities = set(task['priority'] for task in all_tasks)
        self.assertGreaterEqual(len(priorities), 3)

        # 다양한 담당자가 있는지 확인
        assignees = set(task['assignee'] for task in all_tasks)
        self.assertGreaterEqual(len(assignees), 3)

if __name__ == '__main__':
    unittest.main()