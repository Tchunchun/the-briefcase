"""E2E test: provision clean page + full CRUD cycle.

Requires environment variables:
  NOTION_API_TOKEN — Notion integration token
  NOTION_PARENT_PAGE_ID — Page ID to create test sub-page under

Run manually: PYTHONPATH=. python3 tests/e2e/test_notion_v2_e2e.py
Not included in automated test suite (requires live Notion access).
"""
import os
import sys

from src.integrations.notion.client import NotionClient
from src.integrations.notion.provisioner import NotionProvisioner
from src.core.storage.config import NotionConfig
from src.integrations.notion.backend import NotionBackend

PARENT_PAGE_ID = os.environ.get('NOTION_PARENT_PAGE_ID', '')
if not PARENT_PAGE_ID or not os.environ.get('NOTION_API_TOKEN'):
    print('Skipping E2E: set NOTION_API_TOKEN and NOTION_PARENT_PAGE_ID env vars')
    sys.exit(0)

client = NotionClient()

# 1. Create a clean sub-page
test_page = client.create_page(PARENT_PAGE_ID, 'E2E Test v2', icon='\U0001f9ea')
test_page_id = test_page['id']
print(f'Created test page: {test_page_id}')

# 2. Provision
provisioner = NotionProvisioner(client)
resource_ids, result = provisioner.provision(test_page_id, template_dir='template')
print(f'\nProvision success: {result.success}')
print(f'  DBs created: {result.databases_created}')
print(f'  Pages created: {result.pages_created}')
print(f'  Templates seeded: {result.templates_seeded}')
print(f'  Errors: {result.errors}')
for k, v in resource_ids.items():
    print(f'  {k}: {v}')

if not result.success:
    print('\nPROVISION FAILED')
    exit(1)

# 3. Backend CRUD
config = NotionConfig(parent_page_id=test_page_id, databases=resource_ids)
backend = NotionBackend(config, '.')
errors = []

# Inbox
try:
    backend.append_inbox({"text": "E2E test idea", "type": "idea"})
    ideas = backend.read_inbox()
    assert len(ideas) >= 1, f"Expected >= 1 idea, got {len(ideas)}"
    assert ideas[0]["status"] == "new"
    print('\n[PASS] append_inbox + read_inbox')
except Exception as e:
    print(f'\n[FAIL] inbox: {e}')
    errors.append(f'inbox: {e}')

# Backlog Feature
try:
    backend.write_backlog_row({
        "title": "E2E test feature",
        "type": "Feature",
        "status": "draft",
        "priority": "High",
    })
    rows = backend.read_backlog()
    features = [r for r in rows if r["type"] == "Feature"]
    assert len(features) >= 1
    assert features[0]["status"] == "draft"
    print('[PASS] write_backlog_row (Feature) + read_backlog')
except Exception as e:
    print(f'[FAIL] backlog feature: {e}')
    errors.append(f'backlog feature: {e}')

# Backlog Task
try:
    backend.write_backlog_row({
        "title": "E2E test task",
        "type": "Task",
        "status": "to-do",
        "priority": "Medium",
    })
    rows = backend.read_backlog()
    tasks = [r for r in rows if r["type"] == "Task"]
    assert len(tasks) >= 1
    assert tasks[0]["status"] == "to-do"
    print('[PASS] write_backlog_row (Task) + read_backlog')
except Exception as e:
    print(f'[FAIL] backlog task: {e}')
    errors.append(f'backlog task: {e}')

# Decisions
try:
    backend.append_decision({
        "id": "D-E2E",
        "title": "E2E test decision",
        "date": "2026-03-16",
        "status": "accepted",
        "why": "Testing",
    })
    decs = backend.read_decisions()
    assert len(decs) >= 1
    print('[PASS] append_decision + read_decisions')
except Exception as e:
    print(f'[FAIL] decisions: {e}')
    errors.append(f'decisions: {e}')

# Idempotency re-run
try:
    resource_ids2, result2 = provisioner.provision(test_page_id, template_dir='template')
    assert result2.success
    assert len(result2.databases_created) == 0, "Should not create new DBs on re-run"
    assert resource_ids2["backlog"] == resource_ids["backlog"]
    print('[PASS] idempotency re-run')
except Exception as e:
    print(f'[FAIL] idempotency: {e}')
    errors.append(f'idempotency: {e}')

# Summary
print(f'\n=== E2E Summary: {len(errors)} failures ===')
if errors:
    for err in errors:
        print(f'  FAIL: {err}')
else:
    print('  All E2E checks passed!')
