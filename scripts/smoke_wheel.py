"""Build/install a wheel in isolation and exercise both HTTPie auth entry points."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.parse import unquote


def check_installed_plugin(fixtures):
    import httpie_asap_auth
    import jwt

    module = Path(httpie_asap_auth.__file__).resolve()
    assert (
        Path(sys.prefix).resolve() in module.parents
    ), "plugin is not installed in smoke environment"
    config = json.loads((fixtures / "asap.config").read_text(encoding="utf-8"))
    public_key = (fixtures / "publickey.pem").read_text(encoding="utf-8")
    env = os.environ.copy()
    env["HTTPIE_CONFIG_DIR"] = str(Path.cwd() / "httpie-config")
    env["ASAP_PRIVATE_KEY"] = (fixtures / "privatekey.datauri").read_text(
        encoding="utf-8"
    )
    env["ASAP_ISSUER"] = config["issuer"]
    env_kid = unquote(env["ASAP_PRIVATE_KEY"].split(";kid=", 1)[1].split(";", 1)[0])

    def request(auth_type, auth, expected_audience, subject, kid):
        started = int(time.time())
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-m",
                "httpie",
                "--ignore-stdin",
                "--offline",
                "--print=H",
                "--auth-type=" + auth_type,
                "--auth=" + auth,
                "https://example.com/",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "HTTPie offline request failed"
        headers = result.stdout.splitlines()
        token = next(
            line.split(": ", 1)[1].split()[1]
            for line in headers
            if line.lower().startswith("authorization: ")
        )
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "RS256"
        assert header["kid"] == kid
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=expected_audience,
            issuer=config["issuer"],
            options={"require": ["iss", "sub", "aud", "iat", "nbf", "exp", "jti"]},
        )
        assert claims["sub"] == subject
        assert started <= claims["iat"] <= int(time.time())
        assert claims["nbf"] == claims["iat"]
        assert claims["iat"] < claims["exp"] <= claims["iat"] + 120
        assert claims["jti"]

    inline_path = Path.cwd() / "inline.json"
    inline_path.write_text(json.dumps(config), encoding="utf-8")
    request("asap", str(inline_path), "webapp", config["sub"], config["kid"])
    key_dir = Path.cwd() / "credentials"
    key_dir.mkdir()
    (key_dir / "key.pem").write_text(config.pop("privateKey"), encoding="utf-8")
    config["privateKeyFile"] = "key.pem"
    del config["sub"]
    file_path = key_dir / "config.json"
    file_path.write_text(json.dumps(config), encoding="utf-8")
    request("asap", str(file_path), "webapp", config["issuer"], config["kid"])
    request(
        "asapenv", "webapp, webapp2:administration", "webapp", "administration", env_kid
    )
    request("asapenv", "webapp", "webapp", config["issuer"], env_kid)
    request(
        "asapenv",
        json.dumps(
            {
                "audience": ["https://service.example", "urn:foo,bar"],
                "sub": "administration",
            }
        ),
        "https://service.example",
        "administration",
        env_kid,
    )
    env["ASAP_PRIVATE_KEY"] = "SENSITIVE_INVALID_PRIVATE_KEY"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "httpie",
            "--ignore-stdin",
            "--offline",
            "--auth-type=asapenv",
            "--auth=webapp",
            "https://example.com/",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "unable to sign ASAP token" in result.stderr
    assert "SENSITIVE_INVALID_PRIVATE_KEY" not in result.stderr + result.stdout
    assert "Traceback" not in result.stderr
    print(
        "Installed wheel smoke passed: both auth modes, key files, JWT verification and safe errors."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", nargs="?", type=Path)
    parser.add_argument("--check", type=Path, metavar="FIXTURE_DIR")
    args = parser.parse_args()
    if args.check:
        check_installed_plugin(args.check)
        return
    repo = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    with tempfile.TemporaryDirectory(prefix="asap-wheel-") as directory:
        root = Path(directory)
        wheel = args.wheel.resolve() if args.wheel else None
        if wheel is None:
            subprocess.run(
                ["uv", "build", "--wheel", "--out-dir", str(root / "dist")],
                cwd=repo,
                env=env,
                check=True,
            )
            wheels = list((root / "dist").glob("*.whl"))
            assert len(wheels) == 1, "expected exactly one freshly built wheel"
            wheel = wheels[0]
        venv = root / "venv"
        subprocess.run(
            ["uv", "venv", "--python", sys.executable, str(venv)],
            cwd=root,
            env=env,
            check=True,
        )
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            ["uv", "pip", "install", "--python", str(python), str(wheel)],
            cwd=root,
            env=env,
            check=True,
        )
        subprocess.run(
            [
                str(python),
                "-I",
                str(Path(__file__).resolve()),
                "--check",
                str(repo / "tests/data"),
            ],
            cwd=root,
            env=env,
            check=True,
        )


if __name__ == "__main__":
    main()
