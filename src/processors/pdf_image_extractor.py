"""
PDF Image Extractor - Fallback method for extracting images from PDFs
when Document AI doesn't provide actual image data.
"""

import os
import fitz  # PyMuPDF
from PIL import Image
import io
from typing import List, Dict, Any
from loguru import logger


class PDFImageExtractor:
    """Extract images directly from PDF files using PyMuPDF."""
    
    def __init__(self, output_dir: str = "data/extracted_images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def extract_images_from_pdf(self, pdf_path: str, job_id: str, min_width: int = 100, min_height: int = 100, min_file_size: int = 5000) -> List[str]:
        """
        Extract meaningful images directly from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            job_id: Job identifier for organizing output
            min_width: Minimum width in pixels for meaningful images
            min_height: Minimum height in pixels for meaningful images
            min_file_size: Minimum file size in bytes for meaningful images
            
        Returns:
            List of paths to extracted image files
        """
        extracted_files = []
        
        try:
            # Create job-specific output directory
            job_output_dir = os.path.join(self.output_dir, job_id)
            os.makedirs(job_output_dir, exist_ok=True)
            
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(pdf_path)
            
            image_count = 0
            meaningful_count = 0
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Get image list from page
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image dimensions from PDF metadata
                        img_width = img[2]
                        img_height = img[3]
                        
                        # Skip very small images (likely icons, logos, etc.)
                        if img_width < min_width or img_height < min_height:
                            logger.debug(f"Skipping small image {img_index + 1} from page {page_num + 1}: {img_width}x{img_height}")
                            continue
                        
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(pdf_document, xref)
                        
                        # Convert to PIL Image
                        img_data = pix.tobytes("png")
                        pil_image = Image.open(io.BytesIO(img_data))
                        
                        # Check actual image dimensions
                        actual_width, actual_height = pil_image.size
                        
                        # Skip if actual dimensions are too small
                        if actual_width < min_width or actual_height < min_height:
                            logger.debug(f"Skipping small actual image {img_index + 1} from page {page_num + 1}: {actual_width}x{actual_height}")
                            pix = None
                            continue
                        
                        # Convert to RGB if necessary for better quality
                        if pil_image.mode != 'RGB':
                            pil_image = pil_image.convert('RGB')
                        
                        # Save image temporarily to check file size with high quality
                        temp_path = os.path.join(job_output_dir, f"temp_{page_num + 1}_{img_index + 1}.png")
                        pil_image.save(temp_path, 'PNG', optimize=False, quality=95)
                        
                        # Check file size
                        file_size = os.path.getsize(temp_path)
                        if file_size < min_file_size:
                            logger.debug(f"Skipping small file size image {img_index + 1} from page {page_num + 1}: {file_size} bytes")
                            os.remove(temp_path)
                            pix = None
                            continue
                        
                        # Rename to final filename
                        image_filename = f"pdf_image_{page_num + 1}_{img_index + 1}.png"
                        image_path = os.path.join(job_output_dir, image_filename)
                        os.rename(temp_path, image_path)
                        
                        extracted_files.append(image_path)
                        meaningful_count += 1
                        
                        logger.info(f"Extracted meaningful image {meaningful_count} from page {page_num + 1}: {actual_width}x{actual_height}, {file_size} bytes")
                        
                        # Clean up
                        pix = None
                        
                    except Exception as e:
                        logger.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {str(e)}")
                        continue
                
                image_count += len(image_list)
            
            pdf_document.close()
            
            logger.info(f"Found {image_count} total images, extracted {meaningful_count} meaningful images from PDF")
            
            # If no meaningful images found, try extracting full pages as images
            if meaningful_count == 0:
                logger.info("No meaningful embedded images found, extracting full pages as images")
                page_images = self.extract_pages_as_images(pdf_path, job_id)
                extracted_files.extend(page_images)
            
            return extracted_files
            
        except Exception as e:
            logger.error(f"Error extracting images from PDF {pdf_path}: {str(e)}")
            return []
    
    def extract_pages_as_images(self, pdf_path: str, job_id: str, dpi: int = 300) -> List[str]:
        """
        Extract full pages as images from PDF file with high resolution.
        
        Args:
            pdf_path: Path to the PDF file
            job_id: Job identifier for organizing output
            dpi: Resolution for page rendering (default: 300 for high quality)
            
        Returns:
            List of paths to extracted page images
        """
        extracted_files = []
        
        try:
            # Create job-specific output directory
            job_output_dir = os.path.join(self.output_dir, job_id)
            os.makedirs(job_output_dir, exist_ok=True)
            
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Create transformation matrix for high DPI rendering
                # Use higher DPI for better quality
                mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is the default DPI
                
                # Render page to pixmap with high quality
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Convert to RGB if necessary for better quality
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                
                # Save page image with high quality
                page_filename = f"page_{page_num + 1}.png"
                page_path = os.path.join(job_output_dir, page_filename)
                
                # Save with high quality settings
                pil_image.save(page_path, 'PNG', optimize=False, quality=95)
                
                extracted_files.append(page_path)
                
                logger.info(f"Extracted high-quality page {page_num + 1} as image: {pil_image.size[0]}x{pil_image.size[1]} at {dpi} DPI")
                
                # Clean up
                pix = None
            
            pdf_document.close()
            
            logger.info(f"Successfully extracted {len(extracted_files)} pages as high-quality images at {dpi} DPI")
            return extracted_files
            
        except Exception as e:
            logger.error(f"Error extracting pages as images from PDF {pdf_path}: {str(e)}")
            return []
    
    def get_image_info(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Get information about images in PDF without extracting them.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of image information dictionaries
        """
        image_info = []
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    info = {
                        'page_number': page_num + 1,
                        'image_index': img_index + 1,
                        'width': img[2],
                        'height': img[3],
                        'colorspace': img[4],
                        'bits_per_component': img[5]
                    }
                    image_info.append(info)
            
            pdf_document.close()
            
        except Exception as e:
            logger.error(f"Error getting image info from PDF {pdf_path}: {str(e)}")
        
        return image_info 