"""
Line Profiler Script for Users Service

This script uses line_profiler to measure the exact execution time of every individual
line of code inside the user service functions. Unlike cProfile which shows only
function-level performance, the line profiler pinpoints which specific operations—
such as database queries, password hashing, or connection handling—consume the most time.

Output:
    Detailed line-by-line execution time breakdown for each profiled function,
    showing which specific lines are bottlenecks (e.g., password hashing, DB queries).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from line_profiler import LineProfiler
from users_service.app import create_app
from users_service.application.services import UserService


def profile_user_service_line_by_line():
    """Profile user service functions line by line."""

    app = create_app()

    # Create a line profiler instance
    profiler = LineProfiler()

    # Add functions to profile - these will be analyzed line-by-line
    profiler.add_function(UserService.create_user)
    profiler.add_function(UserService.get_user_by_username)
    profiler.add_function(UserService.get_all_users)
    profiler.add_function(UserService.update_user)
    profiler.add_function(UserService.delete_user)
    profiler.add_function(UserService.authenticate_user)

    print("=" * 100)
    print("LINE PROFILER - Users Service")
    print("=" * 100)
    print("\nMeasuring line-by-line execution time for user service functions...")
    print("This shows EXACTLY which lines consume the most time.\n")

    with app.app_context():
        # Enable the profiler and run operations
        profiler.enable()

        # Test user creation (expect password hashing to be slowest)
        print("Testing user creation (password hashing expected to be slow)...")
        for i in range(10):
            try:
                UserService.create_user(
                    name=f'Line Profile User {i}',
                    username=f'lineprofile{i}',
                    password='SecurePass123!',
                    email=f'lineprofile{i}@example.com',
                    role='regular_user'
                )
            except Exception as e:
                pass  # Ignore duplicates

        # Test user retrieval (expect DB query to be dominant)
        print("Testing user retrieval (database query expected to dominate)...")
        for i in range(10):
            try:
                UserService.get_user_by_username(f'lineprofile{i}')
            except Exception:
                pass

        # Test get all users
        print("Testing get all users...")
        try:
            UserService.get_all_users()
        except Exception:
            pass

        # Test authentication (expect password check to be slow)
        print("Testing authentication (password verification expected to be slow)...")
        for i in range(5):
            try:
                UserService.authenticate_user(f'lineprofile{i}', 'SecurePass123!')
            except Exception:
                pass

        # Test user update
        print("Testing user update...")
        for i in range(3):
            try:
                UserService.update_user(
                    user_id=i+1,
                    name=f'Updated User {i}'
                )
            except Exception:
                pass

        profiler.disable()

    # Print line-by-line statistics
    print("\n" + "=" * 100)
    print("LINE-BY-LINE EXECUTION TIME BREAKDOWN")
    print("=" * 100)
    print("\nKey Metrics:")
    print("  - Time: Total time spent on that line (in seconds)")
    print("  - Per Hit: Average time per execution of that line")
    print("  - % Time: Percentage of total function time")
    print("  - Hits: Number of times that line was executed")
    print("\nExpected Bottlenecks:")
    print("  1. Password hashing lines (bcrypt operations)")
    print("  2. Database query execution lines (db.session.query, db.session.add)")
    print("  3. Database connection/commit lines")
    print("\n")

    profiler.print_stats()

    print("\n" + "=" * 100)
    print("ANALYSIS SUMMARY")
    print("=" * 100)
    print("""
Based on line profiler output, you should see:

1. PASSWORD HASHING BOTTLENECK:
   - Lines with bcrypt.hashpw() or .set_password() will show highest time
   - This is intentional for security (bcrypt is designed to be slow)

2. DATABASE OPERATIONS:
   - Lines with db.session.query() or db.session.add() show DB query time
   - Lines with db.session.commit() show transaction commit overhead

3. CONNECTION OVERHEAD:
   - Database connection setup consumes time at start of functions

4. OPTIMIZATION OPPORTUNITIES:
   - If connection time is high: consider connection pooling
   - If query time is high: add indexes or optimize queries
   - Password hashing is expected to be slow (security feature)

The line profiler gives you EXACT line numbers where time is spent,
allowing precise optimization decisions.
""")


if __name__ == '__main__':
    profile_user_service_line_by_line()