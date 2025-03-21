"""
UI Documentation Routes
Provides developers with documentation and examples for UI components
"""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

# Create router
router = APIRouter(
    prefix="/ui-docs",
    tags=["ui docs"]
)

# Set up templates
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def ui_docs_home(request: Request):
    """
    Render UI documentation home page.
    
    Args:
        request: Request object
        
    Returns:
        TemplateResponse: Rendered ui_docs.html
    """
    return templates.TemplateResponse(
        "ui_docs/index.html",
        {
            "request": request,
            "title": "UI Documentation",
            "dev_mode": os.environ.get("DEV_MODE", "false").lower() == "true"
        }
    )

@router.get("/components/{component_name}", response_class=HTMLResponse)
async def ui_docs_component(request: Request, component_name: str):
    """
    Render documentation for a specific UI component.
    
    Args:
        request: Request object
        component_name: Name of the component
        
    Returns:
        TemplateResponse: Rendered component documentation
    """
    # Map component names to template files
    component_templates = {
        "buttons": "ui_docs/components/buttons.html",
        "cards": "ui_docs/components/cards.html",
        "forms": "ui_docs/components/forms.html",
        "notifications": "ui_docs/components/notifications.html",
        "loaders": "ui_docs/components/loaders.html",
        "typography": "ui_docs/components/typography.html",
        "layout": "ui_docs/components/layout.html",
        "state": "ui_docs/components/state.html",
        "accessibility": "ui_docs/components/accessibility.html",
    }
    
    # Get template or default to index
    template = component_templates.get(component_name, "ui_docs/index.html")
    
    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "title": f"UI Docs - {component_name.title()}",
            "component": component_name,
            "dev_mode": os.environ.get("DEV_MODE", "false").lower() == "true"
        }
    )

@router.get("/guidelines", response_class=HTMLResponse)
async def ui_docs_guidelines(request: Request):
    """
    Render UI design guidelines documentation.
    
    Args:
        request: Request object
        
    Returns:
        TemplateResponse: Rendered guidelines documentation
    """
    return templates.TemplateResponse(
        "ui_docs/guidelines.html",
        {
            "request": request,
            "title": "UI Guidelines",
            "dev_mode": os.environ.get("DEV_MODE", "false").lower() == "true"
        }
    )

@router.get("/theme", response_class=HTMLResponse)
async def ui_docs_theme(request: Request):
    """
    Render theme documentation showing colors, spacing, and typography.
    
    Args:
        request: Request object
        
    Returns:
        TemplateResponse: Rendered theme documentation
    """
    return templates.TemplateResponse(
        "ui_docs/theme.html",
        {
            "request": request,
            "title": "UI Theme",
            "dev_mode": os.environ.get("DEV_MODE", "false").lower() == "true"
        }
    ) 