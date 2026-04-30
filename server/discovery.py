import socket
import threading
from protocol import DEFAULT_UDP_PORT, DEFAULT_TCP_PORT

def udp_discovery_server(tcp_port=DEFAULT_TCP_PORT, udp_port=DEFAULT_UDP_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", udp_port))
    print(f"[DISCOVERY] UDP discovery server listening on port {udp_port}")
    def get_lan_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't have to be reachable
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip
    while True:
        data, addr = sock.recvfrom(1024)
        if data == b"DISCOVER_SERVER":
            # Reply with LAN IP and TCP port
            ip = get_lan_ip()
            response = f"{ip}:{tcp_port}"
            sock.sendto(response.encode(), addr)

# To use: import and start in a thread from server.py
