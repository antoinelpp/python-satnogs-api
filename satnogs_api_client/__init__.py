"""
SatNOGS API client module initialization
"""
from __future__ import absolute_import

from ._version import get_versions
from .satnogs_api_client import *

__version__ = get_versions()['version']

del get_versions
