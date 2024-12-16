#!/usr/bin/env bash

# Client-side script to send data for each test scenario that the server runs.
# This script calls tcp_client.py multiple times, once per scenario.
# The server_test.sh script changes sysctls and runs tcp_server.py for each scenario.
#
# Make sure to run this after starting server_test.sh on the server machine.
# You may need to add sleeps if the client starts too quickly before the server is ready.

SERVER_IP="192.168.0.110"   # Replace with your server's IP
PORT=65432
PACKET_COUNT=1000         # Adjust as needed

reset_to_defaults() {
    # Reset to defaults or a chosen baseline configuration
    sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
    sudo sysctl -w net.ipv4.tcp_fastopen=1
    sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=1
    sudo sysctl -w net.ipv4.tcp_ecn=0
    sudo sysctl -w net.ipv4.tcp_window_scaling=1
    sudo sysctl -w net.ipv4.tcp_no_metrics_save=0
}

# A small helper function to send packets for a given scenario
send_data() {
    local scenario="$1"
    echo "Sending $PACKET_COUNT packets for scenario: $scenario"
    # Call tcp_client.py with server IP, port, and packet count
    python3 tcp_client.py
    echo "Done sending data for $scenario."
    echo
}

# If needed, add a sleep to ensure the server is up and ready
sleep 2

########################################
# Run client for each scenario in order #
########################################
reset_to_defaults
# Matches "Reno baseline"
sudo sysctl -w net.ipv4.tcp_congestion_control=reno	
send_data "Reno baseline"
sleep 2

# Matches "Reno with ECN"
sudo sysctl -w net.ipv4.tcp_ecn=1
send_data "Reno with ECN"
sleep 2

# Matches "Reno with no_metrics_save"
sudo sysctl -w net.ipv4.tcp_no_metrics_save=1
send_data "Reno with no_metrics_save"
sleep 2

# Matches "Reno with window scaling disabled"
sudo sysctl -w net.ipv4.tcp_window_scaling=0
send_data "Reno with window scaling disabled"
sleep 2

# Matches "Reno with slow start after idle disabled"
sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0	
send_data "Reno with slow start after idle disabled"
sleep 2

# Matches "Cubic baseline"
# After the server resets to defaults and sets cubic again
reset_to_defaults
sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
send_data "Cubic baseline"
sleep 2

# Matches "Cubic with Fast Open"
sudo sysctl -w net.ipv4.tcp_fastopen=3
send_data "Cubic with Fast Open"
sleep 2

# Matches "Cubic with slow start after idle disabled"
sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0
send_data "Cubic with slow start after idle disabled"
sleep 2

# Server resets and sets Cubic with ECN
reset_to_defaults
sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
sudo sysctl -w net.ipv4.tcp_ecn=1
send_data "Cubic with ECN"
sleep 2

# Matches "Cubic with no_metrics_save"
sudo sysctl -w net.ipv4.tcp_no_metrics_save=1
send_data "Cubic with no_metrics_save"
sleep 2

reset_to_defaults
echo "All scenarios completed."

