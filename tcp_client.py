import socket
import time
import subprocess
import json
from datetime import datetime
# Client settings
HOST = '192.168.0.110'  # Replace with the server's IP address
PORT = 65432
PACKET_COUNT = 30000  # Number of packets to send
PACKET_SIZE = 64  # Size of each packet in bytes

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
METRICS_FILE = f'client_metrics_{timestamp}.json'  # File to store client-side metrics

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Connect to the server
    s.connect((HOST, PORT))
    print("Connection established with server.")

    total_rtt = 0.0  # To accumulate the total RTT of all packets
    total_bytes = 0
    start_time = time.time()

    for i in range(PACKET_COUNT):
        # Create a fixed-size packet with padding
        message = f"Packet {i+1}".ljust(PACKET_SIZE, 'x').encode()
        send_start = time.time()
        s.sendall(message)  # Send the packet to the server
        ack = s.recv(1024)  # Receive acknowledgment
        send_end = time.time()

        # Calculate RTT for the packet in milliseconds
        rtt = (send_end - send_start) * 1000
        total_rtt += rtt

        total_bytes += len(message)  # Update total bytes sent

        # Display real-time progress every 1000 packets
        if (i + 1) % 1000 == 0:
            print(f"Packets sent: {i + 1}")

    end_time = time.time()
    duration = end_time - start_time  # Total time for transmission
    throughput = total_bytes / duration  # Bytes per second

    # Compute average RTT
    avg_rtt = (total_rtt / PACKET_COUNT) if PACKET_COUNT > 0 else "N/A"

    # Save metrics to a JSON file
    metrics_summary = {
        "total_packets_sent": PACKET_COUNT,
        "total_data_sent (bytes)": total_bytes,
        "total_duration (s)": round(duration, 2),
        "throughput (bytes/s)": round(throughput, 2),
        "average_rtt (ms)": round(avg_rtt, 2) if isinstance(avg_rtt, float) else avg_rtt,
    }

    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics_summary, f, indent=4)

    print(f"Metrics stored in {METRICS_FILE}")
    print("All packets sent. Connection will now close.")



