"""
Image extractor using Google Cloud Document AI Toolbox.
Extracts images from Document AI processed documents.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    from google.cloud.documentai_toolbox import document
except ImportError:
    logger.warning("Document AI Toolbox not available. Install with: pip install google-cloud-documentai-toolbox")
    document = None


class ImageExtractor:
    """
    Extract images from Document AI processed documents using the Document AI Toolbox.
    """
    
    def __init__(self, output_dir: str = "data/extracted_images"):
        """
        Initialize the image extractor.
        
        Args:
            output_dir: Directory to save extracted images
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        if document is None:
            raise ImportError("Document AI Toolbox is required. Install with: pip install google-cloud-documentai-toolbox")
    
    def extract_images_from_document(self, 
                                   document_path: str, 
                                   job_id: str,
                                   output_file_prefix: str = "image",
                                   output_file_extension: str = "png") -> List[str]:
        """
        Extract images from a Document AI processed document.
        
        Args:
            document_path: Path to the Document AI JSON response file
            job_id: Unique job identifier for organizing output
            output_file_prefix: Prefix for extracted image files
            output_file_extension: File extension for extracted images
            
        Returns:
            List of paths to extracted image files
        """
        try:
            # Create job-specific output directory
            job_output_dir = os.path.join(self.output_dir, job_id)
            os.makedirs(job_output_dir, exist_ok=True)
            
            # Load document using Document AI Toolbox
            wrapped_document = document.Document.from_document_path(document_path=document_path)
            
            # Extract images using Document AI Toolbox (following the official example)
            output_files = wrapped_document.export_images(
                output_path=job_output_dir,
                output_file_prefix=output_file_prefix,
                output_file_extension=output_file_extension,
            )
            
            logger.info("Images Successfully Exported")
            for output_file in output_files:
                logger.info(f"Extracted image: {output_file}")
            
            return output_files
            
        except Exception as e:
            logger.error(f"Error extracting images from {document_path}: {str(e)}")
            return []
    
    def extract_images_from_json_response(self, 
                                        doc_ai_response: Dict[str, Any], 
                                        job_id: str,
                                        output_file_prefix: str = "image",
                                        output_file_extension: str = "png") -> List[str]:
        """
        Extract images from a Document AI JSON response object.
        
        Args:
            doc_ai_response: Document AI response dictionary
            job_id: Unique job identifier for organizing output
            output_file_prefix: Prefix for extracted image files
            output_file_extension: File extension for extracted images
            
        Returns:
            List of paths to extracted image files
        """
        try:
            # Create job-specific output directory
            job_output_dir = os.path.join(self.output_dir, job_id)
            os.makedirs(job_output_dir, exist_ok=True)
            
            # Save response to temporary file
            temp_doc_path = os.path.join(job_output_dir, "temp_document.json")
            with open(temp_doc_path, 'w') as f:
                json.dump(doc_ai_response, f)
            
            # Extract images
            output_files = self.extract_images_from_document(
                document_path=temp_doc_path,
                job_id=job_id,
                output_file_prefix=output_file_prefix,
                output_file_extension=output_file_extension
            )
            
            # Clean up temporary file
            try:
                os.remove(temp_doc_path)
            except:
                pass
            
            return output_files
            
        except Exception as e:
            logger.error(f"Error extracting images from JSON response: {str(e)}")
            return []
    
    def get_image_metadata(self, document_path: str) -> List[Dict[str, Any]]:
        """
        Get metadata about images in the document without extracting them.
        
        Args:
            document_path: Path to the Document AI JSON response file
            
        Returns:
            List of image metadata dictionaries
        """
        try:
            wrapped_document = document.Document.from_document_path(document_path=document_path)
            
            image_metadata = []
            for page_num, page in enumerate(wrapped_document.pages):
                if hasattr(page, 'image') and page.image:
                    for img_idx, image in enumerate(page.image):
                        metadata = {
                            'page_number': page_num + 1,
                            'image_index': img_idx,
                            'confidence': getattr(image.layout, 'confidence', 0.0),
                            'bounding_box': {
                                'x': image.layout.bounding_poly.vertices[0].x,
                                'y': image.layout.bounding_poly.vertices[0].y,
                                'width': image.layout.bounding_poly.vertices[2].x - image.layout.bounding_poly.vertices[0].x,
                                'height': image.layout.bounding_poly.vertices[2].y - image.layout.bounding_poly.vertices[0].y
                            }
                        }
                        
                        # Add MIME type if available
                        if hasattr(image, 'mime_type'):
                            metadata['mime_type'] = image.mime_type
                        
                        image_metadata.append(metadata)
            
            return image_metadata
            
        except Exception as e:
            logger.error(f"Error getting image metadata from {document_path}: {str(e)}")
            return []
    
    def extract_images_with_metadata(self, 
                                   document_path: str, 
                                   job_id: str,
                                   output_file_prefix: str = "image",
                                   output_file_extension: str = "png") -> Dict[str, Any]:
        """
        Extract images and return both file paths and metadata.
        
        Args:
            document_path: Path to the Document AI JSON response file
            job_id: Unique job identifier for organizing output
            output_file_prefix: Prefix for extracted image files
            output_file_extension: File extension for extracted images
            
        Returns:
            Dictionary containing extracted file paths and metadata
        """
        try:
            # Get image metadata first
            metadata = self.get_image_metadata(document_path)
            
            # Extract images
            output_files = self.extract_images_from_document(
                document_path=document_path,
                job_id=job_id,
                output_file_prefix=output_file_prefix,
                output_file_extension=output_file_extension
            )
            
            # Combine metadata with file paths
            result = {
                'extracted_files': output_files,
                'image_metadata': metadata,
                'total_images': len(output_files),
                'job_id': job_id,
                'output_directory': os.path.join(self.output_dir, job_id)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in extract_images_with_metadata: {str(e)}")
            return {
                'extracted_files': [],
                'image_metadata': [],
                'total_images': 0,
                'job_id': job_id,
                'output_directory': os.path.join(self.output_dir, job_id),
                'error': str(e)
            } 