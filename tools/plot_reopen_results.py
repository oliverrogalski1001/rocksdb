#!/usr/bin/env python3
"""Plot throughput (avg_ops_sec) from reopen benchmark results.

Aggregates multiple traces per worker count into mean ± std (after
dropping the lowest and highest value when there are at least 3 samples).
Requires: pip install matplotlib
"""

import argparse
import csv
import glob
import os
import statistics
import sys
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib not found. Install with: pip install matplotlib", file=sys.stderr)
    sys.exit(1)


def mean_stdev_trimmed(vals):
    """Mean and sample stdev after removing one min and one max.
    With fewer than 3 samples, uses all values (same as untrimmed stats)."""
    if len(vals) < 3:
        m = statistics.mean(vals)
        s = statistics.stdev(vals) if len(vals) > 1 else 0
        return m, s
    trimmed = sorted(vals)[1:-1]
    m = statistics.mean(trimmed)
    s = statistics.stdev(trimmed) if len(trimmed) > 1 else 0
    return m, s


def load_csv(path):
    """Load benchmark results from CSV. Groups by workers, returns (workers, data_dict)
    with trimmed mean and std for throughput."""
    by_workers = defaultdict(list)

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                w = row.get("workers") or row.get("threads")
                w = int(w)
                by_workers[w].append(float(row["avg_ops_sec"]))
            except (ValueError, KeyError) as e:
                print(f"Warning: skipping row {row}: {e}", file=sys.stderr)
                continue

    workers = sorted(by_workers.keys())
    data = {"avg_ops_sec_mean": [], "avg_ops_sec_std": []}
    for w in workers:
        vals = by_workers[w]
        mean, std = mean_stdev_trimmed(vals)
        data["avg_ops_sec_mean"].append(mean)
        data["avg_ops_sec_std"].append(std)

    return workers, data


def get_label(path):
    """Derive a short label from CSV path (e.g. 'threads' or 'processes')."""
    name = os.path.basename(path)
    if "_threads" in name:
        return "threads"
    if "_processes" in name:
        return "processes"
    return os.path.splitext(name)[0]


def plot_results(datasets, output_path=None):
    """Create throughput plot with mean ± std for one or more datasets.
    datasets: list of (workers, data, label) tuples."""
    fig, ax = plt.subplots(figsize=(5, 5))

    colors = ["#2e86ab", "#a23b72", "#28a745", "#fd7e14", "#6f42c1"]
    markers = ["o", "s", "v", "^", "D"]

    for i, (workers, data, label) in enumerate(datasets):
        ax.errorbar(
            workers,
            data["avg_ops_sec_mean"],
            yerr=data["avg_ops_sec_std"],
            fmt=f"{markers[i % len(markers)]}-",
            color=colors[i % len(colors)],
            linewidth=1.5,
            markersize=4,
            capsize=2,
            capthick=1,
            label=label,
        )

    ax.set_xlabel("Number of Workers")
    ax.set_ylabel("Throughput (ops/sec)")
    # ax.set_title("")
    ax.set_yscale("log")
    ax.legend()
    ax.grid(True, alpha=0.3, which="both")

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved plot to {output_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot reopen benchmark results")
    parser.add_argument(
        "csv",
        nargs="*",
        help="Path(s) to results CSV (default: most recent results_*_threads.csv and results_*_processes.csv)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output image path (default: show interactively)",
    )
    args = parser.parse_args()

    if args.csv:
        csv_paths = args.csv
    else:
        # Default: most recent threads and processes results
        threads = sorted(glob.glob("results_*_threads.csv"), reverse=True)
        processes = sorted(glob.glob("results_*_processes.csv"), reverse=True)
        csv_paths = []
        if threads:
            csv_paths.append(threads[0])
        if processes:
            csv_paths.append(processes[0])
        if not csv_paths:
            print("No results_*_threads.csv or results_*_processes.csv found.", file=sys.stderr)
            sys.exit(1)
        print(f"Using {csv_paths}")

    datasets = []
    for csv_path in csv_paths:
        if not os.path.exists(csv_path):
            print(f"File not found: {csv_path}", file=sys.stderr)
            continue
        workers, data = load_csv(csv_path)
        if not workers:
            print(f"No valid data in {csv_path}", file=sys.stderr)
            continue
        datasets.append((workers, data, get_label(csv_path)))

    if not datasets:
        print("No valid data to plot.", file=sys.stderr)
        sys.exit(1)

    plot_results(datasets, args.output)


if __name__ == "__main__":
    main()
