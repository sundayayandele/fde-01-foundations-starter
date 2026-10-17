"""Serving measurements: latency, throughput, CPU time, memory and size on disk."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from complaint_router.models.base import Classifier


def dir_size_mb(directory: Path) -> float:
    total = sum(p.stat().st_size for p in Path(directory).rglob("*") if p.is_file())
    return round(total / 1_048_576, 2)


def latency(model: Classifier, texts: list[str], n: int = 300, warmup: int = 20) -> dict:
    """Single-text prediction latency (ms) and CPU-seconds per 1,000 predictions."""
    sample = [texts[i % len(texts)] for i in range(n + warmup)]
    for text in sample[:warmup]:
        model.predict_proba([text])
    wall: list[float] = []
    cpu0 = time.process_time()
    for text in sample[warmup:]:
        t0 = time.perf_counter()
        model.predict_proba([text])
        wall.append((time.perf_counter() - t0) * 1000)
    cpu = time.process_time() - cpu0
    arr = np.array(wall)
    return {"n": n, "p50_ms": round(float(np.percentile(arr, 50)), 3),
            "p95_ms": round(float(np.percentile(arr, 95)), 3),
            "mean_ms": round(float(arr.mean()), 3),
            "cpu_seconds_per_1k": round(cpu / n * 1000, 3)}


def batch_throughput(model: Classifier, texts: list[str], batch_size: int = 256) -> dict:
    batch = [texts[i % len(texts)] for i in range(batch_size)]
    model.predict_proba(batch)
    t0 = time.perf_counter()
    reps = 5
    for _ in range(reps):
        model.predict_proba(batch)
    seconds = (time.perf_counter() - t0) / reps
    return {"batch_size": batch_size, "texts_per_second": round(batch_size / seconds, 1)}


_RSS_PROBE = """
import json, sys, psutil
from pathlib import Path
from complaint_router.registry import model_class, read_meta
proc = psutil.Process()
start = proc.memory_info().rss
cls = model_class(read_meta(sys.argv[1])["kind"])     # imports the framework (sklearn / torch)
framework = proc.memory_info().rss
model = cls.load(Path(sys.argv[1]))
model.predict_proba(["warm up the model"])
after = proc.memory_info().rss
print(json.dumps({"rss_mb": round(after / 1048576, 1),
                  "framework_rss_mb": round((framework - start) / 1048576, 1),
                  "model_rss_mb": round((after - framework) / 1048576, 1)}))
"""


def load_memory(bundle_dir: Path) -> dict:
    """Resident memory of a fresh process after loading the bundle and predicting once,
    split into the framework import (scikit-learn or PyTorch) and the model itself."""
    env = {**os.environ, "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS", "1")}
    out = subprocess.run([sys.executable, "-c", _RSS_PROBE, str(bundle_dir)],  # noqa: S603
                         capture_output=True, text=True, check=False, env=env)
    if out.returncode != 0:
        raise RuntimeError(f"memory probe failed: {out.stderr.strip()[-500:]}")
    return json.loads(out.stdout.strip().splitlines()[-1])


def cost_per_1k(cpu_seconds_per_1k: float, vcpu_second_usd: float) -> float:
    """Compute cost of 1,000 single predictions at a stated vCPU-second price."""
    return round(cpu_seconds_per_1k * vcpu_second_usd, 6)
