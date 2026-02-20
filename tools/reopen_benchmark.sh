#!/bin/bash

# Generate CSV filename with current datetime
CSV_FILE="results_$(date '+%Y%m%d_%H%M%S').csv"

# Define the CSV header
echo "threads,avg_ops_sec,p50_latency,p95_latency,p99_latency,time,open_time_ms" >"$CSV_FILE"

# Array of thread counts to test
THREAD_COUNTS=(1 2 4 8 12 16 20 24)

echo "Creating DB at /tmp/rocksdbtest/reopen"
mkdir -p /tmp/rocksdbtest
./db_bench --db=/tmp/rocksdbtest/reopen --benchmarks="filluniquerandom" --num=10000000 --seed=425

for T in "${THREAD_COUNTS[@]}"; do
  for i in {1..5}; do
    echo "Cloning fresh DB..."
    rm -rf /tmp/rocksdbtest/updaterandom
    cp -r /tmp/rocksdbtest/reopen /tmp/rocksdbtest/updaterandom

    # Run db_bench and capture output
    # We use 'grep' to find the benchmark line and 'awk' to pull specific columns
    echo "Running benchmark with $T threads..."
    OUTPUT=$(./db_bench --db=/tmp/rocksdbtest/updaterandom --benchmarks="updaterandom" --duration=30 --seed=425 --use_existing_db=1 --num=10000000 --reopen_after_each_op --ops_between_duration_checks=100 --histogram=1 --report_open_timing --use_existing_keys --open_files=1 --threads=$T)

    # Extract values (Note: column positions may shift slightly depending on your RocksDB version)
    OPS=$(echo "$OUTPUT" | grep "updaterandom :" | awk '{print $5}')
    P50=$(echo "$OUTPUT" | grep "Percentiles" | awk -F' ' '{print $3}')
    P95=$(echo "$OUTPUT" | grep "Percentiles" | awk -F' ' '{print $7}')
    P99=$(echo "$OUTPUT" | grep "Percentiles" | awk -F' ' '{print $11}')
    TIME=$(echo "$OUTPUT" | grep "updaterandom :" | awk '{print $7}')
    OPEN_TIME=$(echo "$OUTPUT" | grep "updaterandom :" | awk '{print $15}')

    # Append to CSV
    echo "$T,$OPS,$P50,$P95,$P99,$TIME,$OPEN_TIME" >>"$CSV_FILE"
  done
done

echo "Done! Results saved to $CSV_FILE"
