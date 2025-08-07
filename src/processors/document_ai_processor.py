"""
Document AI processor for extracting engineering design criteria from PDF documents.
Uses Google Cloud Document AI pre-trained models.
"""

import os
import time
import json
from typing import Optional, Dict, Any, List
from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1
from google.cloud import storage
import base64
from loguru import logger

from ..models.schemas import (
    DesignCriteria, LoadSpecification, SeismicForce, 
    DesignVehicle, DesignCrane, TableData, ImageData, 
    DocumentMetadata, LoadType, VehicleType, CraneType, DocumentAIEntity
)
from ..models.document_models import DocumentAIResponse, ProcessingStatus
from .image_extractor import ImageExtractor


class DocumentAIProcessor:
    """
    Processor for extracting engineering design criteria using Google Cloud Document AI.
    """
    
    def __init__(self, project_id: str, processor_id: str, location: str = "us", enable_image_extraction: bool = True):
        """
        Initialize the Document AI processor.
        
        Args:
            project_id: Google Cloud project ID
            processor_id: Document AI processor ID
            location: Processor location (us, eu, etc.)
            enable_image_extraction: Whether to enable image extraction using Document AI Toolbox
        """
        self.project_id = project_id
        self.processor_id = processor_id
        self.location = location
        self.enable_image_extraction = enable_image_extraction
        
        # Set up Document AI client
        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        self.client = documentai_v1.DocumentProcessorServiceClient(client_options=opts)
        
        # Get processor reference
        full_processor_name = self.client.processor_path(project_id, location, processor_id)
        request = documentai_v1.GetProcessorRequest(name=full_processor_name)
        self.processor = self.client.get_processor(request=request)
        
        # Initialize image extractor if enabled
        self.image_extractor = None
        if self.enable_image_extraction:
            try:
                self.image_extractor = ImageExtractor()
                logger.info("Image extraction enabled with Document AI Toolbox")
            except ImportError as e:
                logger.warning(f"Image extraction disabled: {str(e)}")
                self.enable_image_extraction = False
        
        logger.info(f"Initialized Document AI processor: {self.processor.name}")
    
    def process_document(self, file_path: str) -> DocumentAIResponse:
        """
        Process a PDF document using Document AI.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            DocumentAIResponse with extracted data
        """
        start_time = time.time()
        
        try:
            # Read the file into memory
            with open(file_path, "rb") as file:
                file_content = file.read()
            
            # Create raw document
            raw_document = documentai_v1.RawDocument(
                content=file_content,
                mime_type="application/pdf"
            )
            
            # Process document with basic options (OCR config not supported for custom processors)
            request = documentai_v1.ProcessRequest(
                name=self.processor.name, 
                raw_document=raw_document
            )
            
            result = self.client.process_document(request=request)
            document = result.document
            
            processing_time = time.time() - start_time
            
            # Extract entities, tables, and images
            entities = self._extract_entities(document)
            tables = self._extract_tables(document)
            images = self._extract_images(document)
            pages = self._extract_pages(document)
            
            return DocumentAIResponse(
                document_text=document.text,
                pages=pages,
                entities=entities,
                tables=tables,
                images=images,
                confidence=getattr(document, 'confidence', 0.0),
                processor_version=getattr(self.processor, 'processor_version', 'unknown'),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise
    
    def _process_document_raw(self, file_path: str) -> dict:
        """
        Process a document with Document AI and return the raw response as a dictionary.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Raw Document AI response as a dictionary
        """
        try:
            # Read the file into memory
            with open(file_path, "rb") as file:
                file_content = file.read()
            
            # Create raw document
            raw_document = documentai_v1.RawDocument(
                content=file_content,
                mime_type="application/pdf"
            )
            
            # Process document
            request = documentai_v1.ProcessRequest(
                name=self.processor.name, 
                raw_document=raw_document
            )
            
            result = self.client.process_document(request=request)
            document = result.document
            
            # Return the document as-is, let the Toolbox handle the conversion
            return document
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise
    
    def _extract_images_from_response(self, doc_ai_response: DocumentAIResponse, output_dir: str) -> List[str]:
        """
        Extract images from Document AI response and save them to files.
        
        Args:
            doc_ai_response: Document AI response object
            output_dir: Directory to save extracted images
            
        Returns:
            List of paths to extracted image files
        """
        extracted_files = []
        
        try:
            # For now, we'll create placeholder images since the Document AI response
            # doesn't contain the actual image data needed for extraction
            # This is a limitation of the current Document AI processor
            
            for i, image_data in enumerate(doc_ai_response.images):
                # Create a placeholder image file
                image_filename = f"engineering_image_{i+1}.png"
                image_path = os.path.join(output_dir, image_filename)
                
                # Create a simple placeholder image using PIL
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    
                    # Create a 400x300 placeholder image
                    img = Image.new('RGB', (400, 300), color='lightgray')
                    draw = ImageDraw.Draw(img)
                    
                    # Add text to indicate this is an extracted image
                    try:
                        # Try to use a default font
                        font = ImageFont.load_default()
                    except:
                        font = None
                    
                    text = f"Extracted Image {i+1}\nPage {image_data.get('page_number', 'Unknown')}"
                    draw.text((50, 150), text, fill='black', font=font)
                    
                    # Save the image
                    img.save(image_path)
                    extracted_files.append(image_path)
                    
                except ImportError:
                    # If PIL is not available, create an empty file
                    with open(image_path, 'w') as f:
                        f.write(f"Placeholder for extracted image {i+1}")
                    extracted_files.append(image_path)
                
        except Exception as e:
            logger.error(f"Error extracting images from response: {str(e)}")
        
        return extracted_files
    
    def _extract_entities(self, document) -> List[Dict[str, Any]]:
        """Extract entities from Document AI response."""
        entities = []
        
        logger.info(f"Document AI returned {len(document.entities)} entities")
        
        for entity in document.entities:
            entity_data = {
                "type": entity.type_,
                "mention_text": entity.mention_text,
                "confidence": entity.confidence,
                "page_anchor": entity.page_anchor.page_refs[0].page if entity.page_anchor.page_refs else None
            }
            
            # Extract bounding box if available
            if entity.page_anchor and entity.page_anchor.page_refs:
                page_ref = entity.page_anchor.page_refs[0]
                if hasattr(page_ref, 'bounding_poly') and page_ref.bounding_poly.vertices:
                    vertices = page_ref.bounding_poly.vertices
                    if len(vertices) >= 3:
                        entity_data["bounding_box"] = {
                            "x": vertices[0].x,
                            "y": vertices[0].y,
                            "width": vertices[2].x - vertices[0].x,
                            "height": vertices[2].y - vertices[0].y
                        }
            
            entities.append(entity_data)
            
            # Log each entity for debugging
            logger.info(f"Entity: type='{entity.type_}', text='{entity.mention_text[:50]}...', confidence={entity.confidence}")
        
        return entities
    
    def _extract_tables(self, document) -> List[Dict[str, Any]]:
        """Extract tables from Document AI response."""
        tables = []
        
        for page in document.pages:
            for table in page.tables:
                # Safely extract bounding box
                bounding_box = None
                if (hasattr(table, 'layout') and hasattr(table.layout, 'bounding_poly') 
                    and table.layout.bounding_poly.vertices and len(table.layout.bounding_poly.vertices) >= 3):
                    vertices = table.layout.bounding_poly.vertices
                    bounding_box = {
                        "x": vertices[0].x,
                        "y": vertices[0].y,
                        "width": vertices[2].x - vertices[0].x,
                        "height": vertices[2].y - vertices[0].y
                    }
                
                table_data = {
                    "table_id": f"table_{len(tables)}",
                    "page_number": page.page_number,
                    "headers": [],
                    "rows": [],
                    "bounding_box": bounding_box,
                    "confidence": table.layout.confidence if hasattr(table, 'layout') else 0.0
                }
                
                # Extract table headers and rows
                for header_row in table.header_rows:
                    row_data = []
                    for cell in header_row.cells:
                        row_data.append(cell.layout.text_anchor.content)
                    table_data["headers"].append(row_data)
                
                for body_row in table.body_rows:
                    row_data = []
                    for cell in body_row.cells:
                        row_data.append(cell.layout.text_anchor.content)
                    table_data["rows"].append(row_data)
                
                tables.append(table_data)
        
        return tables
    
    def _extract_images(self, document) -> List[Dict[str, Any]]:
        """Extract images from Document AI response using native API."""
        images = []
        
        # Document AI provides images directly in the document
        if hasattr(document, 'images') and document.images:
            for i, image in enumerate(document.images):
                try:
                    # Extract image data directly from Document AI
                    image_data = {
                        "image_id": f"doc_ai_image_{i}",
                        "page_number": getattr(image, 'page_number', 1),
                        "bounding_box": None,  # Will be extracted if available
                        "confidence": getattr(image, 'confidence', 1.0),
                        "mime_type": getattr(image, 'mime_type', 'image/png'),
                        "image": getattr(image, 'image', None)  # Raw image data
                    }
                    
                    # Extract bounding box if available
                    if hasattr(image, 'layout') and hasattr(image.layout, 'bounding_poly'):
                        vertices = image.layout.bounding_poly.vertices
                        if vertices and len(vertices) >= 3:
                            image_data["bounding_box"] = {
                                "x": vertices[0].x,
                                "y": vertices[0].y,
                                "width": vertices[2].x - vertices[0].x,
                                "height": vertices[2].y - vertices[0].y
                            }
                    
                    images.append(image_data)
                    logger.info(f"Extracted image {i+1} from Document AI API")
                    
                except Exception as e:
                    logger.warning(f"Failed to extract image {i+1}: {str(e)}")
                    continue
        
        # Also check for images in pages (fallback)
        for page in document.pages:
            if hasattr(page, 'image') and page.image:
                image = page.image
                bounding_box = None
                if (hasattr(image, 'layout') and hasattr(image.layout, 'bounding_poly') 
                    and image.layout.bounding_poly.vertices and len(image.layout.bounding_poly.vertices) >= 3):
                    vertices = image.layout.bounding_poly.vertices
                    bounding_box = {
                        "x": vertices[0].x,
                        "y": vertices[0].y,
                        "width": vertices[2].x - vertices[0].x,
                        "height": vertices[2].y - vertices[0].y
                    }
                
                image_data = {
                    "image_id": f"page_image_{len(images)}",
                    "page_number": page.page_number,
                    "bounding_box": bounding_box,
                    "confidence": image.layout.confidence if hasattr(image, 'layout') else 0.0,
                    "mime_type": image.mime_type if hasattr(image, 'mime_type') else None,
                    "image": getattr(image, 'image', None)
                }
                images.append(image_data)
        
        logger.info(f"Total images extracted from Document AI: {len(images)}")
        return images
    
    def _extract_pages(self, document) -> List[Dict[str, Any]]:
        """Extract page information from Document AI response."""
        pages = []
        
        for page in document.pages:
            page_data = {
                "page_number": page.page_number,
                "width": getattr(page, 'width', None),
                "height": getattr(page, 'height', None)
            }
            pages.append(page_data)
        
        return pages
    
    def extract_engineering_criteria(self, file_path: str, job_id: str = None) -> DesignCriteria:
        """
        Extract engineering design criteria from a PDF document.
        
        Args:
            file_path: Path to the PDF file
            job_id: Job identifier for organizing extracted images
            
        Returns:
            DesignCriteria object with extracted information
        """
        # Process document with Document AI
        doc_ai_response = self.process_document(file_path)
        
        # Extract images using Document AI response directly
        extracted_image_files = []
        if self.enable_image_extraction and job_id:
            try:
                # Create job-specific output directory
                job_output_dir = os.path.join("data/extracted_images", job_id)
                os.makedirs(job_output_dir, exist_ok=True)
                
                # First try to extract images from the Document AI response
                doc_ai_images = self._extract_images_from_response(doc_ai_response, job_output_dir)
                
                # Check if Document AI provided real images or just placeholders
                has_real_images = any(os.path.getsize(img_path) > 2000 for img_path in doc_ai_images) if doc_ai_images else False
                
                if has_real_images:
                    extracted_image_files = doc_ai_images
                    logger.info(f"Using {len(extracted_image_files)} images from Document AI response")
                else:
                    logger.info("Document AI provided placeholder images, trying direct PDF extraction")
                    try:
                        from .pdf_image_extractor import PDFImageExtractor
                        pdf_extractor = PDFImageExtractor()
                        extracted_image_files = pdf_extractor.extract_images_from_pdf(file_path, job_id)
                        
                        if extracted_image_files:
                            logger.info(f"Successfully extracted {len(extracted_image_files)} images directly from PDF")
                        else:
                            logger.warning("No images found in PDF using direct extraction")
                            # Fall back to Document AI placeholders if PDF extraction fails
                            extracted_image_files = doc_ai_images
                    except ImportError:
                        logger.warning("PyMuPDF not available for direct PDF image extraction")
                        extracted_image_files = doc_ai_images
                    except Exception as e:
                        logger.error(f"Error in direct PDF image extraction: {str(e)}")
                        extracted_image_files = doc_ai_images
                
                logger.info(f"Total extracted images: {len(extracted_image_files)}")
                
            except Exception as e:
                logger.error(f"Error extracting images: {str(e)}")
        
        # Parse the extracted data into engineering criteria using exact Document AI field names
        loads = self._parse_loads(doc_ai_response)
        seismic_forces = self._parse_seismic_forces(doc_ai_response)
        design_vehicles = self._parse_design_vehicles(doc_ai_response)
        design_cranes = self._parse_design_cranes(doc_ai_response)
        tables = self._parse_tables(doc_ai_response)
        
        # Parse other specific fields from Document AI configuration
        design_criteria = self._parse_design_criteria(doc_ai_response)
        design_loads = self._parse_design_loads(doc_ai_response)
        drg_no = self._parse_drg_no(doc_ai_response)
        title = self._parse_title(doc_ai_response)
        date = self._parse_date(doc_ai_response)
        

        
        # Parse additional engineering fields
        structural_elements = self._parse_structural_elements(doc_ai_response)
        material_specifications = self._parse_material_specifications(doc_ai_response)
        safety_factors = self._parse_safety_factors(doc_ai_response)
        environmental_conditions = self._parse_environmental_conditions(doc_ai_response)
        
        # Get the original Document AI response to access bounding box information
        original_doc_ai_response = self._process_document_raw(file_path)
        
        # Extract entity-specific images using Document AI bounding boxes
        entity_images = self._extract_entity_images_with_bbox(original_doc_ai_response, file_path, job_id)
        
        # Use Document AI's native image detection and extraction
        doc_ai_images = self._extract_images_from_document_ai(doc_ai_response, job_id)
        
        # Combine entity images with Document AI detected images
        images = entity_images + doc_ai_images
        
        # If Document AI didn't detect any images, try direct PDF extraction as fallback
        if not doc_ai_images and self.enable_image_extraction:
            logger.info("No images detected by Document AI, trying direct PDF extraction as fallback")
            try:
                from .pdf_image_extractor import PDFImageExtractor
                pdf_extractor = PDFImageExtractor()
                extracted_image_files = pdf_extractor.extract_images_from_pdf(file_path, job_id)
                
                if extracted_image_files:
                    # Convert PDF extracted files to ImageData objects
                    for i, img_path in enumerate(extracted_image_files):
                        image_data = ImageData(
                            image_id=f"pdf_extracted_image_{i+1}",
                            page_number=1,  # Default to page 1
                            bounding_box=None,
                            image_type="pdf_extracted",
                            description=f"Image extracted directly from PDF",
                            confidence=1.0,
                            file_path=os.path.join(job_id, os.path.basename(img_path))
                        )
                        images.append(image_data)
                    logger.info(f"Successfully extracted {len(extracted_image_files)} images directly from PDF")
                
            except Exception as e:
                logger.error(f"Error in direct PDF image extraction: {str(e)}")
        
        # Create Document AI entities list
        document_ai_entities = []
        for entity in doc_ai_response.entities:
            # Convert bounding box if it exists
            bounding_box = None
            if hasattr(entity, 'bounding_box') and entity.bounding_box:
                bounding_box = {
                    'x': getattr(entity.bounding_box, 'x', 0),
                    'y': getattr(entity.bounding_box, 'y', 0),
                    'width': getattr(entity.bounding_box, 'width', 0),
                    'height': getattr(entity.bounding_box, 'height', 0)
                }
            
            doc_entity = DocumentAIEntity(
                type=entity.type,
                text=entity.mention_text,
                confidence=entity.confidence,
                bounding_box=bounding_box
            )
            document_ai_entities.append(doc_entity)
        
        # Create document metadata
        metadata = DocumentMetadata(
            filename=os.path.basename(file_path),
            file_size=os.path.getsize(file_path),
            page_count=len(doc_ai_response.pages),
            processor_version=doc_ai_response.processor_version
        )
        
        return DesignCriteria(
            loads=loads,
            seismic_forces=seismic_forces,
            design_vehicles=design_vehicles,
            design_cranes=design_cranes,
            tables=tables,
            images=images,
            structural_elements=structural_elements,
            material_specifications=material_specifications,
            safety_factors=safety_factors,
            environmental_conditions=environmental_conditions,
            document_ai_entities=document_ai_entities,
            metadata=metadata,
            raw_text=doc_ai_response.document_text,
            confidence_score=doc_ai_response.confidence
        )
    
    def _parse_design_criteria(self, doc_ai_response: DocumentAIResponse) -> List[Dict[str, Any]]:
        """Parse DESIGN_CRITERIA from Document AI entities using exact field name."""
        design_criteria = []
        
        for entity in doc_ai_response.entities:
            if entity.type == "DESIGN_CRITERIA":
                criteria = {
                    "type": "design_criteria",
                    "text": entity.mention_text,
                    "confidence": entity.confidence,
                    "bounding_box": entity.bounding_box,
                    "page_number": getattr(entity, 'page_number', 1)
                }
                design_criteria.append(criteria)
        
        return design_criteria
    
    def _parse_design_loads(self, doc_ai_response: DocumentAIResponse) -> List[Dict[str, Any]]:
        """Parse DESIGN_LOADS from Document AI entities using exact field name."""
        design_loads = []
        
        for entity in doc_ai_response.entities:
            if entity.type == "DESIGN_LOADS":
                load = {
                    "type": "design_loads",
                    "text": entity.mention_text,
                    "confidence": entity.confidence,
                    "bounding_box": entity.bounding_box,
                    "page_number": getattr(entity, 'page_number', 1)
                }
                design_loads.append(load)
        
        return design_loads
    
    def _parse_drg_no(self, doc_ai_response: DocumentAIResponse) -> List[Dict[str, Any]]:
        """Parse DRG_No from Document AI entities using exact field name."""
        drg_numbers = []
        
        for entity in doc_ai_response.entities:
            if entity.type == "DRG_No":
                drg = {
                    "type": "drg_no",
                    "text": entity.mention_text,
                    "confidence": entity.confidence,
                    "bounding_box": entity.bounding_box,
                    "page_number": getattr(entity, 'page_number', 1)
                }
                drg_numbers.append(drg)
        
        return drg_numbers
    
    def _parse_title(self, doc_ai_response: DocumentAIResponse) -> List[Dict[str, Any]]:
        """Parse Title from Document AI entities using exact field name."""
        titles = []
        
        for entity in doc_ai_response.entities:
            if entity.type == "Title":
                title = {
                    "type": "title",
                    "text": entity.mention_text,
                    "confidence": entity.confidence,
                    "bounding_box": entity.bounding_box,
                    "page_number": getattr(entity, 'page_number', 1)
                }
                titles.append(title)
        
        return titles
    
    def _parse_date(self, doc_ai_response: DocumentAIResponse) -> List[Dict[str, Any]]:
        """Parse Date from Document AI entities using exact field name."""
        dates = []
        
        for entity in doc_ai_response.entities:
            if entity.type == "Date":
                date = {
                    "type": "date",
                    "text": entity.mention_text,
                    "confidence": entity.confidence,
                    "bounding_box": entity.bounding_box,
                    "page_number": getattr(entity, 'page_number', 1)
                }
                dates.append(date)
        
        return dates
    
    def _parse_structural_elements(self, doc_ai_response: DocumentAIResponse) -> List[Dict[str, Any]]:
        """Parse structural elements from Document AI entities."""
        structural_elements = []
        
        # Look for various structural element types
        structural_types = ["BEAM", "COLUMN", "SLAB", "WALL", "FOUNDATION", "STRUCTURAL_ELEMENT"]
        
        for entity in doc_ai_response.entities:
            if entity.type in structural_types:
                element = {
                    "type": entity.type.lower(),
                    "text": entity.mention_text,
                    "confidence": entity.confidence,
                    "bounding_box": entity.bounding_box,
                    "page_number": getattr(entity, 'page_number', 1)
                }
                structural_elements.append(element)
        
        return structural_elements
    
    def _parse_material_specifications(self, doc_ai_response: DocumentAIResponse) -> List[Dict[str, Any]]:
        """Parse material specifications from Document AI entities."""
        material_specs = []
        
        # Look for material-related entities
        material_types = ["MATERIAL", "STEEL", "CONCRETE", "WOOD", "ALUMINUM", "MATERIAL_SPEC"]
        
        for entity in doc_ai_response.entities:
            if entity.type in material_types:
                material = {
                    "type": entity.type.lower(),
                    "text": entity.mention_text,
                    "confidence": entity.confidence,
                    "bounding_box": entity.bounding_box,
                    "page_number": getattr(entity, 'page_number', 1)
                }
                material_specs.append(material)
        
        return material_specs
    
    def _parse_safety_factors(self, doc_ai_response: DocumentAIResponse) -> List[Dict[str, Any]]:
        """Parse safety factors from Document AI entities."""
        safety_factors = []
        
        # Look for safety factor related entities
        safety_types = ["SAFETY_FACTOR", "FACTOR_OF_SAFETY", "SAFETY_MARGIN", "SAFETY_COEFFICIENT"]
        
        for entity in doc_ai_response.entities:
            if entity.type in safety_types:
                safety = {
                    "type": entity.type.lower(),
                    "text": entity.mention_text,
                    "confidence": entity.confidence,
                    "bounding_box": entity.bounding_box,
                    "page_number": getattr(entity, 'page_number', 1)
                }
                safety_factors.append(safety)
        
        return safety_factors
    
    def _parse_environmental_conditions(self, doc_ai_response: DocumentAIResponse) -> List[Dict[str, Any]]:
        """Parse environmental conditions from Document AI entities."""
        environmental_conditions = []
        
        # Look for environmental condition entities
        env_types = ["WIND_LOAD", "SNOW_LOAD", "TEMPERATURE", "HUMIDITY", "ENVIRONMENTAL_CONDITION"]
        
        for entity in doc_ai_response.entities:
            if entity.type in env_types:
                condition = {
                    "type": entity.type.lower(),
                    "text": entity.mention_text,
                    "confidence": entity.confidence,
                    "bounding_box": entity.bounding_box,
                    "page_number": getattr(entity, 'page_number', 1)
                }
                environmental_conditions.append(condition)
        
        return environmental_conditions
    
    def _extract_loads_from_text(self, text: str) -> List[LoadSpecification]:
        """Extract loads from text using pattern matching."""
        loads = []
        
        # Look for load patterns in the text
        import re
        
        # Pattern for live loads (e.g., "LIVE LOAD: 10kPa")
        live_load_pattern = r'LIVE\s+LOAD[:\s]*(\d+(?:\.\d+)?)\s*(kPa|kN/m²|kN/m2)'
        live_load_matches = re.findall(live_load_pattern, text, re.IGNORECASE)
        for magnitude, unit in live_load_matches:
            load = LoadSpecification(
                load_type=LoadType.LIVE_LOAD,
                magnitude=float(magnitude),
                unit=unit,
                description=f"Live load: {magnitude} {unit}",
                confidence=0.8,
                bounding_box=None
            )
            loads.append(load)
        
        # Pattern for deck loads (e.g., "CLASS 10 DECK")
        deck_load_pattern = r'CLASS\s+(\d+)\s+DECK'
        deck_load_matches = re.findall(deck_load_pattern, text, re.IGNORECASE)
        for class_num in deck_load_matches:
            load = LoadSpecification(
                load_type=LoadType.DEAD_LOAD,
                magnitude=float(class_num),
                unit="class",
                description=f"Class {class_num} deck load",
                confidence=0.8,
                bounding_box=None
            )
            loads.append(load)
        
        # Pattern for dynamic load allowance
        dynamic_load_pattern = r'DYNAMIC\s+LOAD\s+ALLOWANCE[:\s]*(\d+(?:\.\d+)?)'
        dynamic_load_matches = re.findall(dynamic_load_pattern, text, re.IGNORECASE)
        for allowance in dynamic_load_matches:
            load = LoadSpecification(
                load_type=LoadType.OTHER,
                magnitude=float(allowance),
                unit="factor",
                description=f"Dynamic load allowance: {allowance}",
                confidence=0.8,
                bounding_box=None
            )
            loads.append(load)
        
        return loads
    
    def _extract_design_vehicles_from_text(self, text: str) -> List[DesignVehicle]:
        """Extract design vehicles from text using pattern matching."""
        vehicles = []
        
        import re
        
        # Pattern for design vehicle (e.g., "DESIGN VEHICLE: 12.5+ 12.5+ 6.0t")
        vehicle_pattern = r'DESIGN\s+VEHICLE[:\s]*([^.\n]+)'
        vehicle_matches = re.findall(vehicle_pattern, text, re.IGNORECASE)
        for vehicle_spec in vehicle_matches:
            vehicle = DesignVehicle(
                vehicle_type=VehicleType.TRUCK,
                axle_loads=[],  # Could parse from spec
                total_weight=None,
                dimensions=None,
                wheelbase=None,
                unit="t",
                description=f"Design vehicle: {vehicle_spec.strip()}",
                confidence=0.8,
                bounding_box=None
            )
            vehicles.append(vehicle)
        
        return vehicles
    
    def _extract_design_cranes_from_text(self, text: str) -> List[DesignCrane]:
        """Extract design cranes from text using pattern matching."""
        cranes = []
        
        import re
        
        # Pattern for design crane (e.g., "DESIGN CRANE: 4.25m 4.75m")
        crane_pattern = r'DESIGN\s+CRANE[:\s]*([^.\n]+)'
        crane_matches = re.findall(crane_pattern, text, re.IGNORECASE)
        for crane_spec in crane_matches:
            crane = DesignCrane(
                crane_type=CraneType.MOBILE_CRANE,
                capacity=0.0,  # Could parse from spec
                boom_length=None,
                radius=None,
                unit="m",
                description=f"Design crane: {crane_spec.strip()}",
                confidence=0.8,
                bounding_box=None
            )
            cranes.append(crane)
        
        return cranes
    
    def _extract_images_from_document_ai(self, doc_ai_response: DocumentAIResponse, job_id: str) -> List[ImageData]:
        """
        Extract images using Document AI's native image detection and extraction.
        Document AI provides bounding box information, and we extract the actual images
        using the Document AI Toolbox or direct PDF extraction.
        """
        extracted_images = []
        
        try:
            # Create job-specific output directory
            job_output_dir = os.path.join("data/extracted_images", job_id)
            os.makedirs(job_output_dir, exist_ok=True)
            
            # Document AI provides bounding box information for detected images
            # We need to use the Document AI Toolbox to extract the actual image data
            for i, image_info in enumerate(doc_ai_response.images):
                try:
                    # Check if we have bounding box information
                    if image_info.get('bounding_box'):
                        # Use Document AI Toolbox to extract image from bounding box
                        image_filename = f"doc_ai_image_{i+1}.png"
                        image_path = os.path.join(job_output_dir, image_filename)
                        
                        # For now, create a placeholder since Document AI doesn't provide raw image data
                        # In a production system, you would use Document AI Toolbox's export_images method
                        from PIL import Image, ImageDraw, ImageFont
                        
                        # Create a placeholder image with bounding box info
                        img = Image.new('RGB', (400, 300), color='lightblue')
                        draw = ImageDraw.Draw(img)
                        
                        # Add text with bounding box information
                        bbox = image_info['bounding_box']
                        text = f"Document AI Image {i+1}\nPage: {image_info.get('page_number', 'Unknown')}\nConfidence: {image_info.get('confidence', 0.0):.2f}\nBBox: ({bbox['x']:.0f}, {bbox['y']:.0f}, {bbox['width']:.0f}, {bbox['height']:.0f})"
                        
                        # Try to use a default font, fallback to default if not available
                        try:
                            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
                        except:
                            font = ImageFont.load_default()
                        
                        draw.text((10, 10), text, fill='black', font=font)
                        img.save(image_path)
                        
                        # Create ImageData object
                        image_data = ImageData(
                            image_id=f"doc_ai_image_{i+1}",
                            page_number=image_info.get('page_number', 1),
                            bounding_box=image_info.get('bounding_box'),
                            image_type="document_ai_detected",
                            description=f"Image detected by Document AI (Page {image_info.get('page_number', 'Unknown')})",
                            confidence=image_info.get('confidence', 0.0),
                            file_path=os.path.join(job_id, image_filename)
                        )
                        extracted_images.append(image_data)
                        logger.info(f"Created placeholder for Document AI detected image {i+1}")
                    
                except Exception as e:
                    logger.warning(f"Failed to process Document AI image {i+1}: {str(e)}")
                    continue
            
            logger.info(f"Successfully processed {len(extracted_images)} images from Document AI detection")
            
        except Exception as e:
            logger.error(f"Error processing Document AI images: {str(e)}")
        
        return extracted_images
    
    def _extract_entity_images(self, doc_ai_response: DocumentAIResponse, file_path: str, job_id: str) -> List[ImageData]:
        """
        Extract images for each Document AI entity using their bounding boxes.
        Uses Document AI's bounding box information to crop specific areas from the PDF.
        """
        extracted_images = []
        
        try:
            # Create job-specific output directory
            job_output_dir = os.path.join("data/extracted_images", job_id)
            os.makedirs(job_output_dir, exist_ok=True)
            
            # Get PDF page images for cropping
            from .pdf_image_extractor import PDFImageExtractor
            pdf_extractor = PDFImageExtractor()
            page_images = pdf_extractor.extract_pages_as_images(file_path, job_id)
            
            if not page_images:
                logger.warning("No page images available for entity cropping")
                return extracted_images
            
            # Process each entity with bounding box information
            for i, entity in enumerate(doc_ai_response.entities):
                try:
                    logger.info(f"Processing entity {i+1}: {entity.type}")
                    
                    # Check if entity has bounding box information
                    # For DocumentAIEntity objects, bounding_box is a DocumentAIBoundingBox object
                    if hasattr(entity, 'bounding_box') and entity.bounding_box:
                        logger.info(f"Entity {entity.type} has bounding_box: {entity.bounding_box}")
                        
                        # Get page number (default to 1 if not specified)
                        page_number = getattr(entity, 'page_anchor', 1)
                        
                        # Ensure page number is within range
                        if page_number > len(page_images):
                            page_number = 1
                        
                        # Get the corresponding page image
                        page_image_path = page_images[page_number - 1] if page_number <= len(page_images) else page_images[0]
                        
                        # Extract bounding box coordinates from DocumentAIBoundingBox object
                        bbox = entity.bounding_box
                        x = bbox.x
                        y = bbox.y
                        width = bbox.width
                        height = bbox.height
                        
                        logger.info(f"Entity {entity.type} coordinates: x={x}, y={y}, width={width}, height={height}")
                        
                        # Create entity-specific image filename
                        entity_filename = f"entity_{entity.type.lower().replace('_', '')}_{i+1}.png"
                        entity_image_path = os.path.join(job_output_dir, entity_filename)
                        
                        # Crop the image using PIL
                        from PIL import Image
                        
                        try:
                            with Image.open(page_image_path) as page_img:
                                # Get page dimensions
                                page_width, page_height = page_img.size
                                logger.info(f"Page image dimensions: {page_width}x{page_height}")
                                
                                # Convert normalized coordinates to pixel coordinates
                                # Document AI coordinates are normalized (0-1)
                                pixel_x = int(x * page_width)
                                pixel_y = int(y * page_height)
                                pixel_width = int(width * page_width)
                                pixel_height = int(height * page_height)
                                
                                logger.info(f"Pixel coordinates: x={pixel_x}, y={pixel_y}, width={pixel_width}, height={pixel_height}")
                                
                                # Ensure coordinates are within bounds
                                pixel_x = max(0, min(pixel_x, page_width - 1))
                                pixel_y = max(0, min(pixel_y, page_height - 1))
                                pixel_width = max(1, min(pixel_width, page_width - pixel_x))
                                pixel_height = max(1, min(pixel_height, page_height - pixel_y))
                                
                                # Crop the image
                                cropped_img = page_img.crop((pixel_x, pixel_y, pixel_x + pixel_width, pixel_y + pixel_height))
                                
                                # Save the cropped image
                                cropped_img.save(entity_image_path)
                                
                                # Create ImageData object
                                image_data = ImageData(
                                    image_id=f"entity_{entity.type.lower()}_{i+1}",
                                    page_number=page_number,
                                    bounding_box={
                                        'x': x,
                                        'y': y,
                                        'width': width,
                                        'height': height
                                    },
                                    image_type=f"entity_{entity.type.lower()}",
                                    description=f"{entity.type} entity: {entity.mention_text[:100]}...",
                                    confidence=entity.confidence,
                                    file_path=os.path.join(job_id, entity_filename)
                                )
                                extracted_images.append(image_data)
                                logger.info(f"Extracted image for {entity.type} entity: {entity_filename}")
                        
                        except Exception as e:
                            logger.warning(f"Failed to crop image for {entity.type} entity: {str(e)}")
                            # Create a placeholder image instead
                            self._create_entity_placeholder(entity, entity_image_path, i+1)
                            
                            image_data = ImageData(
                                image_id=f"entity_{entity.type.lower()}_{i+1}",
                                page_number=page_number,
                                bounding_box={
                                    'x': x,
                                    'y': y,
                                    'width': width,
                                    'height': height
                                },
                                image_type=f"entity_{entity.type.lower()}_placeholder",
                                description=f"{entity.type} entity (placeholder): {entity.mention_text[:100]}...",
                                confidence=entity.confidence,
                                file_path=os.path.join(job_id, entity_filename)
                            )
                            extracted_images.append(image_data)
                    else:
                        logger.info(f"Entity {entity.type} has no bounding box information")
                        # Create a placeholder image for entities without bounding box
                        entity_filename = f"entity_{entity.type.lower().replace('_', '')}_{i+1}_placeholder.png"
                        entity_image_path = os.path.join(job_output_dir, entity_filename)
                        self._create_entity_placeholder(entity, entity_image_path, i+1)
                        
                        image_data = ImageData(
                            image_id=f"entity_{entity.type.lower()}_{i+1}",
                            page_number=1,
                            bounding_box=None,
                            image_type=f"entity_{entity.type.lower()}_placeholder",
                            description=f"{entity.type} entity (no bbox): {entity.mention_text[:100]}...",
                            confidence=entity.confidence,
                            file_path=os.path.join(job_id, entity_filename)
                        )
                        extracted_images.append(image_data)
                        # Get page number (default to 1 if not specified)
                        page_number = getattr(entity, 'page_number', 1)
                        
                        # Ensure page number is within range
                        if page_number > len(page_images):
                            page_number = 1
                        
                        # Get the corresponding page image
                        page_image_path = page_images[page_number - 1] if page_number <= len(page_images) else page_images[0]
                        
                        # Extract bounding box coordinates
                        bbox = entity.bounding_box
                        x = getattr(bbox, 'x', 0)
                        y = getattr(bbox, 'y', 0)
                        width = getattr(bbox, 'width', 0)
                        height = getattr(bbox, 'height', 0)
                        
                        # Create entity-specific image filename
                        entity_filename = f"entity_{entity.type.lower().replace('_', '')}_{i+1}.png"
                        entity_image_path = os.path.join(job_output_dir, entity_filename)
                        
                        # Crop the image using PIL
                        from PIL import Image
                        
                        try:
                            with Image.open(page_image_path) as page_img:
                                # Get page dimensions
                                page_width, page_height = page_img.size
                                
                                # Convert normalized coordinates to pixel coordinates
                                # Document AI coordinates are normalized (0-1)
                                pixel_x = int(x * page_width)
                                pixel_y = int(y * page_height)
                                pixel_width = int(width * page_width)
                                pixel_height = int(height * page_height)
                                
                                # Ensure coordinates are within bounds
                                pixel_x = max(0, min(pixel_x, page_width - 1))
                                pixel_y = max(0, min(pixel_y, page_height - 1))
                                pixel_width = max(1, min(pixel_width, page_width - pixel_x))
                                pixel_height = max(1, min(pixel_height, page_height - pixel_y))
                                
                                # Crop the image
                                cropped_img = page_img.crop((pixel_x, pixel_y, pixel_x + pixel_width, pixel_y + pixel_height))
                                
                                # Save the cropped image
                                cropped_img.save(entity_image_path)
                                
                                # Create ImageData object
                                image_data = ImageData(
                                    image_id=f"entity_{entity.type.lower()}_{i+1}",
                                    page_number=page_number,
                                    bounding_box={
                                        'x': x,
                                        'y': y,
                                        'width': width,
                                        'height': height
                                    },
                                    image_type=f"entity_{entity.type.lower()}",
                                    description=f"{entity.type} entity: {entity.mention_text[:100]}...",
                                    confidence=entity.confidence,
                                    file_path=os.path.join(job_id, entity_filename)
                                )
                                extracted_images.append(image_data)
                                logger.info(f"Extracted image for {entity.type} entity: {entity_filename}")
                        
                        except Exception as e:
                            logger.warning(f"Failed to crop image for {entity.type} entity: {str(e)}")
                            # Create a placeholder image instead
                            self._create_entity_placeholder(entity, entity_image_path, i+1)
                            
                            image_data = ImageData(
                                image_id=f"entity_{entity.type.lower()}_{i+1}",
                                page_number=page_number,
                                bounding_box={
                                    'x': x,
                                    'y': y,
                                    'width': width,
                                    'height': height
                                },
                                image_type=f"entity_{entity.type.lower()}_placeholder",
                                description=f"{entity.type} entity (placeholder): {entity.mention_text[:100]}...",
                                confidence=entity.confidence,
                                file_path=os.path.join(job_id, entity_filename)
                            )
                            extracted_images.append(image_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to process entity {i+1} ({getattr(entity, 'type', 'Unknown')}): {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(extracted_images)} entity images")
            
        except Exception as e:
            logger.error(f"Error extracting entity images: {str(e)}")
        
        return extracted_images
    
    def _extract_entity_images_with_bbox(self, original_document, file_path: str, job_id: str) -> List[ImageData]:
        """
        Extract images for each Document AI entity using their bounding boxes from the original Document AI response.
        """
        extracted_images = []
        
        try:
            # Create job-specific output directory
            job_output_dir = os.path.join("data/extracted_images", job_id)
            os.makedirs(job_output_dir, exist_ok=True)
            
            # Get PDF page images for cropping
            from .pdf_image_extractor import PDFImageExtractor
            pdf_extractor = PDFImageExtractor()
            page_images = pdf_extractor.extract_pages_as_images(file_path, job_id)
            
            if not page_images:
                logger.warning("No page images available for entity cropping")
                return extracted_images
            
            # Process each entity with bounding box information from original Document AI response
            for i, entity in enumerate(original_document.entities):
                try:
                    logger.info(f"Processing entity {i+1}: {entity.type_} with original Document AI response")
                    
                    # Debug: Log the entity structure
                    logger.info(f"Entity {entity.type_} structure:")
                    logger.info(f"  - has page_anchor: {hasattr(entity, 'page_anchor')}")
                    if hasattr(entity, 'page_anchor') and entity.page_anchor:
                        logger.info(f"  - page_anchor: {entity.page_anchor}")
                        logger.info(f"  - has page_refs: {hasattr(entity.page_anchor, 'page_refs')}")
                        if hasattr(entity.page_anchor, 'page_refs') and entity.page_anchor.page_refs:
                            logger.info(f"  - page_refs length: {len(entity.page_anchor.page_refs)}")
                            page_ref = entity.page_anchor.page_refs[0]
                            logger.info(f"  - page_ref: {page_ref}")
                            logger.info(f"  - has bounding_poly: {hasattr(page_ref, 'bounding_poly')}")
                            if hasattr(page_ref, 'bounding_poly') and page_ref.bounding_poly:
                                logger.info(f"  - bounding_poly: {page_ref.bounding_poly}")
                                logger.info(f"  - has vertices: {hasattr(page_ref.bounding_poly, 'vertices')}")
                                if hasattr(page_ref.bounding_poly, 'vertices') and page_ref.bounding_poly.vertices:
                                    logger.info(f"  - vertices length: {len(page_ref.bounding_poly.vertices)}")
                                    for j, vertex in enumerate(page_ref.bounding_poly.vertices):
                                        logger.info(f"    - vertex {j}: x={vertex.x}, y={vertex.y}")
                    
                    # Extract bounding box from original Document AI entity
                    bounding_box = None
                    page_number = 1
                    
                    if entity.page_anchor and entity.page_anchor.page_refs:
                        page_ref = entity.page_anchor.page_refs[0]
                        page_number = page_ref.page
                        
                        if hasattr(page_ref, 'bounding_poly') and page_ref.bounding_poly.normalized_vertices:
                            vertices = page_ref.bounding_poly.normalized_vertices
                            if len(vertices) >= 4:
                                # Calculate bounding box from normalized vertices
                                x_coords = [v.x for v in vertices]
                                y_coords = [v.y for v in vertices]
                                
                                x_min, x_max = min(x_coords), max(x_coords)
                                y_min, y_max = min(y_coords), max(y_coords)
                                
                                bounding_box = {
                                    "x": x_min,
                                    "y": y_min,
                                    "width": x_max - x_min,
                                    "height": y_max - y_min
                                }
                                logger.info(f"Entity {entity.type_} has bounding box: {bounding_box}")
                    
                    if bounding_box:
                        # Ensure page number is within range
                        if page_number > len(page_images):
                            page_number = 1
                        
                        # Get the corresponding page image
                        page_image_path = page_images[page_number - 1] if page_number <= len(page_images) else page_images[0]
                        
                        # Extract coordinates
                        x = bounding_box["x"]
                        y = bounding_box["y"]
                        width = bounding_box["width"]
                        height = bounding_box["height"]
                        
                        logger.info(f"Entity {entity.type_} coordinates: x={x}, y={y}, width={width}, height={height}")
                        
                        # Create entity-specific image filename
                        entity_filename = f"entity_{entity.type_.lower().replace('_', '')}_{i+1}.png"
                        entity_image_path = os.path.join(job_output_dir, entity_filename)
                        
                        # Crop the image using PIL
                        from PIL import Image
                        
                        try:
                            with Image.open(page_image_path) as page_img:
                                # Get page dimensions
                                page_width, page_height = page_img.size
                                logger.info(f"Page image dimensions: {page_width}x{page_height}")
                                
                                # Convert normalized coordinates to pixel coordinates
                                # Document AI coordinates are normalized (0-1)
                                pixel_x = int(x * page_width)
                                pixel_y = int(y * page_height)
                                pixel_width = int(width * page_width)
                                pixel_height = int(height * page_height)
                                
                                logger.info(f"Pixel coordinates: x={pixel_x}, y={pixel_y}, width={pixel_width}, height={pixel_height}")
                                
                                # Ensure coordinates are within bounds
                                pixel_x = max(0, min(pixel_x, page_width - 1))
                                pixel_y = max(0, min(pixel_y, page_height - 1))
                                pixel_width = max(1, min(pixel_width, page_width - pixel_x))
                                pixel_height = max(1, min(pixel_height, page_height - pixel_y))
                                
                                # Crop the image
                                cropped_img = page_img.crop((pixel_x, pixel_y, pixel_x + pixel_width, pixel_y + pixel_height))
                                
                                # Save the cropped image
                                cropped_img.save(entity_image_path)
                                
                                # Create ImageData object
                                image_data = ImageData(
                                    image_id=f"entity_{entity.type_.lower()}_{i+1}",
                                    page_number=page_number,
                                    bounding_box=bounding_box,
                                    image_type=f"entity_{entity.type_.lower()}",
                                    description=f"{entity.type_} entity: {entity.mention_text[:100]}...",
                                    confidence=entity.confidence,
                                    file_path=os.path.join(job_id, entity_filename)
                                )
                                extracted_images.append(image_data)
                                logger.info(f"Extracted image for {entity.type_} entity: {entity_filename}")
                        
                        except Exception as e:
                            logger.warning(f"Failed to crop image for {entity.type_} entity: {str(e)}")
                            # Create a placeholder image instead
                            self._create_entity_placeholder_from_original(entity, entity_image_path, i+1)
                            
                            image_data = ImageData(
                                image_id=f"entity_{entity.type_.lower()}_{i+1}",
                                page_number=page_number,
                                bounding_box=bounding_box,
                                image_type=f"entity_{entity.type_.lower()}_placeholder",
                                description=f"{entity.type_} entity (placeholder): {entity.mention_text[:100]}...",
                                confidence=entity.confidence,
                                file_path=os.path.join(job_id, entity_filename)
                            )
                            extracted_images.append(image_data)
                    else:
                        logger.info(f"Entity {entity.type_} has no bounding box information")
                        # Create a placeholder image for entities without bounding box
                        entity_filename = f"entity_{entity.type_.lower().replace('_', '')}_{i+1}_placeholder.png"
                        entity_image_path = os.path.join(job_output_dir, entity_filename)
                        self._create_entity_placeholder_from_original(entity, entity_image_path, i+1)
                        
                        image_data = ImageData(
                            image_id=f"entity_{entity.type_.lower()}_{i+1}",
                            page_number=page_number,
                            bounding_box=None,
                            image_type=f"entity_{entity.type_.lower()}_placeholder",
                            description=f"{entity.type_} entity (no bbox): {entity.mention_text[:100]}...",
                            confidence=entity.confidence,
                            file_path=os.path.join(job_id, entity_filename)
                        )
                        extracted_images.append(image_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to process entity {i+1} ({getattr(entity, 'type_', 'Unknown')}): {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(extracted_images)} entity images with bounding boxes")
            
        except Exception as e:
            logger.error(f"Error extracting entity images with bounding boxes: {str(e)}")
        
        return extracted_images
    
    def _create_entity_placeholder_from_original(self, entity, image_path: str, entity_index: int):
        """Create a placeholder image for an entity from original Document AI response."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a placeholder image
            img = Image.new('RGB', (400, 200), color='lightyellow')
            draw = ImageDraw.Draw(img)
            
            # Add entity information
            text_lines = [
                f"Entity {entity_index}",
                f"Type: {entity.type_}",
                f"Confidence: {entity.confidence:.2f}",
                f"Text: {entity.mention_text[:50]}..."
            ]
            
            # Try to use a default font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            y_offset = 10
            for line in text_lines:
                draw.text((10, y_offset), line, fill='black', font=font)
                y_offset += 20
            
            img.save(image_path)
            logger.info(f"Created placeholder for {entity.type_} entity")
            
        except Exception as e:
            logger.error(f"Failed to create placeholder for entity: {str(e)}")
    
    def _create_entity_placeholder(self, entity, image_path: str, entity_index: int):
        """Create a placeholder image for an entity when cropping fails."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a placeholder image
            img = Image.new('RGB', (400, 200), color='lightyellow')
            draw = ImageDraw.Draw(img)
            
            # Add entity information
            text_lines = [
                f"Entity {entity_index}",
                f"Type: {entity.type}",
                f"Confidence: {entity.confidence:.2f}",
                f"Text: {entity.mention_text[:50]}..."
            ]
            
            # Try to use a default font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            y_offset = 10
            for line in text_lines:
                draw.text((10, y_offset), line, fill='black', font=font)
                y_offset += 20
            
            img.save(image_path)
            logger.info(f"Created placeholder for {entity.type} entity")
            
        except Exception as e:
            logger.error(f"Failed to create placeholder for entity: {str(e)}")
    
    def _extract_images_for_engineering_fields(self, doc_ai_response, loads, seismic_forces, design_vehicles, design_cranes, tables, design_criteria, design_loads, drg_no, title, date, file_path: str, job_id: str) -> List[ImageData]:
        """
        Extract images specifically for detected engineering fields with bounding boxes.
        Only extracts images for fields that have content and bounding box information.
        """
        extracted_images = []
        
        # Check if any engineering fields were detected
        has_engineering_fields = (
            loads or 
            seismic_forces or 
            design_vehicles or 
            design_cranes or
            tables or
            design_criteria or
            design_loads or
            drg_no or
            title or
            date
        )
        
        if not has_engineering_fields:
            logger.info("No engineering fields detected. Skipping image extraction.")
            return []
        
        try:
            # Create job-specific output directory
            job_output_dir = os.path.join("data/extracted_images", job_id)
            os.makedirs(job_output_dir, exist_ok=True)
            
            # Extract full page images first for cropping
            from .pdf_image_extractor import PDFImageExtractor
            pdf_extractor = PDFImageExtractor()
            page_images = pdf_extractor.extract_pages_as_images(file_path, job_id)
            
            if not page_images:
                logger.warning("Could not extract page images for cropping. Skipping field-specific image extraction.")
                return []
            
            # Create mapping of page number to page image path
            page_image_map = {}
            for page_path in page_images:
                filename = os.path.basename(page_path)
                if filename.startswith('page_') and filename.endswith('.png'):
                    try:
                        page_num = int(filename.replace('page_', '').replace('.png', ''))
                        page_image_map[page_num] = page_path
                    except ValueError:
                        continue
            
            image_count = 0
            
            # Extract images for loads
            for load in loads:
                if load.bounding_box:
                    image_data = self._crop_image_from_bounding_box(
                        load.bounding_box, load.description, "load", 
                        page_image_map, job_output_dir, image_count, file_path
                    )
                    if image_data:
                        extracted_images.append(image_data)
                        image_count += 1
            
            # Extract images for seismic forces
            for seismic in seismic_forces:
                if seismic.bounding_box:
                    image_data = self._crop_image_from_bounding_box(
                        seismic.bounding_box, seismic.description, "seismic_force", 
                        page_image_map, job_output_dir, image_count, file_path
                    )
                    if image_data:
                        extracted_images.append(image_data)
                        image_count += 1
            
            # Extract images for design vehicles
            for vehicle in design_vehicles:
                if vehicle.bounding_box:
                    image_data = self._crop_image_from_bounding_box(
                        vehicle.bounding_box, vehicle.description, "design_vehicle", 
                        page_image_map, job_output_dir, image_count, file_path
                    )
                    if image_data:
                        extracted_images.append(image_data)
                        image_count += 1
            
            # Extract images for design cranes
            for crane in design_cranes:
                if crane.bounding_box:
                    image_data = self._crop_image_from_bounding_box(
                        crane.bounding_box, crane.description, "design_crane", 
                        page_image_map, job_output_dir, image_count, file_path
                    )
                    if image_data:
                        extracted_images.append(image_data)
                        image_count += 1
            
            # Extract images for tables
            for table in tables:
                if table.bounding_box:
                    image_data = self._crop_image_from_bounding_box(
                        table.bounding_box, f"Table {table.table_id}", "table", 
                        page_image_map, job_output_dir, image_count, file_path
                    )
                    if image_data:
                        extracted_images.append(image_data)
                        image_count += 1
            
            # Extract images for design criteria
            for criteria in design_criteria:
                if criteria.get('bounding_box'):
                    image_data = self._crop_image_from_bounding_box(
                        criteria['bounding_box'], criteria['text'], "design_criteria", 
                        page_image_map, job_output_dir, image_count, file_path
                    )
                    if image_data:
                        extracted_images.append(image_data)
                        image_count += 1
            
            # Extract images for design loads
            for load in design_loads:
                if load.get('bounding_box'):
                    image_data = self._crop_image_from_bounding_box(
                        load['bounding_box'], load['text'], "design_loads", 
                        page_image_map, job_output_dir, image_count, file_path
                    )
                    if image_data:
                        extracted_images.append(image_data)
                        image_count += 1
            
            # Extract images for DRG numbers
            for drg in drg_no:
                if drg.get('bounding_box'):
                    image_data = self._crop_image_from_bounding_box(
                        drg['bounding_box'], drg['text'], "drg_no", 
                        page_image_map, job_output_dir, image_count, file_path
                    )
                    if image_data:
                        extracted_images.append(image_data)
                        image_count += 1
            
            # Extract images for titles
            for title_item in title:
                if title_item.get('bounding_box'):
                    image_data = self._crop_image_from_bounding_box(
                        title_item['bounding_box'], title_item['text'], "title", 
                        page_image_map, job_output_dir, image_count, file_path
                    )
                    if image_data:
                        extracted_images.append(image_data)
                        image_count += 1
            
            # Extract images for dates
            for date_item in date:
                if date_item.get('bounding_box'):
                    image_data = self._crop_image_from_bounding_box(
                        date_item['bounding_box'], date_item['text'], "date", 
                        page_image_map, job_output_dir, image_count, file_path
                    )
                    if image_data:
                        extracted_images.append(image_data)
                        image_count += 1
            
            logger.info(f"Extracted {len(extracted_images)} images for engineering fields")
            
        except Exception as e:
            logger.error(f"Error extracting images for engineering fields: {str(e)}")
        
        return extracted_images
    
    def _crop_image_from_bounding_box(self, bounding_box, description, field_type, page_image_map, job_output_dir, image_count, file_path):
        """
        Crop an image from a page based on bounding box coordinates.
        """
        try:
            from PIL import Image
            
            # Get page number from bounding box (assuming it's stored in the bounding box)
            page_number = bounding_box.get('page_number', 1)
            
            if page_number not in page_image_map:
                logger.warning(f"Page {page_number} image not found for cropping")
                return None
            
            # Open the page image
            page_image_path = page_image_map[page_number]
            page_image = Image.open(page_image_path)
            
            # Get bounding box coordinates
            x = bounding_box.get('x', 0)
            y = bounding_box.get('y', 0)
            width = bounding_box.get('width', 0)
            height = bounding_box.get('height', 0)
            
            # Convert Document AI coordinates to pixel coordinates
            # Document AI coordinates are in points (1/72 inch) relative to the PDF page
            # We need to get the actual PDF page dimensions and scale accordingly
            
            # Get the page dimensions from the image
            img_width, img_height = page_image.size
            
            # Try to get the actual PDF page dimensions
            try:
                import fitz  # PyMuPDF
                pdf_doc = fitz.open(file_path)
                if page_number <= len(pdf_doc):
                    pdf_page = pdf_doc[page_number - 1]  # 0-indexed
                    pdf_rect = pdf_page.rect
                    pdf_width = pdf_rect.width
                    pdf_height = pdf_rect.height
                    pdf_doc.close()
                    
                    # Calculate scale factors based on actual PDF page dimensions
                    scale_x = img_width / pdf_width
                    scale_y = img_height / pdf_height
                    scale_factor = min(scale_x, scale_y)  # Use the smaller scale to maintain aspect ratio
                    
                    logger.info(f"PDF page dimensions: {pdf_width}x{pdf_height}, Image dimensions: {img_width}x{img_height}, Scale factor: {scale_factor}")
                else:
                    # Fallback to standard A4 dimensions
                    scale_factor = min(img_width / 595.0, img_height / 842.0)
                    logger.warning(f"Page {page_number} not found, using fallback scale factor: {scale_factor}")
            except Exception as e:
                # Fallback to standard A4 dimensions
                scale_factor = min(img_width / 595.0, img_height / 842.0)
                logger.warning(f"Could not get PDF page dimensions, using fallback scale factor: {scale_factor}")
            
            # Convert coordinates using the calculated scale factor
            left = int(x * scale_factor)
            upper = int(y * scale_factor)
            right = int((x + width) * scale_factor)
            lower = int((y + height) * scale_factor)
            
            # Add buffer around the crop area
            buffer = 10
            left = max(0, left - buffer)
            upper = max(0, upper - buffer)
            right = min(page_image.width, right + buffer)
            lower = min(page_image.height, lower + buffer)
            
            # Ensure valid crop dimensions
            if right <= left or lower <= upper:
                logger.warning(f"Invalid crop dimensions for {field_type}: {left}, {upper}, {right}, {lower}")
                logger.warning(f"Original bounding box: x={x}, y={y}, width={width}, height={height}")
                logger.warning(f"Page image size: {page_image.size}, scale_factor: {scale_factor}")
                return None
            
            # Log successful crop dimensions
            logger.info(f"Successfully calculated crop dimensions for {field_type}: {left}, {upper}, {right}, {lower}")
            logger.info(f"Original bounding box: x={x}, y={y}, width={width}, height={height}")
            logger.info(f"Page image size: {page_image.size}, scale_factor: {scale_factor}")
            
            # Crop the image
            cropped_image = page_image.crop((left, upper, right, lower))
            
            # Save the cropped image
            safe_description = "".join(c for c in description if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_description = safe_description.replace(' ', '_')[:30]  # Limit length
            image_filename = f"{field_type}_{safe_description}_{image_count + 1}.png"
            image_path = os.path.join(job_output_dir, image_filename)
            
            cropped_image.save(image_path)
            
            # Create ImageData object
            image_data = ImageData(
                image_id=f"{field_type}_image_{image_count + 1}",
                page_number=page_number,
                bounding_box=bounding_box,
                image_type=field_type,
                description=description,
                confidence=1.0,  # High confidence since we're cropping from detected entities
                file_path=os.path.join(job_id, image_filename)
            )
            
            logger.info(f"Extracted image for {field_type}: {description}")
            return image_data
            
        except Exception as e:
            logger.error(f"Error cropping image for {field_type}: {str(e)}")
            return None
    
    def _parse_loads(self, doc_ai_response: DocumentAIResponse) -> List[LoadSpecification]:
        """Parse loads from Document AI entities using exact field names."""
        loads = []
        
        for entity in doc_ai_response.entities:
            # Use exact field names from Document AI configuration
            if entity.type in ["BERTHING_LOADS", "MOORING_LOADS", "VERTICAL_DEAD_LOADS", "VERTICAL_LIVE_LOADS", "WIND_LOADS"]:
                # Map entity type to load type
                load_type_map = {
                    "BERTHING_LOADS": LoadType.OTHER,
                    "MOORING_LOADS": LoadType.OTHER,
                    "VERTICAL_DEAD_LOADS": LoadType.DEAD_LOAD,
                    "VERTICAL_LIVE_LOADS": LoadType.LIVE_LOAD,
                    "WIND_LOADS": LoadType.WIND_LOAD
                }
                
                # Extract load information from entity
                load = LoadSpecification(
                    load_type=load_type_map.get(entity.type, LoadType.OTHER),
                    magnitude=0.0,  # Extract from text
                    unit="",  # Extract from text
                    description=entity.mention_text,
                    confidence=entity.confidence,
                    bounding_box=entity.bounding_box
                )
                loads.append(load)
                logger.info(f"Extracted load: {entity.type} - {entity.mention_text[:50]}...")
        
        return loads
    
    def _parse_seismic_forces(self, doc_ai_response: DocumentAIResponse) -> List[SeismicForce]:
        """Parse seismic forces from Document AI entities using exact field names."""
        seismic_forces = []
        
        for entity in doc_ai_response.entities:
            # Use exact field name from Document AI configuration
            if entity.type == "SEISMIC_FORCES":
                seismic_force = SeismicForce(
                    unit="",  # Extract from text
                    description=entity.mention_text,
                    confidence=entity.confidence,
                    bounding_box=entity.bounding_box
                )
                seismic_forces.append(seismic_force)
                logger.info(f"Extracted seismic force: {entity.mention_text[:50]}...")
        
        return seismic_forces
    
    def _parse_design_vehicles(self, doc_ai_response: DocumentAIResponse) -> List[DesignVehicle]:
        """Parse design vehicles from Document AI entities using exact field names."""
        vehicles = []
        
        for entity in doc_ai_response.entities:
            # Check for DESIGN_VEHICLE entity or extract from DESIGN_CRITERIA
            if entity.type == "DESIGN_VEHICLE":
                vehicle = DesignVehicle(
                    vehicle_type=VehicleType.OTHER,
                    unit="",  # Extract from text
                    description=entity.mention_text,
                    confidence=entity.confidence,
                    bounding_box=entity.bounding_box
                )
                vehicles.append(vehicle)
                logger.info(f"Extracted design vehicle: {entity.mention_text[:50]}...")
            elif entity.type == "DESIGN_CRITERIA" and "DESIGN VEHICLE:" in entity.mention_text:
                # Extract design vehicle from DESIGN_CRITERIA text
                text = entity.mention_text
                if "DESIGN VEHICLE:" in text:
                    # Extract the design vehicle information
                    vehicle_info = text.split("DESIGN VEHICLE:")[1].split("DESIGN CRANE:")[0].strip()
                    vehicle = DesignVehicle(
                        vehicle_type=VehicleType.OTHER,
                        unit="",  # Extract from text
                        description=vehicle_info,
                        confidence=entity.confidence,
                        bounding_box=entity.bounding_box
                    )
                    vehicles.append(vehicle)
                    logger.info(f"Extracted design vehicle from DESIGN_CRITERIA: {vehicle_info[:50]}...")
        
        return vehicles
    
    def _parse_design_cranes(self, doc_ai_response: DocumentAIResponse) -> List[DesignCrane]:
        """Parse design cranes from Document AI entities using exact field names."""
        cranes = []
        
        for entity in doc_ai_response.entities:
            # Check for DESIGN_CRANE entity or extract from DESIGN_CRITERIA
            if entity.type == "DESIGN_CRANE":
                crane = DesignCrane(
                    crane_type=CraneType.OTHER,
                    capacity=0.0,  # Extract from text
                    unit="",  # Extract from text
                    description=entity.mention_text,
                    confidence=entity.confidence,
                    bounding_box=entity.bounding_box
                )
                cranes.append(crane)
                logger.info(f"Extracted design crane: {entity.mention_text[:50]}...")
            elif entity.type == "DESIGN_CRITERIA" and "DESIGN CRANE:" in entity.mention_text:
                # Extract design crane from DESIGN_CRITERIA text
                text = entity.mention_text
                if "DESIGN CRANE:" in text:
                    # Extract the design crane information
                    crane_info = text.split("DESIGN CRANE:")[1].split("DYNAMIC LOAD ALLOWAN")[0].strip()
                    crane = DesignCrane(
                        crane_type=CraneType.OTHER,
                        capacity=0.0,  # Extract from text
                        unit="",  # Extract from text
                        description=crane_info,
                        confidence=entity.confidence,
                        bounding_box=entity.bounding_box
                    )
                    cranes.append(crane)
                    logger.info(f"Extracted design crane from DESIGN_CRITERIA: {crane_info[:50]}...")
        
        return cranes
    
    def _parse_tables(self, doc_ai_response: DocumentAIResponse) -> List[TableData]:
        """Parse tables from Document AI response."""
        tables = []
        
        for table in doc_ai_response.tables:
            table_data = TableData(
                table_id=table["table_id"],
                page_number=table["page_number"],
                headers=table["headers"][0] if table["headers"] else [],
                rows=table["rows"],
                bounding_box=table["bounding_box"],
                confidence=table["confidence"]
            )
            tables.append(table_data)
        
        return tables
    
    def _parse_images(self, doc_ai_response: DocumentAIResponse, extracted_image_files: List[str] = None) -> List[ImageData]:
        """Parse images from Document AI response or extracted PDF images."""
        images = []
        
        # If we have real extracted images, use those instead of Document AI placeholders
        if extracted_image_files and len(extracted_image_files) > 0:
            for i, image_path in enumerate(extracted_image_files):
                # Extract page number from filename (e.g., pdf_image_1_2.png -> page 1)
                filename = os.path.basename(image_path)
                page_number = 1  # default
                
                # Parse page number from filename
                if filename.startswith('pdf_image_'):
                    try:
                        parts = filename.replace('.png', '').split('_')
                        if len(parts) >= 3:
                            page_number = int(parts[2])
                    except:
                        pass
                
                image_data = ImageData(
                    image_id=f"pdf_image_{i+1}",
                    page_number=page_number,
                    bounding_box=None,  # We don't have bounding box info from PDF extraction
                    confidence=1.0  # High confidence since these are real extracted images
                )
                
                # Store relative path from data/extracted_images/
                if image_path.startswith('data/extracted_images/'):
                    image_data.file_path = image_path.replace('data/extracted_images/', '')
                else:
                    image_data.file_path = image_path
                
                images.append(image_data)
        else:
            # Fall back to Document AI images if no real images were extracted
            for i, image in enumerate(doc_ai_response.images):
                image_data = ImageData(
                    image_id=image.get("image_id", f"image_{i}"),
                    page_number=image.get("page_number", 1),
                    bounding_box=image.get("bounding_box"),
                    confidence=image.get("confidence", 0.0)
                )
                
                # Add extracted image file path if available
                if extracted_image_files and i < len(extracted_image_files):
                    # Store relative path from data/extracted_images/
                    full_path = extracted_image_files[i]
                    if full_path.startswith('data/extracted_images/'):
                        image_data.file_path = full_path.replace('data/extracted_images/', '')
                    else:
                        image_data.file_path = full_path
                
                images.append(image_data)
        
        return images 