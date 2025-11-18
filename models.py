from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, DateTime, Integer, ForeignKey, Enum as SQLEnum
from datetime import datetime, timezone
from typing import Optional, List
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
import enum

db = SQLAlchemy()
bcrypt = Bcrypt()


class PriorityLevel(enum.Enum):
    """Priority levels for todos"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    todos: Mapped[List["Todo"]] = relationship(
        "Todo",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __init__(self, username: str, email: str, **kwargs):
        """Initialize user with required fields"""
        super().__init__(**kwargs)
        self.username = username
        self.email = email
        # password_hash will be set via set_password method

    def set_password(self, password: str) -> None:
        """Hash and set the user's password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the hash"""
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.username}>'


class Category(db.Model):
    """Category model for organizing todos"""
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#6366f1")  # Hex color code
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    todos: Mapped[List["Todo"]] = relationship("Todo", back_populates="category")

    def __init__(self, name: str, user_id: int, color: str = "#6366f1", **kwargs):
        """Initialize category with required fields"""
        super().__init__(**kwargs)
        self.name = name
        self.user_id = user_id
        self.color = color

    def __repr__(self) -> str:
        return f'<Category {self.name}>'

    def to_dict(self) -> dict:
        """Convert category to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat()
        }


class Todo(db.Model):
    """Enhanced Todo model with advanced features"""
    __tablename__ = 'todos'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    priority: Mapped[PriorityLevel] = mapped_column(
        SQLEnum(PriorityLevel),
        default=PriorityLevel.MEDIUM
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey('categories.id'), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="todos")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="todos")

    def __init__(self, title: str, user_id: int, description: Optional[str] = None, 
                 priority: PriorityLevel = PriorityLevel.MEDIUM, due_date: Optional[datetime] = None,
                 category_id: Optional[int] = None, **kwargs):
        """Initialize todo with required and optional fields"""
        super().__init__(**kwargs)
        self.title = title
        self.user_id = user_id
        self.description = description
        self.priority = priority
        self.due_date = due_date
        self.category_id = category_id

    def __repr__(self) -> str:
        return f'<Todo {self.title}>'

    @property
    def is_overdue(self) -> bool:
        """Check if todo is overdue"""
        if self.due_date and not self.is_completed:
            return datetime.now(timezone.utc) > self.due_date.replace(tzinfo=timezone.utc)
        return False

    @property
    def days_until_due(self) -> Optional[int]:
        """Calculate days until due date"""
        if self.due_date and not self.is_completed:
            delta = self.due_date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)
            return delta.days
        return None

    def toggle_complete(self) -> None:
        """Toggle completion status and set completed_at timestamp"""
        self.is_completed = not self.is_completed
        self.completed_at = datetime.now(timezone.utc) if self.is_completed else None

    def to_dict(self) -> dict:
        """Convert todo to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'is_completed': self.is_completed,
            'priority': self.priority.value,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user_id': self.user_id,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'is_overdue': self.is_overdue,
            'days_until_due': self.days_until_due
        }
