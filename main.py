import logging
import os
import socket
from app import create_app

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except socket.error:
            return True

def find_available_port(start_port=5000, max_port=5010):
    """利用可能なポートを探す"""
    for port in range(start_port, max_port):
        if not is_port_in_use(port):
            return port
    raise RuntimeError(f"No available ports found between {start_port} and {max_port}")

try:
    logger.info("Creating Flask application...")
    app = create_app()

    if __name__ == "__main__":
        port = find_available_port()
        logger.info(f"Starting Flask application on port {port}...")
        app.run(host="0.0.0.0", port=port, debug=True)
except Exception as e:
    logger.error(f"Failed to start application: {str(e)}")
    raise