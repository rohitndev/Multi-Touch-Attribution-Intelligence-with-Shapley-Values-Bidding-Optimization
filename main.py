"""Command-line entrypoint for the Multi-Touch Attribution Intelligence platform.

Examples
--------
    # Run the full pipeline with defaults from config.yaml
    python main.py run

    # Larger simulation, skip chart rendering
    python main.py run --users 50000 --no-charts

    # Only print the attribution comparison table
    python main.py attribution
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd
from tabulate import tabulate

from src.config import OUTPUT_DIR, load_config
from src.pipeline import run_pipeline


def _print_header(title: str) -> None:
    bar = "=" * 74
    print(f"\n{bar}\n  {title}\n{bar}")


def _fmt(df: pd.DataFrame, floatfmt: str = ".4f") -> str:
    return tabulate(df, headers="keys", tablefmt="github", floatfmt=floatfmt)


def _print_environment(cfg) -> None:
    _print_header("ENVIRONMENT / INTEGRATIONS")
    rows = [
        ["BigQuery warehouse", "connected" if cfg.bigquery_enabled else "local fallback"],
        ["Groq LLM advisor", "connected" if cfg.groq_enabled else "rule-based fallback"],
        ["Google Ads API", "connected" if cfg.google_ads_enabled else "mock (dry-run)"],
        ["Meta Marketing API", "connected" if cfg.meta_enabled else "mock (dry-run)"],
        ["Apply bid changes", "LIVE" if cfg.apply_bid_changes else "dry-run"],
    ]
    print(tabulate(rows, headers=["Integration", "Status"], tablefmt="github"))


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config()
    if args.users:
        cfg.data["n_users"] = args.users

    _print_environment(cfg)
    print("\nRunning end-to-end attribution pipeline ...")
    res = run_pipeline(cfg, make_charts=not args.no_charts)

    j = res.journeys
    _print_header("DATASET SUMMARY")
    print(
        tabulate(
            [
                ["Journeys", f"{len(j):,}"],
                ["Conversions", f"{int(j['converted'].sum()):,}"],
                ["Conversion rate", f"{j['converted'].mean():.2%}"],
                ["Total revenue", f"${j.loc[j['converted'] == 1, 'revenue'].sum():,.0f}"],
                ["Warehouse backend", res.ingest_summary["backend"]],
            ],
            headers=["Metric", "Value"],
            tablefmt="github",
        )
    )

    _print_header("ATTRIBUTION MODEL COMPARISON (credit share)")
    print(_fmt(res.comparison))

    _print_header("COMPOSITE ATTRIBUTION (70% Shapley + 30% Markov)")
    print(_fmt(res.composite[["composite_share", "attributed_revenue"]],
               floatfmt=".4f"))

    opt = res.optimization
    _print_header("BUDGET OPTIMISATION (SciPy constrained)")
    print(_fmt(opt.allocation[["current_spend", "optimized_spend", "delta_pct"]],
               floatfmt=",.2f"))
    print(
        f"\n  Current predicted revenue   : ${opt.current_revenue:,.0f}"
        f"\n  Optimised predicted revenue : ${opt.optimized_revenue:,.0f}"
        f"\n  Revenue uplift              : ${opt.revenue_uplift:,.0f} "
        f"(+{opt.uplift_pct:.1%})"
    )

    _print_header("SCENARIO ANALYSIS (budget reallocation simulator)")
    print(_fmt(res.scenarios, floatfmt=",.2f"))

    plan = res.plan
    _print_header("ATTRIBUTION ADVISOR AGENT")
    print(f"LLM backend used : {plan.llm_used}")
    print(f"Promote channels : {', '.join(plan.promote)}")
    print(f"Trim channels    : {', '.join(plan.trim)}\n")
    print(plan.rationale)
    print(f"\nBid changes issued: {len(plan.bid_changes)} "
          f"(logged to {OUTPUT_DIR / 'agent_audit_log.jsonl'})")
    if plan.bid_changes:
        bc = pd.DataFrame(plan.bid_changes)[["platform", "channel", "change_pct", "mode"]]
        print(_fmt(bc.set_index("channel"), floatfmt=".2%"))

    if not args.no_charts:
        _print_header("ARTIFACTS")
        print(f"Charts and Sankey written to: {OUTPUT_DIR}")

    print("\nPipeline complete.\n")
    return 0


def cmd_attribution(args: argparse.Namespace) -> int:
    cfg = load_config()
    if args.users:
        cfg.data["n_users"] = args.users
    res = run_pipeline(cfg, make_charts=False)
    _print_header("ATTRIBUTION MODEL COMPARISON (credit share)")
    print(_fmt(res.comparison))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="attribution",
        description="Multi-Touch Attribution Intelligence — Shapley Values & "
        "Bidding Optimization",
    )
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the full end-to-end pipeline")
    run.add_argument("--users", type=int, default=None, help="number of journeys")
    run.add_argument("--no-charts", action="store_true", help="skip chart rendering")
    run.set_defaults(func=cmd_run)

    attr = sub.add_parser("attribution", help="Print the attribution comparison only")
    attr.add_argument("--users", type=int, default=None, help="number of journeys")
    attr.set_defaults(func=cmd_attribution)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
