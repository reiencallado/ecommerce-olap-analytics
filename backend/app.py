import os
from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
from flask_cors import CORS
from datetime import datetime
import traceback

app = Flask(__name__)

ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')

if ALLOWED_ORIGINS.strip() == '*':
    CORS(app, 
         resources={r"/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": False
         }})
else:
    origins = [o.strip() for o in ALLOWED_ORIGINS.split(',') if o.strip()]
    CORS(app, 
         resources={r"/*": {
             "origins": origins,
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": True
         }})

DATABASE_URL = os.environ.get('DATABASE_URL', "mysql+mysqlconnector://chrystel:Chrystel%401234@34.142.244.237:3306/stadvdb")

# Database connection
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT NOW()"))
        print("✓ Database connection successful, current time:", result.fetchone()[0])
except Exception as e:
    print(f"Warning: Could not connect to database on startup: {str(e)}")

def execute_query(query, params=None):
    """Helper function to execute queries and handle errors"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            return [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Query error: {str(e)}")
        traceback.print_exc()
        raise

def build_where_clause(conditions):
    """Helper function to build WHERE clause from conditions list"""
    if not conditions:
        return ""
    return " WHERE " + " AND ".join(conditions)

@app.route('/')
def hello():
    return "OLAP Backend API"


# ========== ORDERS REPORTS ==========
@app.route('/api/orders/total-orders-over-time', methods=['GET'])
def total_orders_over_time():
    """Total Orders Over Time - How many orders do we receive each [DATE CATEGORY]?"""
    date_category = request.args.get('time_granularity')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.get('countries')  # comma-separated list
    cities = request.args.get('cities')  # comma-separated list
    
    # Use more index-friendly date extraction functions
    # For ONLY_FULL_GROUP_BY compatibility, we select the grouped columns and format in application
    date_configs = {
        'day': {
            'select': "DATE(o.deliveryDate) as period",
            'group_by': "DATE(o.deliveryDate)",
            'order_by': "DATE(o.deliveryDate)"
        },
        'week': {
            'select': "DATE_FORMAT(o.deliveryDate, '%Y-%u') as period",
            'group_by': "DATE_FORMAT(o.deliveryDate, '%Y-%u')",
            'order_by': "DATE_FORMAT(o.deliveryDate, '%Y-%u')"
        },
        'month': {
            'select': "DATE_FORMAT(o.deliveryDate, '%Y-%m') as period",
            'group_by': "DATE_FORMAT(o.deliveryDate, '%Y-%m')",
            'order_by': "DATE_FORMAT(o.deliveryDate, '%Y-%m')"
        },
        'quarter': {
            'select': "CONCAT(YEAR(o.deliveryDate), '-Q', QUARTER(o.deliveryDate)) as period",
            'group_by': "CONCAT(YEAR(o.deliveryDate), '-Q', QUARTER(o.deliveryDate))",
            'order_by': "CONCAT(YEAR(o.deliveryDate), '-Q', QUARTER(o.deliveryDate))"
        },
        'year': {
            'select': "YEAR(o.deliveryDate) as period",
            'group_by': "YEAR(o.deliveryDate)",
            'order_by': "YEAR(o.deliveryDate)"
        }
    }
    
    config = date_configs.get(date_category, date_configs['month']) # defaults to month
    date_select = config['select']
    date_group = config['group_by']
    date_order = config['order_by']
    
    # Only join DimUsers if location filters are applied
    needs_user_join = bool(countries or cities)
    
    if needs_user_join:
        query = f"""
            SELECT 
                {date_select},
                COUNT(*) as total_orders
            FROM FactOrders o
            JOIN DimUsers u ON o.userID = u.userID
        """
    else:
        query = f"""
            SELECT 
                {date_select},
                COUNT(*) as total_orders
            FROM FactOrders o
        """
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city
    
    query += build_where_clause(conditions)
    query += f" GROUP BY {date_group} ORDER BY {date_order}"
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========================================
@app.route('/api/orders/total-orders-by-location', methods=['GET'])
def orders_by_location():
    """Total Orders Per Location - How many orders do we receive in [LOCATION CATEGORY]?"""
    location_type = request.args.get('type', 'country')  # city, country
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.get('countries')  # comma-separated list
    cities = request.args.get('cities')  # comma-separated list
    
    location_field = 'city' if location_type == 'city' else 'country' #defaults to country first
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city

    where_clause = build_where_clause(conditions) 
    query = f"""
        SELECT 
            u.{location_field} as location,
            COUNT(DISTINCT o.orderID) as total_orders
        FROM FactOrders o 
        JOIN DimUsers u ON o.userID = u.userID
        {where_clause}
        GROUP BY u.{location_field}
        ORDER BY total_orders DESC
    """

    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# ==============================================
@app.route('/api/orders/total-orders-by-product-category', methods=['GET']) 
def orders_by_product_category():
    """Total Orders Per Product Category - Which product categories generate the most orders?"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.get('countries')  # comma-separated list
    cities = request.args.get('cities')  # comma-separated list

    query = """
        SELECT 
            p.category,
            COUNT(DISTINCT o.orderID) as total_orders
        FROM FactOrders o
        JOIN DimProducts p ON o.productID = p.productID
        JOIN DimUsers u ON o.userID = u.userID
    """
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city
    
    query += build_where_clause(conditions)
    query += " GROUP BY p.category ORDER BY total_orders DESC"
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========== SALES REPORTS ==========
@app.route('/api/orders/total-sales-over-time', methods=['GET'])
def total_sales_over_time():
    """Total Sales Over Time - How many sales do we receive each [DATE CATEGORY]?"""
    date_category = request.args.get('time_granularity')  # day, week, month, quarter, year
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.get('countries')  # comma-separated list
    cities = request.args.get('cities')  # comma-separated list
    
    date_formats = {
        'day': "DATE(o.deliveryDate)",
        'week': "DATE_FORMAT(o.deliveryDate, '%Y-%u')",
        'month': "DATE_FORMAT(o.deliveryDate, '%Y-%m')",
        'quarter': "CONCAT(YEAR(o.deliveryDate), '-Q', QUARTER(o.deliveryDate))",
        'year': "YEAR(o.deliveryDate)"
    }
    
    date_format = date_formats.get(date_category, date_formats['month']) 
    
    query = f"""
        SELECT 
            {date_format} as period,
            SUM(o.quantity * p.price) as total_sales
        FROM FactOrders o
        JOIN DimProducts p ON o.productID = p.productID
        JOIN DimUsers u ON o.userID = u.userID
    """
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city
    
    query += build_where_clause(conditions)
    query += f" GROUP BY {date_format} ORDER BY {date_format}"
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ================================================
@app.route('/api/orders/total-sales-by-location', methods=['GET'])
def sales_by_location():
    """Total Sales Per Location - How many sales do we receive in [LOCATION CATEGORY]?"""
    location_type = request.args.get('type', 'country')  # city, country
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.get('countries')  # comma-separated list
    cities = request.args.get('cities')  # comma-separated list
    
    location_field = 'city' if location_type == 'city' else 'country' # defaults to country first
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city

    where_clause = build_where_clause(conditions) 
    query = f"""
       SELECT 
            u.{location_field} as location,
            SUM(o.quantity * p.price) as total_sales
        FROM FactOrders o
        JOIN DimUsers u ON o.userID = u.userID
        JOIN DimProducts p ON o.productID = p.productID
        {where_clause}
        GROUP BY u.{location_field}
        ORDER BY total_sales DESC
    """

    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================
@app.route('/api/orders/total-sales-by-product-category', methods=['GET']) 
def sales_by_product_category():
    """Total Sales Per Product Category - Which product categories generate the most sales?"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.get('countries')  # comma-separated list
    cities = request.args.get('cities')  # comma-separated list

    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city

    where_clause = build_where_clause(conditions)

    query = f"""
        SELECT 
            p.category,
            SUM(o.quantity * p.price) as total_sales
        FROM FactOrders o
        JOIN DimProducts p ON o.productID = p.productID
        JOIN DimUsers u ON o.userID = u.userID
        {where_clause}
        GROUP BY p.category
        ORDER BY total_sales DESC
    """
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========== CUSTOMER REPORTS ==========
@app.route('/api/customers/orders-by-demographics', methods=['GET'])
def orders_by_demographics():
    """How many orders came from [GENDER] customers aged [AGE GROUP] in [LOCATION]"""
    gender = request.args.get('gender') 
    age_groups = request.args.getlist('age_group')
    location_type = request.args.get('type', 'country')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.get('countries')
    cities = request.args.get('cities') 
    
    location_field = 'city' if location_type == 'city' else 'country'

    conditions = []
    params = {}
    
    if gender:
        gender_list = [g.strip() for g in gender.split(',')]
        
        # Map Male/Female to M/F
        gender_mapping = {'male': 'M', 'female': 'F', 'm': 'M', 'f': 'F'}
        
        if len(gender_list) > 1:
            gender_placeholders = ','.join([f':gender{i}' for i in range(len(gender_list))])
            conditions.append(f"u.gender IN ({gender_placeholders})")
            for i, g in enumerate(gender_list):
                params[f'gender{i}'] = gender_mapping.get(g.lower(), g)
        else:
            conditions.append("u.gender = :gender")
            params['gender'] = gender_mapping.get(gender_list[0].lower(), gender_list[0])
    
    if age_groups:
        age_conditions = []
        for idx, age_group in enumerate(age_groups):
            age_ranges = {
                '18-24': (18, 24),
                '25-34': (25, 34),
                '35-44': (35, 44),
                '45-54': (45, 54),
                '55-64': (55, 64),
                '65+': (65, 150)
            }
            if age_group in age_ranges:
                min_age, max_age = age_ranges[age_group]
                age_conditions.append(
                    f"TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN :min_age_{idx} AND :max_age_{idx}"
                )
                params[f'min_age_{idx}'] = min_age
                params[f'max_age_{idx}'] = max_age
        
        if age_conditions:
            conditions.append(f"({' OR '.join(age_conditions)})")
    
    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date
    
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country.strip()
    
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city.strip()

    where_clause = build_where_clause(conditions)
    
    print(f"Conditions: {conditions}")
    print(f"Params: {params}")
    
    query = f"""
        SELECT 
            u.gender,
            CASE
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 18 AND 24 THEN '18-24'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 25 AND 34 THEN '25-34'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 35 AND 44 THEN '35-44'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 45 AND 54 THEN '45-54'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 55 AND 64 THEN '55-64'
                ELSE '65+'
            END AS age_group,
            u.{location_field} as location,
            COUNT(DISTINCT o.orderID) as total_orders
        FROM FactOrders o
        JOIN DimUsers u ON o.userID = u.userID
        JOIN DimProducts p ON o.productID = p.productID
        {where_clause}
        GROUP BY u.gender, age_group, u.{location_field}
        ORDER BY total_orders DESC
    """
    
    try:
        results = execute_query(query, params)
        print(f"Results count: {len(results)}")
        if results:
            print(f"First few results: {results[:3]}")
        return jsonify({"success": True, "data": results})
    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ===================================================
@app.route('/api/customers/segments-revenue', methods=['GET'])
def customer_segments_revenue():
    """Customer Segments - Which customer segment contributes the most to total revenue?"""
    segment_type = request.args.get('segment')  # age, gender, location
    location_type = request.args.get('location_type') # city, country
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    location_field = 'city' if location_type == 'city' else 'country'

    if segment_type == 'age':
        segment_field = """
            CASE
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 18 AND 24 THEN '18-24'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 25 AND 34 THEN '25-34'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 35 AND 44 THEN '35-44'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 45 AND 54 THEN '45-54'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 55 AND 64 THEN '55-64'
                ELSE '65+'
            END
        """
    elif segment_type == 'gender':
        segment_field = "u.gender"
    else: 
        segment_field = f"u.{location_field}"
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date

    where_clause = build_where_clause(conditions)


    query = f"""
        SELECT 
            {segment_field} as segment,
            SUM(o.quantity * p.price) as total_revenue
        FROM FactOrders o
        JOIN DimUsers u ON o.userID = u.userID
        JOIN DimProducts p ON o.productID = p.productID
        {where_clause}
        GROUP BY {segment_field} 
        ORDER BY total_revenue DESC
        """
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========== PRODUCT REPORTS ==========
@app.route('/api/products/top-performing', methods=['GET'])
def top_performing_products(): #general, works also for lowest sales
    """Top Selling Products - Which products are our top performers?"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    order = request.args.get('order', 'DESC') #DESC for top, ASC for zero sales || default should be DESC
    categories = request.args.get('categories')
    countries = request.args.get('countries') 
    cities = request.args.get('cities')  
    
    conditions = []
    params = {}

    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date

    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date
        
    if categories:
        category_list = categories.split(',')
        placeholders = ','.join([f':category{i}' for i in range(len(category_list))])
        conditions.append(f"p.category IN ({placeholders})")
        for i, category in enumerate(category_list):
            params[f'category{i}'] = category
            
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country
    
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city

    where_clause = build_where_clause(conditions)

    query = f"""
        SELECT 
            p.name,
            p.category,
            SUM(o.quantity * p.price) as total
        FROM FactOrders o
        RIGHT JOIN DimProducts p ON o.productID = p.productID
        INNER JOIN DimUsers u ON o.userID = u.userID
        {where_clause}
        GROUP BY p.name, p.category
        ORDER BY total {order}
    """
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==============================================
@app.route('/api/products/top-performing-per-category', methods=['GET'])
def top_per_category(): #specific
    category = request.args.get('product_category') 
    # if no category was added in param, it shows all categories alphabetically, arranged in their respective ranks within 
    categories = request.args.get('categories') # added this to handle multiple categories
    top_n = request.args.get('top_n')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.get('countries')  
    cities = request.args.get('cities') 

    conditions = []
    conditions2 = []
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "category": category,
        "top_n": top_n
    }

    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date

    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date

    if category:
        conditions.append("p.category = :category")
        params['category'] = category
    elif categories: 
        category_list = categories.split(',')
        placeholders = ','.join([f':category{i}' for i in range(len(category_list))])
        conditions.append(f"p.category IN ({placeholders})")
        for i, cat in enumerate(category_list):
            params[f'category{i}'] = cat
            
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country
    
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city

    if top_n:
        conditions2.append("category_rank <= :top_n")
        params['top_n'] = int(top_n)

    where_clause1 = build_where_clause(conditions)
    where_clause2 = build_where_clause(conditions2)

    query = f"""
        WITH ranked_products AS (
            SELECT 
                p.name,
                p.category,
                SUM(o.quantity * p.price) AS total_revenue,
                DENSE_RANK() OVER (
                    PARTITION BY p.category
                    ORDER BY SUM(o.quantity * p.price) DESC
                ) AS category_rank
            FROM FactOrders o
            JOIN DimProducts p ON o.productID = p.productID
            INNER JOIN DimUsers u ON o.userID = u.userID
            {where_clause1}
            GROUP BY p.productID, p.name, p.category
        )
        SELECT 
            name,
            category,
            total_revenue
        FROM ranked_products
        {where_clause2} 
        ORDER BY category, category_rank;
    """

    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==============================================
@app.route('/api/products/category-performance', methods=['GET'])
def category_performance():
    """Price Trends - What's the average order value per Product Category per [DATE CATEGORY]"""
    date_category = request.args.get('time_granularity')  # day, week, month, quarter, year
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    categories = request.args.get('categories')
    countries = request.args.get('countries') 
    cities = request.args.get('cities')

    date_formats = {
        'day': "DATE(o.deliveryDate)",
        'week': "DATE_FORMAT(o.deliveryDate, '%Y-%u')",
        'month': "DATE_FORMAT(o.deliveryDate, '%Y-%m')",
        'quarter': "CONCAT(YEAR(o.deliveryDate), '-Q', QUARTER(o.deliveryDate))",
        'year': "YEAR(o.deliveryDate)"
    }

    date_format = date_formats.get(date_category, date_formats['month'])

    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date
        
    if categories:
        category_list = categories.split(',')
        placeholders = ','.join([f':category{i}' for i in range(len(category_list))])
        conditions.append(f"p.category IN ({placeholders})")
        for i, category in enumerate(category_list):
            params[f'category{i}'] = category
    
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country
    
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city

    where_clause = build_where_clause(conditions)

    query = f"""
        SELECT 
            {date_format} as period,
            p.category,
            AVG(o.quantity * p.price) as avg_order_value
        FROM FactOrders o
        JOIN DimProducts p ON o.productID = p.productID
        INNER JOIN DimUsers u ON o.userID = u.userID
        {where_clause}
        GROUP BY {date_format}, p.category
        ORDER BY {date_format}, p.category
    """
    
    try:
        results = execute_query(query, params)  # Pass params here!
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# ==============================================   
@app.route('/api/filters/categories', methods=['GET'])
def get_categories():
    """Get list of unique product categories"""
    query = """
        SELECT DISTINCT category
        FROM DimProducts
        WHERE category IS NOT NULL
        ORDER BY category
    """
    
    try:
        results = execute_query(query)
        categories = [{
            'id': row['category'].lower().replace(' ', '_'),
            'name': row['category']
        } for row in results]
        return jsonify({"success": True, "data": categories})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========== RIDER REPORTS ==========
@app.route('/api/riders/orders-per-rider', methods=['GET'])
def orders_per_rider():
    """Orders per Rider - How many orders were delivered by courier per [DATE CATEGORY]?"""
    date_category = request.args.get('time_granularity')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.get('countries')  # comma-separated list
    cities = request.args.get('cities')  # comma-separated list
    
    date_formats = {
        'day': "DATE(o.deliveryDate)",
        'week': "DATE_FORMAT(o.deliveryDate, '%Y-%u')", 
        'month': "DATE_FORMAT(o.deliveryDate, '%Y-%m')",
        'quarter': "CONCAT(YEAR(o.deliveryDate), '-Q', QUARTER(o.deliveryDate))",
        'year': "YEAR(o.deliveryDate)"
    }
    
    date_format = date_formats.get(date_category, date_formats['month']) # defaults to month
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city
   
    where_clause = build_where_clause(conditions)
    
    query = f"""
        SELECT 
            {date_format} as period,
            r.courierName as courier_name,
            COUNT(DISTINCT o.orderID) as total_orders
        FROM FactOrders o
        JOIN DimRiders r ON o.riderID = r.riderID
        JOIN DimUsers u ON o.userID = u.userID
        {where_clause}
        GROUP BY {date_format}, r.courierName
        ORDER BY {date_format}, r.courierName
    """
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==============================================
@app.route('/api/riders/delivery-performance', methods=['GET'])
def delivery_performance():
    """Delivery Time - Average delivery time by rider/courier"""
    date_category = request.args.get('time_granularity')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.get('countries')  # comma-separated list
    cities = request.args.get('cities')  # comma-separated list
    
    date_formats = {
        'day': "DATE(o.deliveryDate)",
        'week': "DATE_FORMAT(o.deliveryDate, '%Y-%u')", 
        'month': "DATE_FORMAT(o.deliveryDate, '%Y-%m')",
        'quarter': "CONCAT(YEAR(o.deliveryDate), '-Q', QUARTER(o.deliveryDate))",
        'year': "YEAR(o.deliveryDate)"
    }
    
    date_format = date_formats.get(date_category, date_formats['month']) # defaults to month
    conditions = ["o.deliveryDate IS NOT NULL"]
    params = {}
    
    if start_date:
        conditions.append("o.deliveryDate >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.deliveryDate <= :end_date")
        params['end_date'] = end_date
    if countries:
        country_list = countries.split(',')
        placeholders = ','.join([f':country{i}' for i in range(len(country_list))])
        conditions.append(f"u.country IN ({placeholders})")
        for i, country in enumerate(country_list):
            params[f'country{i}'] = country
    if cities:
        city_list = cities.split(',')
        placeholders = ','.join([f':city{i}' for i in range(len(city_list))])
        conditions.append(f"u.city IN ({placeholders})")
        for i, city in enumerate(city_list):
            params[f'city{i}'] = city

    
    where_clause = build_where_clause(conditions)
    
    query = f"""
        SELECT 
            {date_format} as period,
            r.courierName as courier_name,
            AVG(ABS(DATEDIFF(o.deliveryDate, o.createdAt))) as avg_delivery_days
        FROM FactOrders o
        JOIN DimRiders r ON o.riderID = r.riderID
        JOIN DimUsers u ON o.userID = u.userID
        {where_clause}
        GROUP BY {date_format}, r.courierName
        ORDER BY {date_format}, r.courierName
    """
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========== FILTER ENDPOINTS ==========
@app.route('/api/filters/countries', methods=['GET'])
def get_countries():
    """Get list of unique countries"""
    query = """
        SELECT DISTINCT country
        FROM DimUsers
        WHERE country IS NOT NULL
        ORDER BY country
    """
    
    try:
        results = execute_query(query)
        # Transform to include id and name
        countries = [{
            'id': row['country'].lower().replace(' ', '_'),
            'name': row['country']
        } for row in results]
        return jsonify({"success": True, "data": countries})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/filters/cities', methods=['GET'])
def get_cities():
    """Get list of unique cities, optionally filtered by country"""
    country = request.args.get('country')
    
    query = """
        SELECT DISTINCT city, country
        FROM DimUsers
        WHERE city IS NOT NULL
    """
    
    params = {}
    if country:
        query += " AND country = :country"
        params['country'] = country
    
    query += " ORDER BY city"
    
    try:
        results = execute_query(query, params)
        cities = [{
            'id': f"{row['country']}_{row['city']}".lower().replace(' ', '_'),
            'name': row['city'],
            'country': row['country']
        } for row in results]
        return jsonify({"success": True, "data": cities})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# test

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)