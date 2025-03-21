"""
Fix for StatReload continuous detection issue.

This script identifies and fixes the issue with StatReload repeatedly detecting changes
in debug_features.py, which can cause constant server reloading.
"""

import os
import sys
import logging
import time
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_reload')

def check_file_attributes(filename):
    """Check file attributes that might be causing reload issues."""
    try:
        path = Path(filename)
        if not path.exists():
            logger.error(f"File {filename} does not exist")
            return False
            
        logger.info(f"Checking file: {filename}")
        stats = path.stat()
        
        # Log file stats
        logger.info(f"Size: {stats.st_size} bytes")
        logger.info(f"Last modified: {time.ctime(stats.st_mtime)}")
        logger.info(f"Last accessed: {time.ctime(stats.st_atime)}")
        logger.info(f"Permissions: {stats.st_mode}")
        
        # Check for write attributes
        if not os.access(filename, os.W_OK):
            logger.warning(f"File {filename} is not writable")
        else:
            logger.info(f"File {filename} is writable")
            
        return True
    except Exception as e:
        logger.error(f"Error checking file attributes: {e}")
        return False

def make_backup(filename):
    """Create a backup of the file."""
    try:
        backup_name = f"{filename}.bak"
        with open(filename, 'rb') as src:
            with open(backup_name, 'wb') as dst:
                dst.write(src.read())
        logger.info(f"Created backup at {backup_name}")
        return backup_name
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None

def touch_file(filename):
    """Touch the file to update its timestamp."""
    try:
        # Update modification time
        path = Path(filename)
        path.touch()
        logger.info(f"Updated timestamp for {filename}")
        
        # Verify the change
        new_stats = path.stat()
        logger.info(f"New last modified: {time.ctime(new_stats.st_mtime)}")
        return True
    except Exception as e:
        logger.error(f"Error touching file: {e}")
        return False

def copy_file_content(filename):
    """Copy content to a new file and replace the original."""
    try:
        # Make a backup
        backup = make_backup(filename)
        if not backup:
            return False
            
        # Read content
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Write to a new file
        new_file = f"{filename}.new"
        with open(new_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Replace original with new file
        os.remove(filename)
        os.rename(new_file, filename)
        
        logger.info(f"Recreated file {filename}")
        return True
    except Exception as e:
        logger.error(f"Error copying file content: {e}")
        return False

def fix_reload_issue(filename):
    """Fix the reload issue for the specified file."""
    if not check_file_attributes(filename):
        return False
        
    # Try touching the file first
    if touch_file(filename):
        logger.info("Attempted to fix by updating timestamp")
    else:
        logger.warning("Failed to update timestamp, trying content recreation")
        
        # If that doesn't work, try recreating the file
        if copy_file_content(filename):
            logger.info("Recreated file to fix reload issues")
        else:
            logger.error("Failed to fix reload issues")
            return False
            
    return True

def fix_uvicorn_config():
    """Check for Uvicorn configuration that might be causing reload issues."""
    logger.info("Checking for Uvicorn configuration")
    
    # Check for startup scripts
    startup_scripts = ['start.py', 'start_servers.py']
    found_scripts = []
    
    for script in startup_scripts:
        if os.path.exists(script):
            found_scripts.append(script)
            
    if not found_scripts:
        logger.warning("No startup scripts found")
        return False
        
    # Check each script for uvicorn configuration
    for script in found_scripts:
        try:
            with open(script, 'r') as f:
                content = f.read()
                
            if 'uvicorn' in content:
                logger.info(f"Found uvicorn configuration in {script}")
                
                # Check for reload settings
                if 'reload=True' in content or '"reload": True' in content or "'reload': True" in content:
                    logger.info("Reload is enabled in the uvicorn configuration")
                    
                    # Create a modified version with debug handling
                    if 'reload_dirs' not in content and 'reload_includes' not in content and 'reload_excludes' not in content:
                        logger.info("No reload customization found, creating a modified version")
                        
                        # Make backup
                        backup = make_backup(script)
                        if not backup:
                            continue
                            
                        # Modify the file to add reload customization
                        with open(script, 'r') as f:
                            lines = f.readlines()
                            
                        with open(script, 'w') as f:
                            for line in lines:
                                if 'reload=True' in line:
                                    f.write(line)
                                    f.write('        reload_excludes=["*.bak", "debug_features.py"],\n')
                                elif '"reload": True' in line or "'reload': True" in line:
                                    f.write(line)
                                    if '"reload"' in line:
                                        f.write('            "reload_excludes": ["*.bak", "debug_features.py"],\n')
                                    else:
                                        f.write("            'reload_excludes': ['*.bak', 'debug_features.py'],\n")
                                else:
                                    f.write(line)
                                    
                        logger.info(f"Modified {script} to exclude debug_features.py from reload")
                        return True
        except Exception as e:
            logger.error(f"Error checking {script}: {e}")
            
    return False

def main():
    """Main function to fix reload issues."""
    logger.info("Starting reload issue fix")
    
    # Fix the debug_features.py file
    debug_features_file = "debug_features.py"
    if os.path.exists(debug_features_file):
        logger.info(f"Found {debug_features_file}, attempting to fix reload issues")
        fix_reload_issue(debug_features_file)
    else:
        logger.warning(f"{debug_features_file} not found")
        
    # Fix uvicorn configuration
    fix_uvicorn_config()
    
    logger.info("Completed reload issue fixes")

if __name__ == "__main__":
    main() 