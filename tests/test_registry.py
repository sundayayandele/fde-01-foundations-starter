import json

import pytest

from complaint_router.registry import list_bundles, load_bundle, model_class, read_meta


def test_model_class_dispatch():
    assert model_class("baseline").kind == "baseline"
    assert model_class("mlp").kind == "mlp"
    assert model_class("transformer").kind == "transformer"
    with pytest.raises(ValueError):
        model_class("xgboost")


def test_list_bundles_missing_dir(tmp_path):
    assert list_bundles(tmp_path / "nope") == []


def test_list_bundles_reads_meta(tmp_path):
    d = tmp_path / "cfpb-product" / "baseline"
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"kind": "baseline", "labels": ["a"]}))
    [b] = list_bundles(tmp_path)
    assert b["name"] == "cfpb-product/baseline" and b["path"] == str(d)
    assert read_meta(d)["kind"] == "baseline"


@pytest.mark.exercise
def test_saved_bundles_load(model_dir):
    names = [b["name"] for b in list_bundles(model_dir)]
    assert names == ["fixture/baseline", "fixture/mlp"]
    model, meta = load_bundle(model_dir / "fixture" / "mlp")
    assert meta["kind"] == "mlp" and meta["dataset"] == "fixture"
    assert meta["labels"] == model.labels and meta["package_version"]
