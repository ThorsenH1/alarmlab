"""Small explicit CLI. Default experiments require no network or credentials."""

import argparse
from pathlib import Path

from .benchmark import download_archive, extract_features, run_benchmark
from .config import Config
from .experiment import run_experiment


def main():
    parser = argparse.ArgumentParser(prog="alarmlab")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["all", "simulate", "benchmark", "report"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--output", type=Path, default=Path("artifacts"))
        cmd.add_argument("--demo", type=Path, default=Path("demo"))
        cmd.add_argument("--config", type=Path, default=Path("configs/default.json"))
        cmd.add_argument("--features", type=Path, default=Path("data/external/uci447_features.csv.gz"))
    extract = sub.add_parser("extract-uci")
    extract.add_argument("--archive", type=Path, required=True)
    extract.add_argument("--output", type=Path, default=Path("data/external"))
    fetch = sub.add_parser("download-uci")
    fetch.add_argument("--output", type=Path, default=Path("data/raw/uci447.zip"))
    args = parser.parse_args()
    if args.command == "download-uci":
        print(download_archive(args.output))
        return
    if args.command == "extract-uci":
        print(extract_features(args.archive, args.output))
        return
    cfg = Config.read(args.config)
    if args.command in {"all", "simulate"}:
        run_experiment(cfg, args.output)
    if args.command in {"all", "benchmark"}:
        run_benchmark(args.features, args.output, cfg.seed)
        print("Real-data benchmark complete.", flush=True)
    if args.command in {"all", "report"}:
        from .reporting import build_reports, build_demo
        build_reports(args.output)
        build_demo(args.output, args.demo)
        print(f"Open {args.demo.resolve() / 'index.html'}", flush=True)
