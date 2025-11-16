from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeLocalField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from models import User


class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username',
                         validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Email',
                      validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                           validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                    validators=[DataRequired(), EqualTo('password')])

    def validate_username(self, username):
        """Check if username already exists"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, email):
        """Check if email already exists"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username',
                         validators=[DataRequired()])
    password = PasswordField('Password',
                           validators=[DataRequired()])


class TodoForm(FlaskForm):
    """Todo creation/editing form"""
    title = StringField('Title',
                       validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description',
                               validators=[Optional(), Length(max=1000)])
    priority = SelectField('Priority',
                          choices=[
                              ('low', 'Low'),
                              ('medium', 'Medium'),
                              ('high', 'High'),
                              ('urgent', 'Urgent')
                          ],
                          default='medium')
    due_date = DateTimeLocalField('Due Date',
                                 validators=[Optional()],
                                 format='%Y-%m-%dT%H:%M')
    category_id = SelectField('Category',
                             coerce=int,
                             validators=[Optional()])


class CategoryForm(FlaskForm):
    """Category creation form"""
    name = StringField('Category Name',
                      validators=[DataRequired(), Length(min=1, max=50)])
    color = StringField('Color',
                       validators=[DataRequired(), Length(min=7, max=7)],
                       default='#6366f1')
