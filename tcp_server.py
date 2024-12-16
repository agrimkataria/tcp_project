import socket
import psutil
import time
import threading
import subprocess
import json
from datetime import datetime

# Server configuration
HOST = ''  # Bind to all available interfaces
PORT = 65432  # Port for client-server communication
PACKET_COUNT = 30000  # Expected number of packets from the client

# Generate a unique filename for metrics based on current timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
METRICS_FILE = f'server_metrics_{timestamp}.json'

def monitor_cwnd(packets_received_data, start_time, stop_event, metrics_data):
    """
    Periodically measures cwnd, lost, retrans, CPU and memory usage.
    Updates sums and keeps track of final or average values as required.
    """
    while not stop_event.is_set():
        try:
            # Run 'ss' command to fetch TCP info
            result = subprocess.run(['ss', '-i', '-t'], stdout=subprocess.PIPE)
            output = result.stdout.decode()

            cwnd_line = None
            for line in output.splitlines():
                if 'cwnd:' in line:
                    cwnd_line = line
                    break

            lost = None
            retrans = None

            if cwnd_line:
                parts = cwnd_line.split()
                for p in parts:
                    if p.startswith("cwnd:"):
                        val_str = p.split(':')[1]
                        try:
                            val = float(val_str)
                            metrics_data["cwnd_sum"] += val
                            metrics_data["cwnd_count"] += 1
                        except ValueError:
                            pass
                    elif p.startswith("lost:"):
                        val_str = p.split(':')[1]
                        try:
                            lost = float(val_str)
                        except ValueError:
                            lost = None
                    elif p.startswith("retrans:"):
                        val_str = p.split(':')[1]
                        try:
                            retrans = float(val_str)
                        except ValueError:
                            retrans = None

            # Record the latest values for lost and retrans
            if lost is not None:
                metrics_data["lost_final"] = lost
            if retrans is not None:
                metrics_data["retrans_final"] = retrans

            # CPU and memory usage to be averaged
            cpu_usage = psutil.cpu_percent(interval=1)
            mem_usage = psutil.virtual_memory().percent
            metrics_data["cpu_sum"] += cpu_usage
            metrics_data["cpu_count"] += 1

            metrics_data["mem_sum"] += mem_usage
            metrics_data["mem_count"] += 1

        except Exception as e:
            print(f"Error monitoring cwnd and packet loss: {e}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print('Server is listening...')

    conn, addr = s.accept()
    print("accepted connection")
    with conn:
        print(f'Connected by {addr}')

        packets_received_data = {"count": 0}
        start_time = time.time()
        stop_event = threading.Event()

        # Initialize data structures for metrics
        metrics_data = {
            "cwnd_sum": 0.0, "cwnd_count": 0,
            "cpu_sum": 0.0, "cpu_count": 0,
            "mem_sum": 0.0, "mem_count": 0,
            "lost_final": None,       # Will store final lost segments value
            "retrans_final": None     # Will store final retrans segments value
        }

        metrics_thread = threading.Thread(
            target=monitor_cwnd, 
            args=(packets_received_data, start_time, stop_event, metrics_data)
        )
        metrics_thread.start()

        # Receive packets
        while packets_received_data["count"] < PACKET_COUNT:
            try:
                data = conn.recv(1024)
                if not data:
                    print("No data received. Exiting loop.")
                    break

                packets_received_data["count"] += 1
                print(packets_received_data["count"])
                conn.sendall(b"ACK")

                if packets_received_data["count"] % 30000 == 0:
                    print(f"Packets received: {packets_received_data['count']}")

            except socket.error as e:
                print(f"Socket error: {e}")
                break

        # Stop monitoring thread
        stop_event.set()
        metrics_thread.join()

        # Compute final metrics:
        # Time Elapsed (final)
        final_time_elapsed = time.time() - start_time
        # Packets Received (final)
        final_packets_received = packets_received_data["count"]

        # cwnd: average if available
        if metrics_data["cwnd_count"] > 0:
            avg_cwnd = metrics_data["cwnd_sum"] / metrics_data["cwnd_count"]
        else:
            avg_cwnd = "N/A"

        # cpu: average if available
        if metrics_data["cpu_count"] > 0:
            avg_cpu = metrics_data["cpu_sum"] / metrics_data["cpu_count"]
        else:
            avg_cpu = "N/A"

        # memory: average if available
        if metrics_data["mem_count"] > 0:
            avg_mem = metrics_data["mem_sum"] / metrics_data["mem_count"]
        else:
            avg_mem = "N/A"

        # lost_final: final reading
        final_lost = metrics_data["lost_final"] if metrics_data["lost_final"] is not None else "N/A"
        # retrans_final: final reading
        final_retrans = metrics_data["retrans_final"] if metrics_data["retrans_final"] is not None else "N/A"

        # Prepare final JSON output
        final_metrics = {
            "time_elapsed (s)": final_time_elapsed,
            "packets_received": final_packets_received,
            "cwnd (packets)": avg_cwnd,
            "lost_segments": final_lost,
            "retrans_segments": final_retrans,
            "cpu_usage (%)": avg_cpu,
            "memory_usage (%)": avg_mem
        }

        # Save to a unique JSON file
        with open(METRICS_FILE, 'w') as f:
            json.dump(final_metrics, f, indent=4)

        conn.sendall(b"Server metrics collection completed. Connection will now close.")
    print('Connection closed.')

