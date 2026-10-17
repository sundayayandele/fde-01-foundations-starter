import hashlib
from collections import Counter

import httpx
import pytest

from complaint_router import data
from complaint_router.data import (
    Dataset,
    find_leakage,
    load_banking77,
    load_cfpb_csv,
    load_fixture,
    make_splits,
    stratified_split,
)

LABELS = ["a"] * 50 + ["b"] * 30 + ["c"] * 20


@pytest.mark.exercise
def test_stratified_split_partitions_and_keeps_shares():
    parts = stratified_split(LABELS, (0.8, 0.1, 0.1), seed=3)
    flat = sorted(i for p in parts for i in p)
    assert flat == list(range(len(LABELS)))
    assert [len(p) for p in parts] == [80, 10, 10]
    for p in parts[1:]:
        counts = Counter(LABELS[i] for i in p)
        assert counts == {"a": 5, "b": 3, "c": 2}


@pytest.mark.exercise
def test_stratified_split_is_seeded():
    assert stratified_split(LABELS, (0.5, 0.5), 1) == stratified_split(LABELS, (0.5, 0.5), 1)
    assert stratified_split(LABELS, (0.5, 0.5), 1) != stratified_split(LABELS, (0.5, 0.5), 2)


def test_stratified_split_rejects_bad_fractions():
    with pytest.raises(ValueError):
        stratified_split(LABELS, (0.5, 0.4))


@pytest.mark.exercise
def test_find_leakage_uses_normalised_text():
    train = ["My card is lost", "refund please"]
    other = ["my  CARD is lost", "new text", "Refund please"]
    assert find_leakage(train, other) == [0, 2]
    assert find_leakage([], other) == []


@pytest.mark.exercise
def test_make_splits_removes_leaked_and_unknown_labels():
    train = Dataset("t", "intent", ["a one", "a two", "b one", "b two"] * 5,
                    ["a", "a", "b", "b"] * 5)
    test = Dataset("t", "intent", ["a one", "fresh a", "fresh c"], ["a", "a", "c"])
    s = make_splits(train, test=test, val_frac=0.2)
    assert s.test.texts == ["fresh a"]
    assert s.test.notes["split"] == "test"


@pytest.mark.exercise
def test_fixture_splits(splits):
    assert splits.summary()["classes"] == 4
    assert not find_leakage(splits.train.texts, splits.test.texts)


def test_dataset_validates_lengths():
    with pytest.raises(ValueError):
        Dataset("x", "y", ["a"], [])


def test_fixture_is_deterministic():
    assert load_fixture().texts == load_fixture().texts
    assert len(load_fixture(n_per_class=5)) == 20


def test_cfpb_csv_skips_empty_narratives_and_rare_classes(tmp_path):
    from tests.conftest import FIXTURES
    ds = load_cfpb_csv(FIXTURES / "cfpb_sample.csv", target="product", min_count=3)
    assert Counter(ds.labels) == {"Credit card": 3, "Mortgage": 3, "Debt collection": 3}
    assert ds.version.startswith("sha256:")
    issues = load_cfpb_csv(FIXTURES / "cfpb_sample.csv", target="issue", min_count=2,
                           max_per_class=1)
    assert Counter(issues.labels) == {"Attempts to collect debt not owed": 1,
                                      "Problem with a purchase shown on your statement": 1,
                                      "Trouble during payment process": 1}
    with pytest.raises(ValueError):
        load_cfpb_csv(FIXTURES / "cfpb_sample.csv", target="company")


def test_cfpb_db_reads_fde00_schema(tmp_path):
    sqlalchemy = pytest.importorskip("sqlalchemy")
    url = f"sqlite:///{tmp_path / 'c.db'}"
    engine = sqlalchemy.create_engine(url)
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE complaints (complaint_id TEXT, narrative TEXT, "
                             "product TEXT, issue TEXT)")
        for i in range(6):
            conn.exec_driver_sql("INSERT INTO complaints VALUES (?, ?, ?, ?)",
                                 (str(i), f"text {i}" if i < 5 else None,
                                  "Mortgage" if i % 2 else "Credit card", "Fees"))
    engine.dispose()
    ds = data.load_cfpb_db(url, target="product", min_count=2)
    assert Counter(ds.labels) == {"Credit card": 3, "Mortgage": 2}
    with pytest.raises(ValueError):
        data.load_cfpb_db(url, target="narrative")


def _mock_client(payloads: dict[str, bytes]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        name = request.url.path.rsplit("/", 1)[-1]
        return httpx.Response(200, content=payloads[name])
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_download_banking77_verifies_checksums(tmp_path, monkeypatch):
    train = b"text,category\nwhere is my card,card_arrival\nlost my card,lost_or_stolen_card\n"
    test = b"text,category\nmy card is late,card_arrival\n"
    monkeypatch.setattr(data, "BANKING77_SHA256", {
        "train.csv": hashlib.sha256(train).hexdigest(),
        "test.csv": hashlib.sha256(test).hexdigest()})
    data.download_banking77(tmp_path, client=_mock_client({"train.csv": train, "test.csv": test}))
    tr, te = load_banking77(tmp_path, download=False)
    assert tr.labels == ["card_arrival", "lost_or_stolen_card"]
    assert te.texts == ["my card is late"]
    assert tr.version.startswith("git:")
    # already present and valid: nothing is downloaded again
    data.download_banking77(tmp_path, client=_mock_client({}))


def test_download_banking77_rejects_tampered_file(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "BANKING77_SHA256", {"train.csv": "0" * 64})
    with pytest.raises(ValueError, match="checksum"):
        data.download_banking77(tmp_path, client=_mock_client({"train.csv": b"tampered"}))
    assert not (tmp_path / "banking77" / "train.csv").exists()


def test_load_rejects_unknown_spec(tmp_path):
    with pytest.raises(ValueError):
        data.load("kaggle:foo", tmp_path)
