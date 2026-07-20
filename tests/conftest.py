from __future__ import annotations

import shutil
from dataclasses import replace

import pytest

import nodes
import tools
from config import get_settings
from repositories import CSVRepository


@pytest.fixture(autouse=True)
def isolated_repository(tmp_path, monkeypatch):
    """Keep graph persistence tests away from the checked-in demo ledger."""

    source = get_settings().data_dir
    shutil.copy2(source / "market_prices.csv", tmp_path / "market_prices.csv")
    shutil.copy2(source / "buyers.csv", tmp_path / "buyers.csv")
    shutil.copy2(source / "transactions.csv", tmp_path / "transactions.csv")
    repository = CSVRepository(tmp_path)
    monkeypatch.setattr(tools, "get_repository", lambda: repository)
    # Unit/integration tests stay deterministic even when the developer's .env
    # enables the live Ollama Cloud workload. Provider behavior is covered with
    # a mocked client in test_model_integration.py.
    offline_settings = replace(get_settings(), ollama_enabled=False)
    monkeypatch.setattr(nodes, "get_settings", lambda: offline_settings)
    return repository
