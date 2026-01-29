"""
JWT helper functions
"""
from flask_jwt_extended import get_jwt_identity, get_jwt


def get_current_user():
    """
    Get current user ID and type from JWT token.
    Returns: {'id': 'uuid-string', 'type': 'doctor'/'patient'}
    """
    user_id = get_jwt_identity()  # This is now just the UUID string
    claims = get_jwt()
    user_type = claims.get('type')
    
    return {'id': user_id, 'type': user_type}
