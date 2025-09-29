# SKIEN: News Threads Tracker

A visual news tracking application that transforms news stories into interactive graphs and timelines. Track evolving news topics as *threads* you can browse visually, rather than rows in a spreadsheet. Zoom from high-level topic maps down to specific claims and events.

## Features

- **Visual Graph View**: Interactive, zoomable graphs showing relationships between news events
- **Timeline View**: Chronological thread lanes for linear story progression
- **Data Import**: Import stories from CSV/Google Sheets with automatic deduplication
- **Topic & Thread Management**: Organize stories into topics and create branching threads
- **Relationship Mapping**: Create typed edges between events (follow-up, refutes, clarifies, etc.)
- **Advanced Filtering**: Filter by date range, tags, sources, and relationship types
- **Search & Discovery**: Fast search across titles, claims, and tags with type-ahead
- **Detail Panel**: Rich detail view with sources, relationships, and metadata
- **Responsive Design**: Works on desktop and mobile with Bootstrap 5
- **Progressive Enhancement**: Server-rendered HTML enhanced with htmx and Alpine.js

## Prerequisites

- Python 3.x
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd skien
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add your configuration:
   ```
   FLASK_ENV=development
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///skien.db  # SQLite for development
   ```

## Database Setup

1. The application will automatically create a SQLite database in development mode
2. Run database migrations to set up the schema:
   ```bash
   flask db upgrade
   ```
3. To create an admin user, run:
   ```bash
   python create_admin.py
   ```

## Running the Application

### Development

To run the application in development mode, use:

```bash
flask run
```
### Production

To run the application in production mode, use:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

## Testing

Run the test suite using pytest:

```bash
pytest
```
For coverage report:

```bash
pytest --cov=app
```

## Project Structure
```
skien/
├── app.py                          # Application entry point
├── config/                         # Configuration modules
│   ├── __init__.py
│   ├── base.py                     # Base configuration
│   └── monitoring.py               # Monitoring configuration
├── flask_app/                      # Main application package
│   ├── __init__.py
│   ├── models/                     # Database models
│   │   ├── __init__.py
│   │   ├── base.py                 # Base model classes
│   │   ├── user.py                 # User model
│   │   └── admin.py                # Admin models
│   ├── routes/                     # Blueprint routes
│   │   ├── __init__.py
│   │   ├── main.py                 # Core routes
│   │   ├── auth.py                 # Authentication routes
│   │   └── admin.py                # Admin routes
│   ├── forms/                      # WTForms definitions
│   │   ├── __init__.py
│   │   ├── auth.py                 # Auth forms
│   │   └── admin.py                # Admin forms
│   └── utils/                      # Utility modules
│       ├── __init__.py
│       ├── error_handler.py        # Error handling
│       ├── logging_config.py       # Logging setup
│       └── monitoring.py           # Monitoring utilities
├── static/                         # Static assets
│   └── css/                        # Stylesheets
├── templates/                      # Jinja2 templates
│   ├── base.html                   # Base template
│   ├── index.html                  # Home page
│   ├── login.html                  # Login page
│   ├── nav.html                    # Navigation component
│   └── admin/                      # Admin templates
├── tests/                          # Test suite
├── requirements.txt                # Python dependencies
├── pytest.ini                     # Pytest configuration
└── run_tests.py                    # Test runner
```

## Data Model

SKIEN tracks news through several core entities:

- **Story**: A single news item (article, post, transcript, video) with URL, source, published date, title, excerpt, and tags
- **Event/Claim**: The atomic thing tracked on a timeline (may map 1:1 with a Story, or be extracted from a Story)
- **Topic**: A named umbrella (e.g., "US Tariffs") that contains many Threads
- **Thread**: A sequence or cluster of related events/claims inside a Topic (e.g., "2025 Tariff Proposal rollouts")
- **Edge**: A typed relationship connecting two Events/Claims (follow-up, refutes, clarifies, repeats, action, other)
- **Tag**: Categorization labels for stories and events

## Configuration

The application supports three environments:
- Development (default)
- Testing
- Production

Configuration is handled in the `config/` directory and can be extended based on requirements.

## Technical Architecture

- **Backend**: Flask with Blueprints for modular organization
- **Frontend**: Server-rendered HTML (Jinja2 + Bootstrap 5) with progressive enhancement via htmx and Alpine.js
- **Graph Visualization**: Cytoscape.js for interactive graph rendering
- **Timeline**: Vis Timeline or custom SVG timeline with D3
- **Database**: SQLite (development) / PostgreSQL (production) with SQLAlchemy ORM
- **API**: RESTful JSON endpoints for graph data, timeline data, and CRUD operations

## Security Features

- Password hashing using Werkzeug
- CSRF protection with Flask-WTF
- Secure session handling
- Environment-based configurations
- SQL injection prevention through SQLAlchemy
- Input sanitization for imported content

## Usage

### Importing Data

1. **CSV Import**: Upload a CSV file with news stories
   - Map columns to: title, url, source, author, published_at, tags, summary
   - Preview and validate data before import
   - Automatic deduplication based on URL and title similarity

2. **Google Sheets**: Export your sheet to CSV and follow the same import process

### Working with Topics and Threads

1. **Create Topics**: Organize related stories under named topics (e.g., "US Tariffs")
2. **Create Threads**: Within topics, create chronological threads of related events
3. **Assign Events**: Link stories to specific events/claims within threads

### Visualizing Data

1. **Graph View**: Interactive network showing relationships between events
   - Zoom and pan to explore the network
   - Filter by date range, tags, or relationship types
   - Click nodes to see details and relationships

2. **Timeline View**: Chronological view organized by threads
   - See events in time order within each thread
   - Multi-select events to create relationships
   - Drag to pan, scroll to zoom

3. **Table View**: Spreadsheet-like view for bulk editing
   - Inline editing of event details
   - Bulk operations for assigning topics/threads
   - Duplicate detection and management

## API Endpoints

### Graph Data
- `GET /api/topics/:id/graph` - Get graph data for a topic
  - Query params: `from`, `to` (date range), `edges` (relationship types), `layout` (time|force)
- `GET /api/topics/:id/timeline` - Get timeline data for a topic

### Events & Stories
- `POST /api/events` - Create a new event
- `PATCH /api/events/:id` - Update an event
- `POST /api/edges` - Create a relationship between events
- `GET /api/search?q=` - Search events and stories

### Example API Response

**Graph Data:**
```json
{
  "nodes": [
    {"id": "e_101", "label": "Announces 10% tariff", "date": "2025-03-01", "threadId": 12, "importance": 3},
    {"id": "e_112", "label": "Clarifies exemptions", "date": "2025-03-05", "threadId": 12}
  ],
  "edges": [
    {"id": "x1", "source": "e_101", "target": "e_112", "relation": "clarifies"}
  ]
}
```

## Development Roadmap

### Milestone 1: Data Plumbing
- Database models and migrations
- CSV import functionality
- Basic deduplication
- Simple table view

### Milestone 2: Topic/Thread Management
- Create and edit topics and threads
- Assign events to topics/threads
- Basic CRUD operations

### Milestone 3: Timeline View
- Thread lanes visualization
- Detail drawer for events
- Timeline navigation controls

### Milestone 4: Graph View
- Cytoscape.js integration
- Interactive graph rendering
- Edge creation and management
- Layout algorithms (time-based and force-directed)

### Milestone 5: Polish & Performance
- Search functionality
- Keyboard shortcuts
- Mini-map for graph navigation
- Bulk editing capabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
