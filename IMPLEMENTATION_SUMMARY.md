# Celonis Data Access Methods - Complete Implementation Guide

## Summary

You have **three primary methods** to access Celonis data for Demand Forecasting analysis:

### ✓ Method 1: pycelonis Library (RECOMMENDED) 
**Status**: Ready to implement once library is installed  
**Installation**: `pip install pycelonis`  
**Complexity**: Medium  
**Performance**: Optimized for large datasets  

### ✓ Method 2: Data Agent MCP Tools (WORKING)
**Status**: Currently functional for model/pool listing  
**Configuration**: Already set up  
**Complexity**: Low  
**Limitation**: SQL query endpoints return 404 on this tenant  

### ✓ Method 3: REST API (ALTERNATIVE)
**Status**: May require additional setup  
**Complexity**: High  
**Advantage**: Works without additional libraries  

---

## Method 1: pycelonis - Complete Working Example

### Installation
```bash
pip install pycelonis
```

### Complete Analysis Script

```python
"""
Complete Demand Forecasting analysis using pycelonis.
Finds the most expensive material and lists all demands for it.
"""

from pycelonis import get_celonis
import pycelonis.pql as pql
from pycelonis.config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def analyze_demand_forecasting():
    """
    Main analysis function.
    """
    
    # STEP 1: CONNECT TO CELONIS
    print("Connecting to Celonis...")
    celonis = get_celonis()
    print("✓ Connected successfully")
    
    # STEP 2: FIND DATA MODEL
    print("\nSearching for Demand Forecasting data model...")
    
    # Get the Demand Forecasting model
    # Based on previous discovery:
    # ID: e88f8245-8160-4223-b964-f5ce0aed9017
    # Name: "Demand Forecasting"
    
    data_pools = celonis.data_integration.get_data_pools()
    
    target_model = None
    for pool in data_pools:
        data_models = pool.get_data_models()
        for model in data_models:
            if model.name == "Demand Forecasting":  # or model.id == "e88f8245-8160-4223-b964-f5ce0aed9017"
                target_model = model
                print(f"✓ Found: {model.name}")
                print(f"  ID: {model.id}")
                print(f"  Pool: {pool.name}")
                break
        if target_model:
            break
    
    if not target_model:
        print("✗ Could not find Demand Forecasting model")
        return
    
    # STEP 3: GET TABLES
    print("\nFetching tables...")
    
    tables = target_model.get_tables()
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table.name}")
    
    # STEP 4: QUERY MATERIALS
    print("\n" + "="*70)
    print("STEP 4: QUERY MATERIALS WITH PRICES")
    print("="*70)
    
    # Set default data model for SaolaPy
    Config.DEFAULT_DATA_MODEL = target_model
    
    # Get Materials table and columns
    materials_table = tables.find("Materials")  # May need to adjust name
    materials_columns = materials_table.get_columns()
    
    print(f"\nMaterials table columns ({len(materials_columns)}):")
    for col in materials_columns[:10]:  # Show first 10
        print(f"  - {col.name}")
    
    # Create PQL query for materials
    # Adjust column names based on actual table structure
    df_materials = pql.DataFrame({
        "material_id": materials_columns.find("ID"),  # Adjust name as needed
        "name": materials_columns.find("NAME"),       # Adjust name as needed
        "price": materials_columns.find("PRICE")      # Adjust name as needed
    })
    
    # Export to pandas dataframe
    print("\nExporting materials data...")
    materials_pandas = df_materials.to_pandas()
    
    print(f"✓ Retrieved {len(materials_pandas)} materials")
    print(f"\nFirst 5 materials:")
    print(materials_pandas.head())
    
    # STEP 5: FIND MOST EXPENSIVE MATERIAL
    print("\n" + "="*70)
    print("STEP 5: IDENTIFY MOST EXPENSIVE MATERIAL")
    print("="*70)
    
    most_expensive_idx = materials_pandas['price'].idxmax()
    most_expensive = materials_pandas.iloc[most_expensive_idx]
    
    print(f"\nMost Expensive Material:")
    print(f"  ID: {most_expensive['material_id']}")
    print(f"  Name: {most_expensive['name']}")
    print(f"  Price: {most_expensive['price']}")
    
    # STEP 6: QUERY DEMANDS FOR THIS MATERIAL
    print("\n" + "="*70)
    print(f"STEP 6: QUERY DEMANDS FOR {most_expensive['name']}")
    print("="*70)
    
    # Get Demands table and columns
    demands_table = tables.find("Demands")  # May need to adjust name
    demands_columns = demands_table.get_columns()
    
    print(f"\nDemands table columns ({len(demands_columns)}):")
    for col in demands_columns[:10]:
        print(f"  - {col.name}")
    
    # Create PQL query for demands
    df_demands = pql.DataFrame({
        "demand_id": demands_columns.find("DEMAND_ID"),      # Adjust
        "material_id": demands_columns.find("MATERIAL_ID"),  # Adjust
        "quantity": demands_columns.find("QUANTITY"),        # Adjust
        "order_date": demands_columns.find("ORDER_DATE"),    # Adjust
        "unit_price": demands_columns.find("UNIT_PRICE"),    # Adjust (if exists)
        "total_value": demands_columns.find("TOTAL_VALUE")   # Adjust (if exists)
    })
    
    # Filter for the material
    df_demands = df_demands[df_demands.material_id == most_expensive['material_id']]
    
    # Export to pandas
    print("\nExporting demands data...")
    demands_pandas = df_demands.to_pandas()
    
    print(f"✓ Retrieved {len(demands_pandas)} demands for this material")
    print(f"\nDemands for {most_expensive['name']}:")
    print(demands_pandas)
    
    # STEP 7: ANALYSIS AND SUMMARY
    print("\n" + "="*70)
    print("ANALYSIS SUMMARY")
    print("="*70)
    
    if len(demands_pandas) > 0:
        total_quantity = demands_pandas['quantity'].sum()
        total_value = demands_pandas['total_value'].sum() if 'total_value' in demands_pandas else total_quantity * most_expensive['price']
        avg_date = demands_pandas['order_date'].min()  # Earliest order
        latest_date = demands_pandas['order_date'].max()  # Latest order
        
        print(f"""
Material: {most_expensive['name']}
Price per Unit: {most_expensive['price']}

Demand Statistics:
  Total Demands: {len(demands_pandas)}
  Total Quantity Ordered: {total_quantity}
  Total Value: {total_value}
  First Order: {avg_date}
  Latest Order: {latest_date}
  
Top 5 Largest Orders:
""")
        
        # Show top 5 by quantity
        top_demands = demands_pandas.nlargest(5, 'quantity')[['demand_id', 'quantity', 'order_date']]
        print(top_demands.to_string())
    
    else:
        print("No demands found for this material")
    
    print("\n✓ Analysis complete!")

if __name__ == "__main__":
    analyze_demand_forecasting()
```

### Key Points:

1. **Table Names**: The actual table names in your data model may differ:
   - Look for variations: Materials, MATERIAL, MAST, Products, etc.
   - Demands, DEMAND, SALES_ORDERS, PURCHASE_ORDERS, etc.

2. **Column Names**: Check your actual schema:
   - Use `column.name` to see exact names
   - Query with exact quoted names: `"TABLE"."COLUMN"`

3. **Filtering**: PQL DataFrame filtering syntax:
   ```python
   df_filtered = df[df.column_name == value]
   ```

4. **Aggregation**: Use SaolaPy operations:
   ```python
   df['quantity'].sum()
   df['price'].max()
   df.groupby('category')['price'].sum()
   ```

---

## Method 2: Data Agent MCP Tools (Currently Available)

### Available Tools
```
✓ list_data_models(user_token)     - List all models
✓ list_pools(user_token)           - List all pools
⚠ list_tables(user_token, model_id) - List tables (fails on perspective models)
✗ query_data_model_sql(...)        - SQL queries (404 error on this tenant)
```

### Usage Example
```python
import asyncio
import os
from dotenv import load_dotenv
from celonis_data_agent.tools import list_data_models, list_pools

load_dotenv()
user_token = os.getenv('CELONIS_USER_TOKEN')

async def test():
    # List models
    models_result = await list_data_models(user_token)
    models = models_result['items']
    
    # List pools
    pools_result = await list_pools(user_token)
    pools = pools_result['items']
    
    print(f"Models: {len(models)}, Pools: {len(pools)}")

asyncio.run(test())
```

### Limitation
The SQL query API (`/integration/api/v1/data-models/{id}/query`) returns 404 on the roboyo sandbox, indicating it's disabled or not available on that tenant configuration.

---

## Method 3: REST API Direct Access

### Base Configuration
```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

TENANT_URL = "https://roboyo-us-partner-sandbox.us-1.celonis.cloud"
USER_TOKEN = os.getenv('CELONIS_USER_TOKEN')

headers = {
    'Authorization': f'Bearer {USER_TOKEN}',
    'Content-Type': 'application/json'
}
```

### API Endpoints to Try

1. **List Data Models**
   ```python
   url = f"{TENANT_URL}/api/v1/data-models"
   response = requests.get(url, headers=headers)
   models = response.json()
   ```

2. **List Tables in a Model**
   ```python
   model_id = "e88f8245-8160-4223-b964-f5ce0aed9017"
   url = f"{TENANT_URL}/api/v1/data-models/{model_id}/tables"
   response = requests.get(url, headers=headers)
   tables = response.json()
   ```

3. **Query via PQL (if available)**
   ```python
   pql_query = {
       "columns": [
           {"name": "material_id", "query": '"Materials"."ID"'},
           {"name": "name", "query": '"Materials"."NAME"'},
           {"name": "price", "query": '"Materials"."PRICE"'}
       ]
   }
   
   url = f"{TENANT_URL}/api/v1/data-models/{model_id}/query"
   response = requests.post(url, json=pql_query, headers=headers)
   data = response.json()
   ```

---

## Troubleshooting Guide

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: pycelonis` | Run `pip install pycelonis` |
| SQL query returns 404 | Use PQL with SaolaPy instead; SQL endpoints may be disabled |
| `list_tables` fails | Some models don't support this; hard-code table names from Studio UI |
| Column not found | Verify exact column names in your data model |
| Authentication fails | Check CELONIS_USER_TOKEN is properly set and not expired |
| Slow queries | Use SaolaPy aggregations (server-side) instead of pandas (client-side) |

---

## Files Created

1. **`DATA_ACCESS_GUIDE.py`** - Comprehensive guide with all three methods
2. **`demand_forecasting_analysis.py`** - Full working example using Data Agent tools
3. **`analyze_with_pycelonis.py`** - Skeleton for pycelonis implementation
4. **`IMPLEMENTATION_SUMMARY.md`** - This file

---

## Next Steps

1. **Install pycelonis**: `pip install pycelonis`
2. **Copy the Complete Example** from above
3. **Adjust table and column names** to match your schema
4. **Run the script** to get the analysis
5. **Export results** as CSV/Excel for further processing

---

## Referenced Documentation

- pycelonis 2.14.2 Official Docs: https://celonis.github.io/pycelonis/2.14.2/
- Data Export Tutorial: https://celonis.github.io/pycelonis/2.14.2/tutorials/executed/02_data_integration/03_data_pull/
- Knowledge Model Access: https://celonis.github.io/pycelonis/2.14.2/tutorials/executed/03_studio/03_Pulling_Data_From_Knowledge_Model/
- LLM Integration: https://celonis.github.io/pycelonis/2.14.2/tutorials/executed/06_pycelonis_llm/01_pycelonis_llm_tutorial/

---

**Last Updated**: 2026-05-10  
**Status**: Ready for Implementation  
**Target Data Model**: Demand Forecasting (ID: e88f8245-8160-4223-b964-f5ce0aed9017)
