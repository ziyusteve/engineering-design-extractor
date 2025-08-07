"""
Tests for the Engineering Design Criteria Extractor.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.extractor import EngineeringCriteriaExtractor
from models.schemas import DesignCriteria, LoadSpecification, LoadType
from models.document_models import ProcessingStatus


class TestEngineeringCriteriaExtractor:
    """Test cases for EngineeringCriteriaExtractor."""
    
    @pytest.fixture
    def mock_processor(self):
        """Mock Document AI processor."""
        with patch('processors.document_ai_processor.DocumentAIProcessor') as mock:
            processor_instance = Mock()
            mock.return_value = processor_instance
            yield processor_instance
    
    @pytest.fixture
    def extractor(self, mock_processor):
        """Create extractor instance with mocked processor."""
        return EngineeringCriteriaExtractor(
            project_id="test-project",
            processor_id="test-processor",
            location="us"
        )
    
    def test_initialization(self, extractor):
        """Test extractor initialization."""
        assert extractor.project_id == "test-project"
        assert extractor.processor_id == "test-processor"
        assert extractor.location == "us"
    
    def test_extract_from_file_success(self, extractor, mock_processor):
        """Test successful file extraction."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\n%Test PDF content")
            temp_file_path = temp_file.name
        
        try:
            # Mock the extraction result
            mock_criteria = DesignCriteria(
                loads=[],
                seismic_forces=[],
                design_vehicles=[],
                design_cranes=[],
                tables=[],
                images=[],
                metadata=Mock(filename="test.pdf", file_size=100, page_count=1),
                confidence_score=0.95
            )
            
            mock_processor.extract_engineering_criteria.return_value = mock_criteria
            
            # Test extraction
            result = extractor.extract_from_file(temp_file_path)
            
            assert result.status == ProcessingStatus.COMPLETED
            assert result.design_criteria == mock_criteria
            assert result.error_message is None
            
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_extract_from_file_not_found(self, extractor):
        """Test extraction with non-existent file."""
        result = extractor.extract_from_file("non_existent_file.pdf")
        
        assert result.status == ProcessingStatus.FAILED
        assert "File not found" in result.error_message
    
    def test_extract_from_file_not_pdf(self, extractor):
        """Test extraction with non-PDF file."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"Not a PDF file")
            temp_file_path = temp_file.name
        
        try:
            result = extractor.extract_from_file(temp_file_path)
            
            assert result.status == ProcessingStatus.FAILED
            assert "must be a PDF" in result.error_message
            
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_directory(self, extractor, mock_processor):
        """Test directory extraction."""
        # Create temporary directory with PDF files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test PDF files
            pdf_files = []
            for i in range(3):
                pdf_path = os.path.join(temp_dir, f"test_{i}.pdf")
                with open(pdf_path, 'wb') as f:
                    f.write(b"%PDF-1.4\n%Test PDF content")
                pdf_files.append(pdf_path)
            
            # Mock the extraction result
            mock_criteria = DesignCriteria(
                loads=[],
                seismic_forces=[],
                design_vehicles=[],
                design_cranes=[],
                tables=[],
                images=[],
                metadata=Mock(filename="test.pdf", file_size=100, page_count=1),
                confidence_score=0.95
            )
            
            mock_processor.extract_engineering_criteria.return_value = mock_criteria
            
            # Test extraction
            results = extractor.extract_from_directory(temp_dir, "data/output")
            
            assert len(results) == 3
            for result in results.values():
                assert result.status == ProcessingStatus.COMPLETED
    
    def test_get_processor_info(self, extractor, mock_processor):
        """Test getting processor information."""
        mock_processor.processor.name = "projects/test-project/locations/us/processors/test-processor"
        mock_processor.processor.type_ = "CUSTOM_EXTRACTOR"
        mock_processor.processor.processor_version = "1.0.0"
        
        info = extractor.get_processor_info()
        
        assert info["project_id"] == "test-project"
        assert info["processor_id"] == "test-processor"
        assert info["location"] == "us"
        assert info["processor_name"] == "projects/test-project/locations/us/processors/test-processor"
        assert info["processor_type"] == "CUSTOM_EXTRACTOR"
        assert info["processor_version"] == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__]) 