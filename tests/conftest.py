"""
Pytest configuration and shared fixtures
"""

import pytest
import asyncio
import os
import tempfile
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient

from api_server import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """FastAPI test client fixture"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client fixture"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Temporary directory fixture"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_text() -> str:
    """Sample text for testing"""
    return """
    Test Cafe Receipt
    Address: Seoul Gangnam-gu
    Phone: 02-1234-5678

    Menu:
    Americano: 4500
    Cafe Latte: 5000
    Cake: 6000

    Total: 15500 Won
    Payment: Card
    """


@pytest.fixture
def sample_receipt_data() -> dict:
    """Sample receipt data for testing"""
    return {
        "blocks": [
            {
                "id": "block_001",
                "text": "Test Cafe Receipt",
                "confidence": 0.95,
                "bbox": {"x": 100, "y": 50, "width": 200, "height": 30},
                "type": "title"
            },
            {
                "id": "block_002",
                "text": "Americano: 4500",
                "confidence": 0.92,
                "bbox": {"x": 100, "y": 100, "width": 150, "height": 25},
                "type": "menu_item"
            },
            {
                "id": "block_003",
                "text": "Total: 15500 Won",
                "confidence": 0.98,
                "bbox": {"x": 100, "y": 200, "width": 120, "height": 25},
                "type": "total"
            }
        ],
        "page_info": {
            "width": 400,
            "height": 600,
            "page_number": 1
        }
    }


@pytest.fixture
def mock_llm_response() -> dict:
    """Mock LLM analysis response"""
    return {
        "section_id": "test_section_001",
        "section_type": "receipt",
        "original_text": "Test Cafe Receipt Total: 15500 Won",
        "analyzed_content": "This is a cafe receipt with total amount of 15,500 won",
        "extracted_data": {
            "merchant": "Test Cafe",
            "total_amount": 15500,
            "currency": "KRW",
            "payment_method": "card"
        },
        "confidence_score": 0.95,
        "model_used": "boto",
        "analysis_timestamp": "2025-10-10T12:00:00"
    }


@pytest.fixture
def test_files_dir() -> str:
    """Test files directory"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "fixtures", "files")


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["TESTING"] = "1"
    os.environ["GUPSA_AI_API_KEY"] = "test_api_key"
    yield
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]