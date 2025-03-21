#!/usr/bin/env python3
"""
UI QA Checklist Tool
Helps validate the UI implementation against best practices
"""

import os
import sys
import glob
import re
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init()

# Define file paths
UI_DIR = os.path.join("src", "ui")
CSS_DIR = os.path.join(UI_DIR, "static", "css")
JS_DIR = os.path.join(UI_DIR, "static", "js")
TEMPLATES_DIR = "templates"

def header(text):
    """Print a header with styling"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * len(text)}{Style.RESET_ALL}")

def success(text):
    """Print a success message"""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def warning(text):
    """Print a warning message"""
    print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")

def error(text):
    """Print an error message"""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def info(text):
    """Print an info message"""
    print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")

def check_css_files():
    """Check CSS files for implementation and best practices"""
    header("Checking CSS Files")
    
    # Get list of CSS files
    css_files = glob.glob(os.path.join(CSS_DIR, "*.css"))
    info(f"Found {len(css_files)} CSS files")
    
    # Check for required CSS files
    required_files = [
        "variables.css", 
        "main.css", 
        "a11y.css", 
        "responsive-utils.css", 
        "ui-states.css"
    ]
    
    for file in required_files:
        file_path = os.path.join(CSS_DIR, file)
        if os.path.exists(file_path):
            success(f"Required file exists: {file}")
        else:
            error(f"Required file missing: {file}")
    
    # Check CSS variables
    variables_path = os.path.join(CSS_DIR, "variables.css")
    if os.path.exists(variables_path):
        with open(variables_path, "r") as f:
            content = f.read()
            
            # Check for theme variables
            if "--primary-color:" in content:
                success("Primary color variable defined")
            else:
                error("Primary color variable missing")
                
            # Check for dark theme
            if ".dark-theme" in content:
                success("Dark theme support implemented")
            else:
                error("Dark theme support missing")
    
    # Check for BEM naming convention in component CSS
    component_files = [
        "buttons.css", 
        "cards.css", 
        "forms.css",
        "notifications.css"
    ]
    
    bem_pattern = r"\.[a-z][\w]*(__[\w-]+|--[\w-]+)?"
    
    for file in component_files:
        file_path = os.path.join(CSS_DIR, file)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()
                if re.search(bem_pattern, content):
                    success(f"BEM naming convention used in {file}")
                else:
                    warning(f"BEM naming convention may not be used in {file}")

def check_js_files():
    """Check JavaScript files for implementation and best practices"""
    header("Checking JavaScript Files")
    
    # Get list of JS files
    js_files = glob.glob(os.path.join(JS_DIR, "*.js"))
    info(f"Found {len(js_files)} JavaScript files")
    
    # Check for required JS files
    required_files = [
        "app.js", 
        "ui-utils.js", 
        "api-client.js", 
        "form-validator.js", 
        "theme-switcher.js"
    ]
    
    for file in required_files:
        file_path = os.path.join(JS_DIR, file)
        if os.path.exists(file_path):
            success(f"Required file exists: {file}")
        else:
            error(f"Required file missing: {file}")
    
    # Check for use of event delegation
    for js_file in js_files:
        with open(js_file, "r") as f:
            content = f.read()
            
            # Check for event delegation pattern
            if "addEventListener" in content and ".querySelectorAll" in content:
                success(f"Event delegation pattern found in {os.path.basename(js_file)}")
            
            # Check for error handling
            if "try" in content and "catch" in content:
                success(f"Error handling found in {os.path.basename(js_file)}")
            
            # Check for global namespace pollution
            if "window." in content:
                info(f"Global namespace accessed in {os.path.basename(js_file)}")

def check_accessibility():
    """Check for accessibility features"""
    header("Checking Accessibility Features")
    
    # Check for ARIA attributes in templates
    template_files = glob.glob(os.path.join(TEMPLATES_DIR, "**/*.html"), recursive=True)
    
    aria_count = 0
    sr_only_count = 0
    focus_visible_count = 0
    
    for template in template_files:
        with open(template, "r") as f:
            content = f.read()
            
            # Count ARIA attributes
            aria_matches = re.findall(r'aria-[a-z]+="[^"]+"', content)
            aria_count += len(aria_matches)
            
            # Count screen reader only classes
            sr_matches = re.findall(r'class="[^"]*\bsr-only\b[^"]*"', content)
            sr_only_count += len(sr_matches)
            
            # Count focus-visible
            focus_matches = re.findall(r':focus-visible', content)
            focus_visible_count += len(focus_matches)
    
    if aria_count > 0:
        success(f"Found {aria_count} ARIA attributes across templates")
    else:
        warning("No ARIA attributes found. Consider adding for improved accessibility")
    
    if sr_only_count > 0:
        success(f"Found {sr_only_count} screen reader only elements")
    else:
        warning("No screen reader only elements found. Consider adding for improved accessibility")
    
    # Check for skip links
    skip_link_found = False
    for template in template_files:
        with open(template, "r") as f:
            content = f.read()
            if "skip-to-content" in content or "skip-link" in content:
                skip_link_found = True
                break
    
    if skip_link_found:
        success("Skip link for keyboard navigation found")
    else:
        warning("No skip link found. Consider adding for improved keyboard navigation")
    
    # Check a11y CSS file
    a11y_path = os.path.join(CSS_DIR, "a11y.css")
    if os.path.exists(a11y_path):
        with open(a11y_path, "r") as f:
            content = f.read()
            
            features = []
            if ":focus" in content:
                features.append("Focus styles")
            if "@media (prefers-reduced-motion" in content:
                features.append("Reduced motion support")
            if ".sr-only" in content:
                features.append("Screen reader utilities")
            
            if features:
                success(f"Accessibility CSS includes: {', '.join(features)}")
            else:
                warning("Accessibility CSS may be missing important features")

def check_responsive_design():
    """Check for responsive design features"""
    header("Checking Responsive Design")
    
    # Check for responsive utilities
    responsive_path = os.path.join(CSS_DIR, "responsive-utils.css")
    if os.path.exists(responsive_path):
        with open(responsive_path, "r") as f:
            content = f.read()
            
            features = []
            if "@media" in content:
                features.append("Media queries")
            if "container" in content:
                features.append("Container classes")
            if "col-" in content or "row" in content:
                features.append("Grid system")
            
            if features:
                success(f"Responsive utilities include: {', '.join(features)}")
            else:
                warning("Responsive utilities may be missing important features")
    
    # Check for viewport meta tag in templates
    viewport_found = False
    for template in glob.glob(os.path.join(TEMPLATES_DIR, "**/*.html"), recursive=True):
        with open(template, "r") as f:
            content = f.read()
            if "viewport" in content and "width=device-width" in content:
                viewport_found = True
                break
    
    if viewport_found:
        success("Viewport meta tag found")
    else:
        error("Viewport meta tag missing. This is critical for responsive design")

def check_dark_mode():
    """Check for dark mode support"""
    header("Checking Dark Mode Support")
    
    # Check for dark mode variables
    dark_mode_vars = False
    variables_path = os.path.join(CSS_DIR, "variables.css")
    if os.path.exists(variables_path):
        with open(variables_path, "r") as f:
            content = f.read()
            if ".dark-theme" in content:
                dark_mode_vars = True
    
    if dark_mode_vars:
        success("Dark theme CSS variables defined")
    else:
        error("Dark theme CSS variables missing")
    
    # Check for theme switcher
    theme_switcher_path = os.path.join(JS_DIR, "theme-switcher.js")
    if os.path.exists(theme_switcher_path):
        with open(theme_switcher_path, "r") as f:
            content = f.read()
            
            features = []
            if "localStorage" in content:
                features.append("Theme persistence")
            if "prefers-color-scheme" in content:
                features.append("System preference detection")
            if "toggleTheme" in content:
                features.append("Theme toggle function")
            
            if features:
                success(f"Theme switcher includes: {', '.join(features)}")
            else:
                warning("Theme switcher may be missing important features")
    else:
        error("Theme switcher JavaScript missing")

def check_documentation():
    """Check for UI documentation"""
    header("Checking UI Documentation")
    
    # Check for UI docs routes
    ui_docs_path = os.path.join(UI_DIR, "routes", "ui_docs.py")
    if os.path.exists(ui_docs_path):
        success("UI documentation routes found")
    else:
        warning("UI documentation routes missing")
    
    # Check for UI docs templates
    ui_docs_templates = os.path.join(TEMPLATES_DIR, "ui_docs")
    if os.path.exists(ui_docs_templates) and os.path.isdir(ui_docs_templates):
        template_count = len(glob.glob(os.path.join(ui_docs_templates, "**/*.html"), recursive=True))
        success(f"UI documentation templates found: {template_count} templates")
    else:
        warning("UI documentation templates missing")

def main():
    """Main function to run all checks"""
    print(f"{Fore.CYAN}{Style.BRIGHT}YouTube Shorts Machine - UI QA Checklist{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================={Style.RESET_ALL}\n")
    
    print(f"Running checks at: {os.getcwd()}")
    
    # Run all checks
    check_css_files()
    check_js_files()
    check_accessibility()
    check_responsive_design()
    check_dark_mode()
    check_documentation()
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}QA Checklist Complete{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 