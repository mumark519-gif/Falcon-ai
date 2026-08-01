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

            return result.stdout

        return result.stderr

    finally:

        os.remove(filename)