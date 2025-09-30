# flask_app/routes/admin.py

from flask import flash, redirect, render_template, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import func, desc
from flask_app.models import User, AdminLog, SystemMetrics, db
from flask_app.forms import CreateUserForm, UpdateUserForm, ChangePasswordForm, BulkUserActionForm
from datetime import datetime, timezone, timedelta

def admin_required(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def register_admin_routes(app):
    """Register admin dashboard routes"""
    
    @app.route('/admin')
    @login_required
    @admin_required
    def admin_dashboard():
        """Admin dashboard main page"""
        try:
            from flask_app.models import Story
            
            # Get system statistics
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            admin_users = User.query.filter_by(is_admin=True).count()
            total_stories = Story.query.count()
            
            # Get recent users (last 30 days)
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
            
            # Get recent admin actions
            recent_actions = AdminLog.query.order_by(desc(AdminLog.created_at)).limit(10).all()
            
            # Update system metrics
            SystemMetrics.set_metric('total_users', total_users)
            SystemMetrics.set_metric('active_users', active_users)
            SystemMetrics.set_metric('admin_users', admin_users)
            SystemMetrics.set_metric('total_stories', total_stories)
            
            stats = {
                'total_users': total_users,
                'active_users': active_users,
                'admin_users': admin_users,
                'total_stories': total_stories,
                'total_events': 0,  # TODO: Add when events are implemented
                'total_topics': 0,  # TODO: Add when topics are implemented
                'recent_users': recent_users,
                'recent_actions': recent_actions
            }
            
            current_app.logger.info(f"Admin dashboard accessed by {current_user.username}")
            return render_template('admin/dashboard.html', stats=stats)
            
        except Exception as e:
            current_app.logger.error(f"Error in admin dashboard: {str(e)}")
            flash('An error occurred while loading the dashboard.', 'danger')
            return render_template('admin/dashboard.html', stats={})
    
    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        """Admin user management page"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 20
            
            users = User.query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return render_template('admin/users.html', users=users)
            
        except Exception as e:
            current_app.logger.error(f"Error in admin users page: {str(e)}")
            flash('An error occurred while loading users.', 'danger')
            return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/users/create', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_create_user():
        """Create new user"""
        # Create form - defaults are already set in the form definition
        form = CreateUserForm()
        
        # For GET requests, ensure defaults are properly set
        if request.method == 'GET':
            form.is_active.data = True
            form.is_admin.data = False
        
        try:
            if form.validate_on_submit():
                # Handle checkbox values explicitly
                is_active = bool(request.form.get('is_active'))
                is_admin = bool(request.form.get('is_admin'))
                
                # Create new user
                new_user, error = User.safe_create(
                    username=form.username.data.strip(),
                    email=form.email.data.strip().lower(),
                    password_hash=generate_password_hash(form.password.data),
                    first_name=form.first_name.data.strip() if form.first_name.data else None,
                    last_name=form.last_name.data.strip() if form.last_name.data else None,
                    is_active=is_active,
                    is_admin=is_admin
                )
                
                if error:
                    flash(f'Error creating user: {error}', 'danger')
                else:
                    # Log admin action
                    AdminLog.log_action(
                        admin_user_id=current_user.id,
                        action='CREATE_USER',
                        target_user_id=new_user.id,
                        details=f'Created user: {new_user.username}',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    flash(f'User {new_user.username} created successfully!', 'success')
                    return redirect(url_for('admin_users'))
            
            return render_template('admin/create_user.html', form=form)
            
        except Exception as e:
            current_app.logger.error(f"Error in admin create user: {str(e)}")
            flash('An error occurred while creating user.', 'danger')
            return render_template('admin/create_user.html', form=form)
    
    @app.route('/admin/users/<int:user_id>')
    @login_required
    @admin_required
    def admin_view_user(user_id):
        """View user details"""
        try:
            user = User.query.get_or_404(user_id)
            
            # Get admin actions for this user
            actions = AdminLog.query.filter_by(target_user_id=user_id).order_by(desc(AdminLog.created_at)).limit(10).all()
            
            return render_template('admin/view_user.html', user=user, actions=actions)
            
        except Exception as e:
            current_app.logger.error(f"Error viewing user {user_id}: {str(e)}")
            flash('User not found.', 'danger')
            return redirect(url_for('admin_users'))
    
    @app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_edit_user(user_id):
        """Edit user information"""
        user = User.query.get_or_404(user_id)
        form = UpdateUserForm(user=user)
        
        try:
            if form.validate_on_submit():
                # Update user
                success, error = user.safe_update(
                    username=form.username.data.strip(),
                    email=form.email.data.strip().lower(),
                    first_name=form.first_name.data.strip() if form.first_name.data else None,
                    last_name=form.last_name.data.strip() if form.last_name.data else None,
                    is_active=form.is_active.data,
                    is_admin=form.is_admin.data
                )
                
                if error:
                    flash(f'Error updating user: {error}', 'danger')
                else:
                    # Log admin action
                    AdminLog.log_action(
                        admin_user_id=current_user.id,
                        action='UPDATE_USER',
                        target_user_id=user.id,
                        details=f'Updated user: {user.username}',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    flash(f'User {user.username} updated successfully!', 'success')
                    return redirect(url_for('admin_view_user', user_id=user.id))
            
            elif request.method == 'GET':
                # Populate form with current user data
                form.username.data = user.username
                form.email.data = user.email
                form.first_name.data = user.first_name
                form.last_name.data = user.last_name
                form.is_active.data = user.is_active
                form.is_admin.data = user.is_admin
            
            return render_template('admin/edit_user.html', form=form, user=user)
            
        except Exception as e:
            current_app.logger.error(f"Error editing user {user_id}: {str(e)}")
            flash('An error occurred while updating user.', 'danger')
            return render_template('admin/edit_user.html', form=form, user=user)
    
    @app.route('/admin/users/<int:user_id>/change-password', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_change_password(user_id):
        """Change user password"""
        user = User.query.get_or_404(user_id)
        form = ChangePasswordForm()
        
        try:
            if form.validate_on_submit():
                # Update password
                success, error = user.safe_update(
                    password_hash=generate_password_hash(form.new_password.data)
                )
                
                if error:
                    flash(f'Error changing password: {error}', 'danger')
                else:
                    # Log admin action
                    AdminLog.log_action(
                        admin_user_id=current_user.id,
                        action='CHANGE_PASSWORD',
                        target_user_id=user.id,
                        details=f'Password changed for user: {user.username}',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    flash(f'Password changed successfully for {user.username}!', 'success')
                    return redirect(url_for('admin_view_user', user_id=user.id))
            
            return render_template('admin/change_password.html', form=form, user=user)
            
        except Exception as e:
            current_app.logger.error(f"Error changing password for user {user_id}: {str(e)}")
            flash('An error occurred while changing password.', 'danger')
            return render_template('admin/change_password.html', form=form, user=user)
    
    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_user(user_id):
        """Delete user"""
        try:
            user = User.query.get_or_404(user_id)
            
            # Prevent deleting self
            if user.id == current_user.id:
                flash('You cannot delete your own account.', 'danger')
                return redirect(url_for('admin_view_user', user_id=user_id))
            
            username = user.username
            
            # Log admin action before deletion
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='DELETE_USER',
                target_user_id=user.id,
                details=f'Deleted user: {username}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            # Delete user
            success, error = user.safe_delete()
            
            if error:
                flash(f'Error deleting user: {error}', 'danger')
            else:
                flash(f'User {username} deleted successfully!', 'success')
            
            return redirect(url_for('admin_users'))
            
        except Exception as e:
            current_app.logger.error(f"Error deleting user {user_id}: {str(e)}")
            flash('An error occurred while deleting user.', 'danger')
            return redirect(url_for('admin_users'))
    
    @app.route('/admin/logs')
    @login_required
    @admin_required
    def admin_logs():
        """View admin action logs"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 50
            
            logs = AdminLog.query.order_by(desc(AdminLog.created_at)).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return render_template('admin/logs.html', logs=logs)
            
        except Exception as e:
            current_app.logger.error(f"Error loading admin logs: {str(e)}")
            flash('An error occurred while loading logs.', 'danger')
            return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/stats')
    @login_required
    @admin_required
    def admin_stats():
        """Get system statistics as JSON"""
        try:
            stats = {
                'total_users': SystemMetrics.get_metric('total_users'),
                'active_users': SystemMetrics.get_metric('active_users'),
                'admin_users': SystemMetrics.get_metric('admin_users'),
                'recent_logins': User.query.filter(User.last_login >= datetime.now(timezone.utc) - timedelta(days=7)).count()
            }
            
            return jsonify(stats)
            
        except Exception as e:
            current_app.logger.error(f"Error getting stats: {str(e)}")
            return jsonify({'error': 'Failed to get statistics'}), 500
    
    @app.route('/admin/stories')
    @login_required
    @admin_required
    def admin_stories():
        """Admin stories management page"""
        try:
            from flask_app.models import Story
            
            page = request.args.get('page', 1, type=int)
            per_page = 20
            search = request.args.get('search', '')
            source = request.args.get('source', '')
            date_from = request.args.get('date_from', '')
            date_to = request.args.get('date_to', '')
            
            # Build query
            query = Story.query
            
            if search:
                query = query.filter(Story.title.contains(search))
            
            if source:
                query = query.filter(Story.source_name == source)
            
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                    query = query.filter(Story.published_at >= date_from_obj)
                except ValueError:
                    pass
            
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                    query = query.filter(Story.published_at <= date_to_obj)
                except ValueError:
                    pass
            
            # Get paginated results
            stories = query.order_by(desc(Story.created_at)).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            # Get unique sources for filter dropdown
            sources = db.session.query(Story.source_name).distinct().all()
            sources = [s[0] for s in sources if s[0]]
            
            # Get stats for dashboard
            stats = {
                'total_stories': Story.query.count(),
                'total_events': 0,  # TODO: Add when events are implemented
                'total_topics': 0,  # TODO: Add when topics are implemented
                'total_users': User.query.count()
            }
            
            current_app.logger.info(f"Admin stories page accessed by {current_user.username}")
            return render_template('admin/stories.html', 
                                 stories=stories, 
                                 sources=sources,
                                 stats=stats)
            
        except Exception as e:
            current_app.logger.error(f"Error in admin stories: {str(e)}")
            flash('An error occurred while loading stories.', 'danger')
            return render_template('admin/stories.html', stories=None, sources=[], stats={})
    
    @app.route('/admin/events')
    @login_required
    @admin_required
    def admin_events():
        """Admin events management page"""
        try:
            from flask_app.models import EventClaim, Topic, Thread
            
            # Get search and filter parameters
            search = request.args.get('search', '').strip()
            sort_by = request.args.get('sort', 'event_date')
            topic_filter = request.args.get('topic', '')
            thread_filter = request.args.get('thread', '')
            importance_filter = request.args.get('importance', '')
            
            # Build query
            query = EventClaim.query
            
            # Apply filters
            if search:
                query = query.filter(EventClaim.claim_text.ilike(f'%{search}%'))
            
            if topic_filter:
                query = query.filter(EventClaim.topic_id == topic_filter)
            
            if thread_filter:
                query = query.join(EventClaim.threads).filter_by(id=thread_filter)
            
            if importance_filter:
                query = query.filter(EventClaim.importance == importance_filter)
            
            # Apply sorting
            if sort_by == 'event_date':
                query = query.order_by(EventClaim.event_date.desc())
            elif sort_by == 'importance':
                query = query.order_by(EventClaim.importance.desc(), EventClaim.event_date.desc())
            elif sort_by == 'created_at':
                query = query.order_by(EventClaim.created_at.desc())
            elif sort_by == 'claim_text':
                query = query.order_by(EventClaim.claim_text.asc())
            
            # Get events with statistics
            events = query.all()
            events_with_stats = []
            
            for event in events:
                event_data = event.to_dict(include_counts=True, include_dates=True)
                # Add thread names
                event_data['threads'] = [thread.name for thread in event.threads]
                events_with_stats.append(event_data)
            
            # Get filter options
            topics = Topic.query.order_by(Topic.name.asc()).all()
            threads = Thread.query.order_by(Thread.name.asc()).all()
            
            # Log admin action
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='VIEW_EVENTS',
                details=f'Viewed events list (search: {search}, filters: topic={topic_filter}, thread={thread_filter}, importance={importance_filter})',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return render_template('admin/events.html',
                                 events=events_with_stats,
                                 topics=topics,
                                 threads=threads,
                                 search=search,
                                 sort_by=sort_by,
                                 topic_filter=topic_filter,
                                 thread_filter=thread_filter,
                                 importance_filter=importance_filter)
            
        except Exception as e:
            current_app.logger.error(f"Error loading events: {str(e)}")
            flash('An error occurred while loading events.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/events/<int:event_id>')
    @login_required
    @admin_required
    def admin_view_event(event_id):
        """View event details"""
        try:
            from flask_app.models import EventClaim, Thread, Story
            
            event = EventClaim.query.get_or_404(event_id)
            
            # Get threads for this event
            threads = list(event.threads)
            
            # Get stories for this event
            stories = event.get_all_stories()
            
            # Add count attributes to event for template
            event.thread_count = event.get_thread_count()
            event.story_count = len(stories)
            
            # Log admin action
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='VIEW_EVENT',
                target_event_id=event.id,
                details=f'Viewed event: {event.claim_text[:50]}...',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return render_template('admin/view_event.html',
                                 event=event,
                                 threads=threads,
                                 stories=stories)
            
        except Exception as e:
            current_app.logger.error(f"Error viewing event {event_id}: {str(e)}")
            flash('An error occurred while loading the event.', 'danger')
            return redirect(url_for('admin_events'))
    
    @app.route('/admin/events/create', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_create_event():
        """Create new event"""
        try:
            from flask_app.models import EventClaim, Topic, Thread, Story
            
            if request.method == 'POST':
                # Get form data
                claim_text = request.form.get('claim_text', '').strip()
                event_date_str = request.form.get('event_date', '').strip()
                importance_str = request.form.get('importance', '').strip()
                topic_id_str = request.form.get('topic_id', '').strip()
                
                # Validate required fields
                if not claim_text:
                    flash('Event description is required.', 'danger')
                    return render_template('admin/create_event.html',
                                         topics=Topic.query.all(),
                                         threads=Thread.query.all(),
                                         stories=Story.query.all())
                
                if not event_date_str:
                    flash('Event date is required.', 'danger')
                    return render_template('admin/create_event.html',
                                         topics=Topic.query.all(),
                                         threads=Thread.query.all(),
                                         stories=Story.query.all())
                
                if not topic_id_str:
                    flash('Topic is required.', 'danger')
                    return render_template('admin/create_event.html',
                                         topics=Topic.query.all(),
                                         threads=Thread.query.all(),
                                         stories=Story.query.all())
                
                # Parse and validate data
                try:
                    event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
                    return render_template('admin/create_event.html',
                                         topics=Topic.query.all(),
                                         threads=Thread.query.all(),
                                         stories=Story.query.all())
                
                importance = int(importance_str) if importance_str else None
                topic_id = int(topic_id_str)
                
                # Create event
                event = EventClaim(
                    claim_text=claim_text,
                    event_date=event_date,
                    importance=importance,
                    topic_id=topic_id
                )
                
                # Handle thread assignments
                thread_ids = request.form.getlist('thread_ids')
                if thread_ids:
                    thread_ids = [int(tid) for tid in thread_ids if tid.isdigit()]
                    for thread_id in thread_ids:
                        thread = Thread.query.get(thread_id)
                        if thread:
                            event.add_thread(thread)
                
                # Handle story assignments
                story_ids = request.form.getlist('story_ids')
                if story_ids:
                    story_ids = [int(sid) for sid in story_ids if sid.isdigit()]
                    for story_id in story_ids:
                        story = Story.query.get(story_id)
                        if story:
                            event.add_story(story)
                
                # Validate event
                validation_errors = event.validate()
                if validation_errors:
                    for error in validation_errors:
                        flash(error, 'danger')
                    return render_template('admin/create_event.html',
                                         topics=Topic.query.all(),
                                         threads=Thread.query.all(),
                                         stories=Story.query.all())
                
                try:
                    db.session.add(event)
                    db.session.commit()
                    
                    # Log admin action
                    AdminLog.log_action(
                        admin_user_id=current_user.id,
                        action='CREATE_EVENT',
                        target_event_id=event.id,
                        details=f'Created event: {event.claim_text[:50]}...',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    flash('Event created successfully!', 'success')
                    return redirect(url_for('admin_view_event', event_id=event.id))
                    
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error creating event: {str(e)}")
                    flash('An error occurred while creating the event.', 'danger')
            
            return render_template('admin/create_event.html',
                                 topics=Topic.query.all(),
                                 threads=Thread.query.all(),
                                 stories=Story.query.all())
            
        except Exception as e:
            current_app.logger.error(f"Error in create event: {str(e)}")
            flash('An error occurred while loading the create event page.', 'danger')
            return redirect(url_for('admin_events'))
    
    @app.route('/admin/events/<int:event_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_edit_event(event_id):
        """Edit event"""
        try:
            from flask_app.models import EventClaim, Topic, Thread, Story
            
            event = EventClaim.query.get_or_404(event_id)
            
            if request.method == 'POST':
                # Get form data
                claim_text = request.form.get('claim_text', '').strip()
                event_date_str = request.form.get('event_date', '').strip()
                importance_str = request.form.get('importance', '').strip()
                topic_id_str = request.form.get('topic_id', '').strip()
                
                # Validate required fields
                if not claim_text:
                    flash('Event description is required.', 'danger')
                    # Get data for template
                    current_threads = list(event.threads)
                    current_stories = event.get_all_stories()
                    return render_template('admin/edit_event.html',
                                         event=event,
                                         topics=Topic.query.all(),
                                         threads=Thread.query.all(),
                                         stories=Story.query.all(),
                                         current_threads=current_threads,
                                         current_stories=current_stories)
                
                if not event_date_str:
                    flash('Event date is required.', 'danger')
                    # Get data for template
                    current_threads = list(event.threads)
                    current_stories = event.get_all_stories()
                    return render_template('admin/edit_event.html',
                                         event=event,
                                         topics=Topic.query.all(),
                                         threads=Thread.query.all(),
                                         stories=Story.query.all(),
                                         current_threads=current_threads,
                                         current_stories=current_stories)
                
                if not topic_id_str:
                    flash('Topic is required.', 'danger')
                    # Get data for template
                    current_threads = list(event.threads)
                    current_stories = event.get_all_stories()
                    return render_template('admin/edit_event.html',
                                         event=event,
                                         topics=Topic.query.all(),
                                         threads=Thread.query.all(),
                                         stories=Story.query.all(),
                                         current_threads=current_threads,
                                         current_stories=current_stories)
                
                # Parse and validate data
                try:
                    event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
                    # Get data for template
                    current_threads = list(event.threads)
                    current_stories = event.get_all_stories()
                    return render_template('admin/edit_event.html',
                                         event=event,
                                         topics=Topic.query.all(),
                                         threads=Thread.query.all(),
                                         stories=Story.query.all(),
                                         current_threads=current_threads,
                                         current_stories=current_stories)
                
                importance = int(importance_str) if importance_str else None
                topic_id = int(topic_id_str)
                
                # Update event
                event.claim_text = claim_text
                event.event_date = event_date
                event.importance = importance
                event.topic_id = topic_id
                
                # Handle thread assignments
                thread_ids = request.form.getlist('thread_ids')
                if thread_ids:
                    thread_ids = [int(tid) for tid in thread_ids if tid.isdigit()]
                    # Clear existing thread associations
                    event.threads = []
                    # Add new thread associations
                    for thread_id in thread_ids:
                        thread = Thread.query.get(thread_id)
                        if thread:
                            event.add_thread(thread)
                else:
                    # No threads selected, clear all thread assignments
                    event.threads = []
                
                # Handle story assignments
                story_ids = request.form.getlist('story_ids')
                if story_ids:
                    story_ids = [int(sid) for sid in story_ids if sid.isdigit()]
                    # Clear existing story associations
                    for link in event.event_story_links:
                        db.session.delete(link)
                    # Add new story associations
                    for story_id in story_ids:
                        story = Story.query.get(story_id)
                        if story:
                            event.add_story(story)
                else:
                    # No stories selected, clear all story assignments
                    for link in event.event_story_links:
                        db.session.delete(link)
                
                # Validate event
                validation_errors = event.validate()
                if validation_errors:
                    for error in validation_errors:
                        flash(error, 'danger')
                    # Get data for template
                    current_threads = list(event.threads)
                    current_stories = event.get_all_stories()
                    return render_template('admin/edit_event.html',
                                         event=event,
                                         topics=Topic.query.all(),
                                         threads=Thread.query.all(),
                                         stories=Story.query.all(),
                                         current_threads=current_threads,
                                         current_stories=current_stories)
                
                try:
                    db.session.commit()
                    
                    # Log admin action
                    AdminLog.log_action(
                        admin_user_id=current_user.id,
                        action='UPDATE_EVENT',
                        target_event_id=event.id,
                        details=f'Updated event: {event.claim_text[:50]}...',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    flash('Event updated successfully!', 'success')
                    return redirect(url_for('admin_view_event', event_id=event.id))
                    
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error updating event: {str(e)}")
                    flash('An error occurred while updating the event.', 'danger')
            
            # Get current threads and stories for display
            current_threads = list(event.threads)
            current_stories = event.get_all_stories()
            
            return render_template('admin/edit_event.html',
                                 event=event,
                                 topics=Topic.query.all(),
                                 threads=Thread.query.all(),
                                 stories=Story.query.all(),
                                 current_threads=current_threads,
                                 current_stories=current_stories)
            
        except Exception as e:
            current_app.logger.error(f"Error editing event {event_id}: {str(e)}")
            flash('An error occurred while loading the event for editing.', 'danger')
            return redirect(url_for('admin_events'))
    
    @app.route('/admin/events/<int:event_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_event(event_id):
        """Delete event"""
        try:
            from flask_app.models import EventClaim
            
            event = EventClaim.query.get_or_404(event_id)
            
            try:
                # Log admin action before deletion
                AdminLog.log_action(
                    admin_user_id=current_user.id,
                    action='DELETE_EVENT',
                    target_event_id=event.id,
                    details=f'Deleted event: {event.claim_text[:50]}...',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                
                db.session.delete(event)
                db.session.commit()
                
                flash('Event deleted successfully!', 'success')
                return redirect(url_for('admin_events'))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error deleting event: {str(e)}")
                flash('An error occurred while deleting the event.', 'danger')
                return redirect(url_for('admin_view_event', event_id=event_id))
            
        except Exception as e:
            current_app.logger.error(f"Error in delete event: {str(e)}")
            flash('An error occurred while deleting the event.', 'danger')
            return redirect(url_for('admin_events'))
    
    @app.route('/admin/topics')
    @login_required
    @admin_required
    def admin_topics():
        """Admin topics management page"""
        try:
            from flask_app.models import Topic
            
            # Get all topics with statistics
            topics = Topic.get_all_ordered()
            topics_with_stats = []
            
            for topic in topics:
                topic_data = topic.to_dict(include_counts=True)
                # Add the count attributes that templates expect
                topic_data['thread_count'] = topic.get_thread_count()
                topic_data['event_count'] = topic.get_event_count()
                topic_data['unsorted_event_count'] = len(topic.get_unsorted_events())
                topics_with_stats.append(topic_data)
            
            # Log admin action
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='VIEW_TOPICS',
                details='Viewed topics management page',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return render_template('admin/topics.html', topics=topics_with_stats)
            
        except Exception as e:
            current_app.logger.error(f"Error in admin_topics: {str(e)}")
            flash('An error occurred while loading topics.', 'danger')
            return redirect(url_for('admin_dashboard'))
    
    # Topic CRUD Operations
    @app.route('/admin/topics/<int:topic_id>')
    @login_required
    @admin_required
    def admin_view_topic(topic_id):
        """View topic details"""
        try:
            from flask_app.models import Topic, Thread, EventClaim
            
            topic = Topic.query.get_or_404(topic_id)
            
            # Get threads for this topic
            threads = Thread.find_by_topic(topic_id)
            threads_with_stats = []

            for thread in threads:
                thread_data = thread.to_dict(include_counts=True, include_dates=True)
                # Add the count attributes that templates expect
                thread_data['event_count'] = thread.get_event_count()
                threads_with_stats.append(thread_data)
            
            # Get unsorted events (events without threads)
            unsorted_events = topic.get_unsorted_events()
            
            # Get stories associated with this topic
            stories = list(topic.stories)
            
            # Add count attributes to topic for template
            topic.thread_count = topic.get_thread_count()
            topic.event_count = topic.get_event_count()
            topic.unsorted_event_count = len(unsorted_events)
            topic.story_count = len(stories)
            
            # Log admin action
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='VIEW_TOPIC',
                target_topic_id=topic.id,
                details=f'Viewed topic: {topic.name}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return render_template('admin/view_topic.html',
                                 topic=topic,
                                 threads=threads_with_stats,
                                 unsorted_events=unsorted_events,
                                 stories=stories)
            
        except Exception as e:
            current_app.logger.error(f"Error viewing topic {topic_id}: {str(e)}")
            flash('An error occurred while loading the topic.', 'danger')
            return redirect(url_for('admin_topics'))
    
    @app.route('/admin/topics/create', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_create_topic():
        """Create new topic"""
        try:
            from flask_app.models import Topic
            
            if request.method == 'POST':
                # Get form data
                name = request.form.get('name', '').strip()
                description = request.form.get('description', '').strip()
                color = request.form.get('color', '').strip()
                
                # Validate required fields
                if not name:
                    flash('Topic name is required.', 'danger')
                    return render_template('admin/create_topic.html')
                
                # Check if topic name already exists
                existing_topic = Topic.find_by_name(name)
                if existing_topic:
                    flash('A topic with this name already exists.', 'danger')
                    return render_template('admin/create_topic.html')
                
                # Create topic
                topic = Topic(
                    name=name,
                    description=description if description else None,
                    color=color if color else None
                )
                
                # Validate topic
                errors = topic.validate()
                if errors:
                    for error in errors:
                        flash(error, 'danger')
                    return render_template('admin/create_topic.html')
                
                try:
                    db.session.add(topic)
                    db.session.commit()
                    
                    # Log admin action
                    AdminLog.log_action(
                        admin_user_id=current_user.id,
                        action='CREATE_TOPIC',
                        target_topic_id=topic.id,
                        details=f'Created topic: {topic.name}',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    flash('Topic created successfully!', 'success')
                    return redirect(url_for('admin_view_topic', topic_id=topic.id))
                    
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error creating topic: {str(e)}")
                    flash('An error occurred while creating the topic.', 'danger')
            
            return render_template('admin/create_topic.html')
            
        except Exception as e:
            current_app.logger.error(f"Error in create topic: {str(e)}")
            flash('An error occurred while loading the create topic page.', 'danger')
            return redirect(url_for('admin_topics'))
    
    @app.route('/admin/topics/<int:topic_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_edit_topic(topic_id):
        """Edit topic"""
        try:
            from flask_app.models import Topic
            
            topic = Topic.query.get_or_404(topic_id)
            
            if request.method == 'POST':
                # Get form data
                name = request.form.get('name', '').strip()
                description = request.form.get('description', '').strip()
                color = request.form.get('color', '').strip()
                
                # Validate required fields
                if not name:
                    flash('Topic name is required.', 'danger')
                    return render_template('admin/edit_topic.html', topic=topic)
                
                # Check if topic name already exists (excluding current topic)
                existing_topic = Topic.find_by_name(name)
                if existing_topic and existing_topic.id != topic.id:
                    flash('A topic with this name already exists.', 'danger')
                    return render_template('admin/edit_topic.html', topic=topic)
                
                # Update topic
                topic.name = name
                topic.description = description if description else None
                topic.color = color if color else None
                
                # Validate topic
                errors = topic.validate()
                if errors:
                    for error in errors:
                        flash(error, 'danger')
                    return render_template('admin/edit_topic.html', topic=topic)
                
                try:
                    db.session.commit()
                    
                    # Log admin action
                    AdminLog.log_action(
                        admin_user_id=current_user.id,
                        action='UPDATE_TOPIC',
                        target_topic_id=topic.id,
                        details=f'Updated topic: {topic.name}',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    flash('Topic updated successfully!', 'success')
                    return redirect(url_for('admin_view_topic', topic_id=topic.id))
                    
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error updating topic {topic_id}: {str(e)}")
                    flash('An error occurred while updating the topic.', 'danger')
            
            # Add count attributes to topic for template
            topic.thread_count = topic.get_thread_count()
            topic.event_count = topic.get_event_count()
            
            return render_template('admin/edit_topic.html', topic=topic)
            
        except Exception as e:
            current_app.logger.error(f"Error editing topic {topic_id}: {str(e)}")
            flash('An error occurred while loading the topic for editing.', 'danger')
            return redirect(url_for('admin_topics'))
    
    @app.route('/admin/topics/<int:topic_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_topic(topic_id):
        """Delete topic"""
        try:
            from flask_app.models import Topic
            
            topic = Topic.query.get_or_404(topic_id)
            topic_name = topic.name
            
            # Log admin action before deletion
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='DELETE_TOPIC',
                target_topic_id=topic.id,
                details=f'Deleted topic: {topic_name}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            # Delete topic (cascade will handle related records)
            db.session.delete(topic)
            db.session.commit()
            
            flash(f'Topic "{topic_name}" deleted successfully!', 'success')
            return redirect(url_for('admin_topics'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting topic {topic_id}: {str(e)}")
            flash('An error occurred while deleting the topic.', 'danger')
            return redirect(url_for('admin_topics'))
    
    
    @app.route('/admin/metrics')
    @login_required
    @admin_required
    def admin_metrics():
        """Admin system metrics page - placeholder"""
        flash('System metrics coming soon!', 'info')
        return redirect(url_for('admin_dashboard'))
    
    # Story CRUD Operations
    @app.route('/admin/stories/<int:story_id>')
    @login_required
    @admin_required
    def admin_view_story(story_id):
        """View story details"""
        try:
            from flask_app.models import Story, EventClaim, StoryTag, Tag
            
            story = Story.query.get_or_404(story_id)
            
            # Get related events
            events = EventClaim.query.filter_by(story_primary_id=story_id).all()
            
            # Get tags
            story_tags = StoryTag.query.filter_by(story_id=story_id).all()
            tags = [st.tag for st in story_tags if st.tag]
            
            # Get topics
            topics = story.get_topics()
            
            # Log admin action
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='VIEW_STORY',
                target_story_id=story.id,
                details=f'Viewed story: {story.title[:50]}...',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return render_template('admin/view_story.html', story=story, events=events, tags=tags, topics=topics)
            
        except Exception as e:
            current_app.logger.error(f"Error viewing story {story_id}: {str(e)}")
            flash('An error occurred while loading the story.', 'danger')
            return redirect(url_for('admin_stories'))
    
    @app.route('/admin/stories/<int:story_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_edit_story(story_id):
        """Edit story"""
        try:
            from flask_app.models import Story, Tag, StoryTag, Topic
            
            story = Story.query.get_or_404(story_id)
            
            if request.method == 'POST':
                # Get form data
                title = request.form.get('title', '').strip()
                source_name = request.form.get('source_name', '').strip()
                author = request.form.get('author', '').strip()
                published_at = request.form.get('published_at', '').strip()
                summary = request.form.get('summary', '').strip()
                raw_text = request.form.get('raw_text', '').strip()
                tags_input = request.form.get('tags', '').strip()
                topic_ids = request.form.getlist('topics')  # Get selected topic IDs
                
                # Validate required fields
                if not title:
                    flash('Title is required.', 'danger')
                    return render_template('admin/edit_story.html', story=story)
                
                if not source_name:
                    flash('Source name is required.', 'danger')
                    return render_template('admin/edit_story.html', story=story)
                
                # Parse published date
                published_date = None
                if published_at:
                    try:
                        published_date = datetime.strptime(published_at, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
                        return render_template('admin/edit_story.html', story=story)
                
                # Update story
                story.title = title
                story.source_name = source_name
                story.author = author if author else None
                story.published_at = published_date
                story.summary = summary if summary else None
                story.raw_text = raw_text if raw_text else None
                
                # Handle tags
                if tags_input:
                    tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                    
                    # Remove existing tags
                    StoryTag.query.filter_by(story_id=story.id).delete()
                    
                    # Add new tags
                    for tag_name in tag_names:
                        # Get or create tag
                        tag = Tag.query.filter_by(name=tag_name).first()
                        if not tag:
                            tag = Tag(name=tag_name)
                            db.session.add(tag)
                            db.session.flush()  # Get the ID
                        
                        # Create story-tag relationship
                        story_tag = StoryTag(story_id=story.id, tag_id=tag.id)
                        db.session.add(story_tag)
                
                # Handle topics
                if topic_ids:
                    # Convert string IDs to integers
                    topic_ids = [int(tid) for tid in topic_ids if tid.isdigit()]
                    success, error = story.set_topics(topic_ids)
                    if not success:
                        flash(f'Error updating topics: {error}', 'danger')
                        return render_template('admin/edit_story.html', story=story)
                
                try:
                    db.session.commit()
                    
                    # Log admin action
                    AdminLog.log_action(
                        admin_user_id=current_user.id,
                        action='UPDATE_STORY',
                        target_story_id=story.id,
                        details=f'Updated story: {story.title[:50]}...',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    flash('Story updated successfully!', 'success')
                    return redirect(url_for('admin_view_story', story_id=story.id))
                    
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error updating story {story_id}: {str(e)}")
                    flash('An error occurred while updating the story.', 'danger')
            
            # Get current tags for display
            story_tags = StoryTag.query.filter_by(story_id=story.id).all()
            current_tags = [st.tag.name for st in story_tags if st.tag]
            
            # Get current topics for display
            current_topics = story.get_topics()
            current_topic_ids = [topic.id for topic in current_topics]
            
            # Get all available topics
            all_topics = Topic.get_all_ordered()
            
            return render_template('admin/edit_story.html', 
                                 story=story, 
                                 current_tags=current_tags,
                                 current_topics=current_topics,
                                 current_topic_ids=current_topic_ids,
                                 all_topics=all_topics)
            
        except Exception as e:
            current_app.logger.error(f"Error editing story {story_id}: {str(e)}")
            flash('An error occurred while loading the story for editing.', 'danger')
            return redirect(url_for('admin_stories'))
    
    @app.route('/admin/stories/<int:story_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_story(story_id):
        """Delete story"""
        try:
            from flask_app.models import Story
            
            story = Story.query.get_or_404(story_id)
            story_title = story.title
            
            # Log admin action before deletion
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='DELETE_STORY',
                target_story_id=story.id,
                details=f'Deleted story: {story_title[:50]}...',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            # Delete story (cascade will handle related records)
            db.session.delete(story)
            db.session.commit()
            
            flash(f'Story "{story_title[:50]}..." deleted successfully!', 'success')
            return redirect(url_for('admin_stories'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting story {story_id}: {str(e)}")
            flash('An error occurred while deleting the story.', 'danger')
            return redirect(url_for('admin_stories'))
    
    @app.route('/admin/stories/create', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_create_story():
        """Create new story"""
        try:
            from flask_app.models import Story, Tag, StoryTag
            
            if request.method == 'POST':
                # Get form data
                url = request.form.get('url', '').strip()
                title = request.form.get('title', '').strip()
                source_name = request.form.get('source_name', '').strip()
                author = request.form.get('author', '').strip()
                published_at = request.form.get('published_at', '').strip()
                summary = request.form.get('summary', '').strip()
                raw_text = request.form.get('raw_text', '').strip()
                tags_input = request.form.get('tags', '').strip()
                
                # Validate required fields
                if not url:
                    flash('URL is required.', 'danger')
                    return render_template('admin/create_story.html')
                
                if not title:
                    flash('Title is required.', 'danger')
                    return render_template('admin/create_story.html')
                
                if not source_name:
                    flash('Source name is required.', 'danger')
                    return render_template('admin/create_story.html')
                
                # Check if URL already exists
                existing_story = Story.query.filter_by(url=url).first()
                if existing_story:
                    flash('A story with this URL already exists.', 'danger')
                    return render_template('admin/create_story.html')
                
                # Parse published date
                published_date = None
                if published_at:
                    try:
                        published_date = datetime.strptime(published_at, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
                        return render_template('admin/create_story.html')
                
                # Create story
                story = Story(
                    url=url,
                    title=title,
                    source_name=source_name,
                    author=author if author else None,
                    published_at=published_date,
                    summary=summary if summary else None,
                    raw_text=raw_text if raw_text else None
                )
                
                db.session.add(story)
                db.session.flush()  # Get the ID
                
                # Handle tags
                if tags_input:
                    tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                    
                    for tag_name in tag_names:
                        # Get or create tag
                        tag = Tag.query.filter_by(name=tag_name).first()
                        if not tag:
                            tag = Tag(name=tag_name)
                            db.session.add(tag)
                            db.session.flush()  # Get the ID
                        
                        # Create story-tag relationship
                        story_tag = StoryTag(story_id=story.id, tag_id=tag.id)
                        db.session.add(story_tag)
                
                try:
                    db.session.commit()
                    
                    # Log admin action
                    AdminLog.log_action(
                        admin_user_id=current_user.id,
                        action='CREATE_STORY',
                        target_story_id=story.id,
                        details=f'Created story: {story.title[:50]}...',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    flash('Story created successfully!', 'success')
                    return redirect(url_for('admin_view_story', story_id=story.id))
                    
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error creating story: {str(e)}")
                    flash('An error occurred while creating the story.', 'danger')
            
            return render_template('admin/create_story.html')
            
        except Exception as e:
            current_app.logger.error(f"Error in create story: {str(e)}")
            flash('An error occurred while loading the create story page.', 'danger')
            return redirect(url_for('admin_stories'))

    # ===== THREAD MANAGEMENT ROUTES =====
    
    @app.route('/admin/threads')
    @login_required
    @admin_required
    def admin_threads():
        """Admin threads management page - all threads"""
        try:
            from flask_app.models import Thread, Topic

            # Get all threads with statistics
            threads = Thread.find_all()
            threads_with_stats = []

            for thread in threads:
                thread_data = thread.to_dict(include_counts=True, include_dates=True)
                # Add the count attributes that templates expect
                thread_data['event_count'] = thread.events.count()
                thread_data['topic_count'] = thread.topics.count()
                thread_data['topics'] = [topic.name for topic in thread.topics]
                threads_with_stats.append(thread_data)

            # Get all topics for the create thread form
            topics = Topic.query.all()

            # Log admin action
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='VIEW_THREADS',
                details='Viewed all threads',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )

            return render_template('admin/threads.html', 
                                 threads=threads_with_stats,
                                 topics=topics)

        except Exception as e:
            current_app.logger.error(f"Error in admin_threads: {str(e)}")
            flash('An error occurred while loading threads.', 'danger')
            return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/topics/<int:topic_id>/threads')
    @login_required
    @admin_required
    def admin_topic_threads(topic_id):
        """Admin threads management page for a specific topic"""
        try:
            from flask_app.models import Topic, Thread

            # Get the topic
            topic = Topic.query.get_or_404(topic_id)

            # Get all threads for this topic with statistics
            threads = Thread.find_by_topic(topic_id)
            threads_with_stats = []

            for thread in threads:
                thread_data = thread.to_dict(include_counts=True, include_dates=True)
                # Add the count attributes that templates expect
                thread_data['event_count'] = thread.events.count()
                thread_data['topic_count'] = thread.topics.count()
                thread_data['topics'] = [t.name for t in thread.topics]
                threads_with_stats.append(thread_data)

            # Log admin action
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='VIEW_TOPIC_THREADS',
                target_topic_id=topic.id,
                details=f'Viewed threads for topic: {topic.name}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )

            return render_template('admin/threads.html', 
                                 topic=topic, 
                                 threads=threads_with_stats)

        except Exception as e:
            current_app.logger.error(f"Error in admin_topic_threads: {str(e)}")
            flash('An error occurred while loading threads.', 'danger')
            return redirect(url_for('admin_topics'))

    @app.route('/admin/threads/<int:thread_id>')
    @login_required
    @admin_required
    def admin_view_thread(thread_id):
        """View thread details"""
        try:
            from flask_app.models import Thread, EventClaim

            thread = Thread.query.get_or_404(thread_id)

            # Get events for this thread
            events = thread.get_events_by_date()
            
            # Get stories for this thread
            stories = thread.get_stories()

            # Add count attributes to thread for template
            thread.event_count = thread.get_event_count()
            thread.story_count = thread.get_story_count()
            first_date, last_date = thread.get_date_range()
            thread.first_event_date = first_date
            thread.last_event_date = last_date

            # Log admin action
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='VIEW_THREAD',
                target_thread_id=thread.id,
                details=f'Viewed thread: {thread.name}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )

            return render_template('admin/view_thread.html',
                                 thread=thread,
                                 events=events,
                                 stories=stories)

        except Exception as e:
            current_app.logger.error(f"Error viewing thread {thread_id}: {str(e)}")
            flash('An error occurred while loading the thread.', 'danger')
            return redirect(url_for('admin_topics'))

    @app.route('/admin/threads/create', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_create_thread():
        """Create new independent thread"""
        try:
            from flask_app.models import Topic, Thread

            if request.method == 'POST':
                # Get form data
                name = request.form.get('name', '').strip()
                description = request.form.get('description', '').strip()
                start_date_str = request.form.get('start_date', '').strip()
                topic_ids = request.form.getlist('topic_ids')  # Multiple topics can be selected

                # Validate required fields
                if not name:
                    flash('Thread name is required.', 'danger')
                    return render_template('admin/create_thread.html', topics=Topic.query.all())

                # Check for duplicate name
                existing_thread = Thread.query.filter_by(name=name).first()
                if existing_thread:
                    flash('A thread with this name already exists.', 'danger')
                    return render_template('admin/create_thread.html', topics=Topic.query.all())

                # Parse start date
                start_date = None
                if start_date_str:
                    try:
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
                        return render_template('admin/create_thread.html', topics=Topic.query.all())

                # Create thread
                thread = Thread(
                    name=name,
                    description=description if description else None,
                    start_date=start_date
                )

                # Validate thread
                validation_errors = thread.validate()
                if validation_errors:
                    for error in validation_errors:
                        flash(error, 'danger')
                    return render_template('admin/create_thread.html', topics=Topic.query.all())

                try:
                    db.session.add(thread)
                    db.session.commit()

                    # Add selected topics to the thread
                    if topic_ids:
                        for topic_id in topic_ids:
                            topic = Topic.query.get(topic_id)
                            if topic:
                                thread.add_topic(topic)

                    # Log admin action
                    AdminLog.log_action(
                        admin_user_id=current_user.id,
                        action='CREATE_THREAD',
                        target_thread_id=thread.id,
                        details=f'Created thread: {thread.name}',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )

                    flash('Thread created successfully!', 'success')
                    return redirect(url_for('admin_view_thread', thread_id=thread.id))

                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error creating thread: {str(e)}")
                    flash('An error occurred while creating the thread.', 'danger')

            return render_template('admin/create_thread.html', topics=Topic.query.all())

        except Exception as e:
            current_app.logger.error(f"Error in create thread: {str(e)}")
            flash('An error occurred while loading the create thread page.', 'danger')
            return redirect(url_for('admin_threads'))

    @app.route('/admin/threads/<int:thread_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_edit_thread(thread_id):
        """Edit thread"""
        try:
            from flask_app.models import Thread

            thread = Thread.query.get_or_404(thread_id)

            if request.method == 'POST':
                # Get form data
                name = request.form.get('name', '').strip()
                description = request.form.get('description', '').strip()
                start_date_str = request.form.get('start_date', '').strip()

                # Validate required fields
                if not name:
                    flash('Thread name is required.', 'danger')
                    # Get data for template
                    current_stories = thread.get_stories()
                    current_story_ids = [story.id for story in current_stories]
                    from flask_app.models import Story, Topic
                    all_stories = Story.query.order_by(Story.title.asc()).all()
                    all_topics = Topic.query.order_by(Topic.name.asc()).all()
                    return render_template('admin/edit_thread.html', 
                                         thread=thread,
                                         current_story_ids=current_story_ids,
                                         all_stories=all_stories,
                                         all_topics=all_topics)

                # Check for duplicate name (excluding current thread)
                existing_thread = Thread.query.filter_by(name=name).first()
                if existing_thread and existing_thread.id != thread.id:
                    flash('A thread with this name already exists.', 'danger')
                    # Get data for template
                    current_stories = thread.get_stories()
                    current_story_ids = [story.id for story in current_stories]
                    from flask_app.models import Story, Topic
                    all_stories = Story.query.order_by(Story.title.asc()).all()
                    all_topics = Topic.query.order_by(Topic.name.asc()).all()
                    return render_template('admin/edit_thread.html', 
                                         thread=thread,
                                         current_story_ids=current_story_ids,
                                         all_stories=all_stories,
                                         all_topics=all_topics)

                # Parse start date
                start_date = None
                if start_date_str:
                    try:
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
                        # Get data for template
                        current_stories = thread.get_stories()
                        current_story_ids = [story.id for story in current_stories]
                        from flask_app.models import Story, Topic
                        all_stories = Story.query.order_by(Story.title.asc()).all()
                        all_topics = Topic.query.order_by(Topic.name.asc()).all()
                        return render_template('admin/edit_thread.html', 
                                             thread=thread,
                                             current_story_ids=current_story_ids,
                                             all_stories=all_stories,
                                             all_topics=all_topics)

                # Update thread
                thread.name = name
                thread.description = description if description else None
                thread.start_date = start_date
                
                # Handle topic assignments
                topic_ids = request.form.getlist('topic_ids')
                if topic_ids:
                    # Convert string IDs to integers
                    topic_ids = [int(tid) for tid in topic_ids if tid.isdigit()]
                    from flask_app.models import Topic
                    # Clear existing topic associations
                    thread.topics = []
                    # Add new topic associations
                    for topic_id in topic_ids:
                        topic = Topic.query.get(topic_id)
                        if topic:
                            thread.add_topic(topic)
                else:
                    # No topics selected, clear all topic assignments
                    thread.topics = []

                # Handle story assignments
                story_ids = request.form.getlist('stories')
                if story_ids:
                    # Convert string IDs to integers
                    story_ids = [int(sid) for sid in story_ids if sid.isdigit()]
                    success, error = thread.set_stories(story_ids)
                    if not success:
                        flash(f'Error updating stories: {error}', 'danger')
                        # Get data for template
                        current_stories = thread.get_stories()
                        current_story_ids = [story.id for story in current_stories]
                        from flask_app.models import Story, Topic
                        all_stories = Story.query.order_by(Story.title.asc()).all()
                        all_topics = Topic.query.order_by(Topic.name.asc()).all()
                        return render_template('admin/edit_thread.html', 
                                             thread=thread,
                                             current_story_ids=current_story_ids,
                                             all_stories=all_stories,
                                             all_topics=all_topics)
                else:
                    # No stories selected, clear all story assignments
                    thread.set_stories([])

                # Validate thread
                validation_errors = thread.validate()
                if validation_errors:
                    for error in validation_errors:
                        flash(error, 'danger')
                    # Get data for template
                    current_stories = thread.get_stories()
                    current_story_ids = [story.id for story in current_stories]
                    from flask_app.models import Story, Topic
                    all_stories = Story.query.order_by(Story.title.asc()).all()
                    all_topics = Topic.query.order_by(Topic.name.asc()).all()
                    return render_template('admin/edit_thread.html', 
                                         thread=thread,
                                         current_story_ids=current_story_ids,
                                         all_stories=all_stories,
                                         all_topics=all_topics)

                try:
                    db.session.commit()

                    # Log admin action
                    AdminLog.log_action(
                        admin_user_id=current_user.id,
                        action='UPDATE_THREAD',
                        target_thread_id=thread.id,
                        details=f'Updated thread: {thread.name}',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )

                    flash('Thread updated successfully!', 'success')
                    return redirect(url_for('admin_view_thread', thread_id=thread.id))

                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error updating thread: {str(e)}")
                    flash('An error occurred while updating the thread.', 'danger')

            # Get current stories for display
            current_stories = thread.get_stories()
            current_story_ids = [story.id for story in current_stories]

            # Get all available stories and topics
            from flask_app.models import Story, Topic
            all_stories = Story.query.order_by(Story.title.asc()).all()
            all_topics = Topic.query.order_by(Topic.name.asc()).all()

            return render_template('admin/edit_thread.html', 
                                 thread=thread,
                                 current_story_ids=current_story_ids,
                                 all_stories=all_stories,
                                 all_topics=all_topics)

        except Exception as e:
            current_app.logger.error(f"Error editing thread {thread_id}: {str(e)}")
            flash('An error occurred while loading the thread for editing.', 'danger')
            return redirect(url_for('admin_threads'))

    @app.route('/admin/threads/<int:thread_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_thread(thread_id):
        """Delete thread"""
        try:
            from flask_app.models import Thread

            thread = Thread.query.get_or_404(thread_id)
            thread_name = thread.name
            topic_id = thread.topic_id

            # Check if thread has events
            event_count = thread.get_event_count()
            if event_count > 0:
                flash(f'Cannot delete thread with {event_count} events. Please move or delete events first.', 'danger')
                return redirect(url_for('admin_view_thread', thread_id=thread_id))

            try:
                db.session.delete(thread)
                db.session.commit()

                # Log admin action
                AdminLog.log_action(
                    admin_user_id=current_user.id,
                    action='DELETE_THREAD',
                    target_topic_id=topic_id,
                    details=f'Deleted thread: {thread_name}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )

                flash('Thread deleted successfully!', 'success')
                return redirect(url_for('admin_threads', topic_id=topic_id))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error deleting thread: {str(e)}")
                flash('An error occurred while deleting the thread.', 'danger')
                return redirect(url_for('admin_view_thread', thread_id=thread_id))

        except Exception as e:
            current_app.logger.error(f"Error in delete thread: {str(e)}")
            flash('An error occurred while deleting the thread.', 'danger')
            return redirect(url_for('admin_topics'))