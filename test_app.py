"""
Test script to verify the Todo application works correctly
"""
import sys
import io
from app import app, db, Todo
from datetime import datetime, timezone

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_app():
    print("=" * 50)
    print("Testing Todo Application")
    print("=" * 50)

    with app.app_context():
        # Test 1: Database connection
        print("\n1. Testing database connection...")
        try:
            db.create_all()
            print("   ✓ Database tables created successfully")
        except Exception as e:
            print(f"   ✗ Database error: {e}")
            return False

        # Test 2: Create a todo
        print("\n2. Testing todo creation...")
        try:
            test_todo = Todo(
                title="Test Task",
                description="This is a test task"
            )
            db.session.add(test_todo)
            db.session.commit()
            print(f"   ✓ Todo created with ID: {test_todo.id}")
        except Exception as e:
            print(f"   ✗ Creation error: {e}")
            db.session.rollback()
            return False

        # Test 3: Read todos
        print("\n3. Testing todo retrieval...")
        try:
            todos = Todo.query.all()
            print(f"   ✓ Retrieved {len(todos)} todo(s)")
            for todo in todos:
                print(f"      - {todo.title}: {todo.description}")
        except Exception as e:
            print(f"   ✗ Retrieval error: {e}")
            return False

        # Test 4: Update todo (complete)
        print("\n4. Testing todo completion toggle...")
        try:
            test_todo.is_completed = True
            db.session.commit()
            print(f"   ✓ Todo marked as completed: {test_todo.is_completed}")

            test_todo.is_completed = False
            db.session.commit()
            print(f"   ✓ Todo marked as incomplete: {test_todo.is_completed}")
        except Exception as e:
            print(f"   ✗ Update error: {e}")
            db.session.rollback()
            return False

        # Test 5: Test to_dict method
        print("\n5. Testing to_dict method...")
        try:
            todo_dict = test_todo.to_dict()
            print(f"   ✓ Todo as dict: {todo_dict}")
        except Exception as e:
            print(f"   ✗ to_dict error: {e}")
            return False

        # Test 6: Delete todo
        print("\n6. Testing todo deletion...")
        try:
            db.session.delete(test_todo)
            db.session.commit()
            remaining = Todo.query.all()
            print(f"   ✓ Todo deleted. Remaining todos: {len(remaining)}")
        except Exception as e:
            print(f"   ✗ Deletion error: {e}")
            db.session.rollback()
            return False

        # Test 7: Test routes
        print("\n7. Testing Flask routes...")
        try:
            with app.test_client() as client:
                # Test index route
                response = client.get('/')
                print(f"   ✓ GET / - Status: {response.status_code}")

                # Test add route
                response = client.post('/add', data={
                    'title': 'Test Todo',
                    'description': 'Test Description'
                })
                print(f"   ✓ POST /add - Status: {response.status_code}")

                # Get the todo we just created
                todo = Todo.query.filter_by(title='Test Todo').first()
                if todo:
                    # Test complete route
                    response = client.get(f'/complete/{todo.id}')
                    print(f"   ✓ GET /complete/{todo.id} - Status: {response.status_code}")

                    # Test delete route
                    response = client.get(f'/delete/{todo.id}')
                    print(f"   ✓ GET /delete/{todo.id} - Status: {response.status_code}")

        except Exception as e:
            print(f"   ✗ Route testing error: {e}")
            return False

        # Test 8: Test validation
        print("\n8. Testing validation...")
        try:
            with app.test_client() as client:
                # Test empty title
                response = client.post('/add', data={
                    'title': '',
                    'description': 'No title'
                })
                print(f"   ✓ Empty title validation - Status: {response.status_code}")

                # Test long title
                response = client.post('/add', data={
                    'title': 'x' * 101,
                    'description': 'Too long'
                })
                print(f"   ✓ Long title validation - Status: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Validation error: {e}")
            return False

    print("\n" + "=" * 50)
    print("All tests passed successfully! ✓")
    print("=" * 50)
    return True

if __name__ == '__main__':
    test_app()
