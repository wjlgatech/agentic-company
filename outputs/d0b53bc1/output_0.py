"""
Simple Todo List Application

A command-line todo list manager that allows users to add, view, and delete todo items.
All data is stored in memory during the application session.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class TodoItem:
    """Represents a single todo item with ID, description, and timestamp."""
    
    def __init__(self, description: str) -> None:
        """
        Initialize a new todo item.
        
        Args:
            description: The todo item description
        """
        self.id: str = str(uuid.uuid4())[:8]  # Short UUID for readability
        self.description: str = description.strip()
        self.created_at: datetime = datetime.now()
    
    def to_dict(self) -> Dict[str, str]:
        """Convert todo item to dictionary format."""
        return {
            'id': self.id,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __str__(self) -> str:
        """String representation of todo item."""
        return f"[{self.id}] {self.description} (Created: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"


class TodoManager:
    """Manages todo items with CRUD operations."""
    
    def __init__(self) -> None:
        """Initialize empty todo list."""
        self._todos: Dict[str, TodoItem] = {}
    
    def add_todo(self, description: str) -> Tuple[bool, str]:
        """
        Add a new todo item to the list.
        
        Args:
            description: The todo item description
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not description or not description.strip():
            return False, "Error: Todo description cannot be empty"
        
        if len(description.strip()) > 200:
            return False, "Error: Todo description must be 200 characters or less"
        
        todo_item = TodoItem(description)
        self._todos[todo_item.id] = todo_item
        
        return True, f"Todo added successfully with ID: {todo_item.id}"
    
    def list_todos(self) -> Tuple[bool, str]:
        """
        List all todo items.
        
        Returns:
            Tuple of (success: bool, formatted_list: str)
        """
        if not self._todos:
            return True, "No todo items found. Your list is empty!"
        
        # Sort by creation timestamp
        sorted_todos = sorted(self._todos.values(), key=lambda x: x.created_at)
        
        result = f"\n--- Todo List ({len(sorted_todos)} items) ---\n"
        for i, todo in enumerate(sorted_todos, 1):
            result += f"{i}. {todo}\n"
        
        return True, result
    
    def delete_todo(self, todo_id: str) -> Tuple[bool, str]:
        """
        Delete a todo item by ID.
        
        Args:
            todo_id: The ID of the todo item to delete
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not todo_id or not todo_id.strip():
            return False, "Error: Todo ID cannot be empty"
        
        todo_id = todo_id.strip()
        
        if todo_id not in self._todos:
            return False, f"Error: Todo item with ID '{todo_id}' not found"
        
        deleted_todo = self._todos.pop(todo_id)
        return True, f"Todo item '{deleted_todo.description}' deleted successfully"
    
    def get_todo_count(self) -> int:
        """Get the total number of todo items."""
        return len(self._todos)
    
    def get_todos_by_id_prefix(self, prefix: str) -> List[TodoItem]:
        """
        Get todos that match an ID prefix (for user convenience).
        
        Args:
            prefix: The ID prefix to search for
            
        Returns:
            List of matching todo items
        """
        return [todo for todo in self._todos.values() if todo.id.startswith(prefix)]


class TodoApp:
    """Command-line interface for the todo list application."""
    
    def __init__(self) -> None:
        """Initialize the todo application."""
        self.todo_manager = TodoManager()
        self.running = True
    
    def display_menu(self) -> None:
        """Display the main menu options."""
        print("\n" + "="*50)
        print("           SIMPLE TODO LIST APP")
        print("="*50)
        print("1. Add Todo Item")
        print("2. List All Todos")
        print("3. Delete Todo Item")
        print("4. Quit")
        print("-"*50)
    
    def get_user_input(self, prompt: str, allow_empty: bool = False) -> str:
        """
        Get validated user input.
        
        Args:
            prompt: The prompt to display to user
            allow_empty: Whether to allow empty input
            
        Returns:
            The user's input string
        """
        while True:
            try:
                user_input = input(prompt).strip()
                if not allow_empty and not user_input:
                    print("Error: Input cannot be empty. Please try again.")
                    continue
                return user_input
            except (EOFError, KeyboardInterrupt):
                print("\n\nGoodbye!")
                self.running = False
                return ""
    
    def handle_add_todo(self) -> None:
        """Handle adding a new todo item."""
        print("\n--- Add New Todo ---")
        description = self.get_user_input("Enter todo description: ")
        
        if not self.running:  # User interrupted
            return
        
        success, message = self.todo_manager.add_todo(description)
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
    
    def handle_list_todos(self) -> None:
        """Handle listing all todo items."""
        print("\n--- Your Todo List ---")
        success, message = self.todo_manager.list_todos()
        print(message)
    
    def handle_delete_todo(self) -> None:
        """Handle deleting a todo item."""
        print("\n--- Delete Todo ---")
        
        # First show current todos if any exist
        if self.todo_manager.get_todo_count() == 0:
            print("No todo items to delete. Your list is empty!")
            return
        
        # Show current todos for reference
        _, todo_list = self.todo_manager.list_todos()
        print(todo_list)
        
        todo_id = self.get_user_input("Enter todo ID to delete: ")
        
        if not self.running:  # User interrupted
            return
        
        # Try to find todo by exact ID or prefix match
        if todo_id not in [todo.id for todo in self.todo_manager._todos.values()]:
            # Try prefix matching
            matches = self.todo_manager.get_todos_by_id_prefix(todo_id)
            if len(matches) == 1:
                todo_id = matches[0].id
                print(f"Found match: {matches[0].description}")
            elif len(matches) > 1:
                print(f"Multiple matches found for '{todo_id}':")
                for match in matches:
                    print(f"  {match}")
                print("Please be more specific with the ID.")
                return
        
        success, message = self.todo_manager.delete_todo(todo_id)
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
    
    def handle_menu_selection(self, choice: str) -> None:
        """
        Handle user menu selection.
        
        Args:
            choice: The user's menu choice
        """
        if choice == "1":
            self.handle_add_todo()
        elif choice == "2":
            self.handle_list_todos()
        elif choice == "3":
            self.handle_delete_todo()
        elif choice == "4":
            print("\nThank you for using Simple Todo List App!")
            print("Have a productive day! 👋")
            self.running = False
        else:
            print(f"✗ Error: Invalid choice '{choice}'. Please select 1, 2, 3, or 4.")
    
    def run(self) -> None:
        """Main application loop."""
        print("Welcome to Simple Todo List App!")
        print("Manage your tasks efficiently from the command line.")
        
        while self.running:
            try:
                self.display_menu()
                
                # Show current todo count
                count = self.todo_manager.get_todo_count()
                print(f"Current todos: {count}")
                
                choice = self.get_user_input("Select an option (1-4): ")
                
                if not self.running:  # User interrupted
                    break
                
                self.handle_menu_selection(choice)
                
                # Pause for user to read output
                if self.running and choice in ["1", "2", "3"]:
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n✗ An unexpected error occurred: {e}")
                print("Please try again.")


def main() -> None:
    """Main entry point for the application."""
    app = TodoApp()
    app.run()


if __name__ == "__main__":
    main()