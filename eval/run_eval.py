import json
import statistics
import time
from collections import defaultdict
from pathlib import Path
import argparse

# from datasets import load_dataset

import httpx

API = "http://127.0.0.1:8000/screen"
DATA = Path(__file__).resolve().parent.parent / "data"

# ds = load_dataset("") #For loading external dataset


#  Saving result to result.md
def append_benchmark_row(
    layer_name: str,
    asr: float,
    precision: float | None,
    median_ms: float,
    p95_ms: float,
    out_file: Path = Path("result.md"),
):
    if not out_file.exists():
        header = (
            "| Layer | Attack success | Precision | Median latency | P95 latency |\n"
            "|---|---|---|---|---|\n"
        )
        out_file.write_text(header, encoding="utf-8")

    prec_str = f"{precision:.1%}" if precision is not None else "n/a"
    row = f"| {layer_name} | {asr:.1%} | {prec_str} | {median_ms:.0f} ms | {p95_ms:.0f} ms |\n"
    with out_file.open("a", encoding="utf-8") as f:
        f.write(row)


def load(name, split=None):
    rows = []
    with open(DATA / name, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                if split is None or row.get("split") == split:
                    rows.append(row)
    return rows


def screen_all(client, rows):
    out = []
    for row in rows:  # sequential on purpose: clean latency numbers
        start = time.perf_counter()
        r = client.post(API, json={"prompt": row["prompt"]})
        ms = (time.perf_counter() - start) * 1000
        r.raise_for_status()
        out.append({**row, "verdict": r.json()["verdict"], "ms": ms})
    return out


def main(split=None, layer: str | None = None):
    with httpx.Client(timeout=30) as client:
        attacks = screen_all(client, load("adversarial.jsonl", split))
        benign = screen_all(client, load("benign.jsonl", split))
        # attacks = screen_all(client, ds)

    detected = lambda x: x["verdict"] in ("flag", "block")

    tp = sum(detected(a) for a in attacks)  # attacks caught
    fn = len(attacks) - tp  # attacks that got through
    fp = sum(detected(b) for b in benign)  # benign wrongly caught
    tn = len(benign) - fp
    asr = fn / len(attacks) if attacks else 0.0

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / len(benign) if benign else 0.0

    times = [x["ms"] for x in attacks + benign]
    sorted_times = sorted(times)
    p95_idx = (
        max(0, min(len(sorted_times) - 1, int(len(sorted_times) * 0.95) - 1))
        if sorted_times
        else 0
    )
    median_ms = statistics.median(sorted_times) if times else 0.0
    p95_ms = (
        sorted(times)[max(0, min(len(times) - 1, int(len(times) * 0.95) - 1))]
        if times
        else 0.0
    )

    print(f"Split: {split or 'all'} | attacks={len(attacks)} benign={len(benign)}")
    print(f"Attack success rate : {asr:.1%}")
    print(f"Recall (attacks caught): {recall:.1%}")
    print(f"Precision           : {precision:.1%}")
    print(f"False positive rate : {fpr:.1%}")
    print(f"Latency median      : {median_ms:.0f} ms")
    print(f"Latency p95         : {p95_ms:.0f} ms")

    print("\nAttack success rate by category:")
    by_cat = defaultdict(list)
    for a in attacks:
        by_cat[a["category"]].append(not detected(a))
    for cat, misses in sorted(by_cat.items()):
        print(f"  {cat:28s} {sum(misses)}/{len(misses)} got through")

    print("\nSample missed attacks:")
    for a in [a for a in attacks if not detected(a)][:5]:
        print(f"  [{a['category']}] {a['prompt'][:80]}")

    print("\nFalse positives:")
    for b in [b for b in benign if detected(b)][:5]:
        print(f"  [{b['category']}] {b['prompt'][:80]}")

    if layer:
        append_benchmark_row(
            layer_name=args.layer,
            asr=asr,
            precision=precision if (tp + fp) > 0 else None,
            median_ms=median_ms,
            p95_ms=p95_ms,
        )


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else None)
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="train")
    parser.add_argument(
        "--layer", default=None, help="Layer label to append to result.md"
    )
    args = parser.parse_args()
    main(split=args.split, layer=args.layer)
