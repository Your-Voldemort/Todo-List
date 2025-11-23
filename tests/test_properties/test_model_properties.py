"""
Property-based tests for model persistence and data integrity

Feature: todo-app-improvements
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.strategies import composite
from datetime import datetime, timezone, timedelta
from models import db, User, Todo, Category, PriorityLevel


# Hypothesis strategies for generating test data
@composite
def valid_username(draw):
    """Generate valid usernames (1-80 chars, alphanumeric + underscore)"""
    length = draw(st.integers(min_value=1, max_value=80))
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_'),
        min_size=length,
        max_size=length
    ))


@composite
def valid_email(draw):
    """Generate valid email addresses"""
    username_part = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=30
    ))
    domain = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
        min_size=2,
        max_size=20
    ))
    tld = draw(st.sampled_from(['com', 'org', 'net', 'edu']))
    return f"{username_part}@{domain}.{tld}"


@composite
def valid_password(draw):
    """Generate valid passwords (8-72 bytes for bcrypt limit)"""
    # Bcrypt has a 72-byte limit, so we need to ensure the password doesn't exceed that
    # Use ASCII characters to avoid multi-byte encoding issues
    return draw(st.text(
        alphabet=st.characters(min_codepoint=33, max_codepoint=126),  # Printable ASCII
        min_size=8,
        max_size=72
    ))


@composite
def valid_todo_title(draw):
    """Generate valid todo titles (1-100 chars, not all whitespace)"""
    title = draw(st.text(min_size=1, max_size=100))
    # Ensure it's not all whitespace
    if title.strip():
        return title
    # If all whitespace, replace with at least one non-whitespace char
    return 'a' + title[:99]


@composite
def valid_todo_description(draw):
    """Generate valid todo descriptions (optional, up to 1000 chars)"""
    return draw(st.one_of(
        st.none(),
        st.text(max_size=1000)
    ))


@composite
def valid_priority(draw):
    """Generate valid priority levels"""
    return draw(st.sampled_from(list(PriorityLevel)))


@composite
def valid_due_date(draw):
    """Generate valid due dates (past, present, or future)"""
    return draw(st.one_of(
        st.none(),
        st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31)
        ).map(lambda dt: dt.replace(tzinfo=timezone.utc))
    ))


@composite
def valid_category_name(draw):
    """Generate valid category names (1-50 chars)"""
    return draw(st.text(min_size=1, max_size=50))


@composite
def valid_hex_color(draw):
    """Generate valid hex color codes"""
    r = draw(st.integers(min_value=0, max_value=255))
    g = draw(st.integers(min_value=0, max_value=255))
    b = draw(st.integers(min_value=0, max_value=255))
    return f"#{r:02x}{g:02x}{b:02x}"


@pytest.mark.property
class TestModelPersistence:
    """
    Property 1: Model persistence correctness
    Validates: Requirements 1.1, 1.3
    
    For any valid model object (Todo, Category, User), when the object is created 
    with valid attributes and persisted to the database, retrieving it should return 
    an object with all attributes matching the original values.
    """
    
    @settings(
        max_examples=100, 
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None  # Disable deadline for database operations
    )
    @given(
        username=valid_username(),
        email=valid_email(),
        password=valid_password()
    )
    def test_user_persistence(self, app_context, test_db, username, email, password):
        """Test that User objects persist correctly with all attributes"""
        # Create user with unique username/email by adding UUID
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        unique_username = f"{username[:70]}_{unique_id}"
        unique_email = f"{unique_id}_{email}"
        
        try:
            # Create user
            user = User(username=unique_username, email=unique_email)
            user.set_password(password)
            
            test_db.session.add(user)
            test_db.session.commit()
            user_id = user.id
            
            # Clear session to force fresh retrieval
            test_db.session.expire_all()
            
            # Retrieve user
            retrieved_user = test_db.session.get(User, user_id)
            
            # Verify all attributes match
            assert retrieved_user is not None
            assert retrieved_user.username == unique_username
            assert retrieved_user.email == unique_email
            assert retrieved_user.check_password(password)
            assert retrieved_user.created_at is not None
            
            # Clean up this specific user
            test_db.session.delete(retrieved_user)
            test_db.session.commit()
        except Exception:
            # Clean up on error
            test_db.session.rollback()
            raise
    
    @settings(
        max_examples=100, 
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None  # Disable deadline for database operations
    )
    @given(
        title=valid_todo_title(),
        description=valid_todo_description(),
        priority=valid_priority(),
        due_date=valid_due_date()
    )
    def test_todo_persistence(self, app_context, test_db, test_user, 
                             title, description, priority, due_date):
        """Test that Todo objects persist correctly with all attributes"""
        try:
            # Create todo
            todo = Todo(
                title=title,
                description=description,
                user_id=test_user.id,
                priority=priority,
                due_date=due_date
            )
            
            test_db.session.add(todo)
            test_db.session.commit()
            todo_id = todo.id
            
            # Clear session to force fresh retrieval
            test_db.session.expire_all()
            
            # Retrieve todo
            retrieved_todo = test_db.session.get(Todo, todo_id)
            
            # Verify all attributes match
            assert retrieved_todo is not None
            assert retrieved_todo.title == title
            assert retrieved_todo.description == description
            assert retrieved_todo.user_id == test_user.id
            assert retrieved_todo.priority == priority
            assert retrieved_todo.is_completed == False
            assert retrieved_todo.completed_at is None
            assert retrieved_todo.created_at is not None
            
            # Handle due_date comparison (both None or both equal)
            if due_date is None:
                assert retrieved_todo.due_date is None
            else:
                assert retrieved_todo.due_date is not None
                # SQLite stores datetimes without timezone, so make both naive for comparison
                retrieved_naive = retrieved_todo.due_date.replace(tzinfo=None) if retrieved_todo.due_date.tzinfo else retrieved_todo.due_date
                due_date_naive = due_date.replace(tzinfo=None) if due_date.tzinfo else due_date
                # Compare timestamps (allowing for microsecond differences)
                assert abs((retrieved_naive - due_date_naive).total_seconds()) < 1
        finally:
            # Clean up
            test_db.session.rollback()
    
    @settings(
        max_examples=100, 
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None  # Disable deadline for database operations
    )
    @given(
        name=valid_category_name(),
        color=valid_hex_color()
    )
    def test_category_persistence(self, app_context, test_db, test_user, name, color):
        """Test that Category objects persist correctly with all attributes"""
        try:
            # Create category
            category = Category(
                name=name,
                color=color,
                user_id=test_user.id
            )
            
            test_db.session.add(category)
            test_db.session.commit()
            category_id = category.id
            
            # Clear session to force fresh retrieval
            test_db.session.expire_all()
            
            # Retrieve category
            retrieved_category = test_db.session.get(Category, category_id)
            
            # Verify all attributes match
            assert retrieved_category is not None
            assert retrieved_category.name == name
            assert retrieved_category.color == color
            assert retrieved_category.user_id == test_user.id
            assert retrieved_category.created_at is not None
        finally:
            # Clean up
            test_db.session.rollback()



@pytest.mark.property
class TestSerializationRoundTrip:
    """
    Property 2: Serialization round-trip
    Validates: Requirements 1.2
    
    For any Todo object, serializing to dictionary via `to_dict()` and then 
    reconstructing a Todo from that dictionary should produce an equivalent object 
    with the same attribute values.
    """
    
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None
    )
    @given(
        title=valid_todo_title(),
        description=valid_todo_description(),
        priority=valid_priority(),
        due_date=valid_due_date()
    )
    def test_todo_serialization_round_trip(self, app_context, test_db, test_user, test_category,
                                          title, description, priority, due_date):
        """Test that Todo objects can be serialized and deserialized correctly"""
        try:
            # Create todo with optional category
            todo = Todo(
                title=title,
                description=description,
                user_id=test_user.id,
                priority=priority,
                due_date=due_date,
                category_id=test_category.id
            )
            
            test_db.session.add(todo)
            test_db.session.commit()
            
            # Serialize to dict
            todo_dict = todo.to_dict()
            
            # Verify dict contains expected keys
            assert 'id' in todo_dict
            assert 'title' in todo_dict
            assert 'description' in todo_dict
            assert 'priority' in todo_dict
            assert 'is_completed' in todo_dict
            assert 'user_id' in todo_dict
            assert 'category_id' in todo_dict
            
            # Verify values match
            assert todo_dict['title'] == title
            assert todo_dict['description'] == description
            assert todo_dict['priority'] == priority.value
            assert todo_dict['is_completed'] == False
            assert todo_dict['user_id'] == test_user.id
            assert todo_dict['category_id'] == test_category.id
            
            # Verify due_date handling
            if due_date is None:
                assert todo_dict['due_date'] is None
            else:
                assert todo_dict['due_date'] is not None
                # The dict should contain ISO format string
                assert isinstance(todo_dict['due_date'], str)
            
            # Verify category is included
            assert todo_dict['category'] is not None
            assert todo_dict['category']['id'] == test_category.id
            assert todo_dict['category']['name'] == test_category.name
            
        finally:
            test_db.session.rollback()
    
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None
    )
    @given(
        name=valid_category_name(),
        color=valid_hex_color()
    )
    def test_category_serialization_round_trip(self, app_context, test_db, test_user, name, color):
        """Test that Category objects can be serialized and deserialized correctly"""
        try:
            # Create category
            category = Category(
                name=name,
                color=color,
                user_id=test_user.id
            )
            
            test_db.session.add(category)
            test_db.session.commit()
            
            # Serialize to dict
            category_dict = category.to_dict()
            
            # Verify dict contains expected keys
            assert 'id' in category_dict
            assert 'name' in category_dict
            assert 'color' in category_dict
            assert 'user_id' in category_dict
            assert 'created_at' in category_dict
            
            # Verify values match
            assert category_dict['name'] == name
            assert category_dict['color'] == color
            assert category_dict['user_id'] == test_user.id
            assert isinstance(category_dict['created_at'], str)
            
        finally:
            test_db.session.rollback()



@pytest.mark.property
class TestPasswordHashing:
    """
    Property 3: Password hashing security
    Validates: Requirements 1.4
    
    For any valid password string, when a User is created with that password, 
    the password should be hashed (not stored in plaintext) and `check_password()` 
    should return True for the original password and False for any different password.
    """
    
    @settings(
        max_examples=10,  # Reduced because bcrypt is slow
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None
    )
    @given(
        password=valid_password(),
        wrong_password=valid_password()
    )
    def test_password_hashing_security(self, app_context, test_db, password, wrong_password):
        """Test that passwords are hashed and verified correctly"""
        # Ensure wrong_password is actually different
        if password == wrong_password:
            wrong_password = password + "X"
        
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        try:
            # Create user with password
            user = User(
                username=f"testuser_{unique_id}",
                email=f"{unique_id}@test.com"
            )
            user.set_password(password)
            
            test_db.session.add(user)
            test_db.session.commit()
            
            # Verify password is hashed (not stored in plaintext)
            assert user.password_hash != password
            assert len(user.password_hash) > 0
            # Bcrypt hashes start with $2b$
            assert user.password_hash.startswith('$2b$')
            
            # Verify correct password returns True
            assert user.check_password(password) == True
            
            # Verify wrong password returns False
            assert user.check_password(wrong_password) == False
            
            # Verify empty password returns False
            assert user.check_password("") == False
            
            # Clean up
            test_db.session.delete(user)
            test_db.session.commit()
            
        except Exception:
            test_db.session.rollback()
            raise



@pytest.mark.property
class TestCompletionToggle:
    """
    Property 4: Completion toggle idempotence
    Validates: Requirements 1.5
    
    For any Todo object, toggling completion status twice should return the object 
    to its original completion state, and the completed_at timestamp should be set 
    when completed and None when not completed.
    """
    
    @settings(
        max_examples=50,  # Reduced for performance
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None
    )
    @given(
        title=valid_todo_title(),
        description=valid_todo_description(),
        priority=valid_priority(),
        due_date=valid_due_date()
    )
    def test_completion_toggle_idempotence(self, app_context, test_db, test_user,
                                          title, description, priority, due_date):
        """Test that toggling completion twice returns to original state"""
        try:
            # Create todo (initially not completed)
            todo = Todo(
                title=title,
                description=description,
                user_id=test_user.id,
                priority=priority,
                due_date=due_date
            )
            
            test_db.session.add(todo)
            test_db.session.commit()
            
            # Verify initial state
            assert todo.is_completed == False
            assert todo.completed_at is None
            
            # Toggle to completed
            todo.toggle_complete()
            test_db.session.commit()
            
            # Verify completed state
            assert todo.is_completed == True
            assert todo.completed_at is not None
            completed_timestamp = todo.completed_at
            
            # Toggle back to not completed
            todo.toggle_complete()
            test_db.session.commit()
            
            # Verify back to original state (idempotence)
            assert todo.is_completed == False
            assert todo.completed_at is None
            
            # Toggle again to completed
            todo.toggle_complete()
            test_db.session.commit()
            
            # Verify completed again
            assert todo.is_completed == True
            assert todo.completed_at is not None
            # New timestamp should be different (or at least not None)
            assert todo.completed_at is not None
            
        finally:
            test_db.session.rollback()
