"""Small, authenticated web remote for the Burner CLI."""

from __future__ import annotations

import hmac
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import threading

from flask import Flask, Response, jsonify, request, send_file


BURNER = "/Users/christopherrittle/.venvs/burner/bin/burner"
ADB = "/Users/christopherrittle/Library/Android/sdk/platform-tools/adb"
ADB_TARGET = "127.0.0.1:5555"
RECIPES_DIR = Path("/Users/christopherrittle/burner/recipes")
BASE_DIR = Path(__file__).resolve().parent
SHOT_PATH = Path(tempfile.gettempdir()) / "burner-dashboard.png"
COMMAND_TIMEOUT = 120

app = Flask(__name__)
shot_lock = threading.Lock()


def credentials() -> tuple[str, str]:
    """Return configured credentials, refusing insecure partial configuration."""
    username = os.environ.get("DASHBOARD_USER", "")
    password = os.environ.get("DASHBOARD_PASS", "")
    if not username or not password:
        raise RuntimeError("DASHBOARD_USER and DASHBOARD_PASS must both be set")
    return username, password


@app.before_request
def require_auth() -> Response | None:
    """Require HTTP Basic authentication for every request."""
    expected_user, expected_pass = credentials()
    supplied = request.authorization
    valid = supplied is not None and hmac.compare_digest(
        supplied.username.encode(), expected_user.encode()
    ) and hmac.compare_digest(supplied.password.encode(), expected_pass.encode())
    if not valid:
        return Response(
            "Authentication required.\n",
            401,
            {"WWW-Authenticate": 'Basic realm="Burner Dashboard"'},
        )
    return None


def run_burner(*args: str, timeout: int = COMMAND_TIMEOUT) -> str:
    """Run Burner without a shell and return its text output."""
    try:
        result = subprocess.run(
            [BURNER, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Burner command timed out") from exc
    except OSError as exc:
        raise RuntimeError(f"Could not start Burner: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "Burner command failed").strip()
        raise RuntimeError(detail) from exc
    return result.stdout.strip()


def list_apps() -> str:
    """List apps with Burner, falling back to the Android SDK's adb."""
    try:
        return run_burner("apps")
    except RuntimeError as burner_error:
        try:
            result = subprocess.run(
                [ADB, "-s", ADB_TARGET, "shell", "pm", "list", "packages"],
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT,
                check=True,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"Could not list apps: {burner_error}") from exc
        return result.stdout


def json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")
    return data


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as image:
        header = image.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("Burner did not produce a valid PNG screenshot")
    return struct.unpack(">II", header[16:24])


@app.errorhandler(ValueError)
def bad_request(error: ValueError):
    return jsonify(error=str(error)), 400


@app.errorhandler(RuntimeError)
def command_error(error: RuntimeError):
    return jsonify(error=str(error)), 502


@app.get("/")
def index():
    return send_file(BASE_DIR / "index.html")


@app.get("/shot")
def shot():
    with shot_lock:
        run_burner("shot", "--out", str(SHOT_PATH))
        png_size(SHOT_PATH)
        response = send_file(SHOT_PATH, mimetype="image/png")
        response.headers["Cache-Control"] = "no-store, max-age=0"
        return response


@app.post("/tap")
def tap():
    data = json_body()
    try:
        x = float(data["x"])
        y = float(data["y"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("x and y must be numbers from 0 to 1000") from exc
    if not (0 <= x <= 1000 and 0 <= y <= 1000):
        raise ValueError("x and y must be numbers from 0 to 1000")
    with shot_lock:
        if not SHOT_PATH.exists():
            run_burner("shot", "--out", str(SHOT_PATH))
        width, height = png_size(SHOT_PATH)
    device_x = round(x * width / 1000)
    device_y = round(y * height / 1000)
    run_burner("tap", "--xy", f"{device_x},{device_y}")
    return jsonify(ok=True, x=device_x, y=device_y)


@app.post("/type")
def type_text():
    text = json_body().get("text")
    if not isinstance(text, str) or not text:
        raise ValueError("text must be a non-empty string")
    if len(text) > 2000:
        raise ValueError("text is too long (maximum 2000 characters)")
    run_burner("type", text)
    return jsonify(ok=True)


@app.post("/press")
def press():
    key = json_body().get("key")
    if key not in {"home", "back"}:
        raise ValueError("key must be home or back")
    run_burner("press", key)
    return jsonify(ok=True)


def clean_lines(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if line.strip()]


@app.get("/apps")
def apps():
    lines = clean_lines(list_apps())
    packages = []
    for line in lines:
        match = re.search(r"(?:package:)?([A-Za-z][\w]*(?:\.[\w]+)+)", line)
        if match:
            packages.append(match.group(1))
    return jsonify(apps=sorted(set(packages), key=str.casefold))


@app.post("/launch")
def launch():
    package = json_body().get("package")
    if not isinstance(package, str) or not re.fullmatch(r"[A-Za-z][\w]*(?:\.[\w]+)+", package):
        raise ValueError("package is not a valid Android package name")
    run_burner("start", package)
    return jsonify(ok=True)


def recipe_names() -> list[str]:
    names: set[str] = set()
    if RECIPES_DIR.is_dir():
        names.update(path.stem for path in RECIPES_DIR.iterdir() if path.is_file())
    for line in clean_lines(run_burner("recipes")):
        candidate = line.lstrip("- *").split()[0] if line.lstrip("- *") else ""
        if re.fullmatch(r"[A-Za-z0-9_.-]+", candidate):
            names.add(Path(candidate).stem)
    return sorted(names, key=str.casefold)


@app.get("/recipes")
def recipes():
    return jsonify(recipes=recipe_names())


@app.post("/recipe/<name>")
def recipe(name: str):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or name not in recipe_names():
        raise ValueError("unknown recipe")
    run_burner("replay", name, timeout=600)
    return jsonify(ok=True)


if __name__ == "__main__":
    credentials()
    app.run(host="127.0.0.1", port=int(os.environ.get("DASHBOARD_PORT", "5000")))
