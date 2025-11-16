from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Todo, Category, PriorityLevel
from datetime import datetime, timezone
from dateutil import parser as date_parser
import csv
import io

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/todos', methods=['GET'])
@login_required
def get_todos():
    """Get all todos for the current user with optional filtering"""
    # Query parameters
    completed = request.args.get('completed')
    priority = request.args.get('priority')
    category_id = request.args.get('category_id')
    search = request.args.get('search')

    # Build query
    query = Todo.query.filter_by(user_id=current_user.id)

    if completed is not None:
        is_completed = completed.lower() == 'true'
        query = query.filter_by(is_completed=is_completed)

    if priority:
        try:
            query = query.filter_by(priority=PriorityLevel(priority))
        except ValueError:
            return jsonify({'error': 'Invalid priority level'}), 400

    if category_id:
        query = query.filter_by(category_id=int(category_id))

    if search:
        query = query.filter(Todo.title.ilike(f'%{search}%'))

    todos = query.order_by(Todo.created_at.desc()).all()

    return jsonify({
        'todos': [todo.to_dict() for todo in todos],
        'count': len(todos)
    })


@api.route('/todos/<int:todo_id>', methods=['GET'])
@login_required
def get_todo(todo_id):
    """Get a specific todo"""
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    return jsonify(todo.to_dict())


@api.route('/todos', methods=['POST'])
@login_required
def create_todo():
    """Create a new todo"""
    data = request.get_json()

    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400

    try:
        todo = Todo(
            title=data['title'],
            description=data.get('description'),
            priority=PriorityLevel(data.get('priority', 'medium')),
            user_id=current_user.id,
            category_id=data.get('category_id')
        )

        if data.get('due_date'):
            todo.due_date = date_parser.parse(data['due_date'])

        db.session.add(todo)
        db.session.commit()

        return jsonify(todo.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@api.route('/todos/<int:todo_id>', methods=['PUT'])
@login_required
def update_todo(todo_id):
    """Update an existing todo"""
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    data = request.get_json()

    try:
        if 'title' in data:
            todo.title = data['title']
        if 'description' in data:
            todo.description = data['description']
        if 'priority' in data:
            todo.priority = PriorityLevel(data['priority'])
        if 'category_id' in data:
            todo.category_id = data['category_id']
        if 'due_date' in data:
            todo.due_date = date_parser.parse(data['due_date']) if data['due_date'] else None
        if 'is_completed' in data:
            todo.is_completed = data['is_completed']
            todo.completed_at = datetime.now(timezone.utc) if data['is_completed'] else None

        db.session.commit()
        return jsonify(todo.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@api.route('/todos/<int:todo_id>', methods=['DELETE'])
@login_required
def delete_todo(todo_id):
    """Delete a todo"""
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()

    try:
        db.session.delete(todo)
        db.session.commit()
        return jsonify({'message': 'Todo deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@api.route('/todos/<int:todo_id>/toggle', methods=['POST'])
@login_required
def toggle_todo(todo_id):
    """Toggle todo completion status"""
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()

    try:
        todo.toggle_complete()
        db.session.commit()
        return jsonify(todo.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@api.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """Get all categories for the current user"""
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'categories': [cat.to_dict() for cat in categories],
        'count': len(categories)
    })


@api.route('/categories', methods=['POST'])
@login_required
def create_category():
    """Create a new category"""
    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400

    try:
        category = Category(
            name=data['name'],
            color=data.get('color', '#6366f1'),
            user_id=current_user.id
        )

        db.session.add(category)
        db.session.commit()

        return jsonify(category.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@api.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get statistics for the current user's todos"""
    todos = Todo.query.filter_by(user_id=current_user.id).all()

    total = len(todos)
    completed = sum(1 for todo in todos if todo.is_completed)
    pending = total - completed

    # Priority breakdown
    priority_stats = {
        'low': 0,
        'medium': 0,
        'high': 0,
        'urgent': 0
    }

    for todo in todos:
        if not todo.is_completed:
            priority_stats[todo.priority.value] += 1

    # Overdue count
    overdue = sum(1 for todo in todos if todo.is_overdue)

    # Due soon (within 3 days)
    due_soon = sum(1 for todo in todos if todo.days_until_due is not None and 0 <= todo.days_until_due <= 3)

    return jsonify({
        'total': total,
        'completed': completed,
        'pending': pending,
        'completion_rate': round((completed / total * 100) if total > 0 else 0, 1),
        'priority_breakdown': priority_stats,
        'overdue': overdue,
        'due_soon': due_soon
    })


@api.route('/export/json', methods=['GET'])
@login_required
def export_json():
    """Export all todos as JSON"""
    todos = Todo.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'todos': [todo.to_dict() for todo in todos],
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'user': current_user.username
    })


@api.route('/export/csv', methods=['GET'])
@login_required
def export_csv():
    """Export all todos as CSV"""
    todos = Todo.query.filter_by(user_id=current_user.id).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['ID', 'Title', 'Description', 'Priority', 'Completed',
                     'Due Date', 'Category', 'Created At', 'Completed At'])

    # Write data
    for todo in todos:
        writer.writerow([
            todo.id,
            todo.title,
            todo.description or '',
            todo.priority.value,
            'Yes' if todo.is_completed else 'No',
            todo.due_date.strftime('%Y-%m-%d %H:%M') if todo.due_date else '',
            todo.category.name if todo.category else '',
            todo.created_at.strftime('%Y-%m-%d %H:%M'),
            todo.completed_at.strftime('%Y-%m-%d %H:%M') if todo.completed_at else ''
        ])

    output.seek(0)
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=todos_{current_user.username}.csv'
    }
