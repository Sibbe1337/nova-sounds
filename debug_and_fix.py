"""
Debug and Fix Script for YouTube Shorts Machine.

This script identifies and fixes common issues:
1. UI indentation errors
2. StatReload continuous detection with debug_features.py
3. Runway ML API key loading issues
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('debug_and_fix')

def run_fix_script(script_name):
    """Run a fix script and capture its output."""
    logger.info(f"Running {script_name}")
    try:
        if not os.path.exists(script_name):
            logger.error(f"Script {script_name} not found")
            return False
            
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True
        )
        
        # Log the output
        logger.info(f"{script_name} stdout:")
        for line in result.stdout.splitlines():
            logger.info(f"  {line}")
            
        if result.stderr:
            logger.warning(f"{script_name} stderr:")
            for line in result.stderr.splitlines():
                logger.warning(f"  {line}")
                
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False

def check_and_restart_servers():
    """Check if servers are running and restart them if needed."""
    logger.info("Checking server status")
    
    # Find server start script
    start_scripts = ['start.py', 'start_servers.py']
    script_to_use = None
    
    for script in start_scripts:
        if os.path.exists(script):
            script_to_use = script
            break
            
    if not script_to_use:
        logger.warning("No server start script found")
        return False
        
    logger.info(f"Found server start script: {script_to_use}")
    
    # Check if servers are already running
    try:
        # Simple check for running processes - might need adjustment for your OS
        import psutil
        
        uvicorn_running = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'uvicorn' in cmdline:
                    uvicorn_running = True
                    logger.info(f"Found running uvicorn process: {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if uvicorn_running:
            logger.info("Uvicorn servers are already running")
            return True
    except ImportError:
        logger.warning("psutil not installed, skipping process check")
    
    # Restart servers
    logger.info(f"Starting servers using {script_to_use}")
    try:
        # Start in background
        if sys.platform == 'win32':
            subprocess.Popen([sys.executable, script_to_use], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen([sys.executable, script_to_use],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           start_new_session=True)
        
        logger.info("Servers started successfully")
        return True
    except Exception as e:
        logger.error(f"Error starting servers: {e}")
        return False

def print_summary(results):
    """Print a summary of the fixes applied."""
    logger.info("\n=== DEBUG AND FIX SUMMARY ===\n")
    
    for script, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"{script}: {status}")
        
    logger.info("\nNext steps:")
    
    all_success = all(results.values())
    if all_success:
        logger.info("1. All fixes were applied successfully")
        logger.info("2. Servers have been restarted")
        logger.info("3. Try accessing the application again")
    else:
        logger.info("1. Some fixes failed - check the logs above")
        logger.info("2. You may need to manually fix remaining issues")
        logger.info("3. Restart the servers manually using 'python start.py' or 'python start_servers.py'")
        
    logger.info("\nIf problems persist:")
    logger.info("1. Check log files in the logs/ directory")
    logger.info("2. Verify .env configuration")
    logger.info("3. Check network connectivity for API calls")

def main():
    """Main function to run all fix scripts."""
    logger.info("Starting debug and fix script")
    
    # Define fix scripts
    fix_scripts = {
        "UI indentation": "debug_ui_fix.py",
        "StatReload issues": "fix_reload_issue.py",
        "API key loading": "fix_api_key.py"
    }
    
    # Run each fix script
    results = {}
    for name, script in fix_scripts.items():
        logger.info(f"\n=== Running {name} fix ===\n")
        success = run_fix_script(script)
        results[name] = success
        
        if success:
            logger.info(f"{name} fix completed successfully")
        else:
            logger.warning(f"{name} fix encountered issues")
    
    # Check and restart servers
    logger.info("\n=== Checking servers ===\n")
    server_result = check_and_restart_servers()
    results["Server restart"] = server_result
    
    # Print summary
    print_summary(results)
    
    logger.info("Debug and fix script completed")

if __name__ == "__main__":
    main() 