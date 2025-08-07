"""
Flask web application for engineering design criteria extraction.
"""

import os
import uuid
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import threading
from loguru import logger

from ..core.extractor import EngineeringCriteriaExtractor
from ..models.schemas import ExtractionResult
from ..models.document_models import ProcessingStatus


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    
    # Use absolute paths to avoid issues with relative paths when running from different directories
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app.config['UPLOAD_FOLDER'] = os.path.join(project_root, 'data/uploads')
    app.config['OUTPUT_FOLDER'] = os.path.join(project_root, 'data/output')
    app.config['EXTRACTED_IMAGES_FOLDER'] = os.path.join(project_root, 'data/extracted_images')
    app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
    
    # Create directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXTRACTED_IMAGES_FOLDER'], exist_ok=True)
    
    # In-memory storage for job tracking (in production, use a database)
    jobs = {}
    
    def allowed_file(filename):
        """Check if file extension is allowed."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    def get_extractor():
        """Get or create the engineering criteria extractor."""
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
        location = os.getenv("DOCUMENT_AI_LOCATION", "us")
        
        if not project_id or not processor_id:
            raise ValueError("Google Cloud configuration not found. Please set GOOGLE_CLOUD_PROJECT_ID and DOCUMENT_AI_PROCESSOR_ID environment variables.")
        
        return EngineeringCriteriaExtractor(
            project_id=project_id,
            processor_id=processor_id,
            location=location
        )
    
    def process_document_async(job_id, file_path):
        """Process document in background thread."""
        try:
            jobs[job_id]['status'] = ProcessingStatus.PROCESSING
            jobs[job_id]['started_at'] = datetime.now()
            
            extractor = get_extractor()
            result = extractor.extract_from_file(file_path, app.config['OUTPUT_FOLDER'])
            
            jobs[job_id].update({
                'status': result.status,
                'result': result,
                'completed_at': datetime.now(),
                'error_message': result.error_message
            })
            
            logger.info(f"Completed processing job {job_id}")
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}")
            jobs[job_id].update({
                'status': ProcessingStatus.FAILED,
                'error_message': str(e),
                'completed_at': datetime.now()
            })
    
    @app.route('/')
    def index():
        """Home page with upload form."""
        return render_template('index.html')
    
    @app.route('/test')
    def test_upload():
        """Test upload page."""
        return render_template('test_upload.html')
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        """Handle file upload and start processing."""
        try:
            # Debug: Print request information
            print(f"DEBUG: Request files: {list(request.files.keys())}")
            print(f"DEBUG: Request form: {list(request.form.keys())}")
            
            # Check if file was uploaded
            if 'file' not in request.files:
                print("DEBUG: No 'file' in request.files")
                flash('No file selected', 'error')
                return redirect(url_for('index'))
            
            file = request.files['file']
            
            # Check if file was selected
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('index'))
            
            # Check file extension
            if not allowed_file(file.filename):
                flash('Only PDF files are allowed', 'error')
                return redirect(url_for('index'))
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Create job
            job_id = str(uuid.uuid4())
            jobs[job_id] = {
                'id': job_id,
                'filename': filename,
                'file_path': file_path,
                'status': ProcessingStatus.PENDING,
                'created_at': datetime.now(),
                'result': None,
                'error_message': None
            }
            
            # Start background processing
            thread = threading.Thread(
                target=process_document_async,
                args=(job_id, file_path)
            )
            thread.daemon = True
            thread.start()
            
            flash(f'File uploaded successfully. Processing started. Job ID: {job_id[:8]}', 'success')
            return redirect(url_for('job_status', job_id=job_id))
            
        except RequestEntityTooLarge:
            flash('File too large. Maximum size is 50MB.', 'error')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/job/<job_id>')
    def job_status(job_id):
        """Show job status and results."""
        if job_id not in jobs:
            flash('Job not found', 'error')
            return redirect(url_for('index'))
        
        job = jobs[job_id]
        return render_template('job_status.html', job=job)
    
    @app.route('/api/job/<job_id>')
    def api_job_status(job_id):
        """API endpoint for job status."""
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = jobs[job_id]
        return jsonify({
            'id': job['id'],
            'filename': job['filename'],
            'status': job['status'],
            'created_at': job['created_at'].isoformat() if job['created_at'] else None,
            'started_at': job['started_at'].isoformat() if job.get('started_at') else None,
            'completed_at': job['completed_at'].isoformat() if job.get('completed_at') else None,
            'error_message': job.get('error_message')
        })
    
    @app.route('/api/job/<job_id>/results')
    def api_job_results(job_id):
        """API endpoint for job results."""
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = jobs[job_id]
        
        if job['status'] != ProcessingStatus.COMPLETED:
            return jsonify({'error': 'Job not completed'}), 400
        
        if not job.get('result') or not job['result'].design_criteria:
            return jsonify({'error': 'No results available'}), 404
        
        # Convert result to JSON-serializable format
        result_data = {
            'job_id': job['id'],
            'status': job['result'].status,
            'design_criteria': job['result'].design_criteria.dict(),
            'processing_time': job['result'].processing_time,
            'created_at': job['result'].created_at.isoformat()
        }
        
        return jsonify(result_data)
    
    @app.route('/jobs')
    def job_list():
        """Show list of all jobs."""
        # Sort jobs by creation date (newest first)
        sorted_jobs = sorted(jobs.values(), key=lambda x: x['created_at'], reverse=True)
        return render_template('job_list.html', jobs=sorted_jobs)
    
    @app.route('/download/<job_id>')
    def download_results(job_id):
        """Download results as JSON file."""
        if job_id not in jobs:
            flash('Job not found', 'error')
            return redirect(url_for('index'))
        
        job = jobs[job_id]
        
        if job['status'] != ProcessingStatus.COMPLETED:
            flash('Job not completed', 'error')
            return redirect(url_for('job_status', job_id=job_id))
        
        if not job.get('result') or not job['result'].design_criteria:
            flash('No results available', 'error')
            return redirect(url_for('job_status', job_id=job_id))
        
        # Create JSON file
        result_data = {
            'job_id': job['id'],
            'filename': job['filename'],
            'status': job['result'].status,
            'design_criteria': job['result'].design_criteria.dict(),
            'processing_time': job['result'].processing_time,
            'created_at': job['result'].created_at.isoformat()
        }
        
        json_filename = f"results_{job_id[:8]}.json"
        json_path = os.path.join(app.config['OUTPUT_FOLDER'], json_filename)
        
        with open(json_path, 'w') as f:
            json.dump(result_data, f, indent=2, default=str)
        
        return send_file(json_path, as_attachment=True, download_name=json_filename)
    
    @app.route('/images/<path:filename>')
    def serve_image(filename):
        """
        Serve extracted images.
        
        Args:
            filename: Image filename with job path
            
        Returns:
            Image file
        """
        try:
            image_path = os.path.join(app.config['EXTRACTED_IMAGES_FOLDER'], filename)
            print(f"DEBUG: Trying to serve image: {image_path}")
            print(f"DEBUG: File exists: {os.path.exists(image_path)}")
            print(f"DEBUG: Is file: {os.path.isfile(image_path)}")
            
            if os.path.exists(image_path) and os.path.isfile(image_path):
                # Check file size
                file_size = os.path.getsize(image_path)
                print(f"DEBUG: File size: {file_size} bytes")
                
                if file_size > 0:
                    return send_file(image_path, mimetype='image/png')
                else:
                    print(f"DEBUG: File is empty")
                    return "Image file is empty", 404
            else:
                print(f"DEBUG: File not found or not a file")
                return "Image not found", 404
        except Exception as e:
            print(f"DEBUG: Error serving image: {str(e)}")
            return f"Error serving image: {str(e)}", 500
    
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        try:
            # Try to get extractor to test configuration
            get_extractor()
            return jsonify({
                'status': 'healthy',
                'extractor_configured': True,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'extractor_configured': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.errorhandler(413)
    def too_large(e):
        """Handle file too large error."""
        flash('File too large. Maximum size is 50MB.', 'error')
        return redirect(url_for('index'))
    
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors."""
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 errors."""
        return render_template('500.html'), 500
    
    return app 