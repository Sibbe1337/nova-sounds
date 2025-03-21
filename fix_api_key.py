"""
Fix for Runway ML API key loading issue.

This script identifies and fixes the issue with the Runway ML API key not being 
properly configured despite being present in the .env file.
"""

import os
import sys
import logging
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_api_key')

def find_api_key_in_env():
    """Find the Runway ML API key in the .env file."""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    try:
        if not os.path.exists(env_file):
            logger.error(f".env file not found at {env_file}")
            return None
            
        logger.info(f"Reading .env file from {env_file}")
        api_key = None
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('RUNWAY_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    # Remove quotes if present
                    if (api_key.startswith('"') and api_key.endswith('"')) or \
                       (api_key.startswith("'") and api_key.endswith("'")):
                        api_key = api_key[1:-1]
                    
                    logger.info(f"Found RUNWAY_API_KEY in .env: {'*' * len(api_key)}")
                    break
        
        return api_key
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
        return None

def find_api_key_loader_files():
    """Find files that load the Runway ML API key."""
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    loader_files = []
    
    try:
        for root, _, files in os.walk(src_dir):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        
                    if 'RUNWAY_API_KEY' in content and ('os.environ' in content or 'getenv' in content):
                        loader_files.append(filepath)
                        logger.info(f"Found API key loader in {filepath}")
                except Exception as e:
                    logger.error(f"Error reading {filepath}: {e}")
        
        return loader_files
    except Exception as e:
        logger.error(f"Error searching for loader files: {e}")
        return []

def find_warning_messages():
    """Find files that log warnings about the Runway ML API key."""
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    warning_files = []
    
    try:
        for root, _, files in os.walk(src_dir):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        
                    if 'RUNWAY_API_KEY' in content and ('warning' in content.lower() or 'logger.warn' in content or 'not configured' in content.lower()):
                        warning_files.append(filepath)
                        logger.info(f"Found warning message in {filepath}")
                except Exception as e:
                    logger.error(f"Error reading {filepath}: {e}")
        
        return warning_files
    except Exception as e:
        logger.error(f"Error searching for warning files: {e}")
        return []

def analyze_loader_code(filepath):
    """Analyze how the API key is loaded and what might be going wrong."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        api_key_lines = []
        for i, line in enumerate(lines):
            if 'RUNWAY_API_KEY' in line:
                # Get context (5 lines before and after)
                start = max(0, i - 5)
                end = min(len(lines), i + 6)
                context = lines[start:end]
                api_key_lines.append((i, line.strip(), context))
        
        issues = []
        for i, line, context in api_key_lines:
            # Check for common issues
            if 'os.environ.get' in line and 'None' not in line and 'or ""' not in line and 'or \'\'' not in line:
                issues.append(f"Line {i+1}: Missing default value for os.environ.get")
            
            if 'os.environ[' in line:
                issues.append(f"Line {i+1}: Using direct dictionary access without try/except")
            
            # Look for if/else checks that might be failing
            condition_found = False
            for ctx_line in context:
                if 'if ' in ctx_line and 'RUNWAY_API_KEY' in ctx_line:
                    condition_found = True
                    if 'not ' in ctx_line or ' is None' in ctx_line or ' == ""' in ctx_line or ' == \'\'':
                        issues.append(f"Context: Check for empty API key might be incorrectly implemented")
            
            if not condition_found and ('warning' in ''.join(context).lower() or 'logger.warn' in ''.join(context)):
                issues.append(f"Context: Warning is issued without proper condition check")
        
        return api_key_lines, issues
    except Exception as e:
        logger.error(f"Error analyzing {filepath}: {e}")
        return [], [f"Error: {str(e)}"]

def fix_loader_issue(filepath, api_key_line_info, issues, api_key):
    """Attempt to fix the API key loading issue."""
    if not api_key:
        logger.warning("No API key available to use for fixing")
        return False
        
    if not issues:
        logger.info(f"No issues found in {filepath}")
        return False
        
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        modified = False
        
        for i, line, _ in api_key_line_info:
            # Fix missing default value
            if 'os.environ.get' in line and 'None' not in line and 'or ""' not in line and 'or \'\'' not in line:
                if ')' in line:
                    new_line = line.replace(')', ', "")')
                    lines[i] = new_line
                    logger.info(f"Fixed missing default value at line {i+1}")
                    modified = True
            
            # Fix direct dictionary access
            if 'os.environ[' in line:
                new_line = line.replace('os.environ[', 'os.environ.get(')
                if ']' in new_line:
                    new_line = new_line.replace(']', ', "")')
                lines[i] = new_line
                logger.info(f"Fixed direct dictionary access at line {i+1}")
                modified = True
                
            # Add a direct environment variable setting for testing
            if modified and api_key:
                # Find a good place to insert the fix - before the current line
                env_set_line = f"os.environ['RUNWAY_API_KEY'] = '{api_key}'  # Added by debug script\n"
                lines.insert(i, env_set_line)
                logger.info(f"Added direct environment variable setting before line {i+1}")
        
        if modified:
            # Create a backup
            backup_path = f"{filepath}.bak"
            with open(backup_path, 'w') as f:
                for line in lines:
                    f.write(line)
            logger.info(f"Created backup at {backup_path}")
            
            # Write the modified file
            with open(filepath, 'w') as f:
                for line in lines:
                    f.write(line)
            logger.info(f"Modified {filepath}")
            return True
        else:
            logger.info(f"No modifications needed for {filepath}")
            return False
    except Exception as e:
        logger.error(f"Error fixing {filepath}: {e}")
        return False

def fix_settings_file():
    """Fix the settings file to properly load the API key."""
    settings_paths = [
        os.path.join('src', 'app', 'core', 'settings.py'),
        os.path.join('src', 'app', 'core', 'config.py'),
        os.path.join('src', 'app', 'settings.py'),
        os.path.join('src', 'config.py')
    ]
    
    api_key = find_api_key_in_env()
    if not api_key:
        logger.warning("No API key found in .env file")
        return False
    
    for path in settings_paths:
        if os.path.exists(path):
            logger.info(f"Found settings file at {path}")
            try:
                with open(path, 'r') as f:
                    content = f.read()
                
                if 'RUNWAY_API_KEY' in content:
                    logger.info(f"Settings file contains RUNWAY_API_KEY reference")
                    
                    # Analyze and fix the file
                    api_key_lines, issues = analyze_loader_code(path)
                    if issues:
                        logger.info(f"Found issues: {issues}")
                        return fix_loader_issue(path, api_key_lines, issues, api_key)
                    else:
                        logger.info("No issues found in settings file")
                else:
                    logger.info(f"Settings file does not contain RUNWAY_API_KEY reference")
                    
                    # Add the API key to the settings file
                    with open(path, 'a') as f:
                        f.write(f"\n# Added by debug script\nRUNWAY_API_KEY = '{api_key}'\n")
                    logger.info(f"Added RUNWAY_API_KEY to settings file")
                    return True
            except Exception as e:
                logger.error(f"Error fixing settings file {path}: {e}")
    
    logger.warning("No suitable settings file found")
    return False

def main():
    """Main function to fix API key loading issues."""
    logger.info("Starting API key fix script")
    
    # Check if API key exists in .env
    api_key = find_api_key_in_env()
    if not api_key:
        logger.error("No API key found in .env file. Please add it and try again.")
        return
    
    # Find files that load the API key
    loader_files = find_api_key_loader_files()
    
    # Find files that warn about missing API key
    warning_files = find_warning_messages()
    
    # Combine the lists, removing duplicates
    all_files = list(set(loader_files + warning_files))
    
    if not all_files:
        logger.warning("No files found that handle the Runway ML API key")
        # Try to fix settings file as a fallback
        if fix_settings_file():
            logger.info("Added API key to settings file")
        return
    
    # Analyze and fix each file
    fixed = False
    for filepath in all_files:
        logger.info(f"Analyzing {filepath}")
        api_key_lines, issues = analyze_loader_code(filepath)
        
        if issues:
            logger.info(f"Found issues in {filepath}: {issues}")
            if fix_loader_issue(filepath, api_key_lines, issues, api_key):
                fixed = True
        else:
            logger.info(f"No issues found in {filepath}")
    
    # If no files were fixed, try to fix settings file
    if not fixed:
        logger.info("No files were fixed, trying to fix settings file")
        if fix_settings_file():
            logger.info("Fixed settings file")
            fixed = True
    
    if fixed:
        logger.info("Successfully fixed API key loading issues")
    else:
        logger.warning("No issues could be fixed automatically")

if __name__ == "__main__":
    main() 