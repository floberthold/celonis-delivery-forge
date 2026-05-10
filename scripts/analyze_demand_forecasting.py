#!/usr/bin/env python3
"""
Analyze Demand Forecasting data model in roboyo sandbox.
Finds the most expensive material and lists concrete demands for it.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the external agent directory to the path
agent_dir = Path(__file__).parent.parent / "external resources" / "Code by Florian" / "celonis-data-agent"
sys.path.insert(0, str(agent_dir))

# Load environment variables from agent .env
from dotenv import load_dotenv
env_file = agent_dir / ".env"
load_dotenv(env_file)

from celonis_data_agent.client import CelonisClient
from celonis_data_agent.config import get_settings
from celonis_data_agent.auth import validate_user_token


async def main():
    settings = get_settings()
    client = CelonisClient(settings)
    
    # Get user token from environment
    user_token = os.getenv("CELONIS_USER_TOKEN")
    if not user_token:
        print("ERROR: CELONIS_USER_TOKEN not set in environment")
        sys.exit(1)
    
    # Validate token
    token = validate_user_token(user_token)
    
    print(f"🔌 Connecting to: {settings.tenant_url}")
    print("=" * 80)
    
    # Step 1: List all data models
    print("\n📊 Listing available data models...")
    models = await client.list_data_models(token)
    
    demand_forecasting_model = None
    for model in models:
        print(f"  - {model.get('name', 'Unknown')} (ID: {model.get('id', 'Unknown')})")
        if "demand" in str(model.get('name', '')).lower() or "forecasting" in str(model.get('name', '')).lower():
            demand_forecasting_model = model
    
    if not demand_forecasting_model:
        print("\n❌ No 'Demand Forecasting' data model found!")
        print("\nSearching for similar model names...")
        for model in models:
            name = str(model.get('name', '')).lower()
            if any(keyword in name for keyword in ['demand', 'forecast', 'planning', 'inventory']):
                demand_forecasting_model = model
                print(f"  Found potential match: {model.get('name')} (ID: {model.get('id')})")
                break
    
    if not demand_forecasting_model:
        print("No suitable model found. Exiting.")
        sys.exit(1)
    
    model_id = demand_forecasting_model.get('id')
    model_name = demand_forecasting_model.get('name')
    print(f"\n✅ Using model: {model_name} (ID: {model_id})")
    print("=" * 80)
    
    # Step 2: List tables in the model
    print(f"\n📋 Tables in '{model_name}':")
    tables = await client.list_tables(token, data_model_id=model_id, page=1, page_size=100)
    
    table_names = []
    for table in tables:
        table_id = table.get('id', 'Unknown')
        table_display_name = table.get('displayName') or table.get('name', 'Unknown')
        print(f"  - {table_display_name} (ID: {table_id})")
        table_names.append(table_display_name)
    
    print("=" * 80)
    
    # Step 3: Find material/product table and price information
    print("\n🔍 Looking for material/product pricing information...")
    
    # Common patterns for material/price tables
    material_tables = [t for t in table_names if any(x in t.lower() for x in ['material', 'product', 'item', 'sku', 'article'])]
    price_keywords = ['price', 'cost', 'value', 'amount']
    
    print(f"\nIdentified potential material tables: {material_tables}")
    
    # Step 4: Execute SQL to find expensive materials
    print("\n💰 Querying for most expensive material...")
    
    if material_tables:
        # Build a query for the first material table found
        material_table = material_tables[0]
        
        # Try different query approaches
        queries = [
            # Approach 1: Simple aggregation
            f"""
            SELECT 
                Material_ID, 
                Material_Name,
                MAX(Price) as Max_Price,
                AVG(Price) as Avg_Price
            FROM "{material_table}"
            WHERE Price IS NOT NULL
            GROUP BY Material_ID, Material_Name
            ORDER BY MAX(Price) DESC
            LIMIT 10
            """,
            
            # Approach 2: Without alias names
            f"""
            SELECT *
            FROM "{material_table}"
            ORDER BY Price DESC
            LIMIT 5
            """,
        ]
        
        result = None
        for i, sql_query in enumerate(queries):
            try:
                print(f"\n  Attempting query {i+1}...")
                result = await client.execute_sql(token, data_model_id=model_id, sql=sql_query.strip(), limit=1000)
                
                if result:
                    print(f"  ✅ Query {i+1} successful!")
                    break
            except Exception as e:
                print(f"  ⚠️  Query {i+1} failed: {str(e)[:100]}")
                continue
        
        if result:
            # Display results
            rows = result.get('rows', [])
            if rows:
                print(f"\n📊 Top Materials by Price:")
                for i, row in enumerate(rows[:5], 1):
                    print(f"\n  {i}. {row}")
                
                # Get the most expensive material
                most_expensive = rows[0] if rows else None
                
                if most_expensive:
                    print("\n" + "=" * 80)
                    print(f"\n🏆 Most Expensive Material:")
                    print(f"  {most_expensive}")
                    print("=" * 80)
                    
                    # Step 5: Find demands for this material
                    print(f"\n📦 Looking for demands for this material...")
                    
                    # Identify demand table
                    demand_tables = [t for t in table_names if any(x in t.lower() for x in ['demand', 'order', 'sales', 'forecast'])]
                    
                    if demand_tables:
                        demand_table = demand_tables[0]
                        print(f"  Using demand table: {demand_table}")
                        
                        # Query demands
                        material_id_key = list(most_expensive.keys())[0]  # Get first key as material ID
                        material_id_value = most_expensive[material_id_key]
                        
                        demand_query = f"""
                        SELECT *
                        FROM "{demand_table}"
                        WHERE Material_ID = '{material_id_value}'
                        LIMIT 50
                        """
                        
                        try:
                            demand_result = await client.execute_sql(token, data_model_id=model_id, sql=demand_query.strip(), limit=1000)
                            
                            demand_rows = demand_result.get('rows', [])
                            if demand_rows:
                                print(f"\n📦 Found {len(demand_rows)} demands for this material:")
                                for i, demand in enumerate(demand_rows[:10], 1):
                                    print(f"\n  {i}. {demand}")
                            else:
                                print("\n  No demands found for this material.")
                        except Exception as e:
                            print(f"\n  Error querying demands: {str(e)[:100]}")
            else:
                print("\n  No rows returned from query.")
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")


if __name__ == "__main__":
    asyncio.run(main())
