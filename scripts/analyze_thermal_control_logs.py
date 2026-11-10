#!/usr/bin/env python3
"""Read-only SBC5 cooling log statistics (no fan/AI/model changes).

Usage: python scripts/analyze_thermal_control_logs.py sbc5.log
       python scripts/analyze_thermal_control_logs.py sbc5.log --json

Notes:
- Uses only logged snapshots. Does NOT reconstruct missing 10 s AI cycles.
- Predictor F30/F60/F120 are forecasts, not observed temperatures.
- Does NOT claim a forecast MAE from unmatched timestamps.
- Comparisons across unequal workload/sampling must be interpreted carefully.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re
import statistics
from typing import Any

TIMESTAMP = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s*(.+)$")
NUM = r"([-+]?(?:\d+(?:\.\d*)?|\.\d+))"


def number(line: str, key: str) -> float | None:
    m = re.search(r"(?<![A-Za-z_])" + re.escape(key) + r"=" + NUM, line)
    if not m:
        return None
    return float(m.group(1))


def string(line: str, key: str) -> str | None:
    m = re.search(r"(?<![A-Za-z_])" + re.escape(key) + r"=([A-Za-z_][\w.-]*)", line)
    return m.group(1) if m else None


def rounded(value: float | None, places: int = 3) -> float | None:
    return round(value, places) if value is not None else None


def analyze(lines: Any) -> dict[str, Any]:
    thermal: list[dict[str, Any]] = []
    actuator: list[dict[str, Any]] = []
    ai: list[dict[str, Any]] = []
    for line in lines:
        match = TIMESTAMP.match(line.strip())
        if not match:
            continue
        timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        message = match.group(2)
        if message.startswith("Thermal Predictor:"):
            gate_match = re.search(r"(?<![A-Za-z_])gate=([A-Za-z_]+)(?:/([A-Za-z_]+))?", message)
            gate = gate_match.group(1) if gate_match else None
            gate_reason = gate_match.group(2) if gate_match else None
            thermal.append({
                "time": timestamp,
                "confidence": number(message, "confidence"),
                "mae": number(message, "MAE_avg"),
                "f30": number(message, "F30"),
                "f60": number(message, "F60"),
                "f120": number(message, "F120"),
                "weighted": number(message, "weighted"),
                "gate": gate,
                "reason": gate_reason,
                "tp_applied": number(message, "TP_applied"),
            })
        elif message.startswith("Adaptive PWM:"):
            actuator.append({
                "time": timestamp,
                "temp_raw": number(message, "T_raw"),
                "temp_control": number(message, "T_control"),
                "target": number(message, "target"),
                "pwm": number(message, "applied"),
            })
        elif message.startswith("AI Cooling:"):
            ai.append({
                "time": timestamp,
                "bucket": string(message, "bucket"),
                "observations": number(message, "observations_total"),
                "qualified": number(message, "qualified_samples_total"),
            })
    for arr in (thermal, actuator, ai):
        arr.sort(key=lambda x: x["time"])
    result: dict[str, Any] = {
        "source": "SBC5 log snapshots",
        "limitations": [
            "Sparse Thermal Predictor logs cannot reconstruct all 10-second control decisions.",
            "F30/F60/F120 are forecasts, not independently verified temperatures.",
            "Temperature/PWM averages are sample-based, not time-weighted.",
        ],
        "thermal_samples": len(thermal),
        "actuator_samples": len(actuator),
        "ai_samples": len(ai),
    }
    times = [x["time"] for arr in (thermal, actuator, ai) for x in arr]
    if times:
        result["first_timestamp"] = min(times).isoformat(sep=" ")
        result["last_timestamp"] = max(times).isoformat(sep=" ")
    if thermal:
        valid_gates = [x["gate"] for x in thermal if x["gate"]]
        confidence = [x["confidence"] for x in thermal if x["confidence"] is not None]
        maes = [x["mae"] for x in thermal if x["mae"] is not None]
        result["thermal"] = {
            "gate_snapshots": dict(Counter(valid_gates)),
            "gate_changes_between_snapshots": sum(a != b for a, b in zip(valid_gates, valid_gates[1:])),
            "confidence_min": rounded(min(confidence) if confidence else None),
            "confidence_max": rounded(max(confidence) if confidence else None),
            "reported_mae_median_c": rounded(statistics.median(maes) if maes else None),
            "tp_applied_snapshot_sum_pp": rounded(sum(x["tp_applied"] for x in thermal if x["tp_applied"] is not None)),
        }
        for horizon in ("f30", "f60", "f120"):
            values = [x[horizon] for x in thermal if x[horizon] is not None]
            steps = [abs(b-a) for a,b in zip(values, values[1:])]
            result["thermal"][f"{horizon}_largest_logged_jump_c"] = rounded(max(steps) if steps else None)
    if actuator:
        temp = [abs(x["temp_raw"]-x["target"]) for x in actuator
                if x["temp_raw"] is not None and x["target"] is not None]
        pwms = [x["pwm"] for x in actuator if x["pwm"] is not None]
        gaps = [(b["time"]-a["time"]).total_seconds() for a,b in zip(actuator, actuator[1:])]
        gaps = [x for x in gaps if x > 0]
        result["actuator"] = {
            "sample_mean_abs_temp_error_c": rounded(statistics.mean(temp) if temp else None),
            "sample_max_abs_temp_error_c": rounded(max(temp) if temp else None),
            "pwm_min_percent": rounded(min(pwms) if pwms else None),
            "pwm_max_percent": rounded(max(pwms) if pwms else None),
            "pwm_sum_abs_sample_steps_pp": rounded(
                sum(abs(b-a) for a,b in zip(pwms, pwms[1:])) if len(pwms)>1 else None
            ),
            "median_sample_gap_s": rounded(statistics.median(gaps) if gaps else None),
        }
    if ai:
        bucket = [x["bucket"] for x in ai if x["bucket"]]
        result["ai"] = {"bucket_snapshots": dict(Counter(bucket))}
        start, end = ai[0], ai[-1]
        if all(x[k] is not None for x in (start, end) for k in ("observations", "qualified")):
            result["ai"]["observations_delta"] = int(end["observations"]-start["observations"])
            result["ai"]["qualified_delta"] = int(end["qualified"]-start["qualified"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile", type=Path, help="Existing exported SBC5 application log")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    with args.logfile.open("r", encoding="utf-8", errors="replace") as handle:
        result = analyze(handle)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("SBC5 READ-ONLY LOG AUDIT")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
