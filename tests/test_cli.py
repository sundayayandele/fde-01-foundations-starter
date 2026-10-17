import json

import pytest

from complaint_router import cli


def test_list_empty(tmp_path, capsys):
    assert cli.main(["list", "--model-dir", str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_download_calls_downloader(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "download_banking77", lambda d: d / "banking77")
    assert cli.main(["--data-dir", str(tmp_path), "download", "banking77"]) == 0
    assert "banking77" in capsys.readouterr().out


@pytest.mark.exercise
def test_train_evaluate_compare_predict(tmp_path, capsys):
    models = tmp_path / "models"
    results = tmp_path / "results"
    assert cli.main(["train", "--dataset", "fixture", "--model", "baseline",
                     "--model-dir", str(models)]) == 0
    assert cli.main(["train", "--dataset", "fixture", "--model", "mlp", "--epochs", "10",
                     "--model-dir", str(models)]) == 0
    assert "test macro-F1" in capsys.readouterr().out
    for kind in ("baseline", "mlp"):
        assert cli.main(["evaluate", "--bundle", str(models / "fixture" / kind),
                         "--out", str(results)]) == 0
    reports = sorted(str(p) for p in results.glob("*.json"))
    assert len(reports) == 2
    assert cli.main(["compare", *reports, "--out", str(tmp_path / "cmp.md")]) == 0
    assert "| fixture/intent | baseline |" in (tmp_path / "cmp.md").read_text()
    capsys.readouterr()
    assert cli.main(["predict", "--bundle", str(models / "fixture" / "baseline"),
                     "my debit card was stolen"]) == 0
    assert json.loads(capsys.readouterr().out)["label"] == "lost_card"
    assert cli.main(["list", "--model-dir", str(models)]) == 0
    assert "fixture/mlp" in capsys.readouterr().out
