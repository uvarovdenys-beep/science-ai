#!/usr/bin/env python3
"""
UA Test v8.0 — Orchestrator

This script initializes the environment and orchestrates the modular components
of the UA v8 protocol (located in the `ua_v8/` package).
"""
import argparse
import csv
import os
import sys
import time

from ua_v8 import config
from ua_v8.collector import collect_results_to_git
from ua_v8.domains import DOMAIN_NAMES, DOMAINS
from ua_v8.model_manager import get_all_models, switch_model
from ua_v8.passport import scan_progress
from ua_v8.runner import run_model
from ua_v8.tee_logger import TeeLogger


def main():
    parser = argparse.ArgumentParser(description="UA Test v8.0")
    parser.add_argument(
        "--tier",
        choices=config.TIERS.keys(),
        default="standard",
        help="Evaluation tier: screening (3 MC), standard (10 MC), certification (30 MC)",
    )
    args = parser.parse_args()

    tier_cfg = config.TIERS[args.tier]
    mc_runs = tier_cfg["mc_runs"]

    log_path = config.REPORT_DIR / f"ua_v8_{args.tier}.log"
    csv_path = config.REPORT_DIR / f"ua_v8_{args.tier}_results.csv"
    sys.stdout = TeeLogger(log_path)

    n_ref_per_model = len(DOMAIN_NAMES) * 2 * len(config.TEMPERATURES) * mc_runs
    n_dil_per_model = len(DOMAIN_NAMES) * 2 * 2 * len(config.TEMPERATURES) * mc_runs
    n_per_model = n_ref_per_model + n_dil_per_model

    print("=" * 60)
    print(f"UA TEST v8.0 — {tier_cfg['label']} Tier")
    print(f"{len(DOMAIN_NAMES)} Domains | 4 Scenarios | {len(config.TEMPERATURES)} Temps | {mc_runs} MC runs")
    print(f"  Refusal per model:  {n_ref_per_model}")
    print(f"  Dilemma per model:  {n_dil_per_model} (counterbalanced x2)")
    print(f"  Total per model:    {n_per_model}")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    sys.stdout.flush()

    try:
        models = get_all_models()
    except Exception as e:
        print(f"\nCANNOT REACH LM STUDIO: {e}")
        sys.exit(1)

    print(f"Found {len(models)} models: {models}\n")
    sys.stdout.flush()

    all_passports = []

    # Resume: scan existing CSV to find fully completed (model, domain) pairs.
    done_domains = scan_progress(csv_path, mc_runs)

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if csv_path.stat().st_size == 0:
            writer.writerow(config.CSV_HEADER)
            print(f"CSV header written: {csv_path}")

        f.flush()
        os.fsync(f.fileno())
        sys.stdout.flush()

        for model_id in models:
            if not switch_model(model_id):
                print(f"  SKIPPED: {model_id}")
                continue
            passport = run_model(
                model_id, writer, f, csv_path, log_path,
                mc_runs, tier_cfg["label"], done_domains
            )
            all_passports.append(passport)
            f.flush()
            os.fsync(f.fileno())

    # ── Final comparison ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"UA TEST v8.0 — FINAL COMPARISON ({tier_cfg['label']} Tier)")
    print(f"{'='*70}")
    print(f"{'Model':<28} {'Ref%':>6} {'MinD%':>6} {'MinDomain':<18} "
          f"{'Bias':>6} {'Cert':<8}")
    print("-" * 70)
    for p in all_passports:
        print(f"{p['model_short']:<28} "
              f"{p['refusal_aggregate_pct']:>5.1f}% "
              f"{p['refusal_min_domain_pct']:>5.1f}% "
              f"{p['refusal_min_domain_name']:<18} "
              f"{p['position_bias_coefficient_pp']:>5.1f} "
              f"{p['certification_tier']:<8}")
    print("=" * 70)
    print(f"\nFull data: {csv_path}")
    print(f"Passports: {config.PASSPORT_DIR}/")
    print(f"Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    sys.stdout.flush()

    # ── Auto-collect results into git ──────────────────────────────────────
    print(f"\n{'='*60}\n[AUTO-COLLECT] gathering results into git")
    collect_results_to_git(tier_cfg["label"], csv_path, log_path, note="FINAL")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
