from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class BlockInfo(BaseModel):
    text: str
    confidence: float
    bbox: List[List[int]]
    block_type: str

class ProcessingResult(BaseModel):
    filename: str
    total_blocks: int
    average_confidence: float
    blocks: List[BlockInfo]
    processing_time: Optional[float] = None
    output_files: Optional[dict] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

class ServerStatus(BaseModel):
    status: str
    uptime_seconds: float
    uptime_formatted: str
    total_requests: int
    total_images_processed: int
    total_pdfs_processed: int
    total_blocks_extracted: int
    average_processing_time: float
    last_request_time: Optional[str]
    errors: int
    gpu_available: bool

class OutputFile(BaseModel):
    filename: str
    content: Dict[str, Any]
    file_info: Dict[str, Any]

class BlockDetail(BaseModel):
    block_id: int
    text: str
    confidence: float
    bbox: List[List[int]]
    block_type: str
    file_info: Dict[str, Any]

class BlockStats(BaseModel):
    total_blocks: int
    confidence_distribution: Dict[str, int]
    block_type_counts: Dict[str, int]
    average_confidence: float
    text_length_stats: Dict[str, float]

class FileStats(BaseModel):
    total_files: int
    total_size_mb: float
    by_type: Dict[str, Dict[str, Any]]
    disk_usage: Dict[str, float]

class BatchOperation(BaseModel):
    action: str
    files: List[str]