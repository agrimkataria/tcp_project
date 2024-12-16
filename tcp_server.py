import socket
import psutil
import time
import threading
import subprocess
import json
from datetime import datetime

#server configs
HOST = '' 
PORT = 65432 
PACKET_COUNT = 30000  #packets to be sent

#make metrics file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
METRICS_FILE = f'server_metrics_{timestamp}.json'

#measure metrics as we run
def monitor_cwnd(packets_received_data, start_time, stop_event, metrics_data):
    while not stop_event.is_set():
        try:
            #runs linux command ss -i -t to get tcp info
            result = subprocess.run(['ss', '-i', '-t'], stdout=subprocess.PIPE)
            output = result.stdout.decode()

            cwnd_line = None
            for line in output.splitlines():
                if 'cwnd:' in line:
                    cwnd_line = line
                    break

            lost = None
            retrans = None

            #parse line of tcp info
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

            #get values for lost and retransmission
            if lost is not None:
                metrics_data["lost_final"] = lost
            if retrans is not None:
                metrics_data["retrans_final"] = retrans

            #calculate avg cpu and memory usage
            cpu_usage = psutil.cpu_percent(interval=1)
            mem_usage = psutil.virtual_memory().percent
            metrics_data["cpu_sum"] += cpu_usage
            metrics_data["cpu_count"] += 1

            metrics_data["mem_sum"] += mem_usage
            metrics_data["mem_count"] += 1

        except Exception as e:
            print(f"Error monitoring cwnd and packet loss: {e}")

#open communication
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT)) #listen to port for incomming connections
    s.listen()
    print('Server is listening...')

    conn, addr = s.accept() #accept connection if it comes in
    print("accepted connection")
    with conn:
        print(f'Connected by {addr}')

        packets_received_data = {"count": 0} #aggregate packet count
        start_time = time.time()
        stop_event = threading.Event()

        #all the data we need
        metrics_data = {
            "cwnd_sum": 0.0, "cwnd_count": 0,
            "cpu_sum": 0.0, "cpu_count": 0,
            "mem_sum": 0.0, "mem_count": 0,
            "lost_final": None,       
            "retrans_final": None     
        }

        #monitor this in a concurrent thread
        metrics_thread = threading.Thread(
            target=monitor_cwnd, 
            args=(packets_received_data, start_time, stop_event, metrics_data)
        )
        metrics_thread.start()

        #receive packets
        while packets_received_data["count"] < PACKET_COUNT:
            try:
                data = conn.recv(1024)
                if not data:
                    print("No data received. Exiting loop.")
                    break

                packets_received_data["count"] += 1
                print(packets_received_data["count"])
                conn.sendall(b"ACK")

                if packets_received_data["count"] % 30000 == 0: #means we're done
                    print(f"Packets received: {packets_received_data['count']}")

            except socket.error as e:
                print(f"Socket error: {e}")
                break

        #join thread into main thread
        stop_event.set()
        metrics_thread.join()

        #get final data
        final_time_elapsed = time.time() - start_time
        final_packets_received = packets_received_data["count"]

        #get avg congestion window
        if metrics_data["cwnd_count"] > 0:
            avg_cwnd = metrics_data["cwnd_sum"] / metrics_data["cwnd_count"]
        else:
            avg_cwnd = "N/A"

        if metrics_data["cpu_count"] > 0:
            avg_cpu = metrics_data["cpu_sum"] / metrics_data["cpu_count"]
        else:
            avg_cpu = "N/A"

        if metrics_data["mem_count"] > 0:
            avg_mem = metrics_data["mem_sum"] / metrics_data["mem_count"]
        else:
            avg_mem = "N/A"

        final_lost = metrics_data["lost_final"] if metrics_data["lost_final"] is not None else "N/A"
        final_retrans = metrics_data["retrans_final"] if metrics_data["retrans_final"] is not None else "N/A"

        #json output
        final_metrics = {
            "time_elapsed (s)": final_time_elapsed,
            "packets_received": final_packets_received,
            "cwnd (packets)": avg_cwnd,
            "lost_segments": final_lost,
            "retrans_segments": final_retrans,
            "cpu_usage (%)": avg_cpu,
            "memory_usage (%)": avg_mem
        }

        #save to json file
        with open(METRICS_FILE, 'w') as f:
            json.dump(final_metrics, f, indent=4)

        conn.sendall(b"Server metrics collection completed. Connection will now close.")
    print('Connection closed.')

