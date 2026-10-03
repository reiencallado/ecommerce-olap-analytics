# E-Commerce OLAP Analytics Platform

An end-to-end e-commerce analytics system that transforms transactional data into a structured data warehouse and provides API-driven reporting for orders, sales, customers, products, and delivery performance.

## Overview

This project implements an OLAP-oriented analytics workflow for e-commerce data.

The system:

- Extracts transactional data from a source MySQL database
- Cleans, normalizes, and transforms the data using Python
- Builds a dimensional data warehouse using fact and dimension tables
- Provides a Flask REST API for analytical queries and reporting
- Supports filtering by date, location, product category, and customer demographics
- Includes SQL query optimization and indexing performance analysis

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
        │    ├── Clean unnecessary fields
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
