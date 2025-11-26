"""Quick test to verify whitespace validation works"""
from app import app
from models import db, Todo, User, PriorityLevel

with app.app_context():
    # Try to create a todo with whitespace-only title
    try:
        user = User.query.first()
        if not user:
            user = User(username='testuser', email='test@test.com')
            user.set_password('test123')
            db.session.add(user)
            db.session.commit()
        
        # This should raise ValueError
        todo = Todo(
            title='   ',  # Whitespace only
            user_id=user.id,
            priority=PriorityLevel.MEDIUM
        )
        db.session.add(todo)
        db.session.commit()
        print("FAIL: Todo with whitespace title was created!")
    except ValueError as e:
        print(f"SUCCESS: Validation worked - {e}")
        db.session.rollback()
    except Exception as e:
        print(f"ERROR: Unexpected exception - {e}")
        db.session.rollback()
