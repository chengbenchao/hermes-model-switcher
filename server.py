#!/usr/bin/env python3
"""Hermes Model Switcher v0.3.0 — multi-profile web panel for switching AI models."""

import http.server
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import yaml

HERMES_HOME = Path.home() / ".hermes"
CONFIG_PATH = HERMES_HOME / "config.yaml"
PROFILES_DIR = HERMES_HOME / "profiles"
STATIC_DIR = Path(__file__).parent
STATIC_EXTENSIONS = {".css", ".js", ".map"}


def _static_mime(path):
    ext = Path(path).suffix.lower()
    return {".css": "text/css", ".js": "application/javascript", ".map": "application/json"}.get(ext, "application/octet-stream")
PORT = int(os.environ.get("PORT", 8899))


# ── profile discovery ────────────────────────────────────────────────

def list_profiles():
    """Return dict: {profile_name: config_path}. "default" maps to CONFIG_PATH."""
    profiles = {"default": CONFIG_PATH}
    if PROFILES_DIR.is_dir():
        for d in sorted(PROFILES_DIR.iterdir()):
            if d.is_dir():
                cfg = d / "config.yaml"
                if cfg.exists():
                    profiles[d.name] = cfg
    return profiles


def resolve_profile(profile_key):
    """profile_key=None → default; otherwise resolve from list_profiles()."""
    profiles = list_profiles()
    if not profile_key or profile_key == "default":
        return CONFIG_PATH
    return profiles.get(profile_key)


def find_hermes():
    """Locate hermes CLI across machines and install layouts."""
    candidates = []
    env_path = os.environ.get("HERMES_BIN", "").strip()
    if env_path:
        candidates.append(Path(env_path).expanduser())
    found = shutil.which("hermes")
    if found:
        candidates.append(Path(found))
    candidates.extend([
        Path.home() / ".local" / "bin" / "hermes",
        Path("/usr/local/bin/hermes"),
        Path("/usr/bin/hermes"),
    ])
    seen = set()
    for p in candidates:
        p = p.expanduser().resolve()
        if str(p) in seen:
            continue
        seen.add(str(p))
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
    return None


# ── config helpers ───────────────────────────────────────────────────

def load_config(profile=None):
    path = resolve_profile(profile)
    if not path or not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f)


def get_models(profile=None):
    """Return all models grouped by provider, with current default marked."""
    cfg = load_config(profile)
    providers = cfg.get("providers", {})
    default_model = cfg.get("model", {}).get("default", "")
    default_provider = cfg.get("model", {}).get("provider", "")

    result = {
        "profile": profile or "default",
        "default_model": default_model,
        "default_provider": default_provider,
        "providers": {},
    }

    for pname, pcfg in providers.items():
        models = []
        for m in pcfg.get("models", []):
            if isinstance(m, str):
                models.append(m)
            elif isinstance(m, dict):
                models.append(m.get("id", m.get("name", str(m))))
        result["providers"][pname] = {
            "name": pcfg.get("name", pname),
            "base_url": pcfg.get("base_url", ""),
            "models": models,
        }
    return result


def get_current_selection(profile=None):
    cfg = load_config(profile)
    model_cfg = cfg.get("model", {})
    return {
        "profile": profile or "default",
        "provider": model_cfg.get("provider", ""),
        "model": model_cfg.get("default", ""),
    }


def get_health(profile=None):
    hermes_bin = find_hermes()
    profiles = list_profiles()
    current = get_current_selection(profile)
    return {
        "ok": True,
        "port": PORT,
        "profile": profile or "default",
        "config_path": str(resolve_profile(profile) or ""),
        "config_exists": resolve_profile(profile).exists() if resolve_profile(profile) else False,
        "html_path": str(STATIC_DIR / "index.html"),
        "html_exists": (STATIC_DIR / "index.html").exists(),
        "hermes_bin": hermes_bin,
        "hermes_found": bool(hermes_bin),
        "current_provider": current["provider"],
        "current_model": current["model"],
        "profiles": list(profiles.keys()),
    }


def get_profiles_summary():
    """Return summary of all profiles with their current model."""
    profiles = {}
    for name, cfg_path in list_profiles().items():
        cfg = load_config(name)
        mc = cfg.get("model", {})
        profiles[name] = {
            "config_path": str(cfg_path),
            "provider": mc.get("provider", ""),
            "model": mc.get("default", ""),
        }
    return {"profiles": profiles, "count": len(profiles)}


# ── model switching ──────────────────────────────────────────────────

def switch_model(provider, model, profile=None):
    """Switch default model + provider for a specific profile via hermes CLI."""
    try:
        hermes_bin = find_hermes()
        if not hermes_bin:
            return {"ok": False, "error": "hermes CLI not found."}

        # Build CLI args with optional --profile
        base_cmd = [hermes_bin]
        if profile and profile != "default":
            base_cmd += ["--profile", profile]

        r1 = subprocess.run(
            base_cmd + ["config", "set", "model.provider", provider],
            capture_output=True, text=True, timeout=15,
        )
        r2 = subprocess.run(
            base_cmd + ["config", "set", "model.default", model],
            capture_output=True, text=True, timeout=15,
        )

        if r1.returncode != 0 or r2.returncode != 0:
            return {
                "ok": False,
                "profile": profile or "default",
                "error": (
                    f"hermes={hermes_bin}\n"
                    f"set model.provider: {r1.stderr.strip()}\n"
                    f"set model.default: {r2.stderr.strip()}"
                ),
            }

        current = get_current_selection(profile)
        if current["provider"] != provider or current["model"] != model:
            return {
                "ok": False,
                "profile": profile or "default",
                "error": (
                    "Config verification failed after switch.\n"
                    f"expected: {provider}/{model}\n"
                    f"actual: {current['provider']}/{current['model']}"
                ),
            }

        return {
            "ok": True,
            "profile": profile or "default",
            "model": model,
            "provider": provider,
            "hermes_bin": hermes_bin,
        }
    except Exception as e:
        return {"ok": False, "profile": profile or "default", "error": str(e)}


# ── HTTP handler ─────────────────────────────────────────────────────

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _send_html(self, content, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content)

    def _send_static(self, filepath):
        full = STATIC_DIR / filepath.lstrip("/")
        if not full.resolve().is_relative_to(STATIC_DIR.resolve()):
            self._send_json({"error": "Not found"}, 404)
            return
        try:
            with open(full, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", _static_mime(filepath) + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self._send_json({"error": "Not found"}, 404)

    def _profile_param(self):
        """Extract ?profile= from query string."""
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        vals = qs.get("profile", [])
        return vals[0] if vals else None

    def _clean_path(self):
        return urlparse(self.path).path

    def do_GET(self):
        path = self._clean_path()
        profile = self._profile_param()

        if path == "/" or path == "/index.html":
            try:
                with open(STATIC_DIR / "index.html", "rb") as f:
                    self._send_html(f.read())
            except FileNotFoundError:
                self._send_json({"error": "index.html not found"}, 404)

        elif any(path.endswith(ext) for ext in STATIC_EXTENSIONS):
            self._send_static(path)

        elif path == "/api/profiles":
            try:
                self._send_json(get_profiles_summary())
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        elif path == "/api/models":
            try:
                self._send_json(get_models(profile))
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        elif path == "/api/health":
            try:
                self._send_json(get_health(profile))
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/switch":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"ok": False, "error": "Invalid JSON"}, 400)
                return

            provider = data.get("provider", "")
            model = data.get("model", "")
            profile = data.get("profile")  # optional, None → default

            if not provider or not model:
                self._send_json({"ok": False, "error": "Missing provider or model"}, 400)
                return

            result = switch_model(provider, model, profile)
            self._send_json(result, 200 if result["ok"] else 500)

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ── main ─────────────────────────────────────────────────────────────

def main():
    if not CONFIG_PATH.exists():
        print(f"Config not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    print(f"🧠 Hermes Model Switcher v0.3.0 → http://localhost:{PORT}")
    print(f"   Profiles: {', '.join(list_profiles().keys())}")
    print("   Press Ctrl+C to stop.")
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
