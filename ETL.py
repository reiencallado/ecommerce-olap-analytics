import mysql.connector
import pandas as pd
from sqlalchemy import create_engine, text, Table, Column, Integer, Date, DateTime, MetaData, ForeignKey
from sqlalchemy.types import VARCHAR, DECIMAL
from sqlalchemy import PrimaryKeyConstraint

#####################################
#           EXTRACT PHASE 
#####################################

# connect to local database
source_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    port="3310",
    password="password",
    database="faker"
)

cursor = source_conn.cursor()

print("Now connected to source database!")

orders = pd.read_sql("SELECT * FROM Orders", source_conn)
order_items = pd.read_sql("SELECT * FROM OrderItems", source_conn)
riders = pd.read_sql("SELECT * FROM Riders", source_conn)
products = pd.read_sql("SELECT * FROM Products", source_conn)
users = pd.read_sql("SELECT * FROM Users", source_conn)
couriers = pd.read_sql("SELECT * FROM Couriers", source_conn)

# just to check if everything's working
query = """
SELECT * FROM Orders
LIMIT 10;
"""
df = pd.read_sql(query, source_conn)
print(df)


#####################################
#          TRANSFORM PHASE 
#####################################

# 1: Rename columns so they match acros tables
orders.rename(columns={'id': 'orderID', 'userId': 'userID', 'deliveryRiderId': 'riderID'}, inplace=True)
order_items.rename(columns={'OrderId': 'orderID', 'ProductId': 'productID'}, inplace=True)
products.rename(columns={'id': 'productID'}, inplace=True)
users.rename(columns={'id': 'userID'}, inplace=True)
riders.rename(columns={'id': 'riderID', 'courierId': 'courierID'}, inplace=True)
couriers.rename(columns={'id': 'courierID', 'name': 'courierName'}, inplace=True)

# 2: Drop columns that aren't really needed
orders.drop(columns=['orderNumber'], inplace=True, errors='ignore')
products.drop(columns=['description', 'productCode'], inplace=True, errors='ignore')
riders.drop(columns=['age', 'gender'], inplace=True, errors='ignore')
users.drop(columns=['username'], inplace=True, errors='ignore')

print("Columns are renamed and cleaned up!")

# 3: Merge related tables to prepare fact and dim tables
## combine orders and order items
orders_merged = pd.merge(
    orders, order_items[['orderID', 'productID', 'quantity']],
    on='orderID',
    how='inner' 
)

print("\nOrders merged successfully! Shape: ", orders_merged.shape)
print(orders_merged.head())

## combine riders and couriers
riders_merged = pd.merge(
    riders, couriers[['courierID', 'courierName']],
    on='courierID',
    how = 'inner'
)

# drop courierID since we already have the name
riders_merged.drop(columns=['courierID'], inplace= True)

print("\nRiders merged successfully! Shape: ", riders_merged.shape)
print(riders_merged.head())

# 4:  Clean and normalize data
## normalize gender for users
def normalize_gender(value):
    if pd.isna(value):
        return None
    value_str = str(value).strip().lower()
    
    if value_str.startswith("m"):
        return 'M'
    elif value_str.startswith("f"):
        return 'F'
    return None
    
users['gender'] = users['gender'].apply(normalize_gender)
print("\n Gender normalized successfully!")

## normalize product categories
def normalize_category(value):
    if pd.isna(value):
        return None
    value_str = str(value).strip().lower()
    if not value_str or value_str == "nan":
        return None
    elif value_str == "toy":
        return "Toys"
    elif value_str == "men's apparel":
        return "Clothing"
    elif value_str == "clothes":
        return "Clothing"
    elif value_str == "make up":
        return "Makeup"
    elif value_str == "laptops":
        return "Gadgets"
    elif value_str == "bag":
            return "Bags"
    return value_str.title()

products['category'] = products['category'].apply(normalize_category)
print("\n Category normalized successfully!")

# for handling date formats
def parse_date(date_str):
    if pd.isna(date_str):
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%b %d, %Y", "%d-%m-%Y"):
        try:
            return pd.to_datetime(date_str, format=fmt).date()
        except (ValueError, TypeError):
            continue
    return None

users['dateOfBirth'] = users['dateOfBirth'].apply(parse_date)
orders_merged['deliveryDate'] = orders_merged['deliveryDate'].apply(parse_date)

# closing connection to the source cb
cursor.close()
source_conn.close()
print("Data transformation is now complete.")


#####################################
#             LOAD PHASE 
#####################################

# connect to cloud database
engine = create_engine(
    "mysql+mysqlconnector://megan:Megan%401234@34.142.244.237:3306/stadvdb"
)

with engine.connect() as connection:
    print("Now connected to Cloud Data Warehouse!")

metadata = MetaData()

# define tables for the data warehouse

# users table
dim_users = Table('DimUsers', metadata,
    Column('userID', Integer, primary_key=True, autoincrement=False),
    Column('firstName', VARCHAR(255)),
    Column('lastName', VARCHAR(255)),
    Column('address1', VARCHAR(255)),
    Column('address2', VARCHAR(255)),
    Column('city', VARCHAR(255)),
    Column('country', VARCHAR(255)),
    Column('zipCode', VARCHAR(10)),
    Column('phoneNumber', VARCHAR (255)),
    Column('gender', VARCHAR(1)),
    Column('dateOfBirth', Date),
    Column('createdAt', DateTime),
    Column('updatedAt', DateTime),
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4'
)
print("\nUser dimension table ready.")

# products table
dim_products = Table('DimProducts', metadata,
    Column('productID', Integer, primary_key=True, autoincrement=False),
    Column('name', VARCHAR(255)),
    Column('category', VARCHAR(255)),
    Column('price', DECIMAL(10, 2)),
    Column('createdAt', DateTime),
    Column('updatedAt', DateTime),
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4'
)
print("\nProduct dimension table ready.")

# riders table
dim_riders = Table('DimRiders', metadata,
    Column('riderID', Integer, primary_key=True, autoincrement=False),
    Column('firstName', VARCHAR(255)),
    Column('lastName', VARCHAR(255)),
    Column('courierName', VARCHAR(255)),
    Column('vehicleType', VARCHAR(255)),
    Column('createdAt', DateTime),
    Column('updatedAt', DateTime),
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4'
)
print("\nRiders dimension table ready.")

# fact orders table (this connects everything)
fact_orders = Table('FactOrders', metadata,
    Column('orderID', Integer, nullable=False),
    Column('userID', Integer, ForeignKey('DimUsers.userID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('productID', Integer, ForeignKey('DimProducts.productID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('riderID', Integer, ForeignKey('DimRiders.riderID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('deliveryDate', Date),
    Column('quantity', Integer, nullable=False),
    Column('createdAt', DateTime),
    Column('updatedAt', DateTime),
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4'
)

# use composite primary key for orderID + productID
fact_orders.append_constraint(
    PrimaryKeyConstraint('orderID', 'productID', name='pk_factorders')
)
print("\nFact orders table ready.")

# create all tables in the cloud db
print("Creating tables in cloud database...")
metadata.drop_all(engine)
metadata.create_all(engine)
print("Tables were created successfully!")

print("Loading data...") # load the cleaned data to cloud

users.to_sql('DimUsers', engine, if_exists='append', index=False, chunksize=5000, method='multi')
print("Useer data loaded.")

products.to_sql('DimProducts', engine, if_exists='append', index=False, chunksize=5000, method='multi')
print("Product data loaded.")

riders_merged.to_sql('DimRiders', engine, if_exists='append', index=False, chunksize=5000, method='multi')
print("Rider data loaded.")

orders_merged.to_sql('FactOrders', engine, if_exists='append', index=False, chunksize=5000, method='multi')
print("Order data loaded.")

engine.dispose() # clean up
print("ETL process is done:) Connection closed.")
