# SKIEN Current Development

## Active Sprint: Milestone 2 - Topic & Thread Management
**Sprint Goal**: Enable organization of data into topics and threads for better content management

> **Note**: This document focuses on current and future work. All completed work is documented in `past_development.md`.

## Current Focus: Topic and Thread Management System

### In Progress
**Current Phase**: Phase 2 - Thread Management CRUD Operations
- **Active Task**: Thread Admin Routes Implementation
- **Next**: Thread Templates and Features
- **Goal**: Complete thread management system for organizing events chronologically

### Immediate Next Steps
1. **Thread Admin Routes** - Create CRUD operations for threads within topics
2. **Thread Templates** - Build responsive UI for thread management
3. **Event-Thread Assignment** - Connect events to threads for chronological organization
4. **Thread Features** - Add statistics, ordering, and date management

### Implementation Progress
- [x] **Phase 1.1: Topic Admin Routes** (Completed)
  - [x] `admin_topics()` - List all topics with statistics
  - [x] `admin_view_topic(id)` - View topic details with threads/events
  - [x] `admin_create_topic()` - Create new topic with validation
  - [x] `admin_edit_topic(id)` - Edit topic name, description, color
  - [x] `admin_delete_topic(id)` - Delete topic with confirmation
  - [x] Admin logging for all topic operations

- [x] **Phase 1.2: Topic Templates** (Completed)
  - [x] `topics.html` - Topic list with stats and search
  - [x] `view_topic.html` - Topic details with threads/events display
  - [x] `create_topic.html` - Topic creation form with color picker
  - [x] `edit_topic.html` - Topic editing form with validation
  - [x] Responsive design with Bootstrap components

- [x] **Phase 1.3: Topic Features** (Completed)
  - [x] Color picker for visual identification
  - [x] Statistics display (thread count, event count, story count)
  - [x] Search and filter functionality
  - [x] Name uniqueness validation
  - [x] Admin panel integration and navigation

- [x] **Phase 1.4: Story-Topic Integration** (Completed)
  - [x] Many-to-many relationship between stories and topics
  - [x] Story edit form with topic selection
  - [x] Story view page displaying assigned topics
  - [x] Topic view page displaying associated stories
  - [x] Database migration for story_topics table
  - [x] Topic assignment functionality in admin interface

### Recently Completed
*All completed work has been moved to past_development.md*

### Next Up (Ready to Start)

#### **Phase 2: Thread Management CRUD (2-3 commits)**
- [ ] **Thread Admin Routes** (1 commit)
  - [ ] `admin_threads(topic_id)` - List threads for specific topic
  - [ ] `admin_view_thread(id)` - View thread details with events
  - [ ] `admin_create_thread()` - Create new thread within topic
  - [ ] `admin_edit_thread(id)` - Edit thread name, description, dates
  - [ ] `admin_delete_thread(id)` - Delete thread with confirmation
  - [ ] Event management within threads

- [ ] **Thread Templates** (1 commit)
  - [ ] `threads.html` - Thread list for topic with chronological ordering
  - [ ] `view_thread.html` - Thread details with events timeline
  - [ ] `create_thread.html` - Thread creation form
  - [ ] `edit_thread.html` - Thread editing form
  - [ ] Event assignment interface

- [ ] **Thread Features** (1 commit)
  - [ ] Chronological ordering by start_date
  - [ ] Event assignment and management
  - [ ] Date auto-update from events
  - [ ] Topic integration and navigation
  - [ ] Thread statistics and metrics

#### **Phase 3: Assignment Interface (1-2 commits)**
- [ ] **Story-Topic Assignment** (1 commit)
  - [ ] Add topic dropdown to story views
  - [ ] Bulk topic assignment for multiple stories
  - [ ] Topic assignment validation
  - [ ] Quick assignment from story detail views

- [ ] **Event-Thread Assignment** (1 commit)
  - [ ] Add thread dropdown to event views
  - [ ] Move events between threads
  - [ ] Thread assignment validation
  - [ ] Bulk event assignment operations

### Future Phases (After Topic/Thread Management)
- [ ] **Event Creation and Linking** (2-3 commits)
  - [ ] Event creation interface
  - [ ] Event-story linking system
  - [ ] Event management and editing
  - [ ] Event timeline visualization

- [ ] **Tag Management System** (1-2 commits)
  - [ ] Tag creation and editing
  - [ ] Tag assignment interface
  - [ ] Tag filtering and search
  - [ ] Tag statistics and analytics

### Blocked/Waiting
*None currently*

## Commit Guidelines

### Commit Message Format
```
type(scope): brief description

- Detailed change 1
- Detailed change 2
- Fixes #issue_number
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Scope Examples
- `models`: Database model changes
- `api`: API endpoint changes
- `ui`: User interface changes
- `import`: Import functionality
- `graph`: Graph visualization
- `timeline`: Timeline functionality

## Development Notes

### Current Architecture Decisions
- Using SQLAlchemy ORM for database operations
- Flask-Migrate (Alembic) for database migrations
- Pytest for testing framework
- Following the existing Flask app structure with blueprints

### Technical Debt to Address
- [ ] Add comprehensive error handling to models
- [ ] Implement proper logging throughout the application
- [ ] Add input validation and sanitization
- [ ] Create database connection pooling for production
- [ ] Fix SQLAlchemy relationship warnings (overlaps parameters)
- [ ] Add CSRF protection to forms
- [ ] Implement proper error pages (404, 500)
- [ ] Add database migration system for production

### Performance Considerations
- [ ] Add database indexes for frequently queried fields
- [ ] Consider pagination for large result sets
- [ ] Plan for lazy loading of relationships
- [ ] Monitor memory usage with large datasets

## Testing Strategy

### Current Testing Focus
- [x] Unit tests for all model classes (basic tests implemented)
- [ ] Integration tests for database operations (in progress)
- [x] Validation tests for data constraints (implemented)
- [ ] Migration tests for database schema changes

### Test Coverage Goals
- Aim for 80%+ code coverage on models
- Test all validation rules and constraints
- Test all relationship operations
- Test error handling scenarios

## Next Sprint Planning

### Potential Next Sprint: Import System
- CSV file upload handling
- Column mapping interface
- Data validation and preview
- Batch import processing
- Deduplication logic

### Dependencies for Next Sprint
- Complete all database models
- Set up proper error handling
- Create test data fixtures
- Implement basic CRUD operations

## Questions & Decisions Needed

### Technical Decisions
- [ ] Should we use UUIDs or auto-incrementing integers for primary keys?
- [ ] How should we handle timezone information for dates?
- [ ] What validation library should we use for complex validations?
- [ ] Should we implement soft deletes or hard deletes?

### Product Decisions
- [ ] What should be the default importance levels for events?
- [ ] How should we handle edge cases in date parsing?
- [ ] What should be the maximum length for text fields?
- [ ] How should we handle duplicate tag names?

## Daily Standup Notes

### Current Focus
- Topic and Thread Management System implementation
- Topic CRUD operations development
- Admin interface enhancements

### Blockers
- None currently

### Recent Accomplishments
*See past_development.md for completed work*

### Next Steps
- Implement Topic Management CRUD operations
- Add topic assignment to stories
- Create thread management system
