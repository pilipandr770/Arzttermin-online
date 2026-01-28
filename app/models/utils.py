"""
Database utilities for TerminFinder
"""
import os


def get_table_args():
    """
    Helper function to get table arguments with proper schema handling
    """
    if 'postgresql' in os.getenv('DATABASE_URL', ''):
        schema = os.getenv('DB_SCHEMA', 'public')
        return {'schema': schema}
    return {}