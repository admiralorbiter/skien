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
        """Admin events management page - placeholder"""
        flash('Events management coming soon!', 'info')
        return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/topics')
    @login_required
    @admin_required
    def admin_topics():
        """Admin topics management page - placeholder"""
        flash('Topics management coming soon!', 'info')
        return redirect(url_for('admin_dashboard'))
    
    
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
            
            # Log admin action
            AdminLog.log_action(
                admin_user_id=current_user.id,
                action='VIEW_STORY',
                target_story_id=story.id,
                details=f'Viewed story: {story.title[:50]}...',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return render_template('admin/view_story.html', story=story, events=events, tags=tags)
            
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
            from flask_app.models import Story, Tag, StoryTag
            
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
            
            return render_template('admin/edit_story.html', story=story, current_tags=current_tags)
            
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