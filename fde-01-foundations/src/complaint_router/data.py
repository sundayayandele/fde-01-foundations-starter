"""Datasets: loaders, stratified splits and leakage checks.

Every loader returns a `Dataset`: parallel lists of texts and labels plus provenance
(name, target, version). Data is downloaded at run time into `data/` and never committed.

Sources
- banking77: PolyAI Banking77 (CC BY 4.0), pinned to a Git commit and checked by SHA-256.
- cfpb-csv:  the CFPB bulk CSV (or a sample of it) with consumer narratives.
- cfpb-db:   the `complaints` table written by fde-00-programming (SQLite or Postgres).
- fixture:   a small generated intent set for tests and offline labs.
"""

from __future__ import annotations

import csv
import hashlib
import random
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from complaint_router.text import normalise

BANKING77_COMMIT = "57ec275d8078af65b7731c2a98be812d844a6d6b"
BANKING77_BASE = (
    "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/"
    f"{BANKING77_COMMIT}/banking_data"
)
BANKING77_SHA256 = {
    "train.csv": "b06e26ac675513959a63135f11b94ea7786ed02da65db93a5650d8838cbc664b",
    "test.csv": "d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d",
}

CFPB_TEXT = "Consumer complaint narrative"
CFPB_TARGETS = {"product": "Product", "issue": "Issue"}


@dataclass
class Dataset:
    """Texts and labels with provenance."""

    name: str
    target: str
    texts: list[str]
    labels: list[str]
    version: str = ""
    notes: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.texts) != len(self.labels):
            raise ValueError("texts and labels must have the same length")

    def __len__(self) -> int:
        return len(self.texts)

    @property
    def label_names(self) -> list[str]:
        return sorted(set(self.labels))

    def subset(self, idx: Iterable[int], suffix: str) -> Dataset:
        idx = list(idx)
        return Dataset(self.name, self.target, [self.texts[i] for i in idx],
                       [self.labels[i] for i in idx], self.version,
                       {**self.notes, "split": suffix})


@dataclass
class Splits:
    train: Dataset
    val: Dataset
    test: Dataset

    def summary(self) -> dict[str, int]:
        return {"train": len(self.train), "val": len(self.val), "test": len(self.test),
                "classes": len(self.train.label_names)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---- splitting and leakage -------------------------------------------------------------

def stratified_split(labels: list[str], fractions: tuple[float, ...],
                     seed: int = 42) -> list[list[int]]:
    """Split indices into len(fractions) parts, keeping each label's share in every part.

    Fractions must sum to 1. Within each label the order is shuffled with `seed`, and each
    part gets round(fraction * n_label) items; the last part takes the remainder. Every
    index appears in exactly one part.
    """
    if abs(sum(fractions) - 1.0) > 1e-9:
        raise ValueError("fractions must sum to 1")
    # >>> SOLUTION: week-05 stratified split
    by_label: dict[str, list[int]] = defaultdict(list)
    for i, label in enumerate(labels):
        by_label[label].append(i)
    rng = random.Random(seed)
    parts: list[list[int]] = [[] for _ in fractions]
    for label in sorted(by_label):
        idx = by_label[label]
        rng.shuffle(idx)
        start = 0
        for p, frac in enumerate(fractions):
            if p == len(fractions) - 1:
                take = idx[start:]
            else:
                take = idx[start:start + round(frac * len(idx))]
            parts[p].extend(take)
            start += len(take)
    return [sorted(p) for p in parts]
    # <<< SOLUTION


def find_leakage(train_texts: list[str], other_texts: list[str]) -> list[int]:
    """Indices in `other_texts` whose normalised text also appears in `train_texts`.

    Exact duplicates across splits inflate test scores; report them and remove them.
    """
    # >>> SOLUTION: week-05 leakage check
    seen = {normalise(t) for t in train_texts}
    return [i for i, t in enumerate(other_texts) if normalise(t) in seen]
    # <<< SOLUTION


def drop_indices(ds: Dataset, idx: Iterable[int]) -> Dataset:
    drop = set(idx)
    keep = [i for i in range(len(ds)) if i not in drop]
    out = ds.subset(keep, str(ds.notes.get("split", "")))
    out.notes["removed_duplicates"] = len(drop)
    return out


def make_splits(ds: Dataset, *, test: Dataset | None = None, val_frac: float = 0.1,
                test_frac: float = 0.1, seed: int = 42) -> Splits:
    """Train/val/test splits. If the source ships a test set, carve only val from train.

    Validation and test rows that duplicate a training text are removed (leakage).
    """
    if test is None:
        tr, va, te = stratified_split(ds.labels, (1 - val_frac - test_frac, val_frac, test_frac),
                                      seed)
        train, val, test_ds = ds.subset(tr, "train"), ds.subset(va, "val"), ds.subset(te, "test")
    else:
        tr, va = stratified_split(ds.labels, (1 - val_frac, val_frac), seed)
        train, val = ds.subset(tr, "train"), ds.subset(va, "val")
        test_ds = test.subset(range(len(test)), "test")
    val = drop_indices(val, find_leakage(train.texts, val.texts))
    test_ds = drop_indices(test_ds, find_leakage(train.texts, test_ds.texts))
    known = set(train.labels)
    test_ds = test_ds.subset([i for i, y in enumerate(test_ds.labels) if y in known], "test")
    val = val.subset([i for i, y in enumerate(val.labels) if y in known], "val")
    return Splits(train, val, test_ds)


# ---- loaders ----------------------------------------------------------------------------

def _read_csv(path: Path, text_col: str, label_col: str) -> tuple[list[str], list[str]]:
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    texts, labels = [], []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            text = (row.get(text_col) or "").strip()
            label = (row.get(label_col) or "").strip()
            if text and label:
                texts.append(text)
                labels.append(label)
    return texts, labels


def download_banking77(data_dir: Path, client: httpx.Client | None = None) -> Path:
    """Download the pinned Banking77 CSVs into data_dir/banking77 and verify checksums."""
    out = Path(data_dir) / "banking77"
    out.mkdir(parents=True, exist_ok=True)
    http = client or httpx.Client(timeout=60, follow_redirects=True)
    try:
        for name, expected in BANKING77_SHA256.items():
            path = out / name
            if path.exists() and sha256_file(path) == expected:
                continue
            response = http.get(f"{BANKING77_BASE}/{name}")
            response.raise_for_status()
            path.write_bytes(response.content)
            actual = sha256_file(path)
            if actual != expected:
                path.unlink()
                raise ValueError(f"{name}: checksum {actual} does not match pinned {expected}")
    finally:
        if client is None:
            http.close()
    return out


def load_banking77(data_dir: Path, *, download: bool = True) -> tuple[Dataset, Dataset]:
    """Return (train, test) for Banking77's 77 intents."""
    folder = Path(data_dir) / "banking77"
    if download and not all((folder / n).exists() for n in BANKING77_SHA256):
        download_banking77(data_dir)
    parts = []
    for name in ("train.csv", "test.csv"):
        texts, labels = _read_csv(folder / name, "text", "category")
        parts.append(Dataset("banking77", "intent", texts, labels,
                             version=f"git:{BANKING77_COMMIT[:12]}",
                             notes={"sha256": BANKING77_SHA256[name]}))
    return parts[0], parts[1]


def _filter_classes(texts: list[str], labels: list[str], min_count: int,
                    max_per_class: int | None, seed: int) -> tuple[list[str], list[str]]:
    counts = Counter(labels)
    keep = {label for label, n in counts.items() if n >= min_count}
    by_label: dict[str, list[int]] = defaultdict(list)
    for i, label in enumerate(labels):
        if label in keep:
            by_label[label].append(i)
    rng = random.Random(seed)
    chosen: list[int] = []
    for label in sorted(by_label):
        idx = by_label[label]
        if max_per_class and len(idx) > max_per_class:
            idx = rng.sample(idx, max_per_class)
        chosen.extend(idx)
    chosen.sort()
    return [texts[i] for i in chosen], [labels[i] for i in chosen]


def load_cfpb_csv(path: Path, *, target: str = "product", min_count: int = 50,
                  max_per_class: int | None = 5000, seed: int = 42) -> Dataset:
    """Complaints with a narrative from the CFPB bulk CSV; label = product or issue."""
    if target not in CFPB_TARGETS:
        raise ValueError(f"target must be one of {sorted(CFPB_TARGETS)}")
    path = Path(path)
    texts, labels = _read_csv(path, CFPB_TEXT, CFPB_TARGETS[target])
    texts, labels = _filter_classes(texts, labels, min_count, max_per_class, seed)
    return Dataset("cfpb", target, texts, labels, version=f"sha256:{sha256_file(path)[:12]}",
                   notes={"source": str(path), "min_count": min_count,
                          "max_per_class": max_per_class})


def load_cfpb_db(url: str, *, target: str = "product", min_count: int = 50,
                 max_per_class: int | None = 5000, seed: int = 42) -> Dataset:
    """Complaints with a narrative from fde-00-programming's `complaints` table."""
    if target not in CFPB_TARGETS:
        raise ValueError(f"target must be one of {sorted(CFPB_TARGETS)}")
    from sqlalchemy import create_engine, text  # optional dependency: pip install .[db]

    engine = create_engine(url)
    query = text(f"SELECT narrative, {target} FROM complaints "  # noqa: S608 - target allow-listed
                 f"WHERE narrative IS NOT NULL AND {target} IS NOT NULL ORDER BY complaint_id")
    with engine.connect() as conn:
        rows = conn.execute(query).all()
    engine.dispose()
    texts = [r[0] for r in rows]
    labels = [r[1] for r in rows]
    texts, labels = _filter_classes(texts, labels, min_count, max_per_class, seed)
    return Dataset("cfpb", target, texts, labels, version=f"db:{len(rows)}rows",
                   notes={"min_count": min_count, "max_per_class": max_per_class})


FIXTURE_INTENTS = {
    "card_arrival": ["when will my {card} arrive", "my {card} has not arrived yet",
                     "still waiting for my new {card}", "how long until my {card} is delivered"],
    "lost_card": ["i lost my {card}", "my {card} was stolen", "i can't find my {card} anywhere",
                  "someone took my {card} please block it"],
    "transfer_failed": ["my {transfer} failed", "why did my {transfer} not go through",
                        "the {transfer} was declined", "{transfer} is stuck and not completed"],
    "refund_request": ["i want a refund for this {charge}", "please refund the {charge}",
                       "how do i get my money back for a {charge}",
                       "request a refund on the {charge}"],
}
FIXTURE_FILL = {"card": ["card", "debit card", "credit card", "visa card"],
                "transfer": ["transfer", "bank transfer", "payment", "wire"],
                "charge": ["charge", "purchase", "transaction", "fee"]}


def load_fixture(n_per_class: int = 40, seed: int = 7) -> Dataset:
    """Small, deterministic four-intent dataset for tests and offline labs."""
    rng = random.Random(seed)  # noqa: S311 - test data, not security
    texts, labels = [], []
    for label, templates in FIXTURE_INTENTS.items():
        for _ in range(n_per_class):
            template = rng.choice(templates)
            slot = next(k for k in FIXTURE_FILL if "{" + k + "}" in template)
            text = template.format(**{slot: rng.choice(FIXTURE_FILL[slot])})
            texts.append(rng.choice(["", "hi, ", "hello ", "urgent: "]) + text
                         + rng.choice(["", "?", "!", " please", " today"]))
            labels.append(label)
    return Dataset("fixture", "intent", texts, labels, version=f"seed:{seed}")


def load(spec: str, data_dir: Path, *, target: str = "product", seed: int = 42,
         max_per_class: int | None = 5000) -> Splits:
    """Load a dataset by spec: banking77 | fixture | cfpb-csv:PATH | cfpb-db:URL."""
    if spec == "banking77":
        train, test = load_banking77(data_dir)
        return make_splits(train, test=test, seed=seed)
    if spec == "fixture":
        return make_splits(load_fixture(), val_frac=0.15, test_frac=0.25, seed=seed)
    if spec.startswith("cfpb-csv:"):
        ds = load_cfpb_csv(Path(spec.split(":", 1)[1]), target=target, seed=seed,
                           max_per_class=max_per_class)
        return make_splits(ds, seed=seed)
    if spec.startswith("cfpb-db:"):
        ds = load_cfpb_db(spec.split(":", 1)[1], target=target, seed=seed,
                          max_per_class=max_per_class)
        return make_splits(ds, seed=seed)
    raise ValueError(f"unknown dataset spec {spec!r}")
