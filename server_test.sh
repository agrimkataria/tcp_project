#!/usr/bin/env bash

#Receives 30k packets and moves to next test

MEASUREMENT_SCRIPT="tcp_server.py"

set_sysctl() {
    sudo sysctl -w "$1=$2" >/dev/null
}

#resets everything to default vals
reset_to_defaults() {
    sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
    sudo sysctl -w net.ipv4.tcp_fastopen=1
    sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=1
    sudo sysctl -w net.ipv4.tcp_ecn=0
    sudo sysctl -w net.ipv4.tcp_window_scaling=1
    sudo sysctl -w net.ipv4.tcp_no_metrics_save=0
}

run_test() {
    local desc="$1"
    echo "========================================"
    echo "Test scenario: $desc"
    echo "========================================"
    python3 "$MEASUREMENT_SCRIPT"
    echo "Test '$desc' completed."
    echo
}


reset_to_defaults

sudo sysctl -w net.ipv4.tcp_congestion_control=reno
run_test "Reno baseline"


sudo sysctl -w net.ipv4.tcp_ecn=1
run_test "Reno with ECN"


sudo sysctl -w net.ipv4.tcp_no_metrics_save=1
run_test "Reno with no_metrics_save"


sudo sysctl -w net.ipv4.tcp_window_scaling=0
run_test "Reno with window scaling disabled"


sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0
run_test "Reno with slow start after idle disabled"


reset_to_defaults
sudo sysctl -w net.ipv4.tcp_congestion_control=cubic


run_test "Cubic baseline"


sudo sysctl -w net.ipv4.tcp_fastopen=3
run_test "Cubic with Fast Open"


sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0
run_test "Cubic with slow start after idle disabled"


reset_to_defaults
sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
sudo sysctl -w net.ipv4.tcp_ecn=1
run_test "Cubic with ECN"


sudo sysctl -w net.ipv4.tcp_no_metrics_save=1
run_test "Cubic with no_metrics_save"


reset_to_defaults
echo "All tests completed."

