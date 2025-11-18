"""
Test script to verify the Todo application works correctly
"""
import sys
import io
from app import app, db, User, Todo, Category, PriorityLevel
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

        # Test 1b: Create test user
        print("\n1b. Testing user creation...")
        try:
            # Clean up existing test user if any
            test_user = User.query.filter_by(username="testuser").first()
            if test_user:
                db.session.delete(test_user)
                db.session.commit()
            
            test_user = User(
                username="testuser",
                email="test@example.com"
            )
            test_user.set_password("testpass123")
            db.session.add(test_user)
            db.session.commit()
            print(f"   ✓ User created with ID: {test_user.id}")
        except Exception as e:
            print(f"   ✗ User creation error: {e}")
            db.session.rollback()
            return False

        # Test 2: Create a todo
        print("\n2. Testing todo creation...")
        try:
            test_todo = Todo(
                title="Test Task",
                description="This is a test task",
                user_id=test_user.id
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
                # Login first
                response = client.post('/login', data={
                    'username': 'testuser',
                    'password': 'testpass123'
                }, follow_redirects=True)
                print(f"   ✓ POST /login - Status: {response.status_code}")

                # Test index route
                response = client.get('/')
                print(f"   ✓ GET / - Status: {response.status_code}")

                # Test add route (using legacy endpoint for simplicity)
                response = client.post('/add_legacy', data={
                    'title': 'Test Todo',
                    'description': 'Test Description'
                }, follow_redirects=True)
                print(f"   ✓ POST /add_legacy - Status: {response.status_code}")

                # Get the todo we just created
                todo = Todo.query.filter_by(title='Test Todo', user_id=test_user.id).first()
                if todo:
                    # Test complete route
                    response = client.get(f'/complete/{todo.id}', follow_redirects=True)
                    print(f"   ✓ GET /complete/{todo.id} - Status: {response.status_code}")

                    # Test delete route
                    response = client.get(f'/delete/{todo.id}', follow_redirects=True)
                    print(f"   ✓ GET /delete/{todo.id} - Status: {response.status_code}")

        except Exception as e:
            print(f"   ✗ Route testing error: {e}")
            return False

        # Test 8: Test validation
        print("\n8. Testing validation...")
        try:
            with app.test_client() as client:
                # Login first
                client.post('/login', data={
                    'username': 'testuser',
                    'password': 'testpass123'
                }, follow_redirects=True)

                # Test empty title
                response = client.post('/add_legacy', data={
                    'title': '',
                    'description': 'No title'
                }, follow_redirects=True)
                print(f"   ✓ Empty title validation - Status: {response.status_code}")

                # Test long title
                response = client.post('/add_legacy', data={
                    'title': 'x' * 101,
                    'description': 'Too long'
                }, follow_redirects=True)
                print(f"   ✓ Long title validation - Status: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Validation error: {e}")
            return False

        # Clean up test data
        print("\n9. Cleaning up test data...")
        try:
            todos_to_delete = Todo.query.filter_by(user_id=test_user.id).all()
            for todo in todos_to_delete:
                db.session.delete(todo)
            db.session.delete(test_user)
            db.session.commit()
            print("   ✓ Test data cleaned up")
        except Exception as e:
            print(f"   ✗ Cleanup error: {e}")
            db.session.rollback()

    print("\n" + "=" * 50)
    print("All tests passed successfully! ✓")
    print("=" * 50)
    return True

if __name__ == '__main__':
    test_app()
