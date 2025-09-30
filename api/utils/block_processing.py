from typing import List, Dict, Any, Optional
from api.models.schemas import BlockStats

def filter_blocks(blocks: List[Dict[str, Any]],
                 confidence_min: Optional[float] = None,
                 confidence_max: Optional[float] = None,
                 text_contains: Optional[str] = None,
                 block_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """블록 필터링"""
    filtered = blocks

    if confidence_min is not None:
        filtered = [b for b in filtered if b.get('confidence', 0) >= confidence_min]

    if confidence_max is not None:
        filtered = [b for b in filtered if b.get('confidence', 0) <= confidence_max]

    if text_contains:
        filtered = [b for b in filtered if text_contains.lower() in b.get('text', '').lower()]

    if block_type:
        filtered = [b for b in filtered if b.get('block_type') == block_type or b.get('type') == block_type]

    return filtered

def calculate_block_stats(blocks: List[Dict[str, Any]]) -> BlockStats:
    """블록 통계 계산"""
    if not blocks:
        return BlockStats(
            total_blocks=0,
            confidence_distribution={},
            block_type_counts={},
            average_confidence=0.0,
            text_length_stats={}
        )

    # 신뢰도 분포 계산 (0.1 단위)
    conf_dist = {}
    for block in blocks:
        conf = block.get('confidence', 0)
        key = f"{int(conf * 10) / 10:.1f}-{int(conf * 10) / 10 + 0.1:.1f}"
        conf_dist[key] = conf_dist.get(key, 0) + 1

    # 블록 타입별 개수
    type_counts = {}
    for block in blocks:
        block_type = block.get('block_type') or block.get('type', 'unknown')
        type_counts[block_type] = type_counts.get(block_type, 0) + 1

    # 텍스트 길이 통계
    text_lengths = [len(block.get('text', '')) for block in blocks]
    text_stats = {
        'min': min(text_lengths) if text_lengths else 0,
        'max': max(text_lengths) if text_lengths else 0,
        'average': sum(text_lengths) / len(text_lengths) if text_lengths else 0
    }

    # 평균 신뢰도
    avg_conf = sum(block.get('confidence', 0) for block in blocks) / len(blocks)

    return BlockStats(
        total_blocks=len(blocks),
        confidence_distribution=conf_dist,
        block_type_counts=type_counts,
        average_confidence=round(avg_conf, 3),
        text_length_stats=text_stats
    )

def find_blocks_by_position(blocks: List[Dict[str, Any]], x: int, y: int, tolerance: int = 10) -> List[Dict[str, Any]]:
    """좌표 기반 블록 찾기"""
    found_blocks = []

    for i, block in enumerate(blocks):
        bbox = block.get('bbox_points') or block.get('bbox', [])
        if not bbox or len(bbox) != 4:
            continue

        # 바운딩 박스 영역 확인
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        # 허용 오차 포함하여 영역 안에 있는지 확인
        if (min_x - tolerance <= x <= max_x + tolerance and
            min_y - tolerance <= y <= max_y + tolerance):
            block_copy = block.copy()
            block_copy['block_id'] = i
            found_blocks.append(block_copy)

    return found_blocks