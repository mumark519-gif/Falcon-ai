import subprocess
import tempfile
import os


def python_tool(
    code: str,
):

    with tempfile.NamedTemporaryFile(
        suffix=".py",
        delete=False,
        mode="w",
        encoding="utf-8",
    ) as f:

        f.write(code)
        filename = f.name

    try:

        result = subprocess.run(
            ["python", filename],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:

            return {
                "success": True,
                "output": result.stdout,
            }

        return {
            "success": False,
            "error": result.stderr,
        }

    finally:

        if os.path.exists(filename):

            os.remove(filename)