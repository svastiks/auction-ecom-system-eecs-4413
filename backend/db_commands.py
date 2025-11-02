#!/usr/bin/env python3
"""
Database management commands for the auction e-commerce system.
Run this script to manage database migrations and operations.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"{description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    """Main function to handle database commands."""
    if len(sys.argv) < 2:
        print("Usage: python db_commands.py <command>")
        print("\nAvailable commands:")
        print("  migrate     - Run database migrations")
        print("  create      - Create a new migration")
        print("  downgrade   - Downgrade database by one revision")
        print("  upgrade     - Upgrade database to latest revision")
        print("  history     - Show migration history")
        print("  current     - Show current database revision")
        print("  init-db     - Initialize database (create tables)")
        return

    command = sys.argv[1].lower()
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    if command == "migrate" or command == "upgrade":
        run_command("alembic upgrade head", "Running database migrations")
        
    elif command == "create":
        if len(sys.argv) < 3:
            print("Usage: python db_commands.py create <migration_message>")
            return
        message = " ".join(sys.argv[2:])
        run_command(f'alembic revision --autogenerate -m "{message}"', f"Creating migration: {message}")
        
    elif command == "downgrade":
        run_command("alembic downgrade -1", "Downgrading database by one revision")
        
    elif command == "history":
        run_command("alembic history", "Showing migration history")
        
    elif command == "current":
        run_command("alembic current", "Showing current database revision")
        
    elif command == "init-db":
        print(" Initializing database...")
        if run_command("alembic upgrade head", "Creating all database tables"):
            print("\nDatabase initialized successfully!")
            print(" Tables created:")
            print("  - users, addresses, auth_sessions, password_reset_tokens")
            print("  - categories, catalogue_items, item_images")
            print("  - auctions, bids")
            print("  - orders, payments, receipts, shipments")
            print("  - event_log")
        else:
            print("\nDatabase initialization failed!")
            
    else:
        print(f"Unknown command: {command}")
        print("Run 'python db_commands.py' to see available commands")

if __name__ == "__main__":
    main()
