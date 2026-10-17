"""Command-line interface: `complaint-router <command>`.

    complaint-router download banking77
    complaint-router train --dataset banking77 --model baseline
    complaint-router train --dataset cfpb-csv:data/complaints.csv --target product --model mlp
    complaint-router evaluate --bundle models/banking77/baseline
    complaint-router compare evals/results/*.json
    complaint-router predict --bundle models/banking77/baseline "my card has not arrived"
    complaint-router list
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from complaint_router.config import get_settings
from complaint_router.data import download_banking77, load
from complaint_router.registry import list_bundles, load_bundle, model_class, save_bundle

DEFAULT_VCPU_SECOND_USD = 0.000024  # assumption; see docs/COST-TCO.md and verify before use


def _model_kwargs(args: argparse.Namespace) -> dict:
    kwargs: dict[str, object] = {"seed": args.seed}
    if args.epochs is not None:
        kwargs["epochs"] = args.epochs
    if args.model == "transformer":
        kwargs["base_model"] = args.base_model
        kwargs["max_length"] = args.max_length
    return kwargs


def cmd_train(args: argparse.Namespace) -> int:
    from complaint_router.metrics import accuracy, macro_f1

    splits = load(args.dataset, args.data_dir, target=args.target, seed=args.seed,
                  max_per_class=args.max_per_class)
    print(f"data {splits.train.name}/{splits.train.target} {splits.train.version}: "
          f"{splits.summary()}")
    model = model_class(args.model)(**_model_kwargs(args))
    t0 = time.perf_counter()
    model.fit(splits.train.texts, splits.train.labels,
              val=(splits.val.texts, splits.val.labels))
    seconds = time.perf_counter() - t0
    pred = model.predict(splits.test.texts)
    metrics = {"test_macro_f1": round(macro_f1(splits.test.labels, pred, labels=model.labels), 4),
               "test_accuracy": round(accuracy(splits.test.labels, pred), 4)}
    name = splits.train.name if splits.train.target in {"intent"} else \
        f"{splits.train.name}-{splits.train.target}"
    out = Path(args.model_dir) / name / args.model
    save_bundle(model, out, dataset=splits.train.name, target=splits.train.target,
                dataset_version=splits.train.version, splits=splits.summary(),
                metrics={**metrics, "spec": args.dataset, "seed": args.seed,
                         "max_per_class": args.max_per_class},
                train_seconds=seconds)
    print(f"trained {args.model} in {seconds:.1f}s: test macro-F1 {metrics['test_macro_f1']}, "
          f"accuracy {metrics['test_accuracy']} -> {out}")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    from complaint_router.evaluate import full_report, write_report

    settings = get_settings()
    model, meta = load_bundle(args.bundle)
    spec = meta["metrics"].get("spec", meta["dataset"])
    splits = load(spec, args.data_dir, target=meta["target"],
                  seed=meta["metrics"].get("seed", 42),
                  max_per_class=meta["metrics"].get("max_per_class", 5000))
    report = full_report(model, meta, Path(args.bundle), splits,
                         vcpu_second_usd=args.vcpu_second_usd,
                         threshold=settings.route_threshold, margin=settings.route_margin)
    json_path, md_path = write_report(report, Path(args.out))
    q, s = report["quality"], report["serving"]
    print(f"{meta['kind']}: macro-F1 {q['macro_f1']}, accuracy {q['accuracy']}, "
          f"p50 {s['p50_ms']} ms, p95 {s['p95_ms']} ms, RSS {s['rss_mb']} MB -> {json_path}, "
          f"{md_path}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    from complaint_router.evaluate import compare

    reports = [json.loads(Path(p).read_text()) for p in args.reports]
    table = compare(reports)
    if args.out:
        Path(args.out).write_text(table)
    print(table, end="")
    return 0


def cmd_predict(args: argparse.Namespace) -> int:
    from complaint_router.routing import route

    settings = get_settings()
    model, meta = load_bundle(args.bundle)
    for text, probs in zip(args.text, model.predict_proba(args.text), strict=True):
        decision = route(probs, model.labels, settings.route_threshold, settings.route_margin)
        print(json.dumps({"text": text, **decision}))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    for b in list_bundles(Path(args.model_dir)):
        m = b.get("metrics", {})
        print(f"{b['name']:<32} {b['kind']:<12} labels {len(b['labels']):>4}  "
              f"test macro-F1 {m.get('test_macro_f1')}  {b['created_at']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    parser = argparse.ArgumentParser(prog="complaint-router", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    sub = parser.add_subparsers(dest="command", required=True)

    dl = sub.add_parser("download", help="download a dataset into --data-dir")
    dl.add_argument("name", choices=["banking77"])

    tr = sub.add_parser("train", help="train a model and save a bundle")
    tr.add_argument("--dataset", default="banking77",
                    help="banking77 | fixture | cfpb-csv:PATH | cfpb-db:URL")
    tr.add_argument("--target", default="product", choices=["product", "issue"],
                    help="label column for CFPB data (ignored for intent datasets)")
    tr.add_argument("--model", default="baseline", choices=["baseline", "mlp", "transformer"])
    tr.add_argument("--model-dir", default=settings.model_dir)
    tr.add_argument("--epochs", type=int)
    tr.add_argument("--seed", type=int, default=42)
    tr.add_argument("--max-per-class", type=int, default=5000)
    tr.add_argument("--base-model", default="distilbert-base-uncased")
    tr.add_argument("--max-length", type=int, default=64)

    ev = sub.add_parser("evaluate", help="full evaluation report for a bundle")
    ev.add_argument("--bundle", required=True)
    ev.add_argument("--out", default="evals/results")
    ev.add_argument("--vcpu-second-usd", type=float, default=DEFAULT_VCPU_SECOND_USD)

    cp = sub.add_parser("compare", help="comparison table from evaluation JSON files")
    cp.add_argument("reports", nargs="+")
    cp.add_argument("--out")

    pr = sub.add_parser("predict", help="predict and route one or more texts")
    pr.add_argument("--bundle", required=True)
    pr.add_argument("text", nargs="+")

    ls = sub.add_parser("list", help="list trained bundles")
    ls.add_argument("--model-dir", default=settings.model_dir)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "download":
        print(f"downloaded to {download_banking77(args.data_dir)}")
        return 0
    handlers = {"train": cmd_train, "evaluate": cmd_evaluate, "compare": cmd_compare,
                "predict": cmd_predict, "list": cmd_list}
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
