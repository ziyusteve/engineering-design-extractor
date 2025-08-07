"""
Document AI specific models for API responses and processing.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DocumentAIBoundingBox(BaseModel):
    """Bounding box coordinates from Document AI."""
    x: float
    y: float
    width: float
    height: float


class DocumentAIEntity(BaseModel):
    """Entity extracted by Document AI."""
    type: str
    mention_text: str
    confidence: float
    bounding_box: Optional[DocumentAIBoundingBox] = None
    page_anchor: Optional[int] = None


class DocumentAIPage(BaseModel):
    """Page information from Document AI."""
    page_number: int
    width: Optional[float] = None
    height: Optional[float] = None
    image: Optional[str] = None  # Base64 encoded image


class DocumentAIResponse(BaseModel):
    """Complete response from Document AI API."""
    document_text: str
    pages: List[DocumentAIPage]
    entities: List[DocumentAIEntity]
    tables: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    confidence: float
    processor_version: str
    processing_time: float


class DocumentAIRequest(BaseModel):
    """Request model for Document AI processing."""
    file_path: str
    processor_id: str
    project_id: str
    location: str = "us"


class ProcessingStatus(str, Enum):
    """Status of document processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed" 