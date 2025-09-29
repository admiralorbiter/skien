# flask_app/routes/import_routes.py

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import os
from datetime import datetime
from flask_app.models import db, Story, Topic, Tag
from flask_app.models.story import Story
from flask_app.models.topic import Topic
from flask_app.models.tag import Tag
import logging

logger = logging.getLogger(__name__)

import_bp = Blueprint('import', __name__, url_prefix='/import')

# Configuration
ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """Ensure upload folder exists"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@import_bp.route('/')
def index():
    """Import dashboard"""
    return render_template('import/index.html')

@import_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle CSV file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only CSV files are allowed.'}), 400
        
        # Ensure upload folder exists
        ensure_upload_folder()
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Read CSV and get column info
        try:
            df = pd.read_csv(filepath)
            columns = list(df.columns)
            
            # Get sample data for preview
            sample_data = df.head(5).to_dict('records')
            
            return jsonify({
                'success': True,
                'filename': filename,
                'columns': columns,
                'sample_data': sample_data,
                'total_rows': len(df)
            })
            
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            return jsonify({'error': f'Error reading CSV file: {str(e)}'}), 400
            
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@import_bp.route('/preview', methods=['POST'])
def preview_import():
    """Preview import with column mapping"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        column_mapping = data.get('column_mapping', {})
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Read CSV
        df = pd.read_csv(filepath)
        
        # Map columns
        mapped_data = []
        for _, row in df.iterrows():
            mapped_row = {}
            for target_field, source_column in column_mapping.items():
                if source_column and source_column in df.columns:
                    mapped_row[target_field] = row[source_column]
                else:
                    mapped_row[target_field] = None
            mapped_data.append(mapped_row)
        
        # Validate data
        validation_results = validate_story_data(mapped_data)
        
        return jsonify({
            'success': True,
            'mapped_data': mapped_data[:10],  # First 10 rows for preview
            'validation_results': validation_results,
            'total_rows': len(mapped_data)
        })
        
    except Exception as e:
        logger.error(f"Error previewing import: {str(e)}")
        return jsonify({'error': f'Preview failed: {str(e)}'}), 500

@import_bp.route('/process', methods=['POST'])
def process_import():
    """Process the actual import"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        column_mapping = data.get('column_mapping', {})
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Read CSV
        df = pd.read_csv(filepath)
        
        # Process each row
        results = {
            'success': 0,
            'errors': 0,
            'duplicates': 0,
            'error_details': []
        }
        
        for index, row in df.iterrows():
            try:
                # Map columns to story fields
                story_data = {}
                for target_field, source_column in column_mapping.items():
                    if source_column and source_column in df.columns:
                        story_data[target_field] = row[source_column]
                
                # Create story
                story = create_story_from_data(story_data)
                if story:
                    results['success'] += 1
                else:
                    results['duplicates'] += 1
                    
            except Exception as e:
                results['errors'] += 1
                results['error_details'].append({
                    'row': index + 1,
                    'error': str(e)
                })
                logger.error(f"Error processing row {index + 1}: {str(e)}")
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error processing import: {str(e)}")
        return jsonify({'error': f'Import failed: {str(e)}'}), 500

def validate_story_data(data_list):
    """Validate story data before import"""
    validation_results = {
        'valid': 0,
        'invalid': 0,
        'errors': []
    }
    
    for i, data in enumerate(data_list):
        try:
            # Check required fields
            if not data.get('title') or not data.get('url'):
                validation_results['invalid'] += 1
                validation_results['errors'].append({
                    'row': i + 1,
                    'error': 'Missing required fields (title, url)'
                })
                continue
            
            # Validate URL format
            url = data.get('url', '')
            if not url.startswith(('http://', 'https://')):
                validation_results['invalid'] += 1
                validation_results['errors'].append({
                    'row': i + 1,
                    'error': 'Invalid URL format'
                })
                continue
            
            # Validate date format if provided
            if data.get('published_at'):
                try:
                    # Try to parse the date
                    pd.to_datetime(data['published_at'])
                except:
                    validation_results['invalid'] += 1
                    validation_results['errors'].append({
                        'row': i + 1,
                        'error': 'Invalid date format'
                    })
                    continue
            
            validation_results['valid'] += 1
            
        except Exception as e:
            validation_results['invalid'] += 1
            validation_results['errors'].append({
                'row': i + 1,
                'error': str(e)
            })
    
    return validation_results

def create_story_from_data(data):
    """Create a Story object from mapped data"""
    try:
        # Check for duplicates
        url = data.get('url')
        if not url:
            return None
        
        # Check if story already exists
        existing_story = Story.find_by_url(url)
        if existing_story:
            return None  # Duplicate
        
        # Parse date
        published_at = None
        if data.get('published_at'):
            try:
                published_at = pd.to_datetime(data['published_at']).date()
            except:
                pass
        
        # Extract source from URL
        source_name = extract_source_from_url(url)
        
        # Create story
        story = Story(
            url=url,
            title=data.get('title', ''),
            source_name=source_name,
            author=data.get('author'),
            published_at=published_at,
            summary=data.get('summary'),
            raw_text=data.get('raw_text')
        )
        
        # Validate and save (exclude auto-generated fields during import)
        validation_errors = story.validate(exclude_auto_fields=True)
        if not validation_errors:
            try:
                db.session.add(story)
                db.session.commit()
                return story
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving story: {str(e)}")
                return None
        else:
            logger.error(f"Story validation failed: {validation_errors}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating story: {str(e)}")
        return None

def extract_source_from_url(url):
    """Extract source name from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove common prefixes
        domain = domain.replace('www.', '')
        
        # Map common domains to readable names
        source_mapping = {
            'politico.com': 'Politico',
            'cnn.com': 'CNN',
            'nytimes.com': 'New York Times',
            'washingtonpost.com': 'Washington Post',
            'reuters.com': 'Reuters',
            'apnews.com': 'Associated Press',
            'npr.org': 'NPR',
            'bbc.com': 'BBC',
            'theguardian.com': 'The Guardian',
            'axios.com': 'Axios',
            'nbcnews.com': 'NBC News',
            'cbsnews.com': 'CBS News',
            'abcnews.go.com': 'ABC News',
            'foxnews.com': 'Fox News',
            'msnbc.com': 'MSNBC',
            'newsweek.com': 'Newsweek',
            'time.com': 'Time',
            'fortune.com': 'Fortune',
            'bloomberg.com': 'Bloomberg',
            'wsj.com': 'Wall Street Journal',
            'usatoday.com': 'USA Today',
            'latimes.com': 'Los Angeles Times',
            'chicagotribune.com': 'Chicago Tribune',
            'bostonglobe.com': 'Boston Globe',
            'miamiherald.com': 'Miami Herald',
            'dallasnews.com': 'Dallas Morning News',
            'denverpost.com': 'Denver Post',
            'seattletimes.com': 'Seattle Times',
            'oregonlive.com': 'The Oregonian',
            'azcentral.com': 'Arizona Republic',
            'mcall.com': 'The Morning Call',
            'baltimoresun.com': 'Baltimore Sun',
            'charlotteobserver.com': 'Charlotte Observer',
            'kansascity.com': 'Kansas City Star',
            'startribune.com': 'Star Tribune',
            'cleveland.com': 'The Plain Dealer',
            'dispatch.com': 'The Columbus Dispatch',
            'jsonline.com': 'Milwaukee Journal Sentinel',
            'stltoday.com': 'St. Louis Post-Dispatch',
            'tampabay.com': 'Tampa Bay Times',
            'orlandosentinel.com': 'Orlando Sentinel',
            'sun-sentinel.com': 'South Florida Sun Sentinel',
            'miamiherald.com': 'Miami Herald',
            'ajc.com': 'Atlanta Journal-Constitution',
            'houstonchronicle.com': 'Houston Chronicle',
            'chron.com': 'Houston Chronicle',
            'dallasnews.com': 'Dallas Morning News',
            'statesman.com': 'Austin American-Statesman',
            'expressnews.com': 'San Antonio Express-News',
            'elpasotimes.com': 'El Paso Times',
            'lubbockonline.com': 'Lubbock Avalanche-Journal',
            'amarillo.com': 'Amarillo Globe-News',
            'wacotrib.com': 'Waco Tribune-Herald',
            'victoriaadvocate.com': 'Victoria Advocate',
            'theeagle.com': 'The Eagle',
            'kbtx.com': 'KBTX',
            'kxxv.com': 'KXXV',
            'kagstv.com': 'KAGS',
            'kcentv.com': 'KCEN',
            'kwtv.com': 'KWTV',
            'kfor.com': 'KFOR',
            'news9.com': 'News 9',
            'okcfox.com': 'OKCFOX',
            'koco.com': 'KOCO',
            'kwtv.com': 'KWTV',
            'kfor.com': 'KFOR',
            'news9.com': 'News 9',
            'okcfox.com': 'OKCFOX',
            'koco.com': 'KOCO',
            'kwtv.com': 'KWTV',
            'kfor.com': 'KFOR',
            'news9.com': 'News 9',
            'okcfox.com': 'OKCFOX',
            'koco.com': 'KOCO'
        }
        
        return source_mapping.get(domain, domain.title())
        
    except Exception as e:
        logger.error(f"Error extracting source from URL {url}: {str(e)}")
        return 'Unknown Source'
