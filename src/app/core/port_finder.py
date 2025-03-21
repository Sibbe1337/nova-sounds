"""
Utility module to find available network ports for the server.
"""

import socket
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

def is_port_in_use(port: int) -> bool:
    """
    Check if a port is already in use.
    
    Args:
        port: Port number to check
        
    Returns:
        True if port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    """
    Find an available port starting from the given port.
    
    Args:
        start_port: Starting port number to check
        max_attempts: Maximum number of ports to check
        
    Returns:
        Available port number, or original port if none found
    """
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            if port != start_port:
                logger.info(f"Port {start_port} is in use, using {port} instead")
            return port
    
    # If no available port found, return the original
    logger.warning(f"No available ports found between {start_port} and {start_port + max_attempts - 1}")
    return start_port

def find_server_ports(api_start_port: int = 8000, ui_start_port: int = 8001) -> Tuple[int, int]:
    """
    Find available ports for both API and UI servers.
    
    Args:
        api_start_port: Starting port for API server
        ui_start_port: Starting port for UI server
        
    Returns:
        Tuple of (api_port, ui_port)
    """
    logger.info(f"Finding available ports for servers (starting with API:{api_start_port}, UI:{ui_start_port})")
    
    # Find API port
    api_port = find_available_port(api_start_port)
    
    # For UI port, start from UI port but skip API port if they would be the same
    if ui_start_port == api_port:
        ui_start_port = api_port + 1
    
    # Find UI port
    ui_port = find_available_port(ui_start_port)
    
    # If they ended up the same (unlikely but possible), increment UI port
    if ui_port == api_port:
        ui_port = find_available_port(api_port + 1)
    
    logger.info(f"Using ports - API: {api_port}, UI: {ui_port}")
    return api_port, ui_port 