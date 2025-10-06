import pytest

from config.BlockChain import get_web3, resolve_provider_url


def setup_function():
    get_web3.cache_clear()


def test_resolve_provider_url_prefers_argument(monkeypatch):
    monkeypatch.setenv("INFURA_URL", "https://example.com")
    assert resolve_provider_url("http://local") == "http://local"


def test_resolve_provider_url_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("INFURA_URL", "")
    monkeypatch.setenv("WEB3_PROVIDER_URI", "https://env-provider")
    assert resolve_provider_url() == "https://env-provider"


def test_get_web3_raises_when_provider_missing(monkeypatch):
    monkeypatch.setenv("INFURA_URL", "")
    monkeypatch.setenv("WEB3_PROVIDER_URI", "")
    get_web3.cache_clear()
    with pytest.raises(RuntimeError):
        get_web3()


def test_get_web3_uses_cached_provider(monkeypatch):
    monkeypatch.setenv("INFURA_URL", "https://example.com")
    get_web3.cache_clear()
    first = get_web3()
    monkeypatch.setenv("INFURA_URL", "https://other.com")
    assert get_web3() is first
