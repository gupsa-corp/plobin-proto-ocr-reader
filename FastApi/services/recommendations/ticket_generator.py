#!/usr/bin/env python3
"""
개발 작업 추천 시스템 (지라 티켓 스타일)
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum

class TicketType(Enum):
    """티켓 유형"""
    FEATURE = "feature"
    BUG = "bug"
    IMPROVEMENT = "improvement"
    TASK = "task"
    RESEARCH = "research"

class Priority(Enum):
    """우선순위"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TicketRecommendationEngine:
    """개발 작업 추천 엔진"""

    def __init__(self):
        self.ocr_tasks = self._initialize_ocr_tasks()
        self.general_tasks = self._initialize_general_tasks()
        self.counter = 1000  # 티켓 번호 시작

    def _initialize_ocr_tasks(self) -> List[Dict]:
        """OCR 관련 작업 템플릿"""
        return [
            {
                "title": "PP-OCRv5 JSON 직렬화 오류 수정",
                "description": "PP-OCRv5 API에서 numpy.int64 타입으로 인한 JSON 직렬화 오류를 수정합니다.\n\n**현상:**\n- `/ppocrv5/process-image` 호출 시 'Object of type int64 is not JSON serializable' 오류\n- OCR 결과의 좌표값이 numpy 타입으로 반환됨\n\n**해결방안:**\n- numpy 타입을 Python 기본 타입으로 변환하는 헬퍼 함수 추가\n- JSON 응답 전 타입 변환 로직 적용",
                "type": TicketType.BUG,
                "priority": Priority.HIGH,
                "story_points": 3,
                "labels": ["ocr", "json", "ppocrv5", "serialization"],
                "assignee": "Backend Developer",
                "component": "OCR Service"
            },
            {
                "title": "한글 OCR 정확도 벤치마크 자동화",
                "description": "한글 OCR 시스템의 정확도를 자동으로 측정하고 리포트하는 벤치마크 시스템을 구축합니다.\n\n**요구사항:**\n- 다양한 한글 문서 샘플 테스트 세트 구성\n- 정확도 측정 메트릭 (CER, WER) 자동 계산\n- 버전별 성능 비교 기능\n- 일일/주간 자동 벤치마크 실행\n- 성능 저하 시 알림 기능",
                "type": TicketType.FEATURE,
                "priority": Priority.MEDIUM,
                "story_points": 8,
                "labels": ["korean", "benchmark", "automation", "testing"],
                "assignee": "QA Engineer",
                "component": "Testing Framework"
            },
            {
                "title": "TensorRT 환경 구성 가이드 작성",
                "description": "TensorRT 가속화 기능 사용을 위한 환경 구성 가이드를 작성합니다.\n\n**포함 내용:**\n- CUDA/cuDNN 설치 가이드\n- TensorRT 라이브러리 설치 방법\n- 환경 변수 설정\n- 트러블슈팅 가이드\n- 성능 최적화 팁\n- Docker 환경 설정 예제",
                "type": TicketType.TASK,
                "priority": Priority.MEDIUM,
                "story_points": 5,
                "labels": ["tensorrt", "documentation", "setup", "performance"],
                "assignee": "DevOps Engineer",
                "component": "Documentation"
            },
            {
                "title": "OCR 결과 캐싱 시스템 개선",
                "description": "현재 OCR 캐싱 시스템을 개선하여 메모리 효율성과 속도를 향상시킵니다.\n\n**개선사항:**\n- Redis 기반 분산 캐시 도입\n- LRU 캐시 정책 적용\n- 캐시 만료 시간 최적화\n- 캐시 히트율 모니터링\n- 캐시 워밍업 기능\n- 캐시 무효화 전략 개선",
                "type": TicketType.IMPROVEMENT,
                "priority": Priority.HIGH,
                "story_points": 13,
                "labels": ["cache", "redis", "performance", "optimization"],
                "assignee": "Backend Developer",
                "component": "Caching Layer"
            },
            {
                "title": "도메인 특화 OCR 모델 파인튜닝 프레임워크",
                "description": "특정 도메인(의료, 법률, 금융 등)에 최적화된 OCR 모델을 생성할 수 있는 파인튜닝 프레임워크를 개발합니다.\n\n**기능:**\n- 커스텀 데이터셋 업로드 및 라벨링\n- 자동 데이터 증강 (Data Augmentation)\n- 파인튜닝 진행상황 모니터링\n- 모델 성능 평가 및 비교\n- 프로덕션 배포 자동화\n- A/B 테스트 지원",
                "type": TicketType.FEATURE,
                "priority": Priority.HIGH,
                "story_points": 21,
                "labels": ["finetuning", "ai", "domain-specific", "framework"],
                "assignee": "ML Engineer",
                "component": "AI/ML Pipeline"
            },
            {
                "title": "OCR 결과 후처리 규칙 엔진",
                "description": "OCR 결과에 적용할 수 있는 규칙 기반 후처리 엔진을 개발합니다.\n\n**기능:**\n- 사용자 정의 후처리 규칙 작성 (정규식, 사전 기반)\n- 규칙 우선순위 및 적용 순서 관리\n- 규칙 효과 A/B 테스트\n- 규칙 성능 분석 대시보드\n- 업종별 기본 규칙 세트 제공\n- 규칙 버전 관리",
                "type": TicketType.FEATURE,
                "priority": Priority.MEDIUM,
                "story_points": 13,
                "labels": ["postprocessing", "rules-engine", "customizable"],
                "assignee": "Backend Developer",
                "component": "Post-processing"
            },
            {
                "title": "실시간 OCR 스트리밍 API",
                "description": "실시간으로 이미지를 스트리밍하여 OCR 처리할 수 있는 WebSocket 기반 API를 개발합니다.\n\n**기능:**\n- WebSocket 기반 실시간 이미지 스트림 처리\n- 프레임별 OCR 결과 실시간 반환\n- 연결 상태 관리 및 재연결 로직\n- 클라이언트별 세션 관리\n- 처리량 제한 및 큐잉\n- 실시간 성능 모니터링",
                "type": TicketType.FEATURE,
                "priority": Priority.LOW,
                "story_points": 21,
                "labels": ["websocket", "realtime", "streaming", "api"],
                "assignee": "Backend Developer",
                "component": "Real-time API"
            },
            {
                "title": "OCR 품질 점수 알고리즘 개발",
                "description": "OCR 결과의 품질을 자동으로 평가하는 점수 알고리즘을 개발합니다.\n\n**평가 요소:**\n- 문자 인식 신뢰도\n- 레이아웃 구조 정확성\n- 텍스트 일관성 (맞춤법, 문법)\n- 이미지 품질 (해상도, 노이즈)\n- 도메인별 특성 반영\n- 종합 품질 점수 (0-100점)",
                "type": TicketType.RESEARCH,
                "priority": Priority.MEDIUM,
                "story_points": 8,
                "labels": ["quality", "algorithm", "scoring", "ml"],
                "assignee": "ML Engineer",
                "component": "Quality Assessment"
            }
        ]

    def _initialize_general_tasks(self) -> List[Dict]:
        """일반 개발 작업 템플릿"""
        return [
            {
                "title": "API 문서 자동 생성 시스템 구축",
                "description": "FastAPI의 OpenAPI 스펙을 활용하여 자동으로 API 문서를 생성하고 배포하는 시스템을 구축합니다.\n\n**기능:**\n- Swagger UI 커스터마이징\n- API 예제 코드 자동 생성\n- 다국어 문서 지원\n- 버전별 문서 관리\n- 변경사항 자동 알림",
                "type": TicketType.IMPROVEMENT,
                "priority": Priority.MEDIUM,
                "story_points": 5,
                "labels": ["documentation", "api", "automation", "swagger"],
                "assignee": "Frontend Developer",
                "component": "Documentation"
            },
            {
                "title": "마이크로서비스 헬스체크 대시보드",
                "description": "모든 마이크로서비스의 상태를 실시간으로 모니터링할 수 있는 대시보드를 개발합니다.\n\n**기능:**\n- 서비스별 상태 표시 (UP/DOWN/DEGRADED)\n- 응답시간 및 처리량 메트릭\n- 알림 및 에스컬레이션 규칙\n- 과거 장애 이력 조회\n- 의존성 그래프 시각화",
                "type": TicketType.FEATURE,
                "priority": Priority.HIGH,
                "story_points": 13,
                "labels": ["monitoring", "dashboard", "microservices", "health"],
                "assignee": "DevOps Engineer",
                "component": "Monitoring"
            },
            {
                "title": "데이터베이스 백업 자동화",
                "description": "프로덕션 데이터베이스의 정기 백업을 자동화하고 복구 절차를 표준화합니다.\n\n**기능:**\n- 일일/주간 자동 백업\n- 백업 파일 암호화\n- 클라우드 스토리지 연동\n- 백업 무결성 검증\n- 원클릭 복구 시스템\n- 백업 보관 정책 관리",
                "type": TicketType.TASK,
                "priority": Priority.HIGH,
                "story_points": 8,
                "labels": ["database", "backup", "automation", "recovery"],
                "assignee": "DevOps Engineer",
                "component": "Database"
            },
            {
                "title": "사용자 인증 시스템 보안 강화",
                "description": "현재 사용자 인증 시스템의 보안을 강화하고 최신 보안 표준을 적용합니다.\n\n**보안 강화 사항:**\n- OAuth 2.0 / OpenID Connect 도입\n- 다중 인증 (MFA) 지원\n- JWT 토큰 보안 강화\n- 세션 관리 개선\n- 비밀번호 정책 강화\n- 보안 감사 로그",
                "type": TicketType.IMPROVEMENT,
                "priority": Priority.CRITICAL,
                "story_points": 13,
                "labels": ["security", "authentication", "oauth", "mfa"],
                "assignee": "Security Engineer",
                "component": "Authentication"
            },
            {
                "title": "CI/CD 파이프라인 최적화",
                "description": "현재 CI/CD 파이프라인을 최적화하여 빌드 시간을 단축하고 안정성을 향상시킵니다.\n\n**최적화 방안:**\n- 병렬 빌드 및 테스트 실행\n- Docker 레이어 캐싱 최적화\n- 테스트 커버리지 자동 체크\n- 자동 롤백 메커니즘\n- 배포 승인 워크플로우\n- 성능 테스트 자동화",
                "type": TicketType.IMPROVEMENT,
                "priority": Priority.MEDIUM,
                "story_points": 8,
                "labels": ["cicd", "optimization", "automation", "testing"],
                "assignee": "DevOps Engineer",
                "component": "CI/CD"
            },
            {
                "title": "로그 중앙화 시스템 구축",
                "description": "마이크로서비스들의 로그를 중앙에서 수집, 분석할 수 있는 시스템을 구축합니다.\n\n**기능:**\n- ELK Stack (Elasticsearch, Logstash, Kibana) 구축\n- 구조화된 로깅 표준 정의\n- 실시간 로그 모니터링\n- 로그 기반 알림 시스템\n- 로그 보관 정책 관리\n- 보안 로그 분석",
                "type": TicketType.FEATURE,
                "priority": Priority.MEDIUM,
                "story_points": 13,
                "labels": ["logging", "elk", "monitoring", "centralization"],
                "assignee": "DevOps Engineer",
                "component": "Logging"
            },
            {
                "title": "API 응답 캐싱 전략 수립",
                "description": "API 성능 향상을 위한 응답 캐싱 전략을 수립하고 구현합니다.\n\n**캐싱 전략:**\n- HTTP 캐시 헤더 최적화\n- CDN 레벨 캐싱\n- 애플리케이션 레벨 캐싱\n- 캐시 무효화 전략\n- 캐시 성능 모니터링\n- A/B 테스트를 통한 효과 검증",
                "type": TicketType.IMPROVEMENT,
                "priority": Priority.MEDIUM,
                "story_points": 8,
                "labels": ["caching", "performance", "api", "optimization"],
                "assignee": "Backend Developer",
                "component": "API Gateway"
            }
        ]

    def generate_recommendations(self, count: int = 10, focus_area: Optional[str] = None) -> List[Dict]:
        """추천 작업 생성"""
        all_tasks = self.ocr_tasks + self.general_tasks

        # 특정 영역에 집중하는 경우
        if focus_area:
            all_tasks = [task for task in all_tasks if focus_area.lower() in str(task.get("labels", []))]

        # 랜덤하게 선택
        selected_tasks = random.sample(all_tasks, min(count, len(all_tasks)))

        # 티켓 정보 생성
        recommendations = []
        for task in selected_tasks:
            ticket = self._create_ticket(task)
            recommendations.append(ticket)

        return recommendations

    def _create_ticket(self, task_template: Dict) -> Dict:
        """티켓 정보 생성"""
        self.counter += 1

        # 예상 완료일 계산 (스토리 포인트 기반)
        story_points = task_template.get("story_points", 5)
        estimated_days = story_points * 0.5  # 1 SP = 0.5일
        due_date = datetime.now() + timedelta(days=estimated_days)

        return {
            "ticket_id": f"OCR-{self.counter}",
            "title": task_template["title"],
            "description": task_template["description"],
            "type": task_template["type"].value,
            "priority": task_template["priority"].value,
            "status": "TO DO",
            "story_points": story_points,
            "estimated_hours": story_points * 4,  # 1 SP = 4시간
            "labels": task_template["labels"],
            "assignee": task_template["assignee"],
            "component": task_template["component"],
            "created_date": datetime.now().isoformat(),
            "due_date": due_date.isoformat(),
            "reporter": "System",
            "sprint": f"Sprint {random.randint(1, 10)}",
            "epic": "OCR Platform Enhancement"
        }

    def generate_sprint_recommendations(self, sprint_capacity: int = 40) -> Dict:
        """스프린트용 추천 작업 생성"""
        all_recommendations = self.generate_recommendations(20)

        # 우선순위별로 정렬
        priority_order = {
            Priority.CRITICAL.value: 0,
            Priority.HIGH.value: 1,
            Priority.MEDIUM.value: 2,
            Priority.LOW.value: 3
        }

        all_recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))

        # 스프린트 용량에 맞게 선택
        selected_tickets = []
        total_points = 0

        for ticket in all_recommendations:
            if total_points + ticket["story_points"] <= sprint_capacity:
                selected_tickets.append(ticket)
                total_points += ticket["story_points"]

            if total_points >= sprint_capacity:
                break

        return {
            "sprint_name": f"Sprint {random.randint(10, 50)}",
            "capacity": sprint_capacity,
            "allocated_points": total_points,
            "remaining_capacity": sprint_capacity - total_points,
            "tickets": selected_tickets,
            "summary": {
                "total_tickets": len(selected_tickets),
                "by_priority": self._count_by_priority(selected_tickets),
                "by_type": self._count_by_type(selected_tickets),
                "by_assignee": self._count_by_assignee(selected_tickets)
            }
        }

    def _count_by_priority(self, tickets: List[Dict]) -> Dict:
        """우선순위별 티켓 수 집계"""
        counts = {}
        for ticket in tickets:
            priority = ticket["priority"]
            counts[priority] = counts.get(priority, 0) + 1
        return counts

    def _count_by_type(self, tickets: List[Dict]) -> Dict:
        """타입별 티켓 수 집계"""
        counts = {}
        for ticket in tickets:
            ticket_type = ticket["type"]
            counts[ticket_type] = counts.get(ticket_type, 0) + 1
        return counts

    def _count_by_assignee(self, tickets: List[Dict]) -> Dict:
        """담당자별 티켓 수 집계"""
        counts = {}
        for ticket in tickets:
            assignee = ticket["assignee"]
            counts[assignee] = counts.get(assignee, 0) + 1
        return counts

# 전역 추천 엔진 인스턴스
recommendation_engine = TicketRecommendationEngine()

def get_recommendations(count: int = 10, focus_area: Optional[str] = None) -> List[Dict]:
    """추천 작업 조회 (편의 함수)"""
    return recommendation_engine.generate_recommendations(count, focus_area)

def get_sprint_recommendations(capacity: int = 40) -> Dict:
    """스프린트 추천 작업 조회 (편의 함수)"""
    return recommendation_engine.generate_sprint_recommendations(capacity)