import pandas as pd
import matplotlib.pyplot as plt


def load_gpu_csv(filepath):
    df = pd.read_csv(filepath)

    if "elapsed_s" not in df or "power_draw_w" not in df:
        raise ValueError("CSV must contain 'elapsed_s' and 'power_draw_w' columns")

    df = df.sort_values("elapsed_s")
    return df


def plot_power(df):
    plt.figure(figsize=(10, 5))
    plt.plot(df["elapsed_s"], df["power_draw_w"])
    plt.xlabel("Time (s)")
    plt.ylabel("GPU Power (W)")
    plt.title("GPU Power Draw Over Time")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def compute_stats(df, start_sec, end_sec):
    window = df[(df["elapsed_s"] >= start_sec) & (df["elapsed_s"] <= end_sec)]

    if len(window) == 0:
        return None, None, None, 0

    avg_w = window["power_draw_w"].mean()
    min_w = window["power_draw_w"].min()
    max_w = window["power_draw_w"].max()

    return avg_w, min_w, max_w, len(window)


def print_summary(df, start_sec, end_sec, label=""):
    avg_w, min_w, max_w, count = compute_stats(df, start_sec, end_sec)

    print(f"\n{'='*60}")
    if label:
        print(f"  Window   : {label}")
    print(f"  Range    : {start_sec:.3f}s  ->  {end_sec:.3f}s  ({end_sec - start_sec:.3f}s)")

    if avg_w is None:
        print("  No samples found in this range.")
    else:
        print(f"  Samples  : {count}")
        print(f"  Min Power: {min_w:8.3f} W")
        print(f"  Avg Power: {avg_w:8.3f} W")
        print(f"  Max Power: {max_w:8.3f} W")

    print(f"{'='*60}")


def main():
    print("=" * 60)
    print("  GPU Power Timeline Analyser")
    print("=" * 60)

    while True:
        csv_path = "C:\\VTuneResults\\gpu_power.csv" #input("\nEnter path to GPU power CSV:\n> ").strip().strip('"')
        try:
            df = load_gpu_csv(csv_path)
            break
        except FileNotFoundError:
            print(f"File not found: {csv_path}")
        except Exception as e:
            print(f"Error: {e}")

    t_min = df["elapsed_s"].min()
    t_max = df["elapsed_s"].max()

    print(f"\nLoaded {len(df)} samples | {t_min:.3f}s -> {t_max:.3f}s ({t_max - t_min:.3f}s total)")

    # Plot before analysis
    plot_power(df)

    # Full-run summary
    print_summary(df, t_min, t_max, label="Full run")

    print("\nEnter time windows to analyse. Press Enter with no input to quit.")

    while True:
        print()
        start_input = input(f"Start time in seconds (0 - {t_max:.1f}, or Enter to quit): ").strip()
        if not start_input:
            print("\nDone.")
            break

        duration_input = input("Duration in seconds: ").strip()
        if not duration_input:
            print("\nDone.")
            break

        try:
            start_sec = float(start_input)
            end_sec = start_sec + float(duration_input)
        except ValueError:
            print("Invalid input — please enter numbers.")
            continue

        if float(duration_input) <= 0:
            print("Duration must be greater than 0.")
            continue

        print_summary(df, start_sec, end_sec)


if __name__ == "__main__":
    main()