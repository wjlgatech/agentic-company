# todo_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models import Todo, User
from schemas import TodoCreate, TodoUpdate

def get_user_todos(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Todo]:
    """Get all todos for a specific user"""
    return db.query(Todo).filter(Todo.user_id == user_id).offset(skip).limit(limit).all()

def get_todo_by_id(db: Session, todo_id: int, user_id: int) -> Optional[Todo]:
    """Get a specific todo by ID for a user"""
    return db.query(Todo).filter(Todo.id == todo_id, Todo.user_id == user_id).first()

def create_todo(db: Session, todo: TodoCreate, user_id: int) -> Todo:
    """Create a new todo for a user"""
    db_todo = Todo(**todo.dict(), user_id=user_id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def update_todo(db: Session, todo_id: int, todo_update: TodoUpdate, user_id: int) -> Optional[Todo]:
    """Update an existing todo"""
    db_todo = get_todo_by_id(db, todo_id, user_id)
    if not db_todo:
        return None
    
    update_data = todo_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_todo, field, value)
    
    db.commit()
    db.refresh(db_todo)
    return db_todo

def delete_todo(db: Session, todo_id: int, user_id: int) -> bool:
    """Delete a todo"""
    db_todo = get_todo_by_id(db, todo_id, user_id)
    if not db_todo:
        return False
    
    db.delete(db_todo)
    db.commit()
    return True