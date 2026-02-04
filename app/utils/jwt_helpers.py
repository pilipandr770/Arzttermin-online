"""
JWT helper functions
"""
from flask_jwt_extended import get_jwt_identity, get_jwt


def get_current_user():
    """
    Get current user ID and type from JWT token.
    Returns: {'id': 'uuid-string', 'type': 'doctor'/'patient', 'practice_id': 'uuid-string' (for doctors only)}
    """
    user_id = get_jwt_identity()  # This is now just the UUID string
    claims = get_jwt()
    user_type = claims.get('type')
    practice_id = claims.get('practice_id')  # For doctors only
    
    result = {'id': user_id, 'type': user_type}
    
    if practice_id:
        result['practice_id'] = practice_id
    
    return result


def get_current_practice_id():
    """
    Get current practice ID from JWT token (for doctors only).
    Returns: UUID string or None
    """
    claims = get_jwt()
    return claims.get('practice_id')


def require_practice_context():
    """
    Ensure current user is a doctor with practice context.
    Raises ValueError if not.
    """
    user = get_current_user()
    
    if user.get('type') != 'doctor':
        raise ValueError('Practice context only available for doctors')
    
    practice_id = user.get('practice_id')
    if not practice_id:
        raise ValueError('Doctor missing practice_id in JWT token')
    
    return practice_id

