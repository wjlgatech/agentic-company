# validation.py
from fastapi import HTTPException, status
from pydantic import ValidationError
from typing import Any, Dict

def validate_request_body(model_class: Any, data: Dict) -> Any:
    """Validate request body against Pydantic model"""
    try:
        return model_class(**data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Validation error",
                "errors": e.errors()
            }
        )

def handle_not_found(resource_name: str, resource_id: int = None) -> HTTPException:
    """Standard not found error response"""
    detail = f"{resource_name} not found"
    if resource_id:
        detail += f" with id {resource_id}"
    
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )

def handle_conflict(message: str) -> HTTPException:
    """Standard conflict error response"""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=message
    )