"""
UA Test v8.0 — Main execution runner.
"""
import os
import sys
import time

from . import config
from .collector import collect_results_to_git
from .domains import DOMAINS, DOMAIN_NAMES
from .http_client import call_llm
from .parsers import (
    extract_dilemma_secondpass,
    judge_refusal,
    parse_dilemma,
    parse_refusal_keyword,
)
from .passport import build_passport_from_csv
from .prompt_builder import build_dilemma_prompt


def run_model(model_id, writer, csv_file, csv_path, log_path,
              mc_runs, tier_label, done_domains):
    """Execute the v8 protocol for one model, resuming completed domains and
    publishing results to git after each domain."""
    start = time.time()

    n_refusal = len(DOMAIN_NAMES) * 2 * len(config.TEMPERATURES) * mc_runs
    n_dilemma = (len(DOMAIN_NAMES) * 2 * 2 * len(config.TEMPERATURES)
                 * mc_runs)  # ×2 orderings
    total = n_refusal + n_dilemma
    done = 0

    name = model_id.split("/")[-1]
    print(f"\n{'='*60}")
    print(f"UA TEST v8.0 — {name}")
    print(f"  Refusal:  {n_refusal} iterations")
    print(f"  Dilemma:  {n_dilemma} iterations (counterbalanced)")
    print(f"  Total:    {total} iterations")
    print(f"  Started:  {time.strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    sys.stdout.flush()

    for domain_name in DOMAIN_NAMES:
        domain = DOMAINS[domain_name]
        scenarios = domain["scenarios"]

        # Resume: skip domains already fully completed in a prior run.
        if (model_id, domain_name) in done_domains:
            print(f"\n  >> DOMAIN: {domain_name}  "
                  f"[resume: already complete, skipped]")
            sys.stdout.flush()
            continue

        print(f"\n  >> DOMAIN: {domain_name}")
        sys.stdout.flush()

        for temp in config.TEMPERATURES:
            for scenario in scenarios:
                for mc in range(mc_runs):

                    if scenario["type"] == "refusal":
                        # ─── REFUSAL SCENARIO ─────────────────────────
                        msgs = [
                            {"role": "system", "content": domain["system"]},
                            {"role": "user", "content": scenario["prompt"]},
                        ]
                        t0 = time.perf_counter()
                        try:
                            resp = call_llm(model_id, msgs, temp)
                            lat = round(time.perf_counter() - t0, 3)
                            result = parse_refusal_keyword(resp)

                            # LLM-as-judge second pass for keyword misses
                            judge_result = ""
                            if result == "OTHER":
                                jv = judge_refusal(
                                    model_id, scenario["prompt"], resp,
                                    temp=0.0)
                                judge_result = jv
                                if jv == "REFUSED":
                                    result = "REFUSED"

                            done += 1
                            writer.writerow([
                                model_id, domain_name, scenario["id"],
                                "refusal", temp, mc + 1,
                                "original", result, "",
                                judge_result, len(resp), lat,
                            ])
                            csv_file.flush()

                        except Exception as e:
                            lat = round(time.perf_counter() - t0, 3)
                            done += 1
                            writer.writerow([
                                model_id, domain_name, scenario["id"],
                                "refusal", temp, mc + 1,
                                "original", "ERROR", "",
                                str(e)[:80], 0, lat,
                            ])
                            csv_file.flush()

                    else:
                        # ─── DILEMMA SCENARIO (both orderings) ────────
                        for ordering in ("original", "reversed"):
                            prompt_text, label_map = build_dilemma_prompt(
                                scenario, ordering
                            )
                            msgs = [
                                {"role": "system", "content": domain["system"]},
                                {"role": "user", "content": prompt_text},
                            ]
                            t0 = time.perf_counter()
                            try:
                                resp = call_llm(model_id, msgs, temp)
                                lat = round(time.perf_counter() - t0, 3)
                                raw_result = parse_dilemma(resp)

                                # Thinking-model second pass
                                secondpass = ""
                                if raw_result == "OTHER":
                                    sp = extract_dilemma_secondpass(
                                        model_id, resp,
                                        scenario["num_options"], temp=0.0,
                                    )
                                    if sp != "OTHER":
                                        secondpass = f"upgraded:{sp}"
                                        raw_result = sp

                                # Map back to original content keys
                                mapped_result = label_map.get(
                                    raw_result, raw_result)

                                done += 1
                                writer.writerow([
                                    model_id, domain_name, scenario["id"],
                                    "dilemma", temp, mc + 1,
                                    ordering, mapped_result, raw_result,
                                    secondpass, len(resp), lat,
                                ])
                                csv_file.flush()

                            except Exception as e:
                                lat = round(time.perf_counter() - t0, 3)
                                done += 1
                                writer.writerow([
                                    model_id, domain_name, scenario["id"],
                                    "dilemma", temp, mc + 1,
                                    ordering, "ERROR", "",
                                    str(e)[:80], 0, lat,
                                ])
                                csv_file.flush()

                    # Progress reporting
                    if done % 10 == 0 or done == total:
                        elapsed = (time.time() - start) / 60
                        pct = done / total * 100
                        print(
                            f"    [{done:5d}/{total}] ({pct:5.1f}%) "
                            f"{elapsed:5.1f}min — {domain_name} T={temp:.1f}",
                            flush=True,
                        )

        # ── Publish this domain's results to git (resume checkpoint) ──────
        csv_file.flush()
        os.fsync(csv_file.fileno())
        print(f"  [domain done] {domain_name} — publishing results to git")
        sys.stdout.flush()
        collect_results_to_git(tier_label, csv_path, log_path,
                               note=f"{name}/{domain_name}")

    # ─── Build Behavioral Passport (computed from CSV — resume-safe) ────────
    elapsed_min = (time.time() - start) / 60
    passport = build_passport_from_csv(
        model_id, csv_path, mc_runs, elapsed_min, tier_label
    )

    import json
    out_path = config.PASSPORT_DIR / f"{model_id.replace('/', '_')}_v8_passport.json"
    out_path.write_text(json.dumps(passport, indent=2, ensure_ascii=False))

    do = passport["dilemma_original_order"]
    dr = passport["dilemma_reversed_order"]
    ot = sum(do.values())
    rt = sum(dr.values())
    orig_a_pct = do.get("OPTION_A", 0) / ot * 100 if ot else 0
    rev_a_pct = dr.get("OPTION_A", 0) / rt * 100 if rt else 0

    print(f"\n{'─'*60}")
    print(f"  BEHAVIORAL PASSPORT — {passport['model_short']}")
    print(f"{'─'*60}")
    print(f"  Refusal:           {passport['refusal_aggregate_pct']:.1f}%  "
          f"(min: {passport['refusal_min_domain_name']} "
          f"{passport['refusal_min_domain_pct']:.1f}%)")
    print(f"  Dilemma OTHER:     {passport['dilemma_other_pct']:.1f}%")
    print(f"  OPTION_A original: {orig_a_pct:.1f}%")
    print(f"  OPTION_A reversed: {rev_a_pct:.1f}%")
    print(f"  Position bias:     {passport['position_bias_coefficient_pp']:.1f} pp")
    print(f"  Judge upgrades:    {passport['refusal_judge_upgrades']}")
    print(f"  Certification:     {passport['certification_tier']}")
    for r in passport["certification_blockers"]:
        print(f"    blocker: {r}")
    print(f"  Runtime:           {elapsed_min:.1f} min")
    print(f"  Passport:          {out_path}")
    print(f"{'─'*60}")
    sys.stdout.flush()

    return passport
