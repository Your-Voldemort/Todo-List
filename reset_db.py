"""
Script to reset and recreate the database with the correct schema
"""
import os
from app import app, db

def reset_database():
    """Drop all tables and recreate them"""
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables with new schema...")
        db.create_all()
        print("Database reset complete!")

if __name__ == '__main__':
    # Confirm before resetting
    response = input("This will delete all data in the database. Continue? (yes/no): ")
    if response.lower() == 'yes':
        reset_database()
    else:
        print("Database reset cancelled.")
