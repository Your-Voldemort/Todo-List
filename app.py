from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Todo
import os

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize the database
db.init_app(app)

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
    title = request.form.get('title')
    description = request.form.get('description')
    
    if not title:
        flash('Title is required!', 'error')
    else:
        new_todo = Todo(title=title, description=description)
        db.session.add(new_todo)
        try:
            db.session.commit()
            flash('Todo added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the todo.', 'error')
    
    return redirect(url_for('index'))

@app.route('/complete/<int:todo_id>')
def complete(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.is_completed = not todo.is_completed
    try:
        db.session.commit()
        flash('Todo status updated!', 'success')
    except Exception as e:
        db.session.rollback()
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
        flash('An error occurred while deleting the todo.', 'error')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)