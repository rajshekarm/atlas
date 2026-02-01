"""
__init__.py for flash service
"""
from app.services.flash.models import *
from app.services.flash.router import router
from app.services.flash.config import settings

__all__ = ['router', 'settings']
