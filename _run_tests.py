"""Run pytest and save results to a file."""
import subprocess
import sys
import os

# Change to project directory
os.chdir(r"D:\ISALAB")

# Run pytest
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-x", "-q", "--tb=short", "--no-header"],
    capture_output=True,
    text=True,
    timeout=120
)

# Write results
with open("_test_results.txt", "w", encoding="utf-8") as f:
    f.write("=== STDOUT ===\n")
    f.write(result.stdout or "(empty)\n")
    f.write("\n=== STDERR ===\n")
    f.write(result.stderr or "(empty)\n")
    f.write(f"\n=== RETURN CODE: {result.returncode} ===\n")

print(f"Tests completed with return code: {result.returncode}")
print(result.stdout[-2000:] if result.stdout else "(no stdout)")
if result.returncode != 0 and result.stderr:
    print("STDERR:", result.stderr[-1000:])
