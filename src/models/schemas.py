"""
Core data schemas for engineering design criteria extraction.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class LoadType(str, Enum):
    """Types of engineering loads."""
    DEAD_LOAD = "dead_load"
    LIVE_LOAD = "live_load"
    WIND_LOAD = "wind_load"
    SNOW_LOAD = "snow_load"
    SEISMIC_LOAD = "seismic_load"
    HYDROSTATIC_LOAD = "hydrostatic_load"
    WAVE_LOAD = "wave_load"
    IMPACT_LOAD = "impact_load"
    THERMAL_LOAD = "thermal_load"
    OTHER = "other"


class VehicleType(str, Enum):
    """Types of design vehicles."""
    PASSENGER_CAR = "passenger_car"
    TRUCK = "truck"
    BUS = "bus"
    TRAILER = "trailer"
    EMERGENCY_VEHICLE = "emergency_vehicle"
    MILITARY_VEHICLE = "military_vehicle"
    CONSTRUCTION_VEHICLE = "construction_vehicle"
    OTHER = "other"


class CraneType(str, Enum):
    """Types of design cranes."""
    MOBILE_CRANE = "mobile_crane"
    TOWER_CRANE = "tower_crane"
    GANTRY_CRANE = "gantry_crane"
    BRIDGE_CRANE = "bridge_crane"
    JIB_CRANE = "jib_crane"
    FLOATING_CRANE = "floating_crane"
    OTHER = "other"


class LoadSpecification(BaseModel):
    """Specification for engineering loads."""
    load_type: LoadType
    magnitude: float
    unit: str = Field(..., description="Unit of measurement (kN, kN/m², etc.)")
    direction: Optional[str] = Field(None, description="Direction of load application")
    location: Optional[str] = Field(None, description="Location where load is applied")
    description: Optional[str] = Field(None, description="Additional description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score")
    bounding_box: Optional[Dict[str, float]] = Field(None, description="Location in document")


class SeismicForce(BaseModel):
    """Seismic force specifications."""
    seismic_zone: Optional[str] = Field(None, description="Seismic zone classification")
    acceleration_coefficient: Optional[float] = Field(None, description="Seismic acceleration coefficient")
    response_modification_factor: Optional[float] = Field(None, description="R-factor")
    importance_factor: Optional[float] = Field(None, description="Importance factor")
    base_shear: Optional[float] = Field(None, description="Base shear force")
    unit: str = Field(..., description="Unit of measurement")
    description: Optional[str] = Field(None, description="Additional description")
    confidence: float = Field(..., ge=0.0, le=1.0)
    bounding_box: Optional[Dict[str, float]] = Field(None)


class DesignVehicle(BaseModel):
    """Design vehicle specifications."""
    vehicle_type: VehicleType
    axle_loads: List[float] = Field(default_factory=list, description="Individual axle loads")
    total_weight: Optional[float] = Field(None, description="Total vehicle weight")
    dimensions: Optional[Dict[str, float]] = Field(None, description="Vehicle dimensions")
    wheelbase: Optional[float] = Field(None, description="Wheelbase length")
    unit: str = Field(..., description="Unit of measurement")
    description: Optional[str] = Field(None, description="Additional description")
    confidence: float = Field(..., ge=0.0, le=1.0)
    bounding_box: Optional[Dict[str, float]] = Field(None)


class DesignCrane(BaseModel):
    """Design crane specifications."""
    crane_type: CraneType
    capacity: float = Field(..., description="Crane capacity")
    boom_length: Optional[float] = Field(None, description="Boom length")
    radius: Optional[float] = Field(None, description="Operating radius")
    unit: str = Field(..., description="Unit of measurement")
    description: Optional[str] = Field(None, description="Additional description")
    confidence: float = Field(..., ge=0.0, le=1.0)
    bounding_box: Optional[Dict[str, float]] = Field(None)


class TableData(BaseModel):
    """Extracted table data."""
    table_id: str = Field(..., description="Unique identifier for the table")
    page_number: int = Field(..., description="Page where table is located")
    headers: List[str] = Field(default_factory=list, description="Table headers")
    rows: List[List[str]] = Field(default_factory=list, description="Table data rows")
    bounding_box: Dict[str, float] = Field(..., description="Table location in document")
    confidence: float = Field(..., ge=0.0, le=1.0)
    extracted_text: Optional[str] = Field(None, description="Raw extracted text")


class ImageData(BaseModel):
    """Extracted image data."""
    image_id: str = Field(..., description="Unique identifier for the image")
    page_number: int = Field(..., description="Page where image is located")
    bounding_box: Optional[Dict[str, float]] = Field(None, description="Image location in document")
    image_type: Optional[str] = Field(None, description="Type of image (diagram, photo, etc.)")
    description: Optional[str] = Field(None, description="Image description or caption")
    confidence: float = Field(..., ge=0.0, le=1.0)
    file_path: Optional[str] = Field(None, description="Path to saved image file")


class DocumentMetadata(BaseModel):
    """Document metadata."""
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Number of pages")
    document_type: Optional[str] = Field(None, description="Type of document")
    creation_date: Optional[datetime] = Field(None, description="Document creation date")
    processing_date: datetime = Field(default_factory=datetime.now)
    processor_version: Optional[str] = Field(None, description="Document AI processor version")


class DocumentAIEntity(BaseModel):
    """Document AI entity information."""
    type: str = Field(..., description="Entity type")
    text: str = Field(..., description="Entity text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Entity confidence score")
    bounding_box: Optional[Dict[str, float]] = Field(None, description="Entity location in document")


class DesignCriteria(BaseModel):
    """Complete engineering design criteria extracted from a document."""
    loads: List[LoadSpecification] = Field(default_factory=list)
    seismic_forces: List[SeismicForce] = Field(default_factory=list)
    design_vehicles: List[DesignVehicle] = Field(default_factory=list)
    design_cranes: List[DesignCrane] = Field(default_factory=list)
    tables: List[TableData] = Field(default_factory=list)
    images: List[ImageData] = Field(default_factory=list)
    
    # Additional engineering fields
    structural_elements: List[Dict[str, Any]] = Field(default_factory=list, description="Structural elements found in document")
    material_specifications: List[Dict[str, Any]] = Field(default_factory=list, description="Material specifications")
    safety_factors: List[Dict[str, Any]] = Field(default_factory=list, description="Safety factors and margins")
    environmental_conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Environmental conditions")
    
    # Document AI entities
    document_ai_entities: List[DocumentAIEntity] = Field(default_factory=list, description="Raw Document AI entities")
    
    metadata: DocumentMetadata
    raw_text: Optional[str] = Field(None, description="Full extracted text")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall extraction confidence")


class ExtractionResult(BaseModel):
    """Result of document extraction process."""
    job_id: str = Field(..., description="Processing job identifier")
    status: str = Field(..., description="Processing status")
    design_criteria: Optional[DesignCriteria] = Field(None, description="Extracted criteria")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ProcessingJob(BaseModel):
    """Job tracking for batch processing."""
    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Document filename")
    status: str = Field(..., description="Job status")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Processing progress")
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    error_message: Optional[str] = Field(None) 