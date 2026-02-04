"""
Event Names for TerminFinder
=============================

Event-style naming for background tasks to prepare for future event bus architecture.

Naming convention: <entity>.<action>
Example: appointment.created, doctor.updated
"""

from .event_names import *

__all__ = ['EVENTS']
