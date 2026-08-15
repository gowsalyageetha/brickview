# brickview
# 🏡 BrickView – Real Estate Analytics Platform

BrickView is a real estate analytics platform developed using Python, SQLite, SQL, Pandas, Plotly, and Streamlit.

The application provides an interactive dashboard for exploring real estate listings, analyzing property prices, evaluating sales performance, understanding agent performance, and analyzing buyer and financing behavior.

---

## 📌 Project Overview

The BrickView platform is designed to help users explore and analyze real estate data through an interactive Streamlit web application.

The application connects to a SQLite database containing information about:

- Property listings
- Property attributes
- Real estate agents
- Property sales
- Buyers and financing details

Users can filter properties, explore market trends, analyze sales performance, evaluate agents, analyze buyer behavior, execute SQL business queries, and perform CRUD operations.

---

## 🎯 Project Objectives

The main objectives of this project are:

- Build an interactive real estate analytics dashboard.
- Store and manage real estate data using SQLite.
- Use SQL queries to answer business questions.
- Analyze property pricing and market trends.
- Analyze property sales and days on market.
- Evaluate real estate agent performance.
- Analyze buyer types and financing behavior.
- Provide CRUD functionality for database management.
- Present insights through interactive visualizations.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development |
| Streamlit | Interactive web application |
| SQLite | Database management |
| SQL | Data querying and business analysis |
| Pandas | Data manipulation and analysis |
| Plotly | Interactive charts and visualizations |

---

## 🗄️ Database Structure

The project uses five main tables.

### 1. Listings

Stores property listing information.

- Listing_ID
- City
- Property_Type
- Price
- Sqft
- Date_Listed
- Agent_ID
- Latitude
- Longitude

### 2. Property Attribute

Stores additional property characteristics.

- attribute_id
- listing_id
- bedrooms
- bathrooms
- floor_number
- total_floors
- year_built
- is_rented
- tenant_count
- furnishing_status
- metro_distance_km
- parking_available
- power_backup

### 3. Agents

Stores real estate agent information and performance metrics.

- Agent_ID
- Name
- Phone
- Email
- commission_rate
- deals_closed
- rating
- experience_years
- avg_closing_days

### 4. Sales

Stores property sale information.

- Listing_ID
- Sale_Price
- Date_Sold
- Days_on_Market

### 5. Buyers

Stores buyer and financing information.

- buyer_id
- sale_id
- buyer_type
- payment_mode
- loan_taken
- loan_provider
- loan_amount

---

## 📊 Application Features

### 📊 Dashboard

The dashboard provides an overview of the real estate market.

Features include:

- Total number of listings
- Average property price
- Average property size
- Average price per square foot
- Number of cities
- Property price distribution
- Average price by city
- Property type distribution
- Property filtering

---

### 🏠 Property Explorer

The Property Explorer allows users to explore available properties.

Features include:

- Property location map
- City filtering
- Property details
- Property type
- Price
- Square footage
- Listing date
- Assigned agent

---

### 📈 Sales Analysis

The Sales Analysis section provides insights into property sales.

Analysis includes:

- Total sales
- Total sales revenue
- Average sale price
- Average days on market
- Sales trends
- Days on market by city
- Days on market by property type
- Sale-to-list price ratio
- Properties sold above listing price
- Properties taking more than 90 days to sell

---

### 👨‍💼 Agent Analysis

The Agent Analysis section evaluates real estate agent performance.

Analysis includes:

- Total agents
- Number of sales
- Sales revenue
- Average agent rating
- Top agents by sales
- Top agents by revenue
- Experience versus sales
- Agent rating versus closing speed
- Active listings by agent

---

### 👤 Buyer Analysis

The Buyer Analysis section focuses on buyer behavior and financing.

Analysis includes:

- Total buyers
- Investor versus end-user distribution
- Loan uptake
- Average loan amount
- Payment mode distribution
- Loan providers
- Loan amount by buyer type

---

### 🧮 SQL Analysis

The application contains SQL-based business analysis covering:

- Property pricing
- Price per square foot
- Property characteristics
- Furnishing status
- Metro distance
- Rental status
- Sales performance
- Days on market
- Sale-to-list price ratio
- Agent performance
- Buyer behavior
- Loan uptake
- Payment modes

The SQL section allows users to select a business question and view both the SQL query and its result.

---

### 🛠️ CRUD Operations

The application provides database management functionality.

Users can:

- Create records
- Read records
- Update records
- Delete records

CRUD operations are available for:

- Listings
- Property attributes
- Agents
- Sales
- Buyers

---

## 📂 Project Structure

```text
brickview_project/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── brickview_realestate.db
