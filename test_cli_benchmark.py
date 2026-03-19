"""Test CLI benchmark mode on all 5 golden designs."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "src", "benchmark"],
    cwd="/Users/hale/projects/project-ava",
)
sys.exit(result.returncode)
