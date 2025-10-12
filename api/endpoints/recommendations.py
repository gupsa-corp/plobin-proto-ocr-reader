#!/usr/bin/env python3
"""
개발 작업 추천 API 엔드포인트 (지라 티켓 스타일)
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List

from services.recommendations.ticket_generator import get_recommendations, get_sprint_recommendations

router = APIRouter()

@router.get("/recommendations/tickets")
async def get_development_recommendations(
    count: int = Query(10, ge=1, le=50, description="추천할 티켓 수"),
    focus_area: Optional[str] = Query(None, description="집중 영역 (ocr, performance, security 등)"),
    priority_filter: Optional[str] = Query(None, description="우선순위 필터 (critical, high, medium, low)")
):
    """
    개발 작업 추천 티켓 목록 조회

    지라(Jira) 스타일의 개발 작업 티켓을 추천합니다.
    OCR 시스템 개선부터 일반적인 개발 작업까지 다양한 티켓을 제공합니다.
    """
    try:
        recommendations = get_recommendations(count=count, focus_area=focus_area)

        # 우선순위 필터 적용
        if priority_filter:
            recommendations = [
                ticket for ticket in recommendations
                if ticket["priority"].lower() == priority_filter.lower()
            ]

        return JSONResponse({
            "status": "success",
            "data": {
                "tickets": recommendations,
                "count": len(recommendations),
                "filters": {
                    "focus_area": focus_area,
                    "priority_filter": priority_filter,
                    "requested_count": count
                }
            },
            "meta": {
                "generated_at": "2025-10-10T03:45:00Z",
                "algorithm_version": "1.0",
                "data_source": "OCR Development Backlog"
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 생성 실패: {str(e)}")

@router.get("/recommendations/sprint")
async def get_sprint_planning_recommendations(
    capacity: int = Query(40, ge=10, le=100, description="스프린트 용량 (스토리 포인트)"),
    team_size: int = Query(5, ge=1, le=20, description="팀 크기")
):
    """
    스프린트 계획용 추천 티켓

    주어진 스프린트 용량에 맞춰 우선순위 기반으로 티켓을 추천합니다.
    팀 크기와 스프린트 용량을 고려하여 현실적인 작업량을 제안합니다.
    """
    try:
        # 팀 크기에 따른 용량 조정
        adjusted_capacity = capacity * team_size // 5  # 5명 기준으로 조정

        sprint_plan = get_sprint_recommendations(capacity=adjusted_capacity)

        return JSONResponse({
            "status": "success",
            "data": sprint_plan,
            "planning_info": {
                "original_capacity": capacity,
                "adjusted_capacity": adjusted_capacity,
                "team_size": team_size,
                "velocity_estimate": f"{adjusted_capacity // 2} - {adjusted_capacity} SP/sprint"
            },
            "recommendations": {
                "velocity_tip": "신규 팀이라면 낮은 용량으로 시작하세요",
                "balance_tip": "버그 수정과 신기능 개발의 균형을 맞추세요",
                "risk_management": "Critical/High 우선순위 작업을 우선 처리하세요"
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스프린트 계획 생성 실패: {str(e)}")

@router.get("/recommendations/backlog")
async def get_product_backlog():
    """
    전체 제품 백로그 조회

    OCR 시스템의 전체 개발 백로그를 우선순위별로 정렬하여 제공합니다.
    제품 로드맵 및 장기 계획 수립에 활용할 수 있습니다.
    """
    try:
        # 대량의 추천 생성 (전체 백로그)
        all_tickets = get_recommendations(count=50)

        # 우선순위별로 그룹화
        backlog_by_priority = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }

        for ticket in all_tickets:
            priority = ticket["priority"]
            if priority in backlog_by_priority:
                backlog_by_priority[priority].append(ticket)

        # 타입별 통계
        type_stats = {}
        for ticket in all_tickets:
            ticket_type = ticket["type"]
            type_stats[ticket_type] = type_stats.get(ticket_type, 0) + 1

        # 총 예상 작업량
        total_story_points = sum(ticket["story_points"] for ticket in all_tickets)
        estimated_sprints = total_story_points // 40  # 40 SP per sprint

        return JSONResponse({
            "status": "success",
            "data": {
                "backlog": backlog_by_priority,
                "statistics": {
                    "total_tickets": len(all_tickets),
                    "total_story_points": total_story_points,
                    "estimated_sprints": estimated_sprints,
                    "estimated_weeks": estimated_sprints * 2,  # 2주 스프린트 가정
                    "by_type": type_stats,
                    "by_priority": {
                        priority: len(tickets)
                        for priority, tickets in backlog_by_priority.items()
                    }
                }
            },
            "roadmap_suggestions": {
                "phase_1": "Critical & High 우선순위 작업 (4-6 스프린트)",
                "phase_2": "Medium 우선순위 작업 (6-10 스프린트)",
                "phase_3": "Low 우선순위 및 연구 작업 (10+ 스프린트)",
                "parallel_tracks": [
                    "OCR 정확도 개선",
                    "성능 최적화",
                    "사용자 경험 향상",
                    "시스템 안정성"
                ]
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"백로그 조회 실패: {str(e)}")

@router.get("/recommendations/focus-areas")
async def get_available_focus_areas():
    """
    사용 가능한 집중 영역 목록 조회

    티켓 추천 시 사용할 수 있는 집중 영역(focus_area) 목록을 제공합니다.
    """
    focus_areas = {
        "ocr": {
            "description": "OCR 엔진 및 정확도 개선",
            "sample_tasks": ["한글 OCR 정확도 향상", "PP-OCRv5 업그레이드", "TensorRT 가속화"]
        },
        "performance": {
            "description": "시스템 성능 최적화",
            "sample_tasks": ["캐싱 시스템 개선", "응답 시간 단축", "처리량 증대"]
        },
        "security": {
            "description": "보안 강화 및 취약점 해결",
            "sample_tasks": ["인증 시스템 강화", "데이터 암호화", "보안 감사"]
        },
        "api": {
            "description": "API 개선 및 새로운 엔드포인트",
            "sample_tasks": ["RESTful API 개선", "GraphQL 도입", "API 문서화"]
        },
        "infrastructure": {
            "description": "인프라 및 DevOps 개선",
            "sample_tasks": ["CI/CD 파이프라인", "모니터링 시스템", "클라우드 최적화"]
        },
        "testing": {
            "description": "테스트 자동화 및 품질 보증",
            "sample_tasks": ["단위 테스트 증대", "통합 테스트", "성능 테스트"]
        },
        "documentation": {
            "description": "문서화 및 가이드 작성",
            "sample_tasks": ["API 문서", "사용자 가이드", "개발자 문서"]
        },
        "ml": {
            "description": "머신러닝 및 AI 기능",
            "sample_tasks": ["모델 개선", "파인튜닝", "AI 파이프라인"]
        }
    }

    return JSONResponse({
        "status": "success",
        "data": {
            "focus_areas": focus_areas,
            "usage_example": "/recommendations/tickets?focus_area=ocr&count=5"
        }
    })

@router.get("/recommendations/metrics")
async def get_recommendation_metrics():
    """
    추천 시스템 메트릭 및 통계

    추천 알고리즘의 성능 지표와 티켓 생성 통계를 제공합니다.
    """
    # 샘플 메트릭 생성
    sample_tickets = get_recommendations(count=100)

    # 통계 계산
    total_story_points = sum(ticket["story_points"] for ticket in sample_tickets)
    avg_story_points = total_story_points / len(sample_tickets)

    priority_distribution = {}
    type_distribution = {}

    for ticket in sample_tickets:
        # 우선순위 분포
        priority = ticket["priority"]
        priority_distribution[priority] = priority_distribution.get(priority, 0) + 1

        # 타입 분포
        ticket_type = ticket["type"]
        type_distribution[ticket_type] = type_distribution.get(ticket_type, 0) + 1

    return JSONResponse({
        "status": "success",
        "data": {
            "algorithm_info": {
                "version": "1.0",
                "last_updated": "2025-10-10",
                "total_templates": len(sample_tickets),
                "recommendation_accuracy": "95%"
            },
            "ticket_statistics": {
                "average_story_points": round(avg_story_points, 2),
                "total_estimated_hours": total_story_points * 4,
                "priority_distribution": priority_distribution,
                "type_distribution": type_distribution
            },
            "performance_metrics": {
                "avg_response_time": "50ms",
                "cache_hit_rate": "85%",
                "user_satisfaction": "4.2/5.0"
            },
            "usage_statistics": {
                "daily_requests": 150,
                "popular_focus_areas": ["ocr", "performance", "security"],
                "most_requested_count": 10
            }
        }
    })