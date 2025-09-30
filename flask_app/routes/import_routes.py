# flask_app/routes/import_routes.py

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import os
from datetime import datetime
from flask_app.models import db, Story, Topic, Tag, Thread, EventClaim
from flask_app.models.story import Story
from flask_app.models.topic import Topic
from flask_app.models.tag import Tag
from flask_app.models.thread import Thread
from flask_app.models.event_claim import EventClaim
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
            # Clean the sample data for JSON serialization
            cleaned_sample_data = clean_json_data(sample_data)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'columns': columns,
                'sample_data': cleaned_sample_data,
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
        
        # Log the column mapping for debugging
        logger.info(f"Column mapping received: {column_mapping}")
        logger.info(f"Available columns in CSV: {list(df.columns)}")
        logger.info(f"Column mapping type: {type(column_mapping)}")
        logger.info(f"Column mapping keys: {list(column_mapping.keys())}")
        
        # Validate that required columns exist in the CSV (only check columns that are actually mapped)
        missing_columns = []
        for target_field, source_column in column_mapping.items():
            if source_column and source_column not in df.columns:
                missing_columns.append(source_column)
        
        if missing_columns:
            return jsonify({'error': f'Columns not found in CSV: {missing_columns}'}), 400
        
        # Map columns
        mapped_data = []
        for _, row in df.iterrows():
            mapped_row = {}
            for target_field, source_column in column_mapping.items():
                if source_column and source_column in df.columns:
                    value = row[source_column]
                    # Handle pandas NaN values and convert to None
                    if pd.isna(value) or value == '' or str(value).strip() == '':
                        mapped_row[target_field] = None
                    else:
                        mapped_row[target_field] = str(value).strip() if value is not None else None
                else:
                    # Only set to None if the field was actually mapped (not if it was omitted)
                    if source_column:  # source_column exists but not in CSV
                        mapped_row[target_field] = None
                    # If source_column is empty/None, don't add this field at all
            mapped_data.append(mapped_row)
        
        # Validate data
        validation_results = validate_story_data(mapped_data)
        
        # Clean data for JSON serialization
        cleaned_mapped_data = clean_json_data(mapped_data[:10])  # First 10 rows for preview
        cleaned_validation_results = clean_json_data(validation_results)
        
        return jsonify({
            'success': True,
            'mapped_data': cleaned_mapped_data,
            'preview_rows': cleaned_mapped_data,
            'validation_results': cleaned_validation_results,
            'total_rows': len(mapped_data)
        })
        
    except Exception as e:
        logger.error(f"Error previewing import: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Preview failed: {str(e)}'}), 500

def clean_json_data(data):
    """Clean data to ensure it's JSON serializable"""
    import numpy as np
    
    if isinstance(data, dict):
        return {key: clean_json_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(item) for item in data]
    elif isinstance(data, (np.integer, np.floating)):
        return data.item() if not np.isnan(data) else None
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif pd.isna(data):
        return None
    else:
        return data

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
                        value = row[source_column]
                        # Handle pandas NaN values and convert to None
                        if pd.isna(value) or value == '' or str(value).strip() == '':
                            story_data[target_field] = None
                        else:
                            story_data[target_field] = str(value).strip() if value is not None else None
                    else:
                        # Only set to None if the field was actually mapped (not if it was omitted)
                        if source_column:  # source_column exists but not in CSV
                            story_data[target_field] = None
                        # If source_column is empty/None, don't add this field at all
                
                # Handle date field mapping (convert 'date' to 'published_at')
                if 'date' in story_data:
                    story_data['published_at'] = story_data['date']
                
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
        
        # Clean results for JSON serialization
        cleaned_results = clean_json_data(results)
        
        return jsonify({
            'success': True,
            'results': cleaned_results
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
    """Create a Story object from mapped data with topics, threads, and events"""
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
                db.session.flush()  # Flush to get story ID
                
                # Handle topics
                if data.get('topics'):
                    topics = parse_topics(data['topics'])
                    for topic_name in topics:
                        topic = get_or_create_topic(topic_name.strip())
                        if topic and topic not in story.topics:
                            story.topics.append(topic)
                            logger.info(f"Added topic '{topic_name}' to story '{data.get('title', 'Unknown')}'")
                
                # Handle thread
                if data.get('thread'):
                    thread = get_or_create_thread(data['thread'].strip(), story.topics.first() if story.topics.count() > 0 else None)
                    if thread and thread not in story.threads:
                        story.threads.append(thread)
                        logger.info(f"Added thread '{data['thread']}' to story '{data.get('title', 'Unknown')}'")
                
                # Handle event claim
                if data.get('event_claim'):
                    event = create_event_claim(
                        data['event_claim'],
                        published_at or datetime.now().date(),
                        story.topics.first() if story.topics.count() > 0 else None,
                        story.threads.first() if story.threads.count() > 0 else None
                    )
                    if event:
                        # Link event to story
                        from flask_app.models.event_story_link import EventStoryLink
                        EventStoryLink.create_link(event, story)
                
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

def parse_topics(topics_string):
    """Parse semicolon-separated topics string into list"""
    if not topics_string:
        return []
    
    # Split by semicolon and clean up
    topics = [topic.strip() for topic in topics_string.split(';')]
    # Remove empty strings
    topics = [topic for topic in topics if topic]
    return topics

def get_or_create_topic(topic_name):
    """Get existing topic or create new one"""
    try:
        # Try to find existing topic
        topic = Topic.find_by_name(topic_name)
        if topic:
            logger.info(f"Using existing topic: {topic_name}")
            return topic
        
        # Create new topic
        topic = Topic(name=topic_name)
        validation_errors = topic.validate()
        if not validation_errors:
            db.session.add(topic)
            db.session.flush()  # Flush to get ID
            logger.info(f"Created new topic: {topic_name}")
            return topic
        else:
            logger.error(f"Topic validation failed for '{topic_name}': {validation_errors}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating topic '{topic_name}': {str(e)}")
        return None

def get_or_create_thread(thread_name, topic=None):
    """Get existing thread or create new one, ensuring topic relationship is updated"""
    try:
        # Try to find existing thread
        thread = Thread.query.filter_by(name=thread_name).first()
        if thread:
            # Update topic relationship if topic is provided and not already associated
            if topic and topic not in thread.topics:
                thread.topics.append(topic)
                db.session.commit()
                logger.info(f"Updated existing thread '{thread_name}' with topic '{topic.name}'")
            return thread
        
        # Create new thread (requires a topic)
        if not topic:
            # Create a default topic if none provided
            topic = get_or_create_topic("General")
            if not topic:
                return None
        
        thread = Thread(
            name=thread_name,
            start_date=datetime.now().date()
        )
        
        validation_errors = thread.validate()
        if not validation_errors:
            db.session.add(thread)
            db.session.flush()  # Flush to get ID
            
            # Add topic to thread via many-to-many relationship
            thread.topics.append(topic)
            db.session.commit()
            logger.info(f"Created new thread: {thread_name}")
            return thread
        else:
            logger.error(f"Thread validation failed for '{thread_name}': {validation_errors}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating thread '{thread_name}': {str(e)}")
        return None

def create_event_claim(claim_text, event_date, topic=None, thread=None):
    """Create an event claim"""
    try:
        # Create a default topic if none provided
        if not topic:
            topic = get_or_create_topic("General")
            if not topic:
                return None
        
        event = EventClaim(
            claim_text=claim_text,
            event_date=event_date,
            topic_id=topic.id,
            thread_id=thread.id if thread else None
        )
        
        validation_errors = event.validate()
        if not validation_errors:
            db.session.add(event)
            db.session.flush()  # Flush to get ID
            return event
        else:
            logger.error(f"Event validation failed for '{claim_text}': {validation_errors}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating event claim '{claim_text}': {str(e)}")
        return None
