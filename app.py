from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, bcrypt, User, Todo, Category, PriorityLevel
from forms import RegistrationForm, LoginForm, TodoForm, CategoryForm
from api import api
from datetime import datetime, timezone
from sqlalchemy import or_, and_, func
import os
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URI',
    'sqlite:///todos.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
app.config['WTF_CSRF_ENABLED'] = True

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


# Register API blueprint
app.register_blueprint(api)

# Ensure the instance folder exists
if not os.path.exists('instance'):
    os.makedirs('instance')

# Create database tables
with app.app_context():
    db.create_all()


# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash(f'Account created successfully for {form.username.data}! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error during registration: {e}')
            flash('An error occurred during registration. Please try again.', 'error')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')

            # Redirect to next page or index
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'error')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    logout_user()
    flash(f'Goodbye, {username}! You have been logged out.', 'success')
    return redirect(url_for('login'))


# Main Todo Routes
@app.route('/')
@login_required
def index():
    """Main dashboard with todos"""
    # Get filter parameters
    filter_priority = request.args.get('priority')
    filter_category = request.args.get('category')
    filter_status = request.args.get('status')
    search_query = request.args.get('search', '').strip()

    # Build query
    query = Todo.query.filter_by(user_id=current_user.id)

    # Apply filters
    if filter_priority:
        try:
            query = query.filter_by(priority=PriorityLevel(filter_priority))
        except ValueError:
            pass

    if filter_category:
        query = query.filter_by(category_id=int(filter_category))

    if filter_status == 'completed':
        query = query.filter_by(is_completed=True)
    elif filter_status == 'pending':
        query = query.filter_by(is_completed=False)
    elif filter_status == 'overdue':
        query = query.filter(
            and_(
                Todo.is_completed == False,
                Todo.due_date < datetime.now(timezone.utc)
            )
        )

    if search_query:
        query = query.filter(
            or_(
                Todo.title.ilike(f'%{search_query}%'),
                Todo.description.ilike(f'%{search_query}%')
            )
        )

    # Order by priority and due date
    todos = query.order_by(
        Todo.is_completed.asc(),
        Todo.priority.desc(),
        Todo.due_date.asc().nullslast(),
        Todo.created_at.desc()
    ).all()

    # Get user categories for filter dropdown
    categories = Category.query.filter_by(user_id=current_user.id).all()

    # Get active filters for display
    active_filters = {
        'priority': filter_priority,
        'category': filter_category,
        'status': filter_status,
        'search': search_query
    }

    return render_template(
        'index.html',
        todos=todos,
        categories=categories,
        active_filters=active_filters,
        PriorityLevel=PriorityLevel
    )


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add new todo with form validation"""
    form = TodoForm()

    # Populate category choices
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form.category_id.choices = [(0, 'No Category')] + [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        try:
            new_todo = Todo(
                title=form.title.data,
                description=form.description.data if form.description.data else None,
                priority=PriorityLevel(form.priority.data),
                due_date=form.due_date.data,
                category_id=form.category_id.data if form.category_id.data != 0 else None,
                user_id=current_user.id
            )

            db.session.add(new_todo)
            db.session.commit()
            flash('Todo added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error adding todo: {e}')
            flash('An error occurred while adding the todo.', 'error')

    return render_template('add_todo.html', form=form)


@app.route('/edit/<int:todo_id>', methods=['GET', 'POST'])
@login_required
def edit(todo_id):
    """Edit existing todo"""
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    form = TodoForm(obj=todo)

    # Populate category choices
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form.category_id.choices = [(0, 'No Category')] + [(c.id, c.name) for c in categories]

    if request.method == 'GET':
        # Pre-populate form with current values
        form.priority.data = todo.priority.value
        form.category_id.data = todo.category_id if todo.category_id else 0

    if form.validate_on_submit():
        try:
            todo.title = form.title.data
            todo.description = form.description.data if form.description.data else None
            todo.priority = PriorityLevel(form.priority.data)
            todo.due_date = form.due_date.data
            todo.category_id = form.category_id.data if form.category_id.data != 0 else None

            db.session.commit()
            flash('Todo updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error updating todo: {e}')
            flash('An error occurred while updating the todo.', 'error')

    return render_template('edit_todo.html', form=form, todo=todo)


@app.route('/complete/<int:todo_id>')
@login_required
def complete(todo_id):
    """Toggle todo completion status"""
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()

    try:
        todo.toggle_complete()
        db.session.commit()

        status = 'completed' if todo.is_completed else 'reopened'
        flash(f'Todo {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error updating todo: {e}')
        flash('An error occurred while updating the todo.', 'error')

    return redirect(url_for('index'))


@app.route('/delete/<int:todo_id>')
@login_required
def delete(todo_id):
    """Delete a todo"""
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()

    try:
        db.session.delete(todo)
        db.session.commit()
        flash('Todo deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting todo: {e}')
        flash('An error occurred while deleting the todo.', 'error')

    return redirect(url_for('index'))


# Category Management Routes
@app.route('/categories')
@login_required
def categories():
    """List all categories"""
    user_categories = Category.query.filter_by(user_id=current_user.id).all()

    # Get todo count for each category
    category_stats = []
    for cat in user_categories:
        todo_count = Todo.query.filter_by(
            user_id=current_user.id,
            category_id=cat.id
        ).count()
        category_stats.append({
            'category': cat,
            'todo_count': todo_count
        })

    return render_template('categories.html', category_stats=category_stats)


@app.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """Add new category"""
    form = CategoryForm()

    if form.validate_on_submit():
        try:
            new_category = Category(
                name=form.name.data,
                color=form.color.data,
                user_id=current_user.id
            )

            db.session.add(new_category)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('categories'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error adding category: {e}')
            flash('An error occurred while adding the category.', 'error')

    return render_template('add_category.html', form=form)


@app.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Edit existing category"""
    category = Category.query.filter_by(
        id=category_id,
        user_id=current_user.id
    ).first_or_404()

    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        try:
            category.name = form.name.data
            category.color = form.color.data

            db.session.commit()
            flash('Category updated successfully!', 'success')
            return redirect(url_for('categories'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error updating category: {e}')
            flash('An error occurred while updating the category.', 'error')

    return render_template('edit_category.html', form=form, category=category)


@app.route('/categories/delete/<int:category_id>')
@login_required
def delete_category(category_id):
    """Delete a category"""
    category = Category.query.filter_by(
        id=category_id,
        user_id=current_user.id
    ).first_or_404()

    # Check if category has todos
    todo_count = Todo.query.filter_by(
        user_id=current_user.id,
        category_id=category_id
    ).count()

    if todo_count > 0:
        flash(f'Cannot delete category with {todo_count} todos. Please reassign or delete the todos first.', 'error')
        return redirect(url_for('categories'))

    try:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting category: {e}')
        flash('An error occurred while deleting the category.', 'error')

    return redirect(url_for('categories'))


# Statistics and Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    """Statistics dashboard"""
    todos = Todo.query.filter_by(user_id=current_user.id).all()

    # Calculate statistics
    total = len(todos)
    completed = sum(1 for todo in todos if todo.is_completed)
    pending = total - completed
    completion_rate = round((completed / total * 100) if total > 0 else 0, 1)

    # Priority breakdown (pending only)
    priority_stats = {
        'low': sum(1 for todo in todos if todo.priority == PriorityLevel.LOW and not todo.is_completed),
        'medium': sum(1 for todo in todos if todo.priority == PriorityLevel.MEDIUM and not todo.is_completed),
        'high': sum(1 for todo in todos if todo.priority == PriorityLevel.HIGH and not todo.is_completed),
        'urgent': sum(1 for todo in todos if todo.priority == PriorityLevel.URGENT and not todo.is_completed)
    }

    # Category breakdown
    categories = Category.query.filter_by(user_id=current_user.id).all()
    category_stats = {}
    for cat in categories:
        cat_todos = [todo for todo in todos if todo.category_id == cat.id]
        category_stats[cat.name] = {
            'total': len(cat_todos),
            'completed': sum(1 for todo in cat_todos if todo.is_completed),
            'color': cat.color
        }

    # Uncategorized todos
    uncategorized = sum(1 for todo in todos if todo.category_id is None)
    if uncategorized > 0:
        category_stats['Uncategorized'] = {
            'total': uncategorized,
            'completed': sum(1 for todo in todos if todo.category_id is None and todo.is_completed),
            'color': '#6b7280'
        }

    # Time-based stats
    overdue = sum(1 for todo in todos if todo.is_overdue)
    due_soon = sum(1 for todo in todos if todo.days_until_due is not None and 0 <= todo.days_until_due <= 3)

    # Recent activity
    recent_completed = Todo.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).order_by(Todo.completed_at.desc()).limit(5).all()

    upcoming_todos = Todo.query.filter(
        and_(
            Todo.user_id == current_user.id,
            Todo.is_completed == False,
            Todo.due_date != None,
            Todo.due_date > datetime.now(timezone.utc)
        )
    ).order_by(Todo.due_date.asc()).limit(5).all()

    stats = {
        'total': total,
        'completed': completed,
        'pending': pending,
        'completion_rate': completion_rate,
        'priority_stats': priority_stats,
        'category_stats': category_stats,
        'overdue': overdue,
        'due_soon': due_soon,
        'recent_completed': recent_completed,
        'upcoming_todos': upcoming_todos
    }

    return render_template('dashboard.html', stats=stats)


# Search functionality
@app.route('/search')
@login_required
def search():
    """Advanced search page"""
    query = request.args.get('q', '').strip()

    if not query:
        return render_template('search.html', results=[], query='')

    # Search in title and description
    results = Todo.query.filter(
        and_(
            Todo.user_id == current_user.id,
            or_(
                Todo.title.ilike(f'%{query}%'),
                Todo.description.ilike(f'%{query}%')
            )
        )
    ).order_by(
        Todo.is_completed.asc(),
        Todo.created_at.desc()
    ).all()

    return render_template('search.html', results=results, query=query)


# Backward compatibility routes (for legacy usage)
@app.route('/add_legacy', methods=['POST'])
@login_required
def add_legacy():
    """Legacy add route for backward compatibility"""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()

    if not title:
        flash('Title is required!', 'error')
        return redirect(url_for('index'))

    if len(title) > 100:
        flash('Title must be 100 characters or less!', 'error')
        return redirect(url_for('index'))

    try:
        new_todo = Todo(
            title=title,
            description=description if description else None,
            user_id=current_user.id,
            priority=PriorityLevel.MEDIUM
        )
        db.session.add(new_todo)
        db.session.commit()
        flash('Todo added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error adding todo: {e}')
        flash('An error occurred while adding the todo.', 'error')

    return redirect(url_for('index'))


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    flash('The requested item was not found.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    app.logger.error(f'Internal error: {error}')
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    flash('You do not have permission to access this resource.', 'error')
    return redirect(url_for('index'))


# Context processors for templates
@app.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def format_datetime(dt):
        """Format datetime for display"""
        if not dt:
            return 'N/A'
        return dt.strftime('%Y-%m-%d %H:%M')

    def get_priority_badge_class(priority):
        """Get CSS class for priority badge"""
        priority_classes = {
            PriorityLevel.LOW: 'badge-secondary',
            PriorityLevel.MEDIUM: 'badge-primary',
            PriorityLevel.HIGH: 'badge-warning',
            PriorityLevel.URGENT: 'badge-danger'
        }
        return priority_classes.get(priority, 'badge-secondary')

    def get_todo_status_class(todo):
        """Get CSS class for todo status"""
        if todo.is_completed:
            return 'todo-completed'
        elif todo.is_overdue:
            return 'todo-overdue'
        elif todo.days_until_due is not None and todo.days_until_due <= 3:
            return 'todo-due-soon'
        return ''

    return dict(
        format_datetime=format_datetime,
        get_priority_badge_class=get_priority_badge_class,
        get_todo_status_class=get_todo_status_class,
        now=datetime.now(timezone.utc)
    )


if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 8000))
    )
