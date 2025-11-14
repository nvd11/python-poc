from loguru import logger
import os
import socket

def check_proxy(proxy_host, proxy_port):
    try:
        with socket.create_connection((proxy_host, proxy_port), timeout=2):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def set_proxy():
    logger.info("Setting up proxy configuration.")
    proxy_host = "10.0.1.223"
    proxy_port = 7890
    if check_proxy(proxy_host, proxy_port):
        os.environ["http_proxy"] = f"http://{proxy_host}:{proxy_port}"
        os.environ["https_proxy"] = f"http://{proxy_host}:{proxy_port}"
        logger.info("Proxy is reachable. Proxy configured.")
    else:
        logger.warning("Proxy is not reachable. Skipping proxy configuration.")
