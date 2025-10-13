"""
Template management services for OCR document processing.
"""

from .manager import TemplateManager
from .storage import TemplateStorage
from .validator import TemplateValidator
from .matcher import TemplateMatcher
from .visualization import TemplateVisualizer

__all__ = [
    'TemplateManager',
    'TemplateStorage',
    'TemplateValidator',
    'TemplateMatcher',
    'TemplateVisualizer'
]