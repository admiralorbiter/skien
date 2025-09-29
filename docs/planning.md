# SKIEN Development Planning

## Overview
This document tracks high-level development tasks and milestones for the SKIEN News Threads Tracker project, based on the product specification v0.

## Milestone 1: Data Plumbing ✅ COMPLETED
**Goal**: Set up core data infrastructure and basic import functionality

### 1.1 Database Models & Schema ✅ COMPLETED
- [x] Create SQLAlchemy models for all entities
  - [x] Story model (id, url, title, source_name, author, published_at, captured_at, summary, raw_text)
  - [x] Event/Claim model (id, topic_id, thread_id, story_primary_id, claim_text, event_date, importance)
  - [x] Topic model (id, name, description, color)
  - [x] Thread model (id, topic_id, name, description, start_date)
  - [x] Edge model (id, src_event_id, dst_event_id, relation)
  - [x] Tag model (id, name)
  - [x] Junction tables (event_story_link, story_tag)
- [x] Set up database migrations with Alembic (SQLite development mode)
- [x] Create database indexes for performance
- [x] Add model relationships and constraints

### 1.2 Data Import System ✅ COMPLETED
- [x] CSV import functionality
  - [x] File upload handling
  - [x] Column mapping interface
  - [x] Data validation and preview
  - [x] Batch import processing
- [x] Deduplication system
  - [x] URL-based exact matching
  - [x] Title similarity detection (Jaro-Winkler)
  - [x] Source + date proximity matching
  - [x] Manual review interface for potential duplicates

### 1.3 Basic Table View ✅ COMPLETED
- [x] DataTable implementation for stories/events
- [x] Inline editing capabilities (Story CRUD)
- [x] Bulk operations (assign topics/threads, delete, tag)
- [x] Filtering and sorting
- [x] Pagination for large datasets

## Milestone 2: Topic/Thread Management
**Goal**: Enable organization of data into topics and threads

### 2.1 Topic Management ✅ COMPLETED
- [x] Topic CRUD operations
- [x] Topic assignment to events/stories
- [x] Topic color coding and metadata
- [x] Topic hierarchy (if needed)

### 2.2 Thread Management
- [ ] Thread CRUD operations within topics
- [ ] Thread assignment to events
- [ ] Thread ordering and chronology
- [ ] Thread branching support

### 2.3 Assignment Interface
- [ ] Bulk assignment tools
- [ ] Drag-and-drop assignment
- [ ] Quick assignment from detail views
- [ ] Assignment validation and constraints

## Milestone 3: Timeline View
**Goal**: Create chronological visualization of threads

### 3.1 Timeline Visualization
- [ ] Thread lane layout
- [ ] Event card rendering
- [ ] Date-based positioning
- [ ] Zoom and pan controls
- [ ] Time scale rendering

### 3.2 Timeline Interactions
- [ ] Event selection and highlighting
- [ ] Multi-select for relationship creation
- [ ] Drag-to-pan and scroll-to-zoom
- [ ] Keyboard navigation
- [ ] Mobile touch support

### 3.3 Detail Drawer
- [ ] Event/claim detail display
- [ ] Source links and metadata
- [ ] Relationship visualization
- [ ] Inline editing
- [ ] Action buttons (edit, delete, reassign)

## Milestone 4: Graph View
**Goal**: Interactive network visualization of relationships

### 4.1 Graph Rendering
- [ ] Cytoscape.js integration
- [ ] Node and edge styling
- [ ] Layout algorithms (time-based, force-directed)
- [ ] Performance optimization for large graphs

### 4.2 Graph Interactions
- [ ] Zoom, pan, and fit controls
- [ ] Node selection and highlighting
- [ ] Edge creation and editing
- [ ] Filtering by edge types
- [ ] Search and focus functionality

### 4.3 Graph Controls
- [ ] Layout switching
- [ ] Filter controls (date, tags, edge types)
- [ ] Legend and mini-map
- [ ] Keyboard shortcuts
- [ ] Export capabilities

## Milestone 5: Polish & Performance
**Goal**: Optimize performance and add advanced features

### 5.1 Search & Discovery
- [ ] Full-text search across all content
- [ ] Type-ahead search suggestions
- [ ] Search result highlighting
- [ ] Advanced search filters
- [ ] Search history and saved searches

### 5.2 Performance Optimization
- [ ] Lazy loading for large datasets
- [ ] Graph performance tuning
- [ ] Database query optimization
- [ ] Caching strategies
- [ ] Progressive loading

### 5.3 User Experience
- [ ] Keyboard shortcuts throughout
- [ ] Bulk editing tools
- [ ] Undo/redo functionality
- [ ] Auto-save capabilities
- [ ] Mobile responsiveness

### 5.4 Advanced Features
- [ ] Export functionality (CSV, JSON, PNG)
- [ ] Import/export of entire datasets
- [ ] Data validation and cleanup tools
- [ ] Analytics and insights
- [ ] User preferences and settings

## Technical Infrastructure

### Backend Architecture
- [ ] Flask application structure
- [ ] Blueprint organization
- [ ] API endpoint design
- [ ] Error handling and logging
- [ ] Configuration management

### Frontend Architecture
- [ ] HTML templates with Jinja2
- [ ] Bootstrap 5 styling
- [ ] htmx for progressive enhancement
- [ ] Alpine.js for interactivity
- [ ] JavaScript modules organization

### Data Services
- [ ] Import service implementation
- [ ] Link service for relationships
- [ ] Search service
- [ ] Suggestion service (future)
- [ ] Validation services

## Testing Strategy

### Unit Testing
- [ ] Model tests
- [ ] Service tests
- [ ] API endpoint tests
- [ ] Utility function tests

### Integration Testing
- [ ] Import workflow tests
- [ ] Graph rendering tests
- [ ] Timeline functionality tests
- [ ] End-to-end user flows

### Performance Testing
- [ ] Large dataset handling
- [ ] Graph performance benchmarks
- [ ] Database query optimization
- [ ] Memory usage monitoring

## Deployment & DevOps

### Development Environment
- [ ] Local development setup
- [ ] Database seeding
- [ ] Development tools and scripts
- [ ] Code quality tools

### Production Deployment
- [ ] Production configuration
- [ ] Database migration strategy
- [ ] Monitoring and logging
- [ ] Backup and recovery

## Future Considerations

### Post-MVP Features
- [ ] NLP assistance for topic/thread suggestions
- [ ] Entity extraction and clustering
- [ ] Browser extension
- [ ] Multi-user support
- [ ] Real-time collaboration

### Scalability
- [ ] Database scaling strategies
- [ ] Caching implementation
- [ ] CDN for static assets
- [ ] Load balancing considerations
