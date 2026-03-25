#!/usr/bin/env python3
"""Plot stacked bar chart for time breakdown (Reopen vs Baseline).

Example data:
  Reopen:  Open 18.47%, Close 1.36%, Operations 0.07%  (total 19.90%)
  Baseline: Operations 38.40%, Open/Close 0.80%       (total 39.20%)

Usage:
  python3 tools/plot_time_breakdown.py
  python3 tools/plot_time_breakdown.py -o breakdown.png
  python3 tools/plot_time_breakdown.py --reopen-open 18.47 --reopen-close 1.36 ...
"""

import argparse
import sys

try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("matplotlib not found. Install with: pip install matplotlib", file=sys.stderr)
    sys.exit(1)


# Colors for each segment type (consistent across bars)
SEGMENT_COLORS = {
    "Open/Close": "#2e86ab",
    "Operations": "#28a745",
}


def plot_stacked(data, output_path=None):
    """Create stacked bar chart: each bar = 100%, showing Open/Close vs Operations share."""
    fig, ax = plt.subplots(figsize=(5, 5))

    labels = list(data.keys())
    segments = ["Open/Close", "Operations"]
    # Normalize each mode to 100%
    normalized = {}
    totals = {}
    for label in labels:
        total = sum(data[label].values())
        totals[label] = total
        normalized[label] = {
            seg: (data[label].get(seg, 0) / total * 100) if total > 0 else 0
            for seg in segments
        }

    x = np.arange(len(labels))
    width = 0.5
    bottom = np.zeros(len(labels))

    for seg in segments:
        values = [normalized[label][seg] for label in labels]
        color = SEGMENT_COLORS.get(seg, "#6c757d")
        bars = ax.bar(x, values, width, bottom=bottom, label=seg, color=color)
        for bar, val in zip(bars, values):
            if val < 0.01:
                continue
            # For thin segments (< 4%), put label above bar; else inside
            cx = bar.get_x() + bar.get_width() / 2
            if val < 4:
                y_pos = bar.get_y() + bar.get_height() + 0.5
                va = "bottom"
                color = "black"
            else:
                y_pos = bar.get_y() + bar.get_height() / 2
                va = "center"
                color = "white"
            fmt = f"{val:.1f}%"
            ax.text(cx, y_pos, fmt, ha="center", va=va, fontsize=9, fontweight="bold", color=color)
        bottom += np.array(values)

    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{l}" for l in labels],
        fontsize=11,
    )
    ax.set_ylabel("Share of total time (%)", fontsize=11)
    ax.set_title("UpdateRandom 4 Threads: Reopen vs Baseline", fontsize=12)
    ax.set_ylim(0, 108)  # Extra space for labels on thin segments
    ax.set_yticks(np.arange(0, 101, 20))
    ax.legend(loc="upper right")
    ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved plot to {output_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Plot stacked time breakdown (Reopen vs Baseline)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output image path (default: show interactively)",
    )
    parser.add_argument(
        "--reopen-open", type=float, default=18.47,
        help="Reopen: Open %% (default: 18.47)",
    )
    parser.add_argument(
        "--reopen-close", type=float, default=1.36,
        help="Reopen: Close %% (default: 1.36)",
    )
    parser.add_argument(
        "--reopen-ops", type=float, default=0.07,
        help="Reopen: Operations %% (default: 0.07)",
    )
    parser.add_argument(
        "--baseline-ops", type=float, default=38.40,
        help="Baseline: Operations %% (default: 38.40)",
    )
    parser.add_argument(
        "--baseline-openclose", type=float, default=0.80,
        help="Baseline: Open/Close %% (default: 0.80)",
    )
    args = parser.parse_args()

    data = {
        "Reopen": {
            "Open/Close": args.reopen_open + args.reopen_close,
            "Operations": args.reopen_ops,
        },
        "Baseline": {
            "Operations": args.baseline_ops,
            "Open/Close": args.baseline_openclose,
        },
    }

    plot_stacked(data, args.output)


if __name__ == "__main__":
    main()
