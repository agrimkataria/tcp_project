#!/usr/bin/env bash

# Server-side test script to run tcp_server.py with various TCP configurations.
# It changes the system's TCP parameters, runs the server script to measure metrics,
# and waits for the client to send data.
#
# Assumptions:
# - tcp_server.py is in the same directory.
# - You have passwordless sudo, or you'll be prompted for your password.
# - The server is ready to accept connections on a known PORT.

MEASUREMENT_SCRIPT="tcp_server.py"

set_sysctl() {
    sudo sysctl -w "$1=$2" >/dev/null
}

reset_to_defaults() {
    # Reset to defaults or a chosen baseline configuration
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

# Begin Testing

reset_to_defaults

# Reno baseline
sudo sysctl -w net.ipv4.tcp_congestion_control=reno
run_test "Reno baseline"

# Reno with ECN enabled
sudo sysctl -w net.ipv4.tcp_ecn=1
run_test "Reno with ECN"

# Reno with no_metrics_save
sudo sysctl -w net.ipv4.tcp_no_metrics_save=1
run_test "Reno with no_metrics_save"

# Reno with window scaling disabled
sudo sysctl -w net.ipv4.tcp_window_scaling=0
run_test "Reno with window scaling disabled"

# Reno with slow start after idle disabled
sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0
run_test "Reno with slow start after idle disabled"

# Reset and switch to Cubic
reset_to_defaults
sudo sysctl -w net.ipv4.tcp_congestion_control=cubic

# Cubic baseline
run_test "Cubic baseline"

# Cubic with Fast Open fully enabled (3 = client & server)
sudo sysctl -w net.ipv4.tcp_fastopen=3
run_test "Cubic with Fast Open"

# Cubic with slow start after idle disabled
sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0
run_test "Cubic with slow start after idle disabled"

# Cubic with ECN
reset_to_defaults
sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
sudo sysctl -w net.ipv4.tcp_ecn=1
run_test "Cubic with ECN"

# Cubic with no_metrics_save
sudo sysctl -w net.ipv4.tcp_no_metrics_save=1
run_test "Cubic with no_metrics_save"

# Done with tests
reset_to_defaults
echo "All tests completed."

