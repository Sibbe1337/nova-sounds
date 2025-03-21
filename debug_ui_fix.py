"""
Debug script to identify and fix UI indentation issues.

This script checks the UI module for indentation errors and reports line numbers.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('debug_ui_fix')

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_indentation_errors(filename):
    """Check for indentation errors in a Python file."""
    logger.info(f"Checking indentation in {filename}")
    
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        # Try to compile to check for syntax errors
        try:
            compile(content, filename, 'exec')
            logger.info(f"No syntax errors found in {filename}")
            return None
        except IndentationError as e:
            logger.error(f"Indentation error in {filename} at line {e.lineno}")
            return {
                'file': filename,
                'line': e.lineno,
                'msg': str(e)
            }
        except SyntaxError as e:
            logger.error(f"Syntax error in {filename} at line {e.lineno}: {e}")
            return {
                'file': filename,
                'line': e.lineno,
                'msg': str(e)
            }
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")
        return {
            'file': filename,
            'msg': str(e)
        }

def show_context(filename, line_number, context=5):
    """Show context around a specific line in a file."""
    logger.info(f"Showing context for {filename} around line {line_number}")
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        start = max(0, line_number - context - 1)
        end = min(len(lines), line_number + context)
        
        logger.info(f"Context for {filename} (lines {start+1}-{end}):")
        for i in range(start, end):
            prefix = ">>>" if i == line_number - 1 else "   "
            logger.info(f"{prefix} {i+1}: {lines[i].rstrip()}")
            
        return {
            'lines': lines[start:end],
            'error_line': line_number - start - 1
        }
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")
        return None

def fix_indentation_error(filename, line_number):
    """Attempt to fix indentation error around the specified line."""
    logger.info(f"Attempting to fix indentation in {filename} around line {line_number}")
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # Check context to determine correct indentation
        start = max(0, line_number - 10)
        end = min(len(lines), line_number + 10)
        context_lines = lines[start:end]
        
        # Look for indentation pattern
        indentation_levels = []
        for i, line in enumerate(context_lines):
            if line.strip() and not line.strip().startswith('#'):
                # Count leading spaces
                leading_spaces = len(line) - len(line.lstrip())
                indentation_levels.append((i, leading_spaces))
        
        if not indentation_levels:
            logger.warning("Could not determine indentation pattern")
            return False
        
        # Find the line with the error
        error_index = line_number - start - 1
        if 0 <= error_index < len(context_lines):
            error_line = context_lines[error_index]
            
            # Determine correct indentation based on surrounding lines
            correct_indent = None
            for i, indent in indentation_levels:
                if i < error_index:
                    # Find the closest line before the error
                    if i == error_index - 1:
                        # Direct previous line
                        if "def " in context_lines[i] or "class " in context_lines[i]:
                            correct_indent = indent + 4  # Python standard indentation
                        elif context_lines[i].rstrip().endswith(':'):
                            correct_indent = indent + 4  # After a colon
                        elif context_lines[i].rstrip().endswith(('(', '[', '{')):
                            correct_indent = indent + 4  # After opening bracket
                        else:
                            correct_indent = indent  # Same level
                        break
            
            if correct_indent is not None:
                # Apply correction
                fixed_line = ' ' * correct_indent + error_line.lstrip()
                context_lines[error_index] = fixed_line
                
                # Update the file
                lines[line_number - 1] = fixed_line
                
                # Write back to file
                with open(filename, 'w') as f:
                    f.writelines(lines)
                
                logger.info(f"Fixed indentation at line {line_number}")
                logger.info(f"Old: '{error_line.rstrip()}'")
                logger.info(f"New: '{fixed_line.rstrip()}'")
                return True
            else:
                logger.warning("Could not determine correct indentation")
                return False
                
        else:
            logger.warning(f"Error line index {error_index} out of bounds")
            return False
    
    except Exception as e:
        logger.error(f"Error fixing {filename}: {e}")
        return False

def check_ui_files():
    """Check all UI Python files for indentation errors."""
    ui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'ui')
    logger.info(f"Checking all Python files in {ui_dir}")
    
    errors = []
    
    for root, _, files in os.walk(ui_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                error = check_indentation_errors(filepath)
                if error:
                    errors.append(error)
                    context = show_context(filepath, error['line'])
                    
                    # Try to fix the error
                    if fix_indentation_error(filepath, error['line']):
                        logger.info(f"Fixed error in {filepath}")
                        
                        # Verify the fix
                        if not check_indentation_errors(filepath):
                            logger.info(f"Successfully fixed {filepath}")
                        else:
                            logger.warning(f"Fix attempt did not resolve all issues in {filepath}")
                    else:
                        logger.warning(f"Could not automatically fix {filepath}")
    
    return errors

def check_api_key_loading():
    """Check if the Runway ML API key is being properly loaded."""
    logger.info("Checking Runway ML API key loading")
    
    # Check the .env file
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    api_key_in_env = False
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip().startswith('RUNWAY_API_KEY='):
                    api_key = line.strip().split('=', 1)[1].strip()
                    api_key_in_env = bool(api_key and api_key != '""' and api_key != "''")
                    logger.info(f"RUNWAY_API_KEY found in .env: {'set' if api_key_in_env else 'empty'}")
                    break
            else:
                logger.warning("RUNWAY_API_KEY not found in .env file")
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
    
    # Check where the API key is loaded in the code
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        if 'RUNWAY_API_KEY' in content and ('os.environ.get' in content or 'os.getenv' in content):
                            logger.info(f"RUNWAY_API_KEY is loaded in {filepath}")
                            # Find the context
                            with open(filepath, 'r') as f:
                                lines = f.readlines()
                                for i, line in enumerate(lines):
                                    if 'RUNWAY_API_KEY' in line:
                                        context = lines[max(0, i-2):min(len(lines), i+3)]
                                        logger.info("Context:")
                                        for ctx_line in context:
                                            logger.info(f"  {ctx_line.rstrip()}")
                except Exception as e:
                    logger.error(f"Error reading {filepath}: {e}")

def main():
    """Main debug function."""
    logger.info("Starting UI debug fix script")
    
    # Check UI files for indentation errors
    ui_errors = check_ui_files()
    
    if ui_errors:
        logger.info(f"Found {len(ui_errors)} indentation errors in UI files")
    else:
        logger.info("No indentation errors found in UI files")
    
    # Check API key loading
    check_api_key_loading()
    
    logger.info("Debug complete")

if __name__ == "__main__":
    main() 