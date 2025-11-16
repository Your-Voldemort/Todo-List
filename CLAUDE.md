# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern Flask-based Todo application with SQLite database backend. The application uses SQLAlchemy 2.0 ORM with type annotations, Flask-Migrate for database migrations, python-dotenv for configuration management, Jinja2 templates for rendering, and Tailwind CSS for styling.

## Architecture

### Application Structure

- **app.py**: Main Flask application entry point
  - Initializes Flask app with configuration from environment variables
  - Configures SQLAlchemy with connection pooling options
  - Defines all routes: index, add, complete, delete
  - Includes error handlers for 404 and 500 errors
  - Creates database tables on startup via `db.create_all()`
  - Uses flash messages for user feedback with proper logging

- **models.py**: Database models using SQLAlchemy 2.0 syntax
  - Defines the `Todo` model with type-annotated columns using `Mapped[]`
  - Uses modern `mapped_column()` syntax instead of `db.Column()`
  - Fields: id, title, description, is_completed, timestamp
  - Includes `to_dict()` method for JSON serialization
  - Uses timezone-aware datetime with UTC

- **templates/index.html**: Single-page UI
  - Contains both the add-todo form and the todo list display
  - Uses Jinja2 templating for dynamic content
  - Styled with Tailwind CSS (via CDN) and Font Awesome 6.5.1
  - Includes client-side validation and confirmation dialogs
  - Meta tags for SEO optimization

- **static/css/style.css**: Custom CSS enhancements
  - Complements Tailwind CSS with custom animations
  - Defines transitions and fade-in effects for flash messages

### Database

- **Type**: SQLite (file-based, configurable to PostgreSQL/MySQL)
- **Location**: `instance/todos.db` (created automatically)
- **ORM**: Flask-SQLAlchemy 3.1.1 with SQLAlchemy 2.0.35
- **Migrations**: Flask-Migrate 4.0.7 (Alembic) for database schema versioning
- Database tables are created automatically when the app starts via `db.create_all()` within the app context
- Connection pooling configured with `pool_pre_ping` and `pool_recycle` for better reliability

### Configuration

- **Environment Variables**: Managed via `.env` file (use `.env.example` as template)
  - `FLASK_DEBUG`: Enable/disable debug mode (default: False)
  - `FLASK_HOST`: Server host (default: 0.0.0.0)
  - `FLASK_PORT`: Server port (default: 8000)
  - `DATABASE_URI`: Database connection string (default: sqlite:///todos.db)
  - `SECRET_KEY`: Flask secret key for sessions (auto-generated if not set)

### Request Flow

1. User visits `/` → `index()` fetches all todos ordered by timestamp (desc) → renders `index.html`
2. User submits form at `/add` → `add()` validates (title required, max 100 chars) → creates new Todo → commits to DB → redirects to `/`
3. User clicks complete/undo → `/complete/<id>` toggles `is_completed` status → redirects to `/`
4. User clicks delete (with confirmation) → `/delete/<id>` removes todo from DB → redirects to `/`

### Error Handling

- All database operations wrapped in try-except with rollback
- Custom 404 handler redirects to index with flash message
- Custom 500 handler logs error and redirects to index with flash message
- Input validation for title length and required fields

## Commands

### Setup and Installation

```bash
# Install dependencies (upgraded to latest compatible versions)
pip install -r requirements.txt

# Copy example environment file and configure
copy .env.example .env
# Edit .env with your configuration
```

### Running the Application

```bash
# Run development server (with auto-reload)
python app.py

# Or using Flask CLI
flask run --host=0.0.0.0 --port=8000

# Set environment variables for custom configuration
set FLASK_DEBUG=True
set FLASK_PORT=5000
python app.py
```

The app runs on `http://0.0.0.0:8000` by default (accessible from any network interface).

### Database Management

```bash
# Database is automatically created when the app starts
python app.py

# Reset the database (delete and recreate)
rm -rf instance/todos.db
python app.py

# Using Flask-Migrate for schema migrations (optional)
flask db init              # Initialize migrations
flask db migrate -m "Initial migration"  # Create migration
flask db upgrade           # Apply migrations
```

### Testing

```bash
# Run the comprehensive test suite
python test_app.py
```

The test suite verifies:
- Database connection and table creation
- CRUD operations (Create, Read, Update, Delete)
- Route functionality with status codes
- Input validation (empty title, long title)
- Model methods (to_dict)

## Important Notes

### Security
- **Secret Key**: Auto-generated using `secrets.token_hex(32)` if not provided in `.env`
- **Debug Mode**: Controlled via `FLASK_DEBUG` environment variable (False by default in production)
- **Input Validation**: Title max length enforced at both frontend (HTML) and backend (Python)

### Database
- **Location**: SQLite database stored in `instance/` folder (auto-created)
- **Type Annotations**: Models use SQLAlchemy 2.0 type annotations for better IDE support
- **Timezone**: All timestamps are UTC-aware using `datetime.now(timezone.utc)`

### Frontend
- **Confirmation**: Delete action requires user confirmation before executing
- **Validation**: Form inputs validated client-side with HTML5 attributes
- **Responsive**: Tailwind CSS provides responsive design out of the box

### Logging
- Database errors logged via `app.logger.error()` for debugging
- Flash messages provide user-friendly feedback for all operations

## Improvements Made

### Libraries Updated
- **Flask**: 2.0.1 → 3.0.3
- **Flask-SQLAlchemy**: 2.5.1 → 3.1.1
- **SQLAlchemy**: 1.4.23 → 2.0.35
- **Werkzeug**: 2.0.1 → 3.0.4
- **Added**: python-dotenv 1.0.1 for environment management
- **Added**: Flask-Migrate 4.0.7 for database migrations

### Code Improvements
- Modern SQLAlchemy 2.0 syntax with type annotations
- Environment-based configuration with .env support
- Better error handling with custom error pages
- Enhanced validation with proper error messages
- Improved logging for debugging
- Connection pooling configuration
- Timezone-aware timestamps
- Delete confirmation dialog
- Better formatted timestamps in UI
