"""
Security Utilities
==================

Helper functions for security checks and validations
"""
import os
import secrets
import logging

logger = logging.getLogger(__name__)


def check_secret_key_strength():
    """
    Check if SECRET_KEY and JWT_SECRET_KEY are strong enough for production
    
    Warnings will be logged if:
    - Keys are using default/weak values
    - Keys are too short
    - Keys are the same (they should be different)
    """
    secret_key = os.getenv('SECRET_KEY', '')
    jwt_secret = os.getenv('JWT_SECRET_KEY', secret_key)
    
    warnings = []
    
    # Check for weak/default keys
    weak_keys = [
        'dev-secret-key-change-in-production',
        'dev',
        'test',
        'secret',
        'password',
        '123456'
    ]
    
    if secret_key.lower() in weak_keys:
        warnings.append('⚠️ CRITICAL: SECRET_KEY is using a weak/default value!')
    
    if jwt_secret.lower() in weak_keys:
        warnings.append('⚠️ CRITICAL: JWT_SECRET_KEY is using a weak/default value!')
    
    # Check key length
    if len(secret_key) < 32:
        warnings.append(f'⚠️ WARNING: SECRET_KEY is too short ({len(secret_key)} chars, recommended: 64+)')
    
    if len(jwt_secret) < 32:
        warnings.append(f'⚠️ WARNING: JWT_SECRET_KEY is too short ({len(jwt_secret)} chars, recommended: 64+)')
    
    # Check if keys are the same
    if secret_key == jwt_secret and len(secret_key) > 0:
        warnings.append('⚠️ WARNING: SECRET_KEY and JWT_SECRET_KEY should be different!')
    
    # Log warnings
    if warnings:
        logger.warning('🔐 SECRET KEY SECURITY WARNINGS:')
        for warning in warnings:
            logger.warning(warning)
        
        # In production, these should be fatal
        if os.getenv('FLASK_ENV') == 'production':
            logger.error('🚨 CRITICAL: Weak secrets detected in PRODUCTION environment!')
            logger.error('Generate strong keys with: python -c "import secrets; print(secrets.token_hex(32))"')
    else:
        logger.info('✅ Secret keys appear to be strong')
    
    return len(warnings) == 0


def generate_strong_secret():
    """
    Generate a cryptographically strong secret key
    
    Returns:
        str: 64-character hexadecimal secret
    """
    return secrets.token_hex(32)


def sanitize_error_message(error, show_details=False):
    """
    Sanitize error messages to prevent information disclosure
    
    Args:
        error: The original error object/message
        show_details: Whether to show detailed error info (dev mode only)
    
    Returns:
        str: Sanitized error message safe for client
    """
    if show_details or os.getenv('FLASK_ENV') == 'development':
        return str(error)
    
    # Generic error message for production
    return 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.'


def log_security_event(event_type, user_id=None, ip_address=None, details=None):
    """
    Log security-relevant events for auditing
    
    Args:
        event_type: Type of event (e.g., 'login_failed', 'rate_limit_exceeded')
        user_id: Optional user identifier
        ip_address: Optional IP address
        details: Optional additional details dict
    """
    from datetime import datetime
    
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event': event_type,
        'user_id': user_id,
        'ip': ip_address,
        'details': details
    }
    
    logger.warning(f'🔒 SECURITY EVENT: {log_entry}')
    
    # TODO: Send to external monitoring service (Sentry, CloudWatch, etc.)
    # For now, just log locally


# Pre-check on module import
if __name__ != '__main__':
    check_secret_key_strength()
