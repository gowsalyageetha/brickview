import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="BrickView - Real Estate Analytics",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ============================================================
# DATABASE CONNECTION
# ============================================================

@st.cache_resource
def get_connection():
    return sqlite3.connect(
        "brickview_realestate.db",
        check_same_thread=False
    )


conn = get_connection()

# ============================================================
# DATABASE HELPER
# ============================================================

def read_query(query, params=None):
    try:
        return pd.read_sql_query(
            query,
            conn,
            params=params if params else []
        )
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def execute_query(query, params=None):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params if params else [])
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

    # ============================================================
# TEST DATABASE
# ============================================================

try:
    conn.execute("SELECT 1")
except sqlite3.Error as e:
    st.error(f"❌ Database connection failed: {e}")
    st.stop()

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("🏡 BrickView")

page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "🗺️ Property Explorer",
        "📈 Sales Analysis",
        "👨‍💼 Agent Analysis",
        "👤 Buyer Analysis",
        "🧮 SQL Queries",
        "🛠️ CRUD Operations"
    ]
)

# ============================================================
# COMMON FILTER VALUES
# ============================================================

cities_df = read_query("""
    SELECT DISTINCT City
    FROM listings
    WHERE City IS NOT NULL
    ORDER BY City
""")

property_types_df = read_query("""
    SELECT DISTINCT Property_Type
    FROM listings
    WHERE Property_Type IS NOT NULL
    ORDER BY property_type
""")

agents_df = read_query("""
    SELECT DISTINCT Name
    FROM agents
    WHERE Name IS NOT NULL
    ORDER BY Name
""")


cities = cities_df["City"].tolist() if not cities_df.empty else []
property_types = (
    property_types_df["Property_Type"].tolist()
    if not property_types_df.empty
    else []
)
agents = agents_df["Name"].tolist() if not agents_df.empty else []

price_df = read_query("""
    SELECT
        MIN(Price) AS min_price,
        MAX(Price) AS max_price
    FROM listings
    WHERE Price IS NOT NULL
""")

if not price_df.empty and pd.notna(price_df["min_price"].iloc[0]):
    min_price = int(price_df["min_price"].iloc[0])
    max_price = int(price_df["max_price"].iloc[0])
else:
    min_price = 0
    max_price = 1000000

# ============================================================
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    st.title("🏡 BrickView Real Estate Analytics")
    st.markdown(
        "Interactive real estate dashboard for property, sales and agent analysis."
    )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    st.sidebar.header("🔎 Property Filters")

    selected_city = st.sidebar.multiselect(
        "City",
        cities
    )

    selected_property = st.sidebar.multiselect(
        "Property Type",
        property_types
    )

    selected_agent = st.sidebar.multiselect(
        "Agent",
        agents
    )

    selected_price = st.sidebar.slider(
        "Price Range",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price)
    )

    
    # --------------------------------------------------------
    # BUILD FILTER QUERY
    # --------------------------------------------------------

    query = """
        SELECT
            l.Listing_ID,
            l.City,
            l.Property_Type,
            l.Price,
            l.Sqft,
            l.Date_Listed,
            l.Agent_ID,
            l.Latitude,
            l.Longitude,
            l.Date_Listed,
            a.Name AS Agent_Name,
            
            pa.bedrooms,
            pa.bathrooms,
            pa.floor_number,
            pa.total_floors,
            pa.year_built,
            pa.is_rented,
            pa.tenant_count,
            pa.furnishing_status,
            pa.metro_distance_km,
            pa.parking_available,
            pa.power_backup

        FROM listings l

        LEFT JOIN agents a
            ON l.Agent_ID = a.Agent_ID

        LEFT JOIN property_attributes pa
            ON l.Listing_ID = pa.listing_id

        WHERE l.Price BETWEEN ? AND ?
    """

    params = [
        selected_price[0],
        selected_price[1]
    ]

    if selected_city:
        placeholders = ",".join(["?"] * len(selected_city))
        query += f" AND l.City IN ({placeholders})"
        params.extend(selected_city)

    if selected_property:
        placeholders = ",".join(["?"] * len(selected_property))
        query += f" AND l.Property_Type IN ({placeholders})"
        params.extend(selected_property)

    if selected_agent:
        placeholders = ",".join(["?"] * len(selected_agent))
        query += f" AND a.Name IN ({placeholders})"
        params.extend(selected_agent)

    query += " ORDER BY l.Price DESC"

    df = read_query(query, params)

    
    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------
    if df.empty:
            st.warning("No properties match the selected filters.")
            st.stop()
    total_listings = len(df)
    average_price = df["Price"].mean()
    average_area = df["Sqft"].mean()

    if "Price" in df.columns and "Sqft" in df.columns:
        valid_area = df[df["Sqft"] > 0]
    
        if not valid_area.empty:
            average_price_sqft = (
                valid_area["Price"] / valid_area["Sqft"]
            ).mean()
        else:
            average_price_sqft = 0
    else:
            average_price_sqft = 0

    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
         "🏠 Total Listings",
         f"{total_listings:,}"
    )
        
    
    
    col2.metric(
         "💰 Average Price",
          f"${average_price:,.0f}"
    )
    
    col3.metric(
         "📐 Average Area",
         f"{average_area:,.0f} Sqft"
    )
    
    col4.metric(
        "💵 Avg Price / Sqft",
        f"${average_price_sqft:,.2f}"
    )
    
    st.divider()

    # --------------------------------------------------------
    # CITY ANALYSIS
    # --------------------------------------------------------
    
    col1, col2 = st.columns(2)
    
    with col1:
    
        city_price = (
            df.groupby("City", as_index=False)["Price"]
            .mean()
            .sort_values("Price", ascending=False)
         )
    
        fig = px.bar(
            city_price,
            x="City",
            y="Price",
            title="Average Property Price by City"
        )
    
        st.plotly_chart(
                fig,
                use_container_width=True
         )
    
    with col2:
    
        property_count = (
            df["Property_Type"]
            .value_counts()
            .reset_index()
        )
    
        property_count.columns = [
            "Property_Type",
            "count"
        ]
    
        fig = px.pie(
            property_count,
            names="Property_Type",
            values="count",
            title="Property Type Distribution"
        )
    
        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # PROPERTY TABLE
    # --------------------------------------------------------
    
        st.subheader("🏠 Filtered Properties")
        # Remove duplicate columns
        df = df.loc[:, ~df.columns.duplicated()]
        st.dataframe(df)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )   

# ============================================================
# PROPERTY EXPLORER
# ============================================================

elif page == "🗺️ Property Explorer":

    st.title("🗺️ Property Explorer")

    property_data = read_query("""
    SELECT
        l.Listing_ID,
        l.City,
        l.Property_Type,
        l.Price,
        l.Sqft,
        l.Date_Listed,
        l.Agent_ID,
        l.Latitude,
        l.Longitude,
        a.Name AS Agent_Name
    FROM listings l
    LEFT JOIN agents a
        ON l.Agent_ID = a.Agent_ID
    WHERE l.Latitude IS NOT NULL
      AND l.Longitude IS NOT NULL
""")

    if property_data.empty:
        st.warning("No location data available.")
    else:

        st.subheader("📍 Property Locations")

        st.map(
            property_data[
                ["Latitude", "Longitude"]
            ].rename(
                columns={
                    "Latitude": "lat",
                    "Longitude": "lon"
                }
            )
        )

        st.subheader("Property Information")

        st.dataframe(
            property_data,
            use_container_width=True,
            hide_index=True
        )

# ============================================================
# 3. SALES ANALYSIS
# ============================================================

elif page == "📈 Sales Analysis":

    st.title("📈 Sales Analysis")

    sales_df = read_query("""
        SELECT
            s.Listing_ID,
            s.Sale_Price,
            s.Date_Sold,
            s.Days_on_Market,
            l.City,
            l.Property_Type,
            l.Price AS Listing_Price,
            a.Name AS Agent_Name
        FROM sales s
        JOIN listings l
            ON s.Listing_ID = l.Listing_ID
        LEFT JOIN agents a
            ON l.Agent_ID = a.Agent_ID
        ORDER BY s.Date_Sold DESC
    """)

    if sales_df.empty:
        st.warning("No sales data available.")
        st.stop()

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    total_sales = len(sales_df)
    total_revenue = sales_df["Sale_Price"].sum()
    average_sale_price = sales_df["Sale_Price"].mean()
    average_days_on_market = sales_df["Days_on_Market"].mean()

    # Calculate percentage sold above listing price
    sold_above = (sales_df["Sale_Price"] > sales_df["Listing_Price"]).sum()
    percentage_above_listing = (sold_above / total_sales * 100) if total_sales > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "🏷️ Total Sales",
        f"{total_sales:,}"
    )

    col2.metric(
        "💰 Total Revenue",
        f"${total_revenue:,.0f}"
    )

    col3.metric(
        "📊 Avg Sale Price",
        f"${average_sale_price:,.0f}"
    )

    col4.metric(
        "📅 Avg Days on Market",
        f"{average_days_on_market:.0f} days"
    )

    st.divider()

    # --------------------------------------------------------
    # SALES BY CITY
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        city_sales = (
            sales_df.groupby("City", as_index=False)["Sale_Price"]
            .sum()
            .sort_values("Sale_Price", ascending=False)
        )

        fig = px.bar(
            city_sales,
            x="City",
            y="Sale_Price",
            title="Total Sales Revenue by City"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        days_by_city = (
            sales_df.groupby("City", as_index=False)["Days_on_Market"]
            .mean()
            .sort_values("Days_on_Market", ascending=False)
        )

        fig = px.bar(
            days_by_city,
            x="City",
            y="Days_on_Market",
            title="Average Days on Market by City"
        )

        st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------------
    # SALES BY PROPERTY TYPE
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        property_type_sales = (
            sales_df.groupby("Property_Type", as_index=False)["Sale_Price"]
            .mean()
            .sort_values("Sale_Price", ascending=False)
        )

        fig = px.bar(
            property_type_sales,
            x="Property_Type",
            y="Sale_Price",
            title="Average Sale Price by Property Type"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        property_count = (
            sales_df["Property_Type"]
            .value_counts()
            .reset_index()
        )

        property_count.columns = ["Property_Type", "count"]

        fig = px.pie(
            property_count,
            names="Property_Type",
            values="count",
            title="Sales Distribution by Property Type"
        )

        st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------------
    # PRICE COMPARISON: LISTING vs SALE
    # --------------------------------------------------------

    st.subheader("Price Comparison Analysis")

    col1, col2 = st.columns(2)

    with col1:
        above_below = pd.DataFrame({
            "Category": ["Sold Above Listing", "Sold At or Below"],
            "Count": [sold_above, total_sales - sold_above]
        })

        fig = px.pie(
            above_below,
            names="Category",
            values="Count",
            title=f"Properties Sold Above Listing ({percentage_above_listing:.1f}%)"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        sales_df["Price_Difference"] = sales_df["Sale_Price"] - sales_df["Listing_Price"]
        
        fig = px.histogram(
            sales_df,
            x="Price_Difference",
            nbins=30,
            title="Distribution of Sale Price Difference",
            labels={"Price_Difference": "Sale Price - Listing Price ($)"}
        )

        st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------------
    # TIME ON MARKET ANALYSIS
    # --------------------------------------------------------

    st.subheader("Time on Market Analysis")

    fig = px.scatter(
        sales_df,
        x="Days_on_Market",
        y="Sale_Price",
        color="City",
        hover_name="Property_Type",
        title="Days on Market vs Sale Price"
    )

    st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------------
    # SALES TABLE
    # --------------------------------------------------------

    st.subheader("Sales Records")

    st.dataframe(
        sales_df,
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# 5. AGENT ANALYSIS
# ============================================================

elif page == "👨‍💼 Agent Analysis":

    st.title("👨‍💼 Agent Performance")

    agent_df = read_query("""
        SELECT
            a.Agent_ID,
            a.Name,
            a.Phone,
            a.Email,
            a.commission_rate,
            a.deals_closed,
            a.rating,
            a.experience_years,
            a.avg_closing_days,

            COUNT(
                DISTINCT l.Listing_ID
            ) AS Total_Listings,

            COUNT(
                DISTINCT s.Listing_ID
            ) AS Actual_Sales,

            COALESCE(
                SUM(s.Sale_Price),
                0
            ) AS Total_Sales_Revenue,

            AVG(
                s.Days_on_Market
            ) AS Actual_Avg_Days

        FROM agents a

        LEFT JOIN listings l
            ON a.Agent_ID = l.Agent_ID

        LEFT JOIN sales s
            ON l.Listing_ID = s.Listing_ID

        GROUP BY
            a.Agent_ID,
            a.Name,
            a.Phone,
            a.Email,
            a.commission_rate,
            a.deals_closed,
            a.rating,
            a.experience_years,
            a.avg_closing_days

        ORDER BY
            Total_Sales_Revenue DESC
    """)

    if agent_df.empty:

        st.warning("No agent data available.")
        st.stop()

    # --------------------------------------------------------
    # KPIs
    # --------------------------------------------------------

    total_agents = len(agent_df)

    total_agent_sales = agent_df[
        "Actual_Sales"
    ].sum()

    total_agent_revenue = agent_df[
        "Total_Sales_Revenue"
    ].sum()

    average_rating = agent_df[
        "rating"
    ].mean()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "👨‍💼 Agents",
        f"{total_agents:,}"
    )

    c2.metric(
        "🏷️ Sales",
        f"{total_agent_sales:,}"
    )

    c3.metric(
        "💰 Revenue",
        f"{total_agent_revenue:,.0f}"
    )

    c4.metric(
        "⭐ Avg Rating",
        f"{average_rating:.2f}"
    )

    st.divider()

    # --------------------------------------------------------
    # CHARTS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        top_agents = (
            agent_df
            .sort_values(
                "Actual_Sales",
                ascending=False
            )
            .head(10)
        )

        fig = px.bar(
            top_agents,
            x="Name",
            y="Actual_Sales",
            title="Top Agents by Sales"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        top_revenue = (
            agent_df
            .sort_values(
                "Total_Sales_Revenue",
                ascending=False
            )
            .head(10)
        )

        fig = px.bar(
            top_revenue,
            x="Name",
            y="Total_Sales_Revenue",
            title="Top Agents by Sales Revenue"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # EXPERIENCE VS DEALS
    # --------------------------------------------------------

    fig = px.scatter(
        agent_df,
        x="experience_years",
        y="Actual_Sales",
        size="rating",
        hover_name="Name",
        title="Experience vs Actual Sales"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # RATING VS CLOSING DAYS
    # --------------------------------------------------------

    rating_df = (
        agent_df
        .dropna(
            subset=[
                "rating",
                "avg_closing_days"
            ]
        )
        .groupby(
            "rating",
            as_index=False
        )["avg_closing_days"]
        .mean()
    )

    if not rating_df.empty:

        fig = px.bar(
            rating_df,
            x="rating",
            y="avg_closing_days",
            title="Agent Rating vs Average Closing Days"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # AGENT TABLE
    # --------------------------------------------------------

    st.subheader("Agent Performance Table")

    st.dataframe(
        agent_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 6. BUYER ANALYSIS
# ============================================================

elif page == "👤 Buyer Analysis":

    st.title("👤 Buyer & Financing Analysis")

    buyer_df = read_query("""
        SELECT
            buyer_id,
            sale_id,
            buyer_type,
            payment_mode,
            loan_taken,
            loan_provider,
            loan_amount
        FROM buyers
    """)

    if buyer_df.empty:

        st.warning("No buyer data available.")
        st.stop()

    # --------------------------------------------------------
    # KPIs
    # --------------------------------------------------------

    total_buyers = len(buyer_df)

    investor_count = len(
        buyer_df[
            buyer_df["buyer_type"]
            .astype(str)
            .str.lower()
            .str.contains("investor", na=False)
        ]
    )

    investor_percentage = (
        investor_count /
        total_buyers *
        100
    ) if total_buyers > 0 else 0

    loan_count = len(
        buyer_df[
            buyer_df["loan_taken"] == 1
        ]
    )

    loan_percentage = (
        loan_count /
        total_buyers *
        100
    ) if total_buyers > 0 else 0

    average_loan = buyer_df[
        buyer_df["loan_amount"] > 0
    ]["loan_amount"].mean()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "👤 Total Buyers",
        f"{total_buyers:,}"
    )

    c2.metric(
        "📊 Investors",
        f"{investor_percentage:.2f}%"
    )

    c3.metric(
        "🏦 Loan Uptake",
        f"{loan_percentage:.2f}%"
    )

    c4.metric(
        "💰 Avg Loan",
        f"{average_loan:,.0f}"
        if pd.notna(average_loan)
        else "0"
    )

    st.divider()

    # --------------------------------------------------------
    # BUYER TYPE
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        buyer_type = (
            buyer_df["buyer_type"]
            .value_counts()
            .reset_index()
        )

        buyer_type.columns = [
            "Buyer_Type",
            "Count"
        ]

        fig = px.pie(
            buyer_type,
            names="Buyer_Type",
            values="Count",
            title="Investor vs End User"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        payment_mode = (
            buyer_df["payment_mode"]
            .value_counts()
            .reset_index()
        )

        payment_mode.columns = [
            "Payment_Mode",
            "Count"
        ]

        fig = px.bar(
            payment_mode,
            x="Payment_Mode",
            y="Count",
            title="Payment Mode Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # LOAN BY BUYER TYPE
    # --------------------------------------------------------

    loan_type = (
        buyer_df
        .dropna(subset=["buyer_type"])
        .groupby(
            "buyer_type",
            as_index=False
        )["loan_amount"]
        .mean()
    )

    if not loan_type.empty:

        fig = px.bar(
            loan_type,
            x="buyer_type",
            y="loan_amount",
            title="Average Loan Amount by Buyer Type"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # LOAN PROVIDER
    # --------------------------------------------------------

    provider_df = (
        buyer_df
        .dropna(subset=["loan_provider"])
        ["loan_provider"]
        .value_counts()
        .reset_index()
    )

    provider_df.columns = [
        "Loan_Provider",
        "Count"
    ]

    if not provider_df.empty:

        fig = px.bar(
            provider_df,
            x="Loan_Provider",
            y="Count",
            title="Loan Provider Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # BUYER TABLE
    # --------------------------------------------------------

    st.subheader("Buyer Records")

    st.dataframe(
        buyer_df,
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "Note: The current sales table contains Listing_ID but "
        "does not contain Sale_ID. Therefore buyer.sale_id is "
        "not automatically joined to sales."
    )


# ============================================================
# 7. SQL QUERIES
# ============================================================

elif page == "🧮 SQL Queries":

    st.title("🧮 SQL Analysis")

    st.markdown(
        "Select a business question to view its SQL query and result."
    )

    sql_queries = {

        # ----------------------------------------------------
        # PROPERTY & PRICING
        # ----------------------------------------------------

        "1. Average listing price by city": """
SELECT
    City,
    ROUND(AVG(Price), 2) AS Average_Price
FROM listings
GROUP BY City
ORDER BY Average_Price DESC;
""",

        "2. Average price per square foot by property type": """
SELECT
    Property_Type,
    ROUND(
        AVG(
            CASE
                WHEN Sqft > 0
                THEN Price / Sqft
            END
        ),
        2
    ) AS Average_Price_Per_Sqft
FROM listings
GROUP BY Property_Type
ORDER BY Average_Price_Per_Sqft DESC;
""",

        "3. Furnishing status and property prices": """
SELECT
    pa.furnishing_status,
    ROUND(AVG(l.Price), 2) AS Average_Price
FROM listings l
JOIN property_attributes pa
    ON l.Listing_ID = pa.listing_id
GROUP BY pa.furnishing_status
ORDER BY Average_Price DESC;
""",

        "4. Metro distance and property prices": """
SELECT
    CASE
        WHEN pa.metro_distance_km <= 2
            THEN '0-2 km'
        WHEN pa.metro_distance_km <= 5
            THEN '2-5 km'
        ELSE 'Above 5 km'
    END AS Metro_Distance_Group,

    ROUND(AVG(l.Price), 2) AS Average_Price

FROM listings l

JOIN property_attributes pa
    ON l.Listing_ID = pa.listing_id

GROUP BY
    CASE
        WHEN pa.metro_distance_km <= 2
            THEN '0-2 km'
        WHEN pa.metro_distance_km <= 5
            THEN '2-5 km'
        ELSE 'Above 5 km'
    END;
""",

        "5. Rented vs non-rented property prices": """
SELECT
    pa.is_rented,
    ROUND(AVG(l.Price), 2) AS Average_Price
FROM listings l
JOIN property_attributes pa
    ON l.Listing_ID = pa.listing_id
GROUP BY pa.is_rented;
""",

        "6. Bedrooms and bathrooms vs pricing": """
SELECT
    pa.bedrooms,
    pa.bathrooms,
    ROUND(AVG(l.Price), 2) AS Average_Price
FROM listings l
JOIN property_attributes pa
    ON l.Listing_ID = pa.listing_id
GROUP BY
    pa.bedrooms,
    pa.bathrooms
ORDER BY Average_Price DESC;
""",

        "7. Parking and power backup vs price": """
SELECT
    pa.parking_available,
    pa.power_backup,
    ROUND(AVG(l.Price), 2) AS Average_Price
FROM listings l
JOIN property_attributes pa
    ON l.Listing_ID = pa.listing_id
GROUP BY
    pa.parking_available,
    pa.power_backup;
""",

        "8. Year built and listing price": """
SELECT
    pa.year_built,
    ROUND(AVG(l.Price), 2) AS Average_Price
FROM listings l
JOIN property_attributes pa
    ON l.Listing_ID = pa.listing_id
GROUP BY pa.year_built
ORDER BY pa.year_built;
""",

        "9. Cities with highest average property prices": """
SELECT
    City,
    ROUND(AVG(Price), 2) AS Average_Price
FROM listings
GROUP BY City
ORDER BY Average_Price DESC;
""",

        "10. Properties by price bucket": """
SELECT
    CASE
        WHEN Price < 100000
            THEN 'Below 100K'
        WHEN Price < 250000
            THEN '100K - 250K'
        WHEN Price < 500000
            THEN '250K - 500K'
        WHEN Price < 1000000
            THEN '500K - 1M'
        ELSE 'Above 1M'
    END AS Price_Bucket,

    COUNT(*) AS Property_Count

FROM listings

GROUP BY
    CASE
        WHEN Price < 100000
            THEN 'Below 100K'
        WHEN Price < 250000
            THEN '100K - 250K'
        WHEN Price < 500000
            THEN '250K - 500K'
        WHEN Price < 1000000
            THEN '500K - 1M'
        ELSE 'Above 1M'
    END

ORDER BY Property_Count DESC;
""",

        # ----------------------------------------------------
        # SALES
        # ----------------------------------------------------

        "11. Average days on market by city": """
SELECT
    l.City,
    ROUND(AVG(s.Days_on_Market), 2)
        AS Average_Days_On_Market
FROM sales s
JOIN listings l
    ON s.Listing_ID = l.Listing_ID
GROUP BY l.City
ORDER BY Average_Days_On_Market;
""",

        "12. Property types that sell fastest": """
SELECT
    l.Property_Type,
    ROUND(AVG(s.Days_on_Market), 2)
        AS Average_Days_On_Market
FROM sales s
JOIN listings l
    ON s.Listing_ID = l.Listing_ID
GROUP BY l.Property_Type
ORDER BY Average_Days_On_Market;
""",

        "13. Percentage sold above listing price": """
SELECT
    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN s.Sale_Price > l.Price
                THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS Percentage_Sold_Above_Listing
FROM sales s
JOIN listings l
    ON s.Listing_ID = l.Listing_ID;
""",

        "14. Sale-to-list price ratio by city": """
SELECT
    l.City,

    ROUND(
        AVG(
            CASE
                WHEN l.Price > 0
                THEN s.Sale_Price / l.Price
            END
        ),
        3
    ) AS Sale_To_List_Ratio

FROM sales s

JOIN listings l
    ON s.Listing_ID = l.Listing_ID

GROUP BY l.City

ORDER BY Sale_To_List_Ratio DESC;
""",

        "15. Listings taking more than 90 days": """
SELECT
    s.Listing_ID,
    l.City,
    l.Property_Type,
    l.Price AS Listing_Price,
    s.Sale_Price,
    s.Days_on_Market
FROM sales s
JOIN listings l
    ON s.Listing_ID = l.Listing_ID
WHERE s.Days_on_Market > 90
ORDER BY s.Days_on_Market DESC;
""",

        "16. Metro distance and time on market": """
SELECT
    CASE
        WHEN pa.metro_distance_km <= 2
            THEN '0-2 km'
        WHEN pa.metro_distance_km <= 5
            THEN '2-5 km'
        ELSE 'Above 5 km'
    END AS Metro_Distance_Group,

    ROUND(
        AVG(s.Days_on_Market),
        2
    ) AS Average_Days_On_Market

FROM sales s

JOIN listings l
    ON s.Listing_ID = l.Listing_ID

JOIN property_attributes pa
    ON l.Listing_ID = pa.listing_id

GROUP BY
    CASE
        WHEN pa.metro_distance_km <= 2
            THEN '0-2 km'
        WHEN pa.metro_distance_km <= 5
            THEN '2-5 km'
        ELSE 'Above 5 km'
    END;
""",

        "17. Monthly sales trend": """
SELECT
    strftime(
        '%Y-%m',
        Date_Sold
    ) AS Month,

    COUNT(*) AS Sales_Count

FROM sales

GROUP BY Month

ORDER BY Month;
""",

        "18. Currently unsold properties": """
SELECT
    l.Listing_ID,
    l.City,
    l.Property_Type,
    l.Price,
    l.Sqft,
    l.Date_Listed,
    l.Agent_ID

FROM listings l

LEFT JOIN sales s
    ON l.Listing_ID = s.Listing_ID

WHERE s.Listing_ID IS NULL

ORDER BY l.Price DESC;
""",

        # ----------------------------------------------------
        # AGENTS
        # ----------------------------------------------------

        "19. Agents with most sales": """
SELECT
    a.Agent_ID,
    a.Name,
    COUNT(s.Listing_ID) AS Sales_Count

FROM agents a

JOIN listings l
    ON a.Agent_ID = l.Agent_ID

JOIN sales s
    ON l.Listing_ID = s.Listing_ID

GROUP BY
    a.Agent_ID,
    a.Name

ORDER BY Sales_Count DESC;
""",

        "20. Agents by total sales revenue": """
SELECT
    a.Agent_ID,
    a.Name,
    ROUND(
        SUM(s.Sale_Price),
        2
    ) AS Total_Sales_Revenue

FROM agents a

JOIN listings l
    ON a.Agent_ID = l.Agent_ID

JOIN sales s
    ON l.Listing_ID = s.Listing_ID

GROUP BY
    a.Agent_ID,
    a.Name

ORDER BY Total_Sales_Revenue DESC;
""",

        "21. Agents who close deals fastest": """
SELECT
    a.Agent_ID,
    a.Name,

    ROUND(
        AVG(s.Days_on_Market),
        2
    ) AS Average_Days_On_Market

FROM agents a

JOIN listings l
    ON a.Agent_ID = l.Agent_ID

JOIN sales s
    ON l.Listing_ID = s.Listing_ID

GROUP BY
    a.Agent_ID,
    a.Name

ORDER BY Average_Days_On_Market;
""",

        "22. Experience vs deals closed": """
SELECT
    Agent_ID,
    Name,
    experience_years,
    deals_closed
FROM agents
ORDER BY experience_years;
""",

        "23. Agent rating vs closing speed": """
SELECT
    rating,
    ROUND(
        AVG(avg_closing_days),
        2
    ) AS Average_Closing_Days
FROM agents
GROUP BY rating
ORDER BY rating DESC;
""",

        "24. Commission information by agent": """
SELECT
    Agent_ID,
    Name,
    commission_rate,
    deals_closed,
    ROUND(
        commission_rate * deals_closed,
        2
    ) AS Commission_Index
FROM agents
ORDER BY Commission_Index DESC;
""",

        "25. Agents with most active listings": """
SELECT
    a.Agent_ID,
    a.Name,
    COUNT(l.Listing_ID) AS Active_Listings

FROM agents a

JOIN listings l
    ON a.Agent_ID = l.Agent_ID

LEFT JOIN sales s
    ON l.Listing_ID = s.Listing_ID

WHERE s.Listing_ID IS NULL

GROUP BY
    a.Agent_ID,
    a.Name

ORDER BY Active_Listings DESC;
""",

# ----------------------------------------------------
# BUYERS
# ----------------------------------------------------

        "26. Investor vs end user percentage": """
SELECT
    buyer_type,

    ROUND(
        100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM buyers),
        2
    ) AS Percentage

FROM buyers

GROUP BY buyer_type;
""",

        "27. Loan uptake by buyer type": """
SELECT
    buyer_type,

    COUNT(*) AS Total_Buyers,

    SUM(
        CASE
            WHEN loan_taken = 1
            THEN 1
            ELSE 0
        END
    ) AS Loan_Buyers,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN loan_taken = 1
                THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS Loan_Uptake_Rate

FROM buyers

GROUP BY buyer_type

ORDER BY Loan_Uptake_Rate DESC;
""",

        "28. Average loan amount by buyer type": """
SELECT
    buyer_type,
    ROUND(
        AVG(
            CASE
                WHEN loan_amount > 0
                THEN loan_amount
            END
        ),
        2
    ) AS Average_Loan_Amount
FROM buyers
GROUP BY buyer_type;
""",

        "29. Most commonly used payment mode": """
SELECT
    payment_mode,
    COUNT(*) AS Transaction_Count
FROM buyers
GROUP BY payment_mode
ORDER BY Transaction_Count DESC;
""",

        "30. Loan-backed buyer records": """
SELECT
    buyer_id,
    sale_id,
    buyer_type,
    payment_mode,
    loan_taken,
    loan_provider,
    loan_amount
FROM buyers
WHERE loan_taken = 1
ORDER BY loan_amount DESC;
"""
    }

    selected_question = st.selectbox(
        "Select Business Question",
        list(sql_queries.keys())
    )

    st.subheader(selected_question)

    selected_sql = sql_queries[
        selected_question
    ]

    st.code(
        selected_sql,
        language="sql"
    )

    result_df = read_query(
        selected_sql
    )

    if result_df.empty:

        st.info(
            "The query returned no records."
        )

    else:

        st.dataframe(
            result_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 8. CRUD OPERATIONS
# ============================================================

elif page == "🛠️ CRUD Operations":

    st.title("🛠️ CRUD Operations")

    st.markdown(
        "Create, read, update and delete records from the database."
    )

    table = st.selectbox(
        "Select Table",
        [
            "listings",
            "property_attributes",
            "agents",
            "sales",
            "buyers"
        ]
    )

    # --------------------------------------------------------
    # TABLE SCHEMA
    # --------------------------------------------------------

    schema_df = read_query(
        f'PRAGMA table_info("{table}")'
    )

    if schema_df.empty:
        st.error(
            "Unable to read table schema."
        )
        st.stop()

    columns = schema_df[
        "name"
    ].tolist()

    primary_keys = schema_df[
        schema_df["pk"] == 1
    ]["name"].tolist()

    primary_key = (
        primary_keys[0]
        if primary_keys
        else None
    )

    # Auto-detect ID column if no primary key declared
    if not primary_key:
        # Common ID column patterns
        id_patterns = ["_id", "id", "ID", "_ID"]
        for pattern in id_patterns:
            matching_cols = [col for col in columns if pattern in col.lower()]
            if matching_cols:
                primary_key = matching_cols[0]
                st.warning(f"⚠️ No primary key declared. Using '{primary_key}' as identifier.")
                break
        
        if not primary_key and columns:
            # Use first column if it looks like an identifier
            primary_key = columns[0]
            st.info(f"ℹ️ Using '{primary_key}' as identifier (first column)")


    # --------------------------------------------------------
    # READ
    # --------------------------------------------------------

    st.subheader(
        f"📖 {table} Records"
    )

    # Get record count
    count_df = read_query(
        f'SELECT COUNT(*) AS record_count FROM "{table}"'
    )
    record_count = count_df["record_count"].iloc[0] if not count_df.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("📊 Total Records", f"{record_count:,}")
    col2.metric("🔑 Primary Key", primary_key if primary_key else "None")
    col3.metric("📋 Columns", len(columns))

    # Search functionality
    st.write("**Search/Filter Records:**")
    search_col = st.selectbox(
        "Filter by column",
        columns,
        key=f"search_col_{table}"
    )
    search_value = st.text_input(
        "Enter search value",
        key=f"search_value_{table}"
    )

    if search_value:
        table_df = read_query(
            f'SELECT * FROM "{table}" WHERE CAST("{search_col}" AS TEXT) LIKE ?',
            [f"%{search_value}%"]
        )
    else:
        table_df = read_query(
            f'SELECT * FROM "{table}"'
        )

    # Pagination
    if not table_df.empty:
        rows_per_page = st.slider(
            "Rows per page",
            min_value=5,
            max_value=100,
            value=10,
            key=f"rows_per_page_{table}"
        )
        page = st.number_input(
            "Page",
            min_value=1,
            max_value=max(1, (len(table_df) // rows_per_page) + 1),
            key=f"page_{table}"
        )
        start_idx = (page - 1) * rows_per_page
        end_idx = start_idx + rows_per_page
        table_df_page = table_df.iloc[start_idx:end_idx]

        st.info(f"Showing {start_idx + 1} to {min(end_idx, len(table_df))} of {len(table_df)} records")
    else:
        table_df_page = table_df
        st.warning("No records found.")

    st.dataframe(
        table_df_page,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ========================================================
    # CREATE
    # ========================================================

    st.subheader("➕ Add New Record")

    st.write("**Column Schema:**")
    schema_display = schema_df[["name", "type", "notnull"]].copy()
    schema_display.columns = ["Column Name", "Data Type", "Required"]
    schema_display["Required"] = schema_display["Required"].apply(lambda x: "✅ Yes" if x == 1 else "⚠️ No")
    st.dataframe(schema_display, use_container_width=True, hide_index=True)

    with st.form(
        f"add_record_form_{table}"
    ):

        values = {}

        for idx, column in enumerate(columns):
            col_type = schema_df[schema_df["name"] == column]["type"].values[0]
            is_required = schema_df[schema_df["name"] == column]["notnull"].values[0]
            
            placeholder_text = f"{column} ({col_type})"
            if is_required:
                placeholder_text += " [Required]"

            values[column] = st.text_input(
                placeholder_text,
                key=f"add_{table}_{column}"
            )

        add_button = st.form_submit_button(
            "✅ Add Record"
        )

    if add_button:

        insert_columns = [
            column
            for column in columns
            if values[column] != ""
        ]

        insert_values = [
            values[column]
            for column in insert_columns
        ]

        if not insert_columns:

            st.warning(
                "Please enter at least one value."
            )

        else:

            placeholders = ",".join(
                ["?"] * len(insert_columns)
            )

            insert_query = f"""
                INSERT INTO "{table}"
                ({",".join(
                    '"' + column + '"'
                    for column in insert_columns
                )})
                VALUES ({placeholders})
            """

            if execute_query(
                insert_query,
                insert_values
            ):

                st.success(
                    "✅ Record added successfully."
                )

                st.rerun()

            else:
                st.error(
                    "❌ Failed to add record. Check your data and try again."
                )

    st.divider()

    # ========================================================
    # UPDATE
    # ========================================================

    st.subheader("✏️ Update Record")

    if primary_key:

        col1, col2 = st.columns(2)

        with col1:
            update_id = st.text_input(
                f"Enter {primary_key}",
                key=f"update_id_{table}",
                help=f"Enter the unique {primary_key} of the record to update"
            )

        with col2:
            update_column = st.selectbox(
                "Column to update",
                [
                    column
                    for column in columns
                    if column != primary_key
                ],
                key=f"update_column_{table}"
            )

        new_value = st.text_input(
            "New value",
            key=f"new_value_{table}",
            help="Enter the new value for the selected column"
        )

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button(
                "🔍 Preview",
                key=f"preview_button_{table}"
            ):
                if update_id == "":
                    st.warning("Please enter the primary key.")
                else:
                    preview_df = read_query(
                        f'SELECT * FROM "{table}" WHERE "{primary_key}" = ?',
                        [update_id]
                    )
                    if preview_df.empty:
                        st.error(f"No record found with {primary_key} = {update_id}")
                    else:
                        st.info(f"**Current Record:**")
                        st.dataframe(preview_df, use_container_width=True, hide_index=True)

        with col2:
            if st.button(
                "✅ Update Record",
                key=f"update_button_{table}"
            ):

                if update_id == "":
                    st.warning(
                        "Please enter the primary key."
                    )

                elif new_value == "":
                    st.warning(
                        "Please enter a new value."
                    )

                else:

                    update_query = f"""
                        UPDATE "{table}"
                        SET "{update_column}" = ?
                        WHERE "{primary_key}" = ?
                    """

                    if execute_query(
                        update_query,
                        [
                            new_value,
                            update_id
                        ]
                    ):

                        st.success(
                            "✅ Record updated successfully."
                        )

                        st.rerun()

                    else:
                        st.error(
                            "❌ Failed to update record. Please check the values and try again."
                        )

    else:

        st.error(
            "❌ Cannot perform update: No identifier column found. Please ensure the table has a primary key or an ID column."
        )

    st.divider()

    # ========================================================
    # DELETE
    # ========================================================

    st.subheader("🗑️ Delete Record")

    if primary_key:

        col1, col2 = st.columns([2, 1])

        with col1:
            delete_id = st.text_input(
                f"Enter {primary_key} of record to delete",
                key=f"delete_id_{table}",
                help=f"Enter the unique {primary_key} of the record to delete"
            )

        with col2:
            if st.button(
                "🔍 Preview",
                key=f"delete_preview_button_{table}"
            ):
                if delete_id == "":
                    st.warning("Please enter the primary key.")
                else:
                    preview_df = read_query(
                        f'SELECT * FROM "{table}" WHERE "{primary_key}" = ?',
                        [delete_id]
                    )
                    if preview_df.empty:
                        st.error(f"No record found with {primary_key} = {delete_id}")
                    else:
                        st.warning(f"**Record to be deleted:**")
                        st.dataframe(preview_df, use_container_width=True, hide_index=True)

        if st.button(
            "🗑️ Delete Record",
            key=f"delete_button_{table}"
        ):

            if delete_id == "":

                st.warning(
                    "Please enter the primary key."
                )

            else:

                delete_query = f"""
                    DELETE FROM "{table}"
                    WHERE "{primary_key}" = ?
                """

                if execute_query(
                    delete_query,
                    [delete_id]
                ):

                    st.success(
                        "✅ Record deleted successfully."
                    )

                    st.rerun()

                else:
                    st.error(
                        "❌ Failed to delete record."
                    )

    else:

        st.error(
            "❌ Cannot perform delete: No identifier column found. Please ensure the table has a primary key or an ID column."
        )


# ============================================================
# SIDEBAR FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption(
    "BrickView Real Estate Analytics Platform"
)

st.sidebar.caption(
    "Python • SQLite • SQL • Streamlit"
)