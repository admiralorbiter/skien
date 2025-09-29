# SKIEN Current Development

## Active Sprint: Milestone 1 - Data Plumbing
**Sprint Goal**: Set up core data infrastructure and basic import functionality

## Current Focus: Database Models & Schema

### In Progress
- [ ] **Create base model classes** (1-2 commits)
  - [ ] Set up SQLAlchemy base with common fields (id, created_at, updated_at)
  - [ ] Add utility methods (to_dict, from_dict, validation)
  - [ ] Create base model tests

### Next Up (Ready to Start)
- [ ] **Story model implementation** (2-3 commits)
  - [ ] Create Story model with all required fields
  - [ ] Add validation for URL uniqueness and date formats
  - [ ] Create Story model tests
  - [ ] Add Story model to database migration

- [ ] **Event/Claim model implementation** (2-3 commits)
  - [ ] Create EventClaim model with foreign keys
  - [ ] Add validation for date ranges and importance levels
  - [ ] Create EventClaim model tests
  - [ ] Add EventClaim model to database migration

- [ ] **Topic and Thread models** (2-3 commits)
  - [ ] Create Topic model with name uniqueness
  - [ ] Create Thread model with topic relationship
  - [ ] Add validation for required fields
  - [ ] Create Topic and Thread model tests
  - [ ] Add models to database migration

- [ ] **Edge and Tag models** (2-3 commits)
  - [ ] Create Edge model with relationship validation
  - [ ] Create Tag model with name uniqueness
  - [ ] Create junction table models (EventStoryLink, StoryTag)
  - [ ] Add validation to prevent self-loops in edges
  - [ ] Create Edge and Tag model tests
  - [ ] Add models to database migration

### Blocked/Waiting
- [ ] **Database migration setup** (1 commit)
  - [ ] Initialize Alembic for database migrations
  - [ ] Create initial migration script
  - [ ] Set up migration commands in Flask CLI
  - [ ] Test migration up/down functionality

### Completed This Sprint
*None yet - starting fresh*

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
- [ ] Unit tests for all model classes
- [ ] Integration tests for database operations
- [ ] Validation tests for data constraints
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
