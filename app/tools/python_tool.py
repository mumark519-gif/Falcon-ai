from __future__ import annotations

import os
import subprocess
import sys
import tempfile


PYTHON_TIMEOUT_SECONDS = 10


def python_tool(
    code: str,
):

    if not code or not code.strip():

        return {
            "success": False,
            "error": "Python code is empty.",
        }

    filename = None

    try:

        with tempfile.NamedTemporaryFile(
            suffix=".py",
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as f:

            f.write(code)

            filename = f.name

        result = subprocess.run(
            [
                sys.executable,
                filename,
            ],
            capture_output=True,
            text=True,
            timeout=PYTHON_TIMEOUT_SECONDS,
        )

        if result.returncode == 0:

            return {
                "success": True,
                "output": result.stdout,
                "error": None,
            }

        return {
            "success": False,
            "output": result.stdout,
            "error": result.stderr,
        }

    except subprocess.TimeoutExpired:

        return {
            "success": False,
            "error": (
                "Python execution timed out."
            ),
        }

    except Exception as exc:

        return {
            "success": False,
            "error": str(exc),
        }

    finally:

        if filename and os.path.exists(
            filename
        ):

            os.remove(filename)