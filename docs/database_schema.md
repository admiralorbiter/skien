# SKIEN Database Schema

## Overview
This document describes the database schema for the SKIEN News Threads Tracker, including table definitions, relationships, indexes, and constraints.

## Entity Relationship Diagram

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│    Topic    │    │    Thread    │    │ EventClaim  │
│             │    │              │    │             │
│ id (PK)     │◄───┤ topic_id (FK)│◄───┤ topic_id(FK)│
│ name        │    │ id (PK)      │    │ id (PK)     │
│ description │    │ name         │    │ thread_id   │
│ color       │    │ description  │    │ claim_text  │
└─────────────┘    │ start_date   │    │ event_date  │
                   └──────────────┘    │ importance  │
                                       └─────────────┘
                                              │
                                              │
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│    Story    │    │EventStoryLink│    │ EventClaim  │
│             │    │              │    │             │
│ id (PK)     │◄───┤ story_id (FK)│    │ id (PK)     │
│ url         │    │ event_id (FK)│◄───┤ id (PK)     │
│ title       │    │ note         │    │             │
│ source_name │    └──────────────┘    └─────────────┘
│ author      │                                │
│ published_at│                                │
│ captured_at │                                │
│ summary     │                                │
│ raw_text    │                                │
└─────────────┘                                │
       │                                       │
       │                                       │
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  StoryTag   │    │     Tag      │    │    Edge     │
│             │    │              │    │             │
│ story_id(FK)│◄───┤ id (PK)      │    │ id (PK)     │
│ tag_id (FK) │    │ name         │    │ src_event_id│
└─────────────┘    └──────────────┘    │ dst_event_id│
                                       │ relation    │
                                       └─────────────┘
```

## Table Definitions

### story
Primary table for news articles and content.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing primary key |
| url | VARCHAR(2048) | UNIQUE, NOT NULL | Article URL (canonicalized) |
| title | VARCHAR(500) | NOT NULL | Article title |
| source_name | VARCHAR(200) | NOT NULL | News source name |
| author | VARCHAR(200) | NULL | Article author |
| published_at | DATE | NULL | Publication date |
| captured_at | DATETIME | NOT NULL, DEFAULT NOW() | When story was imported |
| summary | TEXT | NULL | Article summary/excerpt |
| raw_text | TEXT | NULL | Full article text (optional) |

**Indexes:**
- `idx_story_url` (url) - Unique index for URL lookups
- `idx_story_published_at` (published_at) - For date-based queries
- `idx_story_source` (source_name) - For source-based filtering
- `idx_story_captured_at` (captured_at) - For import tracking

### event_claim
Core entity representing trackable events or claims.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing primary key |
| topic_id | INTEGER | NOT NULL, FK → topic.id | Associated topic |
| thread_id | INTEGER | NULL, FK → thread.id | Associated thread (optional) |
| story_primary_id | INTEGER | NULL, FK → story.id | Primary source story |
| claim_text | TEXT | NOT NULL | The claim/event description |
| event_date | DATE | NOT NULL | When the event occurred |
| importance | INTEGER | NULL | Importance level (1-5) |

**Indexes:**
- `idx_event_topic` (topic_id) - For topic-based queries
- `idx_event_thread` (thread_id) - For thread-based queries
- `idx_event_date` (event_date) - For chronological queries
- `idx_event_importance` (importance) - For importance filtering

### topic
Top-level organizational category.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing primary key |
| name | VARCHAR(200) | UNIQUE, NOT NULL | Topic name |
| description | TEXT | NULL | Topic description |
| color | VARCHAR(7) | NULL | Hex color code for UI |

**Indexes:**
- `idx_topic_name` (name) - Unique index for name lookups

### thread
Chronological sequence within a topic.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing primary key |
| topic_id | INTEGER | NOT NULL, FK → topic.id | Parent topic |
| name | VARCHAR(200) | NOT NULL | Thread name |
| description | TEXT | NULL | Thread description |
| start_date | DATE | NULL | Computed or manual start date |

**Indexes:**
- `idx_thread_topic` (topic_id) - For topic-based queries
- `idx_thread_start_date` (start_date) - For chronological ordering

### edge
Relationships between events/claims.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing primary key |
| src_event_id | INTEGER | NOT NULL, FK → event_claim.id | Source event |
| dst_event_id | INTEGER | NOT NULL, FK → event_claim.id | Destination event |
| relation | ENUM | NOT NULL | Relationship type |

**Relation Types:**
- `follow_up` - B happens after A and references/extends A
- `refutes` - B contradicts A
- `clarifies` - B qualifies A without contradicting
- `repeats` - B restates A
- `action` - B is a concrete policy/action following A
- `other` - Other relationship type

**Indexes:**
- `idx_edge_src` (src_event_id) - For outgoing relationships
- `idx_edge_dst` (dst_event_id) - For incoming relationships
- `idx_edge_relation` (relation) - For relationship type filtering

**Constraints:**
- `CHECK (src_event_id != dst_event_id)` - Prevent self-loops
- `UNIQUE (src_event_id, dst_event_id, relation)` - Prevent duplicate edges

### tag
Categorization labels.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing primary key |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Tag name |

**Indexes:**
- `idx_tag_name` (name) - Unique index for name lookups

### event_story_link
Many-to-many relationship between events and stories.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| event_id | INTEGER | NOT NULL, FK → event_claim.id | Event ID |
| story_id | INTEGER | NOT NULL, FK → story.id | Story ID |
| note | TEXT | NULL | Optional note about the relationship |

**Constraints:**
- `PRIMARY KEY (event_id, story_id)` - Composite primary key
- `UNIQUE (event_id, story_id)` - Prevent duplicate links

### story_tag
Many-to-many relationship between stories and tags.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| story_id | INTEGER | NOT NULL, FK → story.id | Story ID |
| tag_id | INTEGER | NOT NULL, FK → tag.id | Tag ID |

**Constraints:**
- `PRIMARY KEY (story_id, tag_id)` - Composite primary key
- `UNIQUE (story_id, tag_id)` - Prevent duplicate links

## Relationships

### One-to-Many Relationships
- **Topic → Threads**: One topic can have many threads
- **Topic → Events**: One topic can have many events
- **Thread → Events**: One thread can have many events
- **Story → Events**: One story can be the primary source for many events

### Many-to-Many Relationships
- **Events ↔ Stories**: Events can be supported by multiple stories
- **Stories ↔ Tags**: Stories can have multiple tags

### Self-Referential Relationships
- **Events → Events**: Events can be related to other events via edges

## Data Integrity Rules

### Business Rules
1. **Event Assignment**: Every event must belong to exactly one topic
2. **Thread Assignment**: Events can optionally belong to one thread within their topic
3. **Edge Validation**: Edges cannot connect an event to itself
4. **Date Consistency**: Event dates should be reasonable (not in far future)
5. **URL Canonicalization**: URLs should be normalized (remove UTM parameters, etc.)

### Referential Integrity
- All foreign key constraints are enforced
- Cascade deletes are handled at the application level for data safety
- Soft deletes may be implemented for critical data

## Performance Considerations

### Query Optimization
- All foreign keys are indexed
- Date fields used in filtering are indexed
- Text search fields may need full-text indexes
- Composite indexes for common query patterns

### Scalability
- Consider partitioning large tables by date
- Implement connection pooling
- Monitor query performance with large datasets
- Consider read replicas for reporting queries

## Migration Strategy

### Initial Migration
1. Create all tables with basic structure
2. Add indexes after table creation
3. Add constraints after data population
4. Populate with seed data for testing

### Future Migrations
- Use Alembic for version control
- Test migrations on copy of production data
- Plan for zero-downtime deployments
- Maintain backward compatibility when possible

## Data Validation

### Application-Level Validation
- URL format validation
- Date range validation
- Text length limits
- Required field validation
- Business rule enforcement

### Database-Level Validation
- Foreign key constraints
- Unique constraints
- Check constraints for enum values
- Not null constraints where appropriate
