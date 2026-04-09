#!/usr/bin/env python3
"""Debug script to diagnose package asset extraction issues.

Usage:
    python debug_package_extraction.py <connection_id> --package-key <key> --package-id <id> --token <token>
    
Example:
    python debug_package_extraction.py 550e8400-e29b-41d4-a716-446655440000 \
      --package-key "9a124d42_6793_4246_9091_5ae9d2ae13f6" \
      --package-id "513cc93d-50fb-45ab-98e3-c43ae7445790" \
      --token "YOUR_CELONIS_API_TOKEN"
"""

import json
import sys
from pathlib import Path
from uuid import UUID

# Add repo to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from foundry.integrations.celonis_import import CelonisGateway
from foundry.models import CelonisConnection
from foundry.db import engine
from foundry.settings import Settings
from sqlmodel import Session, select


def debug_package_extraction(
    connection_id: str,
    package_key: str,
    package_id: str,
    token: str | None = None,
):
    """Debug why assets aren't being extracted for a package."""
    
    # Get connection
    try:
        conn_uuid = UUID(connection_id)
    except ValueError:
        print(f"❌ Invalid connection ID: {connection_id}")
        return
    
    with Session(engine) as session:
        conn = session.exec(
            select(CelonisConnection).where(CelonisConnection.id == conn_uuid)
        ).first()
        
        if not conn:
            print(f"❌ Connection {connection_id} not found in database")
            return
    
    print(f"📡 Debugging package extraction for:")
    print(f"   Package Key: {package_key}")
    print(f"   Package ID: {package_id}")
    print(f"   Tenant: {conn.tenant_base_url}")
    print()
    
    if not token:
        print("⚠️  No token provided. Using default CelonisGateway (may fail if no credentials configured)")
        print("    Provide --token to use a specific API token")
        print()
    
    # Create gateway
    try:
        if token:
            settings_obj = Settings(celonis_api_token=token)
        else:
            settings_obj = Settings()
        gw = CelonisGateway(settings_obj)
    except Exception as e:
        print(f"❌ Failed to create gateway: {e}")
        return
    candidates = [row for row in (package_key, package_id) if row]
    unique_candidates = list(dict.fromkeys(candidates))
    
    print(f"📋 Testing {len(unique_candidates)} unique identifier(s):")
    for i, candidate in enumerate(unique_candidates, 1):
        print(f"   {i}. {candidate}")
    print()
    
    endpoints_to_test = [
        "/package-manager/api/packages/{candidate}/assets",
        "/studio/api/packages/{candidate}/assets",
        "/package-manager/api/packages/{candidate}/nodes",
    ]
    
    results = []
    
    for candidate in unique_candidates:
        print(f"\n🔍 Testing with candidate: {candidate}")
        print("=" * 70)
        
        for endpoint_template in endpoints_to_test:
            endpoint = endpoint_template.replace("{candidate}", candidate)
            print(f"\n  Endpoint: {endpoint}")
            
            try:
                result = gw.extract_full(
                    tenant_base_url=conn.tenant_base_url,
                    source_path=endpoint,
                )
                
                print(f"    Status: {'✓ OK' if result.ok else '✗ ERROR'}")
                print(f"    Body length: {len(result.body) if result.body else 0} bytes")
                
                if result.body:
                    try:
                        payload = json.loads(result.body)
                        print(f"    Response type: {type(payload).__name__}")
                        
                        # Check for common asset list keys
                        if isinstance(payload, dict):
                            print(f"    Top-level keys: {list(payload.keys())[:10]}")
                            
                            for key in ["assets", "items", "data", "content"]:
                                if key in payload:
                                    value = payload[key]
                                    if isinstance(value, list):
                                        print(f"    → '{key}' is a list with {len(value)} item(s)")
                                    elif isinstance(value, dict):
                                        print(f"    → '{key}' is a dict with keys: {list(value.keys())[:5]}")
                                    else:
                                        print(f"    → '{key}' is {type(value).__name__}")
                        elif isinstance(payload, list):
                            print(f"    → Response is a list with {len(payload)} item(s)")
                        
                        results.append({
                            "endpoint": endpoint,
                            "ok": result.ok,
                            "has_data": bool(result.body) and json.loads(result.body) not in [[], {}, None],
                            "payload_type": type(payload).__name__,
                        })
                    except json.JSONDecodeError:
                        print(f"    ⚠️  Response body is not valid JSON")
                        results.append({
                            "endpoint": endpoint,
                            "ok": result.ok,
                            "has_data": False,
                            "error": "Invalid JSON",
                        })
                else:
                    print(f"    ⚠️  Empty response body")
                    results.append({
                        "endpoint": endpoint,
                        "ok": result.ok,
                        "has_data": False,
                        "error": "Empty body",
                    })
            
            except Exception as e:
                print(f"    ✗ Exception: {type(e).__name__}: {e}")
                results.append({
                    "endpoint": endpoint,
                    "ok": False,
                    "has_data": False,
                    "error": str(e),
                })
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    successful = sum(1 for r in results if r.get("ok"))
    with_data = sum(1 for r in results if r.get("has_data"))
    
    print(f"Total endpoints tested: {len(results)}")
    print(f"✓ OK responses: {successful}")
    print(f"✓ Responses with data: {with_data}")
    print(f"✗ Error/empty responses: {len(results) - successful}")
    
    if with_data == 0:
        print("\n⚠️  NO ENDPOINTS RETURNED ASSET DATA")
        print("\nPossible causes:")
        print("  1. Package genuinely has no assets")
        print("  2. Token doesn't have permission to see assets (despite broad permissions)")
        print("  3. Endpoints don't exist on this tenant")
        print("  4. Package ID/key is incorrect")
        print("  5. API response format is different than expected")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Debug package asset extraction",
        epilog="Example: python debug_package_extraction.py 550e8400-e29b-41d4-a716-446655440000 --package-key 9a124d42_... --package-id 513cc93d-... --token YOUR_TOKEN"
    )
    parser.add_argument("connection_id", help="UUID of the Celonis connection")
    parser.add_argument("--package-key", required=True, help="Package key")
    parser.add_argument("--package-id", required=True, help="Package ID")
    parser.add_argument("--token", help="Celonis API token (optional, uses default if not provided)")
    
    args = parser.parse_args()
    
    debug_package_extraction(
        args.connection_id,
        args.package_key,
        args.package_id,
        token=args.token,
    )
