# app/routes/main.py

from flask import flash, render_template, request, current_app

def register_main_routes(app):
    """Register main application routes"""
    
    @app.route('/')
    def index():
        try:
            from flask_app.models import Story, EventClaim, Topic, Tag
            
            # Get real stats from database
            stats = {
                'total_stories': Story.query.count(),
                'total_events': EventClaim.query.count(),
                'total_topics': Topic.query.count(),
                'total_tags': Tag.query.count()
            }
            
            current_app.logger.info(f"Index page accessed by {request.remote_addr}")
            return render_template('index.html', stats=stats)
        except Exception as e:
            current_app.logger.error(f"Error in index route: {str(e)}")
            # Fallback stats in case of error
            stats = {
                'total_stories': 0,
                'total_events': 0,
                'total_topics': 0,
                'total_tags': 0
            }
            flash('An error occurred while loading the page.', 'danger')
            return render_template('index.html', stats=stats), 500
