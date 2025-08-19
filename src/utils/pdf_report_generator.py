"""
PDF Report Generator for Engineering Design Criteria Extraction
Generates comprehensive PDF reports with extracted fields, entity text, and images.
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import blue, black, grey, white, lightgrey
from reportlab.lib import colors
from PIL import Image
import tempfile
import logging

logger = logging.getLogger(__name__)


class EngineeringPDFReportGenerator:
    """Generate comprehensive PDF reports for engineering document extraction results."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=5,
            backColor=colors.lightgrey
        ))
        
        # Field header style
        self.styles.add(ParagraphStyle(
            name='FieldHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.darkgreen
        ))
        
        # Entity text style
        self.styles.add(ParagraphStyle(
            name='EntityText',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Courier',
            spaceBefore=5,
            spaceAfter=5,
            backColor=colors.lightgrey,
            borderWidth=1,
            borderColor=colors.grey,
            borderPadding=8
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            spaceBefore=3,
            spaceAfter=3
        ))
    
    def generate_engineering_report(self, 
                                  design_criteria: Dict[str, Any], 
                                  output_path: str,
                                  job_id: str,
                                  image_base_path: str = None) -> bool:
        """
        Generate a comprehensive PDF report with extracted engineering data.
        
        Args:
            design_criteria: Extracted design criteria data
            output_path: Path to save the PDF report
            job_id: Job identifier for image paths
            image_base_path: Base path for entity images
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            # Add title and metadata
            self._add_title_section(story, design_criteria)
            
            # Add document metadata
            self._add_metadata_section(story, design_criteria)
            
            # Add summary table
            summary_table = self._create_summary_table(design_criteria)
            if summary_table:
                story.append(Paragraph("Extraction Summary", self.styles['SectionHeader']))
                story.append(summary_table)
                story.append(Spacer(1, 20))
            
            # Add Document AI entities section only
            self._add_entities_section(story, design_criteria, image_base_path, job_id)
            
            # Build PDF
            doc.build(story)
            logger.info(f"PDF report generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return False
    
    def _add_title_section(self, story: List, design_criteria: Dict[str, Any]):
        """Add title and header information."""
        story.append(Paragraph("Engineering Design Criteria Extraction Report", self.styles['ReportTitle']))
        story.append(Spacer(1, 20))
        
        # Add generation info
        generation_info = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(generation_info, self.styles['Metadata']))
        story.append(Spacer(1, 30))
    
    def _add_metadata_section(self, story: List, design_criteria: Dict[str, Any]):
        """Add document metadata section."""
        story.append(Paragraph("Document Information", self.styles['SectionHeader']))
        
        metadata = design_criteria.get('metadata', {})
        
        # Create metadata table
        metadata_data = [
            ['Property', 'Value'],
            ['Filename', metadata.get('filename', 'N/A')],
            ['File Size', f"{metadata.get('file_size', 0):,} bytes"],
            ['Page Count', str(metadata.get('page_count', 'N/A'))],
            ['Processing Date', str(metadata.get('processing_date', 'N/A'))],
            ['Overall Confidence', f"{design_criteria.get('confidence_score', 0) * 100:.1f}%"]
        ]
        
        table = Table(metadata_data, colWidths=[4*cm, 8*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
    
    def _add_specific_fields_section(self, story: List, design_criteria: Dict[str, Any], 
                                   image_base_path: str, job_id: str):
        """Add specific extracted fields section."""
        story.append(Paragraph("Extracted Fields", self.styles['SectionHeader']))
        
        # Define the new field types
        field_types = [
            'berthing_loads', 'date', 'design_criteria', 'design_loads',
            'drawing_number', 'drawing_title', 'mooring_loads', 
            'vertical_dead_loads', 'vertical_live_loads', 'wind_loads'
        ]
        
        # Get images for matching with fields
        images = design_criteria.get('images', [])
        
        for field_type in field_types:
            field_data = design_criteria.get(field_type, [])
            if field_data:
                self._add_field_section(story, field_type, field_data, image_base_path, job_id, images)
        
        story.append(Spacer(1, 20))
    
    def _add_field_section(self, story: List, field_type: str, field_data: List[Dict], 
                          image_base_path: str, job_id: str, images: List[Dict]):
        """Add a specific field section with text and images."""
        # Format field name for display
        display_name = field_type.replace('_', ' ').title()
        story.append(Paragraph(display_name, self.styles['FieldHeader']))
        
        for i, field_item in enumerate(field_data):
            # Add field text
            field_text = field_item.get('text', 'No text available')
            confidence = field_item.get('confidence', 0)
            
            text_content = f"<b>Text:</b> {field_text}<br/>"
            text_content += f"<b>Confidence:</b> {confidence * 100:.1f}%<br/>"
            
            if field_item.get('page_number'):
                text_content += f"<b>Page:</b> {field_item['page_number']}<br/>"
            
            story.append(Paragraph(text_content, self.styles['Normal']))
            
            # Add associated image if available
            self._add_field_image_from_results(story, field_type, field_text, images, image_base_path)
            
            story.append(Spacer(1, 15))
    
    def _add_field_image(self, story: List, field_type: str, index: int, 
                        image_base_path: str, job_id: str):
        """Add field-specific image if available."""
        if not image_base_path or not job_id:
            return
        
        # Try multiple possible image filename patterns
        possible_filenames = [
            f"entity_{field_type.lower()}_{index}.png",
            f"entity_{field_type.lower().replace('_', '')}_{index}.png",
            f"entity_{field_type}_{index}.png"
        ]
        
        for image_filename in possible_filenames:
            image_path = os.path.join(image_base_path, job_id, image_filename)
            
            if os.path.exists(image_path):
                try:
                    # Check image dimensions and resize if needed
                    with Image.open(image_path) as img:
                        img_width, img_height = img.size
                        
                        # Calculate scaling to fit within reasonable bounds
                        max_width = 4 * inch
                        max_height = 3 * inch
                        
                        width_scale = max_width / img_width
                        height_scale = max_height / img_height
                        scale = min(width_scale, height_scale, 1.0)
                        
                        final_width = img_width * scale
                        final_height = img_height * scale
                    
                    # Add image to story
                    rl_img = RLImage(image_path, width=final_width, height=final_height)
                    story.append(rl_img)
                    story.append(Paragraph(f"<i>Entity Image: {image_filename}</i>", self.styles['Metadata']))
                    return  # Successfully added image, exit function
                    
                except Exception as e:
                    logger.warning(f"Could not add image {image_path}: {str(e)}")
        
        # If no image found with any pattern, don't add anything (no placeholder text)
    
    def _add_field_image_from_results(self, story: List, field_type: str, field_text: str, 
                                     images: List[Dict], image_base_path: str):
        """Add field image by matching with extraction results."""
        if not images or not image_base_path:
            return
        
        # Try to find matching image by field type or text content
        matching_images = []
        
        for image in images:
            image_type = image.get('image_type', '').lower()
            description = image.get('description', '').lower()
            
            # Match by field type
            if field_type.lower() in image_type or field_type.replace('_', '') in image_type:
                matching_images.append(image)
            # Match by text content (for more specific matching)
            elif field_text and any(word.lower() in description for word in field_text.split()[:3]):
                matching_images.append(image)
        
        # Add the first matching image
        for image in matching_images[:1]:  # Only add first match
            file_path = image.get('file_path')
            if file_path:
                full_image_path = os.path.join(image_base_path, file_path)
                
                if os.path.exists(full_image_path):
                    try:
                        # Check image dimensions and resize if needed
                        with Image.open(full_image_path) as img:
                            img_width, img_height = img.size
                            
                            # Calculate scaling to fit within reasonable bounds
                            max_width = 4 * inch
                            max_height = 3 * inch
                            
                            width_scale = max_width / img_width
                            height_scale = max_height / img_height
                            scale = min(width_scale, height_scale, 1.0)
                            
                            final_width = img_width * scale
                            final_height = img_height * scale
                        
                        # Add image to story
                        rl_img = RLImage(full_image_path, width=final_width, height=final_height)
                        story.append(rl_img)
                        story.append(Paragraph(f"<i>Image: {os.path.basename(file_path)}</i>", self.styles['Metadata']))
                        break  # Successfully added image, exit
                        
                    except Exception as e:
                        logger.warning(f"Could not add image {full_image_path}: {str(e)}")
    
    def _add_entities_section(self, story: List, design_criteria: Dict[str, Any], 
                            image_base_path: str, job_id: str):
        """Add Document AI entities section."""
        entities = design_criteria.get('document_ai_entities', [])
        if not entities:
            return
        
        story.append(Paragraph("Document AI Entities", self.styles['SectionHeader']))
        
        # Get images for matching
        images = design_criteria.get('images', [])
        
        for i, entity in enumerate(entities):
            # Entity header
            entity_type = entity.get('type', 'Unknown')
            confidence = entity.get('confidence', 0)
            
            header_text = f"<b>{entity_type}</b> (Confidence: {confidence * 100:.1f}%)"
            story.append(Paragraph(header_text, self.styles['FieldHeader']))
            
            # Entity text
            entity_text = entity.get('text', 'No text available')
            story.append(Paragraph(entity_text, self.styles['EntityText']))
            
            # Bounding box info
            bbox = entity.get('bounding_box')
            if bbox:
                bbox_text = f"Location: x={bbox.get('x', 0):.0f}, y={bbox.get('y', 0):.0f}, " \
                           f"width={bbox.get('width', 0):.0f}, height={bbox.get('height', 0):.0f}"
                story.append(Paragraph(bbox_text, self.styles['Metadata']))
            
            # Add entity image if available - use both methods for better matching
            self._add_entity_image_from_results(story, entity_type, entity_text, images, image_base_path)
            
            story.append(Spacer(1, 20))
    
    def _add_entity_image(self, story: List, entity_type: str, index: int, 
                         image_base_path: str, job_id: str):
        """Add entity-specific image."""
        if not image_base_path or not job_id:
            return
        
        # Try different possible image filenames
        possible_filenames = [
            f"entity_{entity_type.lower()}_{index}.png",
            f"entity_{entity_type.lower().replace('_', '')}_{index}.png",
            f"{entity_type.lower()}_{index}.png"
        ]
        
        for filename in possible_filenames:
            image_path = os.path.join(image_base_path, job_id, filename)
            if os.path.exists(image_path):
                try:
                    # Add image with proper sizing
                    with Image.open(image_path) as img:
                        img_width, img_height = img.size
                        
                        # Scale image to fit page
                        max_width = 5 * inch
                        max_height = 4 * inch
                        
                        width_scale = max_width / img_width
                        height_scale = max_height / img_height
                        scale = min(width_scale, height_scale, 1.0)
                        
                        final_width = img_width * scale
                        final_height = img_height * scale
                    
                    rl_img = RLImage(image_path, width=final_width, height=final_height)
                    story.append(rl_img)
                    story.append(Paragraph(f"<i>Entity Image: {filename}</i>", self.styles['Metadata']))
                    return
                    
                except Exception as e:
                    logger.warning(f"Could not add entity image {image_path}: {str(e)}")
        
        # If no image found, add placeholder text
        story.append(Paragraph("<i>No entity image available</i>", self.styles['Metadata']))
    
    def _add_entity_image_from_results(self, story: List, entity_type: str, entity_text: str, 
                                      images: List[Dict], image_base_path: str):
        """Add entity image by matching with extraction results."""
        if not images or not image_base_path:
            return
        
        # Try to find matching image by entity type with exact matching
        matching_images = []
        
        for image in images:
            image_type = image.get('image_type', '').lower()
            file_path = image.get('file_path', '').lower()
            description = image.get('description', '').lower()
            
            # Exact match: entity type should match the image type exactly
            expected_image_type = f"entity_{entity_type.lower()}"
            
            # Check for exact match first
            if image_type == expected_image_type:
                matching_images.append((image, 1))  # Priority 1 (highest)
            # Check file path for match (handles naming variations)
            elif entity_type.lower().replace('_', '') in file_path:
                matching_images.append((image, 2))  # Priority 2
            # Match by entity type in description (as fallback)
            elif entity_type.lower() in description and f"{entity_type.lower()} entity:" in description:
                matching_images.append((image, 3))  # Priority 3 (lowest)
        
        # Sort by priority and take the best match
        if matching_images:
            matching_images.sort(key=lambda x: x[1])  # Sort by priority (lower is better)
            best_match = matching_images[0][0]  # Get the image from the best match
            
            # Use the best matching image
            file_path = best_match.get('file_path')
            if file_path:
                full_image_path = os.path.join(image_base_path, file_path)
                
                if os.path.exists(full_image_path):
                    try:
                        # Check image dimensions and resize if needed
                        with Image.open(full_image_path) as img:
                            img_width, img_height = img.size
                            
                            # Calculate scaling to fit within reasonable bounds
                            max_width = 5 * inch
                            max_height = 4 * inch
                            
                            width_scale = max_width / img_width
                            height_scale = max_height / img_height
                            scale = min(width_scale, height_scale, 1.0)
                            
                            final_width = img_width * scale
                            final_height = img_height * scale
                        
                        # Add image to story
                        rl_img = RLImage(full_image_path, width=final_width, height=final_height)
                        story.append(rl_img)
                        story.append(Paragraph(f"<i>Entity Image: {os.path.basename(file_path)}</i>", self.styles['Metadata']))
                        return  # Successfully added image, exit
                        
                    except Exception as e:
                        logger.warning(f"Could not add entity image {full_image_path}: {str(e)}")
    
    def _add_extracted_images_section(self, story: List, design_criteria: Dict[str, Any], 
                                     image_base_path: str, job_id: str):
        """Add extracted images section showing all available images."""
        images = design_criteria.get('images', [])
        if not images:
            return
        
        story.append(PageBreak())
        story.append(Paragraph("Extracted Images", self.styles['SectionHeader']))
        
        # Limit to first 6 images like the web interface
        for i, image in enumerate(images[:6]):
            # Image header
            image_type = image.get('image_type', 'Unknown')
            description = image.get('description', 'No description available')
            confidence = image.get('confidence', 0)
            
            header_text = f"<b>Image {i+1}: {image_type}</b> (Confidence: {confidence * 100:.1f}%)"
            story.append(Paragraph(header_text, self.styles['FieldHeader']))
            
            # Image description
            if description and len(description) > 10:
                # Truncate long descriptions
                short_desc = description[:200] + "..." if len(description) > 200 else description
                story.append(Paragraph(f"<i>{short_desc}</i>", self.styles['Metadata']))
            
            # Add the actual image
            file_path = image.get('file_path')
            if file_path and image_base_path:
                full_image_path = os.path.join(image_base_path, file_path)
                
                if os.path.exists(full_image_path):
                    try:
                        # Check image dimensions and resize if needed
                        with Image.open(full_image_path) as img:
                            img_width, img_height = img.size
                            
                            # Calculate scaling to fit within reasonable bounds
                            max_width = 6 * inch
                            max_height = 4 * inch
                            
                            width_scale = max_width / img_width
                            height_scale = max_height / img_height
                            scale = min(width_scale, height_scale, 1.0)
                            
                            final_width = img_width * scale
                            final_height = img_height * scale
                        
                        # Add image to story
                        rl_img = RLImage(full_image_path, width=final_width, height=final_height)
                        story.append(rl_img)
                        
                        # Add image metadata
                        page_num = image.get('page_number', 0)
                        bbox = image.get('bounding_box')
                        metadata_text = f"<i>File: {os.path.basename(file_path)}"
                        if page_num is not None:
                            metadata_text += f" | Page: {page_num}"
                        if bbox:
                            metadata_text += f" | Location: ({bbox.get('x', 0):.0f}, {bbox.get('y', 0):.0f})"
                        metadata_text += "</i>"
                        
                        story.append(Paragraph(metadata_text, self.styles['Metadata']))
                        
                    except Exception as e:
                        logger.warning(f"Could not add extracted image {full_image_path}: {str(e)}")
                        story.append(Paragraph(f"<i>Error loading image: {os.path.basename(file_path)}</i>", self.styles['Metadata']))
                else:
                    story.append(Paragraph(f"<i>Image file not found: {file_path}</i>", self.styles['Metadata']))
            
            story.append(Spacer(1, 20))
        
        # Add note if there are more images
        if len(images) > 6:
            note_text = f"<i>Showing first 6 of {len(images)} images</i>"
            story.append(Paragraph(note_text, self.styles['Metadata']))
            story.append(Spacer(1, 20))
    
    def _add_raw_text_section(self, story: List, design_criteria: Dict[str, Any]):
        """Add raw extracted text section."""
        raw_text = design_criteria.get('raw_text')
        if not raw_text:
            return
        
        story.append(PageBreak())
        story.append(Paragraph("Raw Extracted Text", self.styles['SectionHeader']))
        
        # Split long text into chunks to avoid memory issues
        max_chunk_size = 2000
        text_chunks = [raw_text[i:i+max_chunk_size] for i in range(0, len(raw_text), max_chunk_size)]
        
        for chunk in text_chunks:
            # Clean and format text
            clean_chunk = chunk.replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(clean_chunk, self.styles['EntityText']))
            story.append(Spacer(1, 10))
    
    def _create_summary_table(self, design_criteria: Dict[str, Any]) -> Table:
        """Create a summary table of all extracted fields."""
        # Count non-empty fields
        field_counts = []
        
        field_types = [
            'berthing_loads', 'date', 'design_criteria', 'design_loads',
            'drawing_number', 'drawing_title', 'mooring_loads', 
            'vertical_dead_loads', 'vertical_live_loads', 'wind_loads'
        ]
        
        for field_type in field_types:
            field_data = design_criteria.get(field_type, [])
            count = len(field_data) if field_data else 0
            if count > 0:
                display_name = field_type.replace('_', ' ').title()
                field_counts.append([display_name, str(count)])
        
        if not field_counts:
            return None
        
        # Add header
        table_data = [['Field Type', 'Count']] + field_counts
        
        table = Table(table_data, colWidths=[6*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return table


def generate_pdf_report_for_job(job_id: str, 
                               design_criteria: Dict[str, Any], 
                               output_dir: str = "data/reports",
                               image_base_path: str = "data/extracted_images") -> Optional[str]:
    """
    Generate PDF report for a specific job.
    
    Args:
        job_id: Job identifier
        design_criteria: Extracted design criteria data
        output_dir: Directory to save the report
        image_base_path: Base path for entity images
        
    Returns:
        str: Path to generated PDF, or None if failed
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = design_criteria.get('metadata', {}).get('filename', 'document')
        base_name = os.path.splitext(filename)[0]
        pdf_filename = f"report_{base_name}_{job_id[:8]}_{timestamp}.pdf"
        output_path = os.path.join(output_dir, pdf_filename)
        
        # Generate report
        generator = EngineeringPDFReportGenerator()
        success = generator.generate_engineering_report(
            design_criteria, 
            output_path, 
            job_id, 
            image_base_path
        )
        
        if success:
            logger.info(f"PDF report generated: {output_path}")
            return output_path
        else:
            logger.error(f"Failed to generate PDF report for job {job_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error in generate_pdf_report_for_job: {str(e)}")
        return None