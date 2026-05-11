"""Tests for Hermes Model Switcher server — core functions (no hermes CLI required)."""

import sys
from pathlib import Path

# Add parent dir to path so we can import server
sys.path.insert(0, str(Path(__file__).parent.parent))

import server  # noqa: E402


class TestStaticMime:
    """TDD Cycle 1: _static_mime maps extensions to MIME types."""

    def test_css_returns_text_css(self):
        assert server._static_mime("style.css") == "text/css"

    def test_js_returns_application_javascript(self):
        assert server._static_mime("app.js") == "application/javascript"

    def test_map_returns_application_json(self):
        assert server._static_mime("bundle.js.map") == "application/json"

    def test_unknown_returns_octet_stream(self):
        assert server._static_mime("file.xyz") == "application/octet-stream"


class TestResolveProfile:
    """TDD Cycle 2: resolve_profile maps names to config paths."""

    def test_none_returns_default_config(self):
        result = server.resolve_profile(None)
        assert result == server.CONFIG_PATH

    def test_default_returns_default_config(self):
        result = server.resolve_profile("default")
        assert result == server.CONFIG_PATH

    def test_nonexistent_profile_returns_none(self):
        result = server.resolve_profile("nonexistent-xyz-profile")
        assert result is None


class TestListProfiles:
    """TDD Cycle 3: list_profiles discovers profiles from filesystem."""

    def test_default_always_present(self):
        profiles = server.list_profiles()
        assert "default" in profiles
        assert profiles["default"] == server.CONFIG_PATH

    def test_returns_absolute_paths(self):
        profiles = server.list_profiles()
        for path in profiles.values():
            assert path.is_absolute()


class TestGetModels:
    """TDD Cycle 4: get_models parses config correctly."""

    def test_empty_config_returns_empty_providers(self):
        # Patch load_config to return empty dict
        import server as srv
        original = srv.load_config
        srv.load_config = lambda profile=None: {}
        try:
            result = srv.get_models()
            assert result["profile"] == "default"
            assert result["default_model"] == ""
            assert result["providers"] == {}
        finally:
            srv.load_config = original

    def test_returns_default_model_when_set(self):
        import server as srv
        original = srv.load_config
        srv.load_config = lambda profile=None: {
            "model": {"default": "gpt-4", "provider": "openai"},
            "providers": {},
        }
        try:
            result = srv.get_models()
            assert result["default_model"] == "gpt-4"
            assert result["default_provider"] == "openai"
        finally:
            srv.load_config = original

    def test_parses_provider_models(self):
        import server as srv
        original = srv.load_config
        srv.load_config = lambda profile=None: {
            "model": {"default": "claude", "provider": "anthropic"},
            "providers": {
                "anthropic": {
                    "name": "Anthropic",
                    "base_url": "https://api.anthropic.com",
                    "models": ["claude-sonnet-4", "claude-opus-4"],
                }
            },
        }
        try:
            result = srv.get_models()
            providers = result["providers"]
            assert "anthropic" in providers
            assert providers["anthropic"]["name"] == "Anthropic"
            assert providers["anthropic"]["models"] == ["claude-sonnet-4", "claude-opus-4"]
        finally:
            srv.load_config = original

    def test_handles_dict_models_with_id(self):
        import server as srv
        original = srv.load_config
        srv.load_config = lambda profile=None: {
            "model": {},
            "providers": {
                "test": {
                    "name": "Test",
                    "models": [{"id": "model-a"}, {"id": "model-b"}],
                }
            },
        }
        try:
            result = srv.get_models()
            assert result["providers"]["test"]["models"] == ["model-a", "model-b"]
        finally:
            srv.load_config = original


class TestGetCurrentSelection:
    """TDD Cycle 5: get_current_selection returns active model/provider."""

    def test_empty_config_returns_blanks(self):
        import server as srv
        original = srv.load_config
        srv.load_config = lambda profile=None: {}
        try:
            result = srv.get_current_selection()
            assert result["profile"] == "default"
            assert result["provider"] == ""
            assert result["model"] == ""
        finally:
            srv.load_config = original

    def test_returns_set_model(self):
        import server as srv
        original = srv.load_config
        srv.load_config = lambda profile=None: {
            "model": {"default": "deepseek-v4-pro", "provider": "deepseek"}
        }
        try:
            result = srv.get_current_selection()
            assert result["provider"] == "deepseek"
            assert result["model"] == "deepseek-v4-pro"
        finally:
            srv.load_config = original


class TestGetProfilesSummary:
    """TDD Cycle 6: get_profiles_summary returns multi-profile overview."""

    def test_includes_count(self):
        result = server.get_profiles_summary()
        assert "count" in result
        assert result["count"] >= 1
        assert "profiles" in result
        assert "default" in result["profiles"]
