"""
Export API endpoint proxy.

This file forwards requests to the endpoints/export.py implementation.
"""
from src.app.api.endpoints.export import router

# Export the router directly
__all__ = ['router'] 