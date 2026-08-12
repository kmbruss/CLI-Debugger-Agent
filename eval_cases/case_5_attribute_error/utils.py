"""
Utility functions for case 5
"""

def format_user_list(users):
    """Format a list of users for display"""
    return [user.to_dict() for user in users]

def validate_user(user):
    """Validate a user object"""
    if not hasattr(user, 'id'):
        raise ValueError("User missing 'id' attribute")
    if not hasattr(user, 'name'):
        raise ValueError("User missing 'name' attribute")
    return True
