import socket
import time
import subprocess
import json
from datetime import datetime

HOST = '192.168.0.110' 
PORT = 65432
PACKET_COUNT = 30000  
PACKET_SIZE = 64  #sending 64 byte packets

#make metrics file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
METRICS_FILE = f'client_metrics_{timestamp}.json'

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #establish connection
    s.connect((HOST, PORT))
    print("Connection established with server.")

    total_rtt = 0.0
    total_bytes = 0
    start_time = time.time()

    for i in range(PACKET_COUNT):
        #make packet
        message = f"Packet {i+1}".ljust(PACKET_SIZE, 'x').encode()
        send_start = time.time()
        s.sendall(message)  #send packet
        ack = s.recv(1024)  #look for ACK
        send_end = time.time()

        #calculate RTT
        rtt = (send_end - send_start) * 1000
        total_rtt += rtt

        total_bytes += len(message)  

        #for monitoring show evrey 1000 packets
        if (i + 1) % 1000 == 0:
            print(f"Packets sent: {i + 1}")

    end_time = time.time()
    duration = end_time - start_time 
    throughput = total_bytes / duration 

    avg_rtt = (total_rtt / PACKET_COUNT) if PACKET_COUNT > 0 else "N/A"

    #save stff to json file
    metrics_summary = {
        "total_packets_sent": PACKET_COUNT,
        "total_data_sent (bytes)": total_bytes,
        "total_duration (s)": round(duration, 2),
        "throughput (bytes/s)": round(throughput, 2),
        "average_rtt (ms)": round(avg_rtt, 2) if isinstance(avg_rtt, float) else avg_rtt,
    }

    #save file
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics_summary, f, indent=4)

    print(f"Metrics stored in {METRICS_FILE}")
    print("All packets sent. Connection will now close.")



