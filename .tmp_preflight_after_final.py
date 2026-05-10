import sqlite3
from pathlib import Path
from uuid import UUID
from sqlmodel import Session
from foundry.db import engine
from foundry.services.snapshot_service import preflight_snapshot_endpoints

adb = Path.home() / 'AppData' / 'Local' / 'CelonisDeliveryForge' / 'foundry-local.db'
conn = sqlite3.connect(str(adb))
cur = conn.cursor()
cur.execute('SELECT c.id, c.name, cc.tenant_base_url FROM client c JOIN celonisconnection cc ON cc.client_id = c.id WHERE cc.is_active = 1')
rows = cur.fetchall()
conn.close()

cid = None
for r in rows:
    s = f"{r[1] or ''} {r[2] or ''}".lower()
    if 'roboyo sandbox' in s:
        cid = UUID(r[0]); name=r[1]; base=r[2]; break
if cid is None:
    raise SystemExit('Roboyo Sandbox not found')

print('target_client_id=', cid)
print('target_name=', name)
print('target_base_url=', base)

with Session(engine) as session:
    report = preflight_snapshot_endpoints(session, client_id=cid)

print('\n=== PREFLIGHT SUMMARY (AFTER FIX, FINAL) ===')
for family, entries in report.get('families', {}).items():
    attempted = len(entries)
    ok = sum(1 for e in entries if e.get('ok'))
    with_items = sum(1 for e in entries if (e.get('items_detected') or 0) > 0)
    redirects = sum(1 for e in entries if e.get('error') == 'redirect-to-login')
    print(f"{family}: attempted={attempted}, ok={ok}, endpoints_with_items={with_items}, redirects={redirects}")
