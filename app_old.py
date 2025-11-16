from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Todo
from flask_migrate import Migrate
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

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# Ensure the instance folder exists
if not os.path.exists('instance'):
    os.makedirs('instance')

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    todos = Todo.query.order_by(Todo.timestamp.desc()).all()
    return render_template('index.html', todos=todos)

@app.route('/add', methods=['POST'])
def add():
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
            description=description if description else None
        )
        db.session.add(new_todo)
        db.session.commit()
        flash('Todo added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error adding todo: {e}')
        flash('An error occurred while adding the todo.', 'error')

    return redirect(url_for('index'))

@app.route('/complete/<int:todo_id>')
def complete(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.is_completed = not todo.is_completed

    try:
        db.session.commit()
        status = 'completed' if todo.is_completed else 'reopened'
        flash(f'Todo {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error updating todo: {e}')
        flash('An error occurred while updating the todo.', 'error')

    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>')
def delete(todo_id):
    todo = Todo.query.get_or_404(todo_id)

    try:
        db.session.delete(todo)
        db.session.commit()
        flash('Todo deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting todo: {e}')
        flash('An error occurred while deleting the todo.', 'error')

    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found(error):
    flash('The requested item was not found.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Internal error: {error}')
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 8000))
    )