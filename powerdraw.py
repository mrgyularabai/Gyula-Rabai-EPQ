import subprocess
import time
import sys
import argparse
import statistics
from datetime import datetime


def get_gpu_power() -> list[dict]:
    """Query nvidia-smi for current power draw on all GPUs."""
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,power.draw,power.limit,temperature.gpu,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"nvidia-smi failed: {result.stderr.strip()}")

    gpus = []
    for line in result.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        gpus.append(
            {
                "index":       int(parts[0]),
                "name":        parts[1],
                "power_draw":  float(parts[2]) if parts[2] != "[N/A]" else None,
                "power_limit": float(parts[3]) if parts[3] != "[N/A]" else None,
                "temperature": float(parts[4]) if parts[4] != "[N/A]" else None,
                "utilization": float(parts[5]) if parts[5] != "[N/A]" else None,
            }
        )
    return gpus


def format_row(elapsed: float, gpus: list[dict]) -> str:
    """Format a single data row for console output."""
    parts = [f"{elapsed:7.2f}s"]
    for g in gpus:
        pw = f"{g['power_draw']:6.1f}W" if g["power_draw"] is not None else "   N/A "
        ut = f"{g['utilization']:3.0f}%" if g["utilization"] is not None else " N/A"
        tp = f"{g['temperature']:3.0f}°C" if g["temperature"] is not None else "N/A"
        parts.append(f"  GPU{g['index']}: {pw}  util={ut}  temp={tp}")
    return "  |".join(parts)


def print_summary(history: list[tuple[float, list[dict]]], gpu_names: list[str]) -> None:
    """Print per-GPU power draw statistics."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    num_gpus = len(gpu_names)
    for idx in range(num_gpus):
        samples = [
            entry[1][idx]["power_draw"]
            for entry in history
            if entry[1][idx]["power_draw"] is not None
        ]

        if not samples:
            print(f"\nGPU {idx} ({gpu_names[idx]}): no data")
            continue

        print(f"\nGPU {idx} — {gpu_names[idx]}")
        print(f"  Samples   : {len(samples)}")
        print(f"  Min power : {min(samples):.1f} W")
        print(f"  Max power : {max(samples):.1f} W")
        print(f"  Avg power : {statistics.mean(samples):.1f} W")
        print(f"  Std dev   : {statistics.stdev(samples):.2f} W" if len(samples) > 1 else "  Std dev   : N/A")

        # Energy estimate (Wh)
        duration_h = (history[-1][0] - history[0][0]) / 3600
        energy_wh = statistics.mean(samples) * duration_h
        print(f"  Energy    : {energy_wh * 1000:.2f} mWh  ({duration_h * 3600:.1f}s)")


def monitor(duration_seconds: float, interval: float = 0.25, quiet: bool = False) -> None:
    """Main monitoring loop."""
    print(f"Monitoring GPU power draw for {duration_seconds}s "
          f"at {interval}s intervals (press Ctrl+C to stop early)\n")

    # Validate nvidia-smi is available
    try:
        initial = get_gpu_power()
    except FileNotFoundError:
        print("ERROR: 'nvidia-smi' not found. Is the NVIDIA driver installed?", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    gpu_names = [g["name"] for g in initial]
    num_gpus  = len(gpu_names)

    # Print header
    if not quiet:
        header = f"{'Elapsed':>8}  "
        for i, name in enumerate(gpu_names):
            header += f"  GPU{i} ({name[:20]})"
        print(header)
        print("-" * max(60, len(header)))

    history: list[tuple[float, list[dict]]] = []
    start = time.monotonic()
    next_tick = start

    try:
        while True:
            now = time.monotonic()
            elapsed = now - start

            if elapsed > duration_seconds:
                break

            gpus = get_gpu_power()
            history.append((elapsed, gpus))

            if not quiet:
                print(format_row(elapsed, gpus))

            # Sleep until the next scheduled tick (drift-corrected)
            next_tick += interval
            sleep_for = next_tick - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)

    except KeyboardInterrupt:
        print("\n[Interrupted by user]")

    print_summary(history, gpu_names)

    # Optionally save CSV
    csv_path = f"C:\\VTuneResults\\gpu_power.csv"
    with open(csv_path, "w") as f:
        f.write("elapsed_s,gpu_index,gpu_name,power_draw_w,power_limit_w,temperature_c,utilization_pct\n")
        for elapsed, gpus in history:
            for g in gpus:
                f.write(
                    f"{elapsed:.4f},{g['index']},{g['name']},"
                    f"{g['power_draw'] or ''},"
                    f"{g['power_limit'] or ''},"
                    f"{g['temperature'] or ''},"
                    f"{g['utilization'] or ''}\n"
                )
    print(f"\nData saved to: {csv_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor NVIDIA GPU power draw via nvidia-smi."
    )
    parser.add_argument(
        "duration",
        type=float,
        help="How many seconds to monitor (e.g. 30 or 120.5)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.25,
        help="Sampling interval in seconds (default: 0.25)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-sample output; only print summary",
    )
    args = parser.parse_args()

    if args.duration <= 0:
        parser.error("duration must be positive")
    if args.interval <= 0:
        parser.error("interval must be positive")

    monitor(args.duration, interval=args.interval, quiet=args.quiet)


if __name__ == "__main__":
    main()