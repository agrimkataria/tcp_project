#!/usr/bin/env bash

#sends 30k packets to server per test

SERVER_IP="192.168.0.110"
PORT=65432
PACKET_COUNT=30000        

#resets to defaults
reset_to_defaults() {
    sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
    sudo sysctl -w net.ipv4.tcp_fastopen=1
    sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=1
    sudo sysctl -w net.ipv4.tcp_ecn=0
    sudo sysctl -w net.ipv4.tcp_window_scaling=1
    sudo sysctl -w net.ipv4.tcp_no_metrics_save=0
}

#sends data and shows in terminal what we did
send_data() {
    local scenario="$1"
    echo "Sending $PACKET_COUNT packets for scenario: $scenario"
    
    python3 tcp_client.py
    echo "Done sending data for $scenario."
    echo
}

sleep 2

reset_to_defaults

sudo sysctl -w net.ipv4.tcp_congestion_control=reno	
send_data "Reno baseline"
sleep 2


sudo sysctl -w net.ipv4.tcp_ecn=1
send_data "Reno with ECN"
sleep 2


sudo sysctl -w net.ipv4.tcp_no_metrics_save=1
send_data "Reno with no_metrics_save"
sleep 2


sudo sysctl -w net.ipv4.tcp_window_scaling=0
send_data "Reno with window scaling disabled"
sleep 2


sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0	
send_data "Reno with slow start after idle disabled"
sleep 2


reset_to_defaults
sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
send_data "Cubic baseline"
sleep 2


sudo sysctl -w net.ipv4.tcp_fastopen=3
send_data "Cubic with Fast Open"
sleep 2


sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0
send_data "Cubic with slow start after idle disabled"
sleep 2


reset_to_defaults
sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
sudo sysctl -w net.ipv4.tcp_ecn=1
send_data "Cubic with ECN"
sleep 2


sudo sysctl -w net.ipv4.tcp_no_metrics_save=1
send_data "Cubic with no_metrics_save"
sleep 2

reset_to_defaults
echo "All scenarios completed."

