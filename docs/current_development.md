# SKIEN Current Development

## Active Sprint: Milestone 2 - Topic & Thread Management
**Sprint Goal**: Enable organization of data into topics and threads for better content management

> **Note**: This document focuses on current and future work. All completed work is documented in `past_development.md`.

## Current Focus: Topic and Thread Management System

### In Progress
**Next Priority**: Topic Management CRUD Operations
- Implement topic creation, viewing, editing, and deletion
- Add topic management interface to admin panel
- Enable topic assignment to stories and events
- Add topic color coding and metadata management

### Immediate Next Steps
1. **Topic CRUD Routes** - Create admin routes for topic management
2. **Topic Templates** - Build view, edit, create templates for topics
3. **Topic Assignment** - Add topic assignment to story views
4. **Topic Filtering** - Add topic-based filtering to story list

### Recently Completed
*All completed work has been moved to past_development.md*

### Next Up (Ready to Start)
- [ ] **Topic Management System** (2-3 commits)
  - [ ] Topic CRUD operations (create, view, edit, delete)
  - [ ] Topic management interface in admin panel
  - [ ] Topic color coding and metadata
  - [ ] Topic assignment to stories and events

- [ ] **Thread Management System** (2-3 commits)
  - [ ] Thread CRUD operations within topics
  - [ ] Thread management interface
  - [ ] Thread assignment to events
  - [ ] Thread ordering and chronology

- [ ] **Assignment Interface** (1-2 commits)
  - [ ] Bulk assignment tools for stories/events
  - [ ] Topic/thread assignment from story views
  - [ ] Assignment validation and constraints
  - [ ] Quick assignment from detail views

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
