"""
SoC Watch Power Timeline Analyser
===================================
Computes time-weighted average Package Power for any time window
from a SoC Watch *_trace.csv file (generated with: socwatch -r int ...).
"""


def parse_trace_csv(filepath):
    samples = []
    in_section = False

    with open(filepath, encoding='utf-8', errors='replace') as f:
        for line in f:
            stripped = line.strip()

            if 'Package Power' in stripped and 'Instantaneous rate' in stripped:
                in_section = True
                continue

            if in_section:
                if stripped.startswith('Sample #'):
                    continue
                if not stripped or stripped.startswith('=') or stripped.startswith('-'):
                    if samples:
                        break
                    continue

                parts = [p.strip() for p in stripped.split(',')]
                if len(parts) < 4:
                    break
                try:
                    time_usec   = float(parts[1])
                    duration_ms = float(parts[2])
                    power_mw    = float(parts[3])
                    samples.append((time_usec / 1e6, duration_ms / 1e3, power_mw))
                except ValueError:
                    break

    return samples


def compute_stats(samples, start_sec, end_sec):
    total_energy     = 0.0
    total_time       = 0.0
    powers_in_window = []

    for t_sec, dur_sec, power_mw in samples:
        sample_start = t_sec - dur_sec
        sample_end   = t_sec
        overlap = min(sample_end, end_sec) - max(sample_start, start_sec)
        if overlap > 0:
            total_energy += power_mw * overlap
            total_time   += overlap
            powers_in_window.append(power_mw)

    if total_time == 0 or not powers_in_window:
        return None, None, None, 0

    avg_mw = total_energy / total_time
    return avg_mw, min(powers_in_window), max(powers_in_window), len(powers_in_window)


def print_summary(samples, start_sec, end_sec, label=""):
    avg_mw, min_mw, max_mw, count = compute_stats(samples, start_sec, end_sec)

    print(f"\n{'='*60}")
    if label:
        print(f"  Window   : {label}")
    print(f"  Range    : {start_sec:.3f}s  ->  {end_sec:.3f}s  ({end_sec - start_sec:.3f}s)")

    if avg_mw is None:
        print(f"  No samples found in this range.")
    else:
        print(f"  Samples  : {count}")
        print(f"  Min Power:  {min_mw:>10.2f} mW  =  {min_mw/1000:.3f} W")
        print(f"  Avg Power:  {avg_mw:>10.2f} mW  =  {avg_mw/1000:.3f} W")
        print(f"  Max Power:  {max_mw:>10.2f} mW  =  {max_mw/1000:.3f} W")
    print(f"{'='*60}")


def main():
    print("=" * 60)
    print("  SoC Watch Power Timeline Analyser")
    print("=" * 60)

    # Get CSV path
    while True:
        csv_path = "C:\VTuneResults\power_run1_timeline_trace.csv"#input("\nEnter path to *_trace.csv file:\n> ").strip().strip('"')
        try:
            samples = parse_trace_csv(csv_path)
            if not samples:
                print("  ERROR: No 'Package Power : Instantaneous rate' data found.")
                print("  Make sure the CSV was generated with:  -r int")
                continue
            break
        except FileNotFoundError:
            print(f"  File not found: {csv_path}")

    t_min = samples[0][0]
    t_max = samples[-1][0]
    print(f"\n  Loaded {len(samples)} samples  |  {t_min:.3f}s -> {t_max:.3f}s  ({t_max - t_min:.3f}s total)")

    # Show full-run summary immediately
    print_summary(samples, t_min, t_max, label="Full run")

    # Interactive window loop
    print("\nEnter time windows to analyse. Press Enter with no input to quit.")
    while True:
        print()
        start_input = input(f"  Start time in seconds (0 - {t_max:.1f}, or Enter to quit): ").strip()
        if not start_input:
            print("\nDone.")
            break

        duration_input = input(f"  Duration in seconds: ").strip()
        if not duration_input:
            print("\nDone.")
            break

        try:
            start_sec = float(start_input)
            end_sec   = start_sec + float(duration_input)
        except ValueError:
            print("  Invalid input — please enter numbers.")
            continue

        if float(duration_input) <= 0:
            print("  Duration must be greater than 0.")
            continue

        if start_sec < 0 or end_sec > t_max + 1:
            print(f"  Warning: range extends outside collected data ({t_min:.3f}s - {t_max:.3f}s).")

        print_summary(samples, start_sec, end_sec)


if __name__ == '__main__':
    main()