# E-Commerce OLAP Analytics Platform

An end-to-end e-commerce analytics system that transforms transactional data into a structured data warehouse and provides API-driven reporting for orders, sales, customers, products, and delivery performance.

## Overview

This project implements an **OLAP-oriented analytics workflow** for e-commerce data. It combines an ETL pipeline, dimensional data warehousing, a Flask REST API, and an interactive analytics dashboard.

The system:

* Extracts transactional data from a MySQL database
* Cleans and transforms data using Python and Pandas
* Builds a dimensional data warehouse using fact and dimension tables
* Provides REST API endpoints for analytical reporting
* Supports filtering by date, location, product category, and customer demographics
* Includes SQL query optimization and indexing performance analysis
* Visualizes analytical results through a web-based dashboard

## Architecture

```text
Source MySQL Database
        │
        ▼
   ETL Pipeline
        │
        ├── Extract
        ├── Transform
        │    ├── Rename columns
        │    ├── Remove unnecessary fields
        │    ├── Normalize categories
        │    ├── Normalize gender values
        │    └── Standardize dates
        │
        ▼
Dimensional Data Warehouse
        │
        ├── DimUsers
        ├── DimProducts
        ├── DimRiders
        └── FactOrders
        │
        ▼
    Flask REST API
        │
        ├── Order Reports
        ├── Sales Reports
        ├── Customer Reports
        ├── Product Reports
        ├── Rider Reports
        └── Filter Endpoints
        │
        ▼
  Analytics Dashboard
```

## Key Features

### ETL Pipeline

The ETL pipeline prepares transactional data for analytical use by:

* Extracting data from MySQL
* Cleaning and transforming raw data
* Standardizing categories, gender values, and dates
* Removing unnecessary fields
* Creating fact and dimension tables
* Loading transformed data into the analytics warehouse

### Analytics API

The Flask backend provides reporting endpoints for:

* Order analytics
* Sales analytics
* Customer demographics
* Product and category performance
* Rider and delivery performance
* Date- and location-based filtering

### Query Optimization

The project includes SQL query performance analysis to evaluate query execution before and after optimization techniques such as indexing.

## Tech Stack

**Backend & Data Processing**

* Python
* Pandas
* SQLAlchemy
* Flask

**Database**

* MySQL
* SQL

**Frontend**

* React
* Vite
* JavaScript

## Project Structure

```text
.
├── ETL.py
├── optimization.py
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── wsgi.py
├── stadvdb-app/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── runtime.txt
├── package-lock.json
└── README.md
```

## Project Focus

This project demonstrates the integration of:

* ETL and data transformation
* Dimensional data warehousing
* OLAP-oriented analytics
* REST API development
* Interactive data visualization
* SQL query optimization and performance analysis
