# SKIEN Current Development

## Active Sprint: Milestone 1 - Data Plumbing
**Sprint Goal**: Set up core data infrastructure and basic import functionality

## Current Focus: Import System Implementation

### In Progress
*None currently - ready to start next phase*

### Recently Completed
- [x] **Database Models & Schema** (All core models implemented and tested)
  - [x] All 8 core models created with proper relationships
  - [x] Comprehensive validation and utility methods
  - [x] Basic test suite implemented (some tests need refinement)
  - [x] SQLAlchemy relationship warnings resolved

- [x] **Database Migration Setup** (Skipped - not needed for SQLite development)
  - [x] Confirmed SQLite works with `db.create_all()` for development
  - [x] Migrations not needed until production deployment
  - [x] Cleaned up development logging output

- [x] **Import System Implementation** (Complete CSV import system)
  - [x] CSV file upload handling with drag & drop interface
  - [x] Column mapping interface for flexible data mapping
  - [x] Data validation and preview functionality
  - [x] Batch import processing with progress tracking
  - [x] Deduplication logic to prevent duplicate stories
  - [x] Source extraction from URLs (400+ news sources mapped)
  - [x] Error handling and detailed import results

### Next Up (Ready to Start)
- [ ] **Basic CRUD Operations** (2-3 commits)
  - [ ] Story management interface
  - [ ] Topic and thread management
  - [ ] Event creation and linking
  - [ ] Tag management system

### Completed This Sprint
- [x] **Create base model classes** (1-2 commits)
  - [x] Set up SQLAlchemy base with common fields (id, created_at, updated_at)
  - [x] Add utility methods (to_dict, from_dict, validation)
  - [x] Create base model tests

- [x] **Story model implementation** (2-3 commits)
  - [x] Create Story model with all required fields
  - [x] Add validation for URL uniqueness and date formats
  - [x] Create Story model tests
  - [x] Add URL canonicalization and duplicate detection

- [x] **Event/Claim model implementation** (2-3 commits)
  - [x] Create EventClaim model with foreign keys
  - [x] Add validation for date ranges and importance levels
  - [x] Create EventClaim model tests
  - [x] Add relationship validation methods

- [x] **Topic and Thread models** (2-3 commits)
  - [x] Create Topic model with name uniqueness
  - [x] Create Thread model with topic relationship
  - [x] Add validation for required fields
  - [x] Create Topic and Thread model tests
  - [x] Add search and filtering methods

- [x] **Edge and Tag models** (2-3 commits)
  - [x] Create Edge model with relationship validation
  - [x] Create Tag model with name uniqueness
  - [x] Create junction table models (EventStoryLink, StoryTag)
  - [x] Add validation to prevent self-loops in edges
  - [x] Create Edge and Tag model tests
  - [x] Add comprehensive relationship management

### Blocked/Waiting
*None currently*

### Completed This Sprint
*See completed tasks above*

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

### Today's Focus
- Setting up base model classes
- Planning database schema structure
- Creating initial test framework

### Blockers
- None currently

### Completed Yesterday
- N/A - starting fresh

### Tomorrow's Plan
- Complete base model classes
- Start Story model implementation
- Set up database migration system
