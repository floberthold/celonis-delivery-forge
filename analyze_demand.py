#!/usr/bin/env python3
"""
Use Celonis Data Agent tools to analyze Demand Forecasting model.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add agent to path
agent_dir = Path(__file__).parent.parent / "external resources" / "Code by Florian" / "celonis-data-agent"
sys.path.insert(0, str(agent_dir))

# Load .env
from dotenv import load_dotenv
load_dotenv(agent_dir / ".env")

from celonis_data_agent.tools import (
    list_data_models,
    list_tables,
    query_data_model_sql,
)

async def main():
    user_token = os.getenv("CELONIS_USER_TOKEN")
    if not user_token:
        print("ERROR: CELONIS_USER_TOKEN not set")
        sys.exit(1)
    
    print("🔍 Using Celonis Data Agent Tools")
    print("=" * 80)
    
    # Step 1: List data models
    print("\n📊 Listing data models...")
    models_result = await list_data_models(user_token)
    
    if not models_result.get("count"):
        print("No data models found!")
        return
    
    models = models_result.get("items", [])
    print(f"Found {models_result['count']} data models")
    
    # Find Demand Forecasting model
    demand_model = None
    for model in models:
        name = model.get("name", "").lower()
        print(f"  - {model.get('name')} (ID: {model.get('id')})")
        
        if any(keyword in name for keyword in ["demand", "forecast"]):
            demand_model = model
    
    if not demand_model:
        print("\n⚠️ No Demand Forecasting model found. Trying first available model...")
        demand_model = models[0] if models else None
    
    if not demand_model:
        print("No model available!")
        return
    
    model_id = demand_model.get("id")
    model_name = demand_model.get("name")
    print(f"\n✅ Using: {model_name} (ID: {model_id})")
    print("=" * 80)
    
    # Step 2: List tables
    print(f"\n📋 Tables in '{model_name}':")
    tables_result = await list_tables(user_token, data_model_id=model_id)
    
    tables = tables_result.get("items", [])
    for table in tables:
        print(f"  - {table.get('name')} (ID: {table.get('id')})")
    
    # Step 3: Query for expensive materials
    print("\n" + "=" * 80)
    print("💰 Querying for expensive materials...")
    
    # Try to find materials and their prices
    sql_queries = [
        # Generic query for materials with prices
        """
        SELECT * FROM "Materials"
        WHERE Price IS NOT NULL
        ORDER BY Price DESC
        LIMIT 10
        """,
        # Alternative
        """
        SELECT TOP 10 * FROM Materials
        ORDER BY Price DESC
        """,
        # Another alternative
        """
        SELECT * FROM "MATERIAL"
        WHERE "PRICE" IS NOT NULL
        ORDER BY "PRICE" DESC
        LIMIT 10
        """,
    ]
    
    result = None
    for i, sql in enumerate(sql_queries):
        try:
            print(f"\n  Attempting query {i+1}...")
            result = await query_data_model_sql(user_token, data_model_id=model_id, sql=sql.strip(), limit=1000)
            
            rows = result.get("rows", [])
            if rows:
                print(f"  ✅ Query successful! Found {len(rows)} rows")
                break
        except Exception as e:
            print(f"  ⚠️ Query {i+1} failed: {str(e)[:80]}")
    
    if result and result.get("rows"):
        rows = result["rows"]
        print(f"\n📊 Top Materials by Price:")
        print("-" * 80)
        for i, row in enumerate(rows[:5], 1):
            print(f"{i}. {row}")
        
        # Most expensive material
        most_expensive = rows[0]
        print("\n" + "=" * 80)
        print("🏆 MOST EXPENSIVE MATERIAL:")
        print(most_expensive)
        print("=" * 80)
        
        # Step 4: Get demands for this material
        print("\n📦 Querying demands for most expensive material...")
        
        # Get the material identifier (usually first key)
        material_keys = list(most_expensive.keys())
        material_id_key = next((k for k in material_keys if "id" in k.lower() or "material" in k.lower()), material_keys[0])
        material_id = most_expensive[material_id_key]
        
        print(f"  Material ID: {material_id} (Key: {material_id_key})")
        
        # Query demands
        demand_queries = [
            f"""
            SELECT * FROM "Demands"
            WHERE MaterialID = '{material_id}'
            ORDER BY Quantity DESC
            LIMIT 20
            """,
            f"""
            SELECT * FROM "DEMAND"
            WHERE "MATERIAL_ID" = '{material_id}'
            LIMIT 20
            """,
            f"""
            SELECT * FROM "Orders"
            WHERE Material = '{material_id}'
            LIMIT 20
            """,
        ]
        
        for i, sql in enumerate(demand_queries):
            try:
                print(f"\n  Attempting demand query {i+1}...")
                demand_result = await query_data_model_sql(user_token, data_model_id=model_id, sql=sql.strip(), limit=1000)
                
                demand_rows = demand_result.get("rows", [])
                if demand_rows:
                    print(f"  ✅ Query successful! Found {len(demand_rows)} demands")
                    
                    print(f"\n📦 DEMANDS FOR MATERIAL '{material_id}':")
                    print("-" * 80)
                    for j, demand in enumerate(demand_rows[:10], 1):
                        print(f"{j}. {demand}")
                    break
            except Exception as e:
                print(f"  ⚠️ Demand query {i+1} failed: {str(e)[:80]}")
    else:
        print("\n⚠️ No results from material query")
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")

if __name__ == "__main__":
    asyncio.run(main())
