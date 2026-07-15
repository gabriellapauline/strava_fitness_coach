#!/usr/bin/env python3
"""
Analyze Strava run history and print monthly aggregates + trend comparisons.
Reads a CSV with columns: date,distance_km,duration_sec,indoor
Prints: monthly table, 6-month window comparison, baseline vs recent, longest run per month.
No third-party packages required.
"""
import csv
import sys
from collections import defaultdict
from statistics import mean


def pace_min_per_km(sec, km):
    if km <= 0:
        return None
    return (sec / 60.0) / km


def fmt_pace(p):
    if p is None:
        return "N/A"
    mm, ss = divmod(p * 60, 60)
    return f"{int(mm)}'{int(ss):02d}\"/km"


def stats(rs, label):
    if not rs:
        print(f"\n{label}: (no runs)")
        return
    tot_km = sum(x['km'] for x in rs)
    avg_km = tot_km / len(rs)
    paces = [pace_min_per_km(x['sec'], x['km']) for x in rs]
    avg_pace = mean(paces)
    long_runs = sum(1 for x in rs if x['km'] >= 6.0)
    outdoor = [x for x in rs if x['indoor'] == 0]
    out_pace = mean([pace_min_per_km(x['sec'], x['km']) for x in outdoor]) if outdoor else None
    weeks = max(1, len(rs) / 2.5)  # rough: ~2.5 runs/wk assumption
    print(f"\n{label}:")
    print(f"  Runs: {len(rs)} | Total: {tot_km:.1f} km | Avg dist: {avg_km:.2f} km")
    print(f"  Avg pace: {fmt_pace(avg_pace)} | Long runs (>=6km): {long_runs}")
    print(f"  Outdoor runs: {len(outdoor)}" + (f" | Avg outdoor pace: {fmt_pace(out_pace)}" if out_pace else ""))


def main(path):
    runs = []
    with open(path) as f:
        for r in csv.DictReader(f):
            runs.append({
                'date': r['date'],
                'ym': r['date'][:7],
                'km': float(r['distance_km']),
                'sec': int(r['duration_sec']),
                'indoor': int(r['indoor']),
            })

    # Filter out tiny warm-up runs (<1 km) for pace quality
    real = [r for r in runs if r['km'] >= 1.0]

    by_month = defaultdict(list)
    for r in real:
        by_month[r['ym']].append(r)

    print("MONTH\t RUNS  KM_TOT  AVG_KM  PACE         INDOOR%  LONGEST")
    print("-" * 76)
    for ym in sorted(by_month):
        rs = by_month[ym]
        tot_km = sum(x['km'] for x in rs)
        avg_km = tot_km / len(rs)
        paces = [pace_min_per_km(x['sec'], x['km']) for x in rs]
        avg_pace = mean(paces)
        indoor_pct = 100.0 * sum(x['indoor'] for x in rs) / len(rs)
        longest = max(x['km'] for x in rs)
        print(f"{ym}\t {len(rs):3d}  {tot_km:6.1f}  {avg_km:5.2f}   {fmt_pace(avg_pace):10s}  {indoor_pct:4.0f}%   {longest:5.2f}")

    # 6-month window comparison
    sorted_ym = sorted(by_month)
    if len(sorted_ym) >= 6:
        recent6_ym = sorted_ym[-6:]
        first3 = sorted_ym[:3]
        print(f"\n=== 6-MONTH WINDOW ({recent6_ym[0]} to {recent6_ym[-1]}) ===")
        first_half = [r for r in real if r['ym'] in recent6_ym[:3]]
        second_half = [r for r in real if r['ym'] in recent6_ym[3:]]
        stats(first_half, f"FIRST HALF ({recent6_ym[0]}-{recent6_ym[2]})")
        stats(second_half, f"SECOND HALF ({recent6_ym[3]}-{recent6_ym[5]})")

    # Baseline vs recent
    print("\n=== BASELINE vs RECENT ===")
    baseline = [r for r in real if r['ym'] in sorted_ym[:2]]
    recent6 = [r for r in real if r['ym'] in sorted_ym[-6:]]
    stats(baseline, f"BASELINE ({sorted_ym[0]}-{sorted_ym[1]})")
    stats(recent6, f"RECENT 6 MONTHS ({sorted_ym[-6]}-{sorted_ym[-1]})")

    # Longest run per month
    print("\n=== LONGEST RUN PER MONTH ===")
    for ym in sorted(by_month):
        lr = max(by_month[ym], key=lambda x: x['km'])
        print(f"  {ym}: {lr['km']:.2f} km")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: analyze.py <csv_path>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])