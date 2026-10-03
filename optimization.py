from sqlalchemy import create_engine, text
import time
from typing import List, Tuple
import pandas as pd

engine = create_engine(
    "mysql+mysqlconnector://chrystel:Chrystel%401234@34.142.244.237:3306/stadvdb"
)

def create_indexes():

    secondary_indexes = [
        "CREATE INDEX indx_products_category ON DimProducts(productID)",
        "CREATE INDEX indx_users_couriername ON DimRiders(couriername)",
        "CREATE INDEX indx_users_country ON DimUsers(country)",
        "CREATE INDEX indx_users_city ON DimUsers(city)",
        "CREATE INDEX indx_orders_deliverydate ON FactOrders(deliveryDate)",
        "CREATE INDEX indx_orders_deliverydate_orderid ON FactOrders(deliveryDate, orderID)",
    ]

    with engine.connect() as conn:
            print("\nCreating secondary indexes...")
            for idx_query in secondary_indexes:
                try:
                    conn.execute(text(idx_query))
                    conn.commit()
                    print(f"✓ Created: {idx_query.split('INDEX')[1].split('ON')[0].strip()}")
                except Exception as e:
                    # Check if it's a duplicate key error (index already exists)
                    if "1061" in str(e) or "Duplicate key" in str(e):
                        print(f"○ Already exists: {idx_query.split('INDEX')[1].split('ON')[0].strip()}")
                    else:
                        print(f"✗ Error: {idx_query.split('INDEX')[1].split('ON')[0].strip()}")
                        print(f"  Details: {str(e)[:100]}")


def drop_indexes():
    """Drop all created indexes for testing purposes"""
    
    indexes_to_drop = [
        "DROP INDEX indx_products_category ON DimProducts",
        "DROP INDEX indx_users_couriername ON DimRiders",
        "DROP INDEX indx_users_country ON DimUsers",
        "DROP INDEX indx_users_city ON DimUsers",
        "DROP INDEX indx_orders_deliverydate ON FactOrders",
        "DROP INDEX indx_orders_deliverydate_orderid ON FactOrders"
    ]
    
    with engine.connect() as conn:
        print("Dropping indexes...")
        for drop_query in indexes_to_drop:
            try:
                conn.execute(text(drop_query))
                conn.commit()
                print(f"✓ Dropped: {drop_query.split('INDEX')[1].split('ON')[0].strip()}")
            except Exception as e:
                print(f"✗ Index not found or error: {drop_query.split('INDEX')[1].split('ON')[0].strip()}")


def execute_query_with_timing(query: str, description: str) -> Tuple[float, any]:
    """Execute a query and return execution time and results"""
    with engine.connect() as conn:
        start_time = time.time()
        result = conn.execute(text(query))
        rows = result.fetchall()
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"{description}: {execution_time:.4f} seconds ({len(rows)} rows)")
        return execution_time, rows


def analyze_performance():
    """
    Analyze query performance before and after optimization.
    Compares original queries vs optimized versions.
    """
    # BEFORE: Original unoptimized queries
    original_queries = {
        "Q1: Total Orders Over Time (ORIGINAL)":
            """ SELECT
                    DATE_FORMAT(o.deliveryDate, '%Y-%m') as period,
                    COUNT(DISTINCT o.orderID) as total_orders
                FROM FactOrders o
                JOIN DimUsers u ON o.userID = u.userID
                WHERE o.deliveryDate >= '2025-01-01' AND o.deliveryDate <= '2025-10-01'
                GROUP BY DATE_FORMAT(o.deliveryDate, '%Y-%m')
            """,
    }
   
    # AFTER: Optimized queries
    optimized_queries = {
        "Q1: Total Orders Over Time (OPTIMIZED)":
            """ SELECT
                    YEAR(o.deliveryDate) as year,
                    MONTH(o.deliveryDate) as month,
                    COUNT(*) as total_orders
                FROM FactOrders o
                WHERE o.deliveryDate >= '2025-01-01' AND o.deliveryDate <= '2025-10-01'
                GROUP BY YEAR(o.deliveryDate), MONTH(o.deliveryDate)
                ORDER BY YEAR(o.deliveryDate), MONTH(o.deliveryDate)
            """,
    }
   
    # Keep other queries for index testing
    other_queries = {
       
        "Q2: Total Sales Per Location":
            """ SELECT
                    u.city as location,
                    SUM(o.quantity * p.price) as total_sales
                FROM FactOrders o
                JOIN DimUsers u ON o.userID = u.userID
                JOIN DimProducts p ON o.productID = p.productID
                WHERE o.deliveryDate >= '2025-01-01' AND o.deliveryDate <= '2025-10-01'
                AND u.city IN ('Adrienfield', 'Alexandria', 'Alexzandermouth', 'Aliborough', 'Alisashire')
                GROUP BY u.city
                ORDER BY total_sales DESC
            """,




        "Q3: Orders by Demographics":
            """ SELECT
                    u.gender,
                    CASE
                        WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 18 AND 24 THEN '18-24'
                        WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 25 AND 34 THEN '25-34'
                        WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 35 AND 44 THEN '35-44'
                        WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 45 AND 54 THEN '45-54'
                        WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 55 AND 64 THEN '55-64'
                        ELSE '65+'
                    END AS age_group,
                    u.city as location,
                    COUNT(DISTINCT o.orderID) as total_orders
                FROM FactOrders o
                JOIN DimUsers u ON o.userID = u.userID
                JOIN DimProducts p ON o.productID = p.productID
                WHERE o.deliveryDate >= '2025-01-01' AND o.deliveryDate <= '2025-10-01'
                AND u.city IN ('Adrienfield', 'Alexandria', 'Alexzandermouth', 'Aliborough', 'Alisashire')
                AND u.gender = 'F' AND TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 18 AND 24
                GROUP BY u.gender, age_group, u.city
                ORDER BY total_orders DESC
            """,




        "Q4: Top-performing per Category":
            """ WITH ranked_products AS (
                    SELECT
                        p.name,
                        p.category,
                        SUM(o.quantity) AS total_quantity,
                        SUM(o.quantity * p.price) AS total_revenue,
                        DENSE_RANK() OVER (
                            PARTITION BY p.category
                            ORDER BY SUM(o.quantity * p.price) DESC
                        ) AS category_rank
                    FROM FactOrders o
                    JOIN DimProducts p ON o.productID = p.productID
                    INNER JOIN DimUsers u ON o.userID = u.userID
                    WHERE o.deliveryDate >= '2025-01-01' AND o.deliveryDate <= '2025-10-01'
                        AND p.category IN ('Electronics', 'Appliances', 'Toys', 'Bags', 'Gadgets')
                        AND u.city IN ('Adrienfield', 'Alexandria', 'Alexzandermouth', 'Aliborough', 'Alisashire')
                    GROUP BY p.productID, p.name, p.category
                )
                SELECT
                    name,
                    category,
                    total_quantity,
                    total_revenue
                FROM ranked_products
                WHERE category_rank <= 3
                ORDER BY category, category_rank
            """
    }
    
    print("\n" + "="*80)
    print("PERFORMANCE ANALYSIS: ORIGINAL vs OPTIMIZED QUERIES")
    print("="*80)
    
    # Ensure indexes are created for fair comparison
    print("\nEnsuring indexes are in place...")
    create_indexes()
    
    # Store results for comparison
    results = []
    
    print("\n--- TESTING ORIGINAL QUERIES (BEFORE Optimization) ---")
    original_times = {}
    for desc, query in original_queries.items():
        try:
            exec_time, _ = execute_query_with_timing(query, desc)
            original_times[desc] = exec_time
        except Exception as e:
            print(f"Error executing {desc}: {str(e)[:100]}")
            original_times[desc] = None
    
    print("\n--- TESTING OPTIMIZED QUERIES (AFTER Optimization) ---")
    optimized_times = {}
    for desc, query in optimized_queries.items():
        try:
            exec_time, _ = execute_query_with_timing(query, desc)
            optimized_times[desc] = exec_time
        except Exception as e:
            print(f"Error executing {desc}: {str(e)[:100]}")
            optimized_times[desc] = None
    
    # Test other queries with/without indexes for comparison
    print("\n--- TESTING OTHER QUERIES (Index Impact) ---")
    print("Dropping indexes...")
    drop_indexes()
    
    other_before = {}
    for desc, query in other_queries.items():
        try:
            exec_time, _ = execute_query_with_timing(query, desc)
            other_before[desc] = exec_time
        except Exception as e:
            print(f"Error executing {desc}: {str(e)[:100]}")
            other_before[desc] = None
    
    print("\nCreating indexes...")
    create_indexes()
    
    other_after = {}
    for desc, query in other_queries.items():
        try:
            exec_time, _ = execute_query_with_timing(query, desc)
            other_after[desc] = exec_time
        except Exception as e:
            print(f"Error executing {desc}: {str(e)[:100]}")
            other_after[desc] = None
    
    # Calculate improvements
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON SUMMARY")
    print("="*80)
    print(f"{'Query':<50} {'Before':<12} {'After':<12} {'Improvement':<15}")
    print("-"*80)
    
    # Q1: Compare original vs optimized
    orig_key = "Q1: Total Orders Over Time (ORIGINAL)"
    opt_key = "Q1: Total Orders Over Time (OPTIMIZED)"
    
    if orig_key in original_times and opt_key in optimized_times:
        orig_time = original_times[orig_key]
        opt_time = optimized_times[opt_key]
        
        if orig_time and opt_time:
            improvement = ((orig_time - opt_time) / orig_time) * 100
            speedup = orig_time / opt_time
            print(f"{'Q1: Total Orders Over Time':<50} {orig_time:>10.4f}s {opt_time:>10.4f}s {improvement:>10.2f}% ({speedup:.2f}x)")
    
    # Other queries: Compare without indexes vs with indexes
    for desc in other_queries.keys():
        before = other_before.get(desc)
        after = other_after.get(desc)
        
        if before and after:
            improvement = ((before - after) / before) * 100
            speedup = before / after
            print(f"{desc:<50} {before:>10.4f}s {after:>10.4f}s {improvement:>10.2f}% ({speedup:.2f}x)")
        else:
            print(f"{desc:<50} {'ERROR':<12} {'ERROR':<12} {'N/A':<15}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    print("Starting Database Optimization Process...")
    print("="*80)
    
    analyze_performance()