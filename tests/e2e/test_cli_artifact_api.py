"""E2E test: CLI artifact commands against live Notion (Consumer v2 E2E page)."""
import os
import sys
import json
import subprocess

PA_ROOT = os.path.dirname(os.path.abspath(__file__))
UPSTREAM_ROOT = os.path.dirname(os.path.dirname(PA_ROOT))
CONSUMER_ROOT = "/Users/chunchun/Documents/Playground - Code/consumer project - notion"
os.environ['NOTION_API_TOKEN'] = os.environ.get('NOTION_API_TOKEN', '')

# Use the consumer project which has Notion storage.yaml configured
PROJECT_DIR = CONSUMER_ROOT

def run_cli(args):
    """Run a CLI command and return parsed JSON."""
    cmd = [sys.executable, "-m", "src.cli.main"] + args + ["--project-dir", PROJECT_DIR]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=UPSTREAM_ROOT, env={**os.environ, "PYTHONPATH": UPSTREAM_ROOT})
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr.strip()}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  RAW OUTPUT: {result.stdout.strip()}")
        return None

errors = []

# --- Inbox ---
print("=== Inbox ===")

result = run_cli(["inbox", "add", "--text", "CLI E2E: test idea from CLI", "--type", "idea"])
if result and result.get("success"):
    print("[PASS] inbox add")
else:
    print(f"[FAIL] inbox add: {result}")
    errors.append("inbox add")

result = run_cli(["inbox", "list"])
if result and result.get("success") and len(result["data"]) >= 1:
    print(f"[PASS] inbox list ({len(result['data'])} items)")
else:
    print(f"[FAIL] inbox list: {result}")
    errors.append("inbox list")

# --- Backlog ---
print("\n=== Backlog ===")

result = run_cli(["backlog", "upsert", "--title", "CLI E2E: test feature", "--type", "Feature", "--status", "draft", "--priority", "High"])
if result and result.get("success"):
    print("[PASS] backlog upsert (Feature)")
else:
    print(f"[FAIL] backlog upsert Feature: {result}")
    errors.append("backlog upsert Feature")

result = run_cli(["backlog", "upsert", "--title", "CLI E2E: test task", "--type", "Task", "--status", "to-do", "--priority", "Medium"])
if result and result.get("success"):
    print("[PASS] backlog upsert (Task)")
else:
    print(f"[FAIL] backlog upsert Task: {result}")
    errors.append("backlog upsert Task")

result = run_cli(["backlog", "list"])
if result and result.get("success") and len(result["data"]) >= 2:
    print(f"[PASS] backlog list ({len(result['data'])} items)")
else:
    print(f"[FAIL] backlog list: {result}")
    errors.append("backlog list")

result = run_cli(["backlog", "list", "--type", "Feature"])
if result and result.get("success"):
    print(f"[PASS] backlog list --type Feature ({len(result['data'])} items)")
else:
    print(f"[FAIL] backlog list --type Feature: {result}")
    errors.append("backlog list --type Feature")

# --- Decision ---
print("\n=== Decision ===")

result = run_cli(["decision", "add", "--id", "D-CLI", "--title", "CLI E2E: test decision", "--date", "2026-03-16", "--why", "Testing CLI", "--status", "accepted"])
if result and result.get("success"):
    print("[PASS] decision add")
else:
    print(f"[FAIL] decision add: {result}")
    errors.append("decision add")

result = run_cli(["decision", "list"])
if result and result.get("success") and len(result["data"]) >= 1:
    print(f"[PASS] decision list ({len(result['data'])} items)")
else:
    print(f"[FAIL] decision list: {result}")
    errors.append("decision list")

# --- Brief ---
print("\n=== Brief ===")

result = run_cli(["brief", "write", "cli-e2e-test", "--title", "CLI E2E Test", "--status", "draft", "--problem", "Testing the CLI", "--goal", "Verify CLI works with Notion"])
if result and result.get("success"):
    print("[PASS] brief write")
else:
    print(f"[FAIL] brief write: {result}")
    errors.append("brief write")

result = run_cli(["brief", "list"])
if result and result.get("success"):
    print(f"[PASS] brief list ({len(result['data'])} items)")
else:
    print(f"[FAIL] brief list: {result}")
    errors.append("brief list")

result = run_cli(["brief", "read", "cli-e2e-test"])
if result and result.get("success") and "Testing the CLI" in str(result["data"]):
    print("[PASS] brief read")
else:
    print(f"[FAIL] brief read: {result}")
    errors.append("brief read")

# --- Summary ---
print(f"\n{'='*50}")
print(f"E2E CLI RESULT: {len(errors)} failures out of 10 checks")
if errors:
    for err in errors:
        print(f"  FAIL: {err}")
    sys.exit(1)
else:
    print("  ALL CLI CHECKS PASSED!")
