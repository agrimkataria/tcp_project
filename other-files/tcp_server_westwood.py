import socket

HOST = ''  # Bind to all available network interfaces
PORT = 65432  # Port to listen on

# Define a list of supported metrics
supported_metrics = {
    "cpu": "Request CPU usage",
    "memory": "Request memory usage",
    "network": "Request network statistics",
    "tcp_connections": "Request active TCP connections",
    "bye": "Close the connection"
}

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Enable address reuse
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print('Server is listening...')
    
    while True:  # Keep the server running to handle multiple clients
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            conn.sendall("Welcome to the Network Metrics Server. Available commands: cpu, memory, network, tcp_connections, bye".encode())
            
            while True:
                data = conn.recv(1024)
                if not data:
                    print('Client disconnected')
                    break
                
                # Decode the client's request
                client_request = data.decode().lower()
                print(f'Client requested: {client_request}')
                
                # Validate the request
                if client_request in supported_metrics:
                    response = f"Fetching {client_request} data..."
                else:
                    response = "Unsupported metric. Try: cpu, memory, network, tcp_connections, bye"
                
                conn.sendall(response.encode())
                
                # End the connection if the client says "bye"
                if client_request == "bye":
                    print('Conversation ended.')
                    break
