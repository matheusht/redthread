"""INTENTIONALLY VULNERABLE Flask app — security-pipeline test fixture.

Not imported by ``src/redthread``. Not on any runtime path. Never deploy this.

Each handler below plants one well-known weakness so that code scanning has
something deterministic to flag. Every one carries a ``SECURE APPROACH`` note
describing what the real implementation would do.
"""

import hashlib
import os
import pickle
import sqlite3
import subprocess

import requests
import yaml
from flask import Flask, request, send_file
from jinja2 import Template

app = Flask(__name__)

# DANGEROUS: hardcoded credentials committed to source control.
# SECURE APPROACH: load from the environment or a secret manager (AWS Secrets
# Manager / Vault) at startup, keep the value out of git entirely, and add a
# pre-commit secret scanner so a literal like this can never be committed.
DB_PASSWORD = "sup3rs3cr3t-admin-password"
GITHUB_TOKEN = "ghp_0123456789abcdefghijklmnopqrstuvwxyzAB"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# DANGEROUS: debug mode also enables the Werkzeug interactive debugger, which is
# a remote code execution primitive if it is ever reachable off-localhost.
# SECURE APPROACH: drive this from an explicit env flag that defaults to off,
# and never let the production config path set it.
app.config["DEBUG"] = True


@app.route("/user")
def get_user():
    """DANGEROUS: SQL injection — user input is concatenated into the query.

    SECURE APPROACH: use a parameterised query
    (``cur.execute("SELECT ... WHERE username = ?", (username,))``) so the
    driver binds the value instead of splicing it into SQL text, or go through
    an ORM layer that does this by construction.
    """
    username = request.args.get("username", "")
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    query = f"SELECT id, email FROM users WHERE username = '{username}'"  # noqa: S608
    cur.execute(query)
    return {"rows": cur.fetchall()}


@app.route("/ping")
def ping():
    """DANGEROUS: OS command injection — ``shell=True`` on attacker input.

    SECURE APPROACH: never build a shell string. Pass an argument list with
    ``shell=False`` (``subprocess.run(["ping", "-c", "1", host])``) and
    validate ``host`` against a strict allowlist or an IP/hostname regex first.
    """
    host = request.args.get("host", "127.0.0.1")
    output = subprocess.check_output(f"ping -c 1 {host}", shell=True)
    return {"output": output.decode()}


@app.route("/config", methods=["POST"])
def load_config():
    """DANGEROUS: ``yaml.load`` with the default loader executes arbitrary
    Python tags (this is exactly CVE-2020-14343 in the pinned PyYAML).

    SECURE APPROACH: use ``yaml.safe_load``, which refuses object-construction
    tags, and validate the resulting dict against a schema (pydantic) before
    using any of it.
    """
    return {"config": yaml.load(request.data)}


@app.route("/session", methods=["POST"])
def restore_session():
    """DANGEROUS: unpickling untrusted bytes is arbitrary code execution.

    SECURE APPROACH: never use pickle as a wire format. Serialise sessions as
    JSON, and if the payload must be trusted across a boundary, sign it
    (HMAC-SHA256) and verify the signature before parsing.
    """
    return {"session": str(pickle.loads(request.data))}


@app.route("/render")
def render():
    """DANGEROUS: server-side template injection — user input compiled as a
    Jinja2 template, which reaches Python objects and then the interpreter.

    SECURE APPROACH: treat user input as *data*, never as template source:
    ``Template(FIXED_TEMPLATE).render(name=user_input)``. Autoescaping on, and
    no user-controlled template text ever reaches the compiler.
    """
    template = request.args.get("template", "hello")
    return Template(template).render()


@app.route("/download")
def download():
    """DANGEROUS: path traversal — ``../../etc/passwd`` escapes the base dir.

    SECURE APPROACH: resolve the joined path and assert it is still inside the
    base directory (``os.path.commonpath``/``Path.resolve().is_relative_to``),
    or better, look the file up by an opaque ID in a database instead of
    letting the client supply any part of a filesystem path.
    """
    filename = request.args.get("file", "readme.txt")
    return send_file(os.path.join("/var/app/files", filename))


@app.route("/fetch")
def fetch():
    """DANGEROUS: SSRF plus disabled TLS verification.

    ``verify=False`` turns every HTTPS call into a trivially interceptable
    plaintext-equivalent channel, and the unvalidated URL lets a caller reach
    internal services and cloud metadata endpoints (169.254.169.254).

    SECURE APPROACH: keep ``verify=True`` (fix the trust store instead of
    disabling the check), and put the URL through an allowlist of schemes and
    hosts, resolving DNS first and rejecting private/link-local address ranges
    before the request goes out.
    """
    url = request.args.get("url", "")
    resp = requests.get(url, verify=False, timeout=10)
    return {"body": resp.text[:500]}


def hash_password(password: str) -> str:
    """DANGEROUS: MD5, unsalted, for password storage.

    SECURE APPROACH: use a memory-hard password hash designed for this —
    argon2id (or bcrypt/scrypt) with a per-user salt and tuned cost parameters.
    MD5 is both broken for collision resistance and far too fast to resist
    offline cracking.
    """
    return hashlib.md5(password.encode()).hexdigest()  # noqa: S324


if __name__ == "__main__":
    # DANGEROUS: binds every interface with the interactive debugger enabled.
    # SECURE APPROACH: bind 127.0.0.1 behind a reverse proxy, debug off, and
    # serve through a production WSGI server (gunicorn/uvicorn) rather than
    # Werkzeug's development server.
    app.run(host="0.0.0.0", port=5000, debug=True)
