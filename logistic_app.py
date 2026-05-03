import streamlit as st
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt

# DB CONNECTION
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="JaiKomal@Puja04",
        database="logistics_db"
    )

def fetch_data(query, params=None):
    conn = get_connection()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

# SIDEBAR
with st.sidebar:
    st.title("🚚 Logistics Dashboard")
    page = st.radio("Navigate", [
        "🏠 Home",
        "🔍 Shipment Search",
        "📈 Delivery Performance",
        "👤 Courier Performance",
        "💰 Cost Analytics",
        "❌ Cancellation Analysis",
        "🏭 Warehouse Insights"
    ])

# HOME PAGE
if page == "🏠 Home":
    st.title("🚚 Smart Logistics Dashboard")
    st.write("Welcome to the Logistics Management Platform!")

    col1, col2, col3 = st.columns(3)

    total = fetch_data("SELECT COUNT(*) AS total FROM shipments")
    delivered = fetch_data("SELECT ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM shipments), 2) AS delivered_percentage FROM shipments WHERE status = 'Delivered'")
    cancelled = fetch_data("SELECT ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM shipments), 2) AS cancelled_percentage FROM shipments WHERE status = 'Cancelled'")
    avg_time = fetch_data("SELECT ROUND(AVG(ABS(DATEDIFF(order_date, delivery_date))), 2) AS avg_delivery_days FROM shipments WHERE delivery_date IS NOT NULL")
    total_cost = fetch_data("SELECT ROUND(SUM(fuel_cost + labor_cost + misc_cost), 2) AS total_cost FROM costs")

    with col1:
        st.metric("Total Shipments", total["total"][0])
        st.metric("Avg Delivery Time", f"{avg_time['avg_delivery_days'][0]} days")

    with col2:
        st.metric("Delivered %", f"{delivered['delivered_percentage'][0]}%")
        st.metric("Cancelled %", f"{cancelled['cancelled_percentage'][0]}%")

    with col3:
        st.metric("Total Cost", f"₹{total_cost['total_cost'][0]}")
    
# SHIPMENT SEARCH PAGE
if page == '🔍 Shipment Search':
    st.title('🔍 Shipment Search & Filtering')
    
    search_id = st.text_input('Search by Shipment ID')
    origin_filter = st.text_input('Search by Origin')
    order_date = st.text_input('Order Date (YYYY-MM-DD)')
    delivery_date = st.text_input('Delivery Date (YYYY-MM-DD)')
    courier_filter = st.text_input('Search by Courier ID')
    status_filter = st.selectbox('Filter by Status', ['All', 'Delivered', 'Cancelled', 'In Transit'])

    query = "SELECT * FROM shipments WHERE 1=1"
    params = []

    if search_id:
        query += " AND shipment_id LIKE %s"
        params.append(f"%{search_id}%")

    if origin_filter:
        query += " AND origin LIKE %s"
        params.append(f"%{origin_filter}%")

    if courier_filter:
        query += " AND courier_id LIKE %s"
        params.append(f"%{courier_filter}%")

    if status_filter != "All":
        query += " AND status = %s"
        params.append(status_filter)

    if order_date and delivery_date:
        query += " AND order_date BETWEEN %s AND %s"
        params.append(order_date)
        params.append(delivery_date)

    query += " LIMIT 100"

    df_search = fetch_data(query, params)

    st.subheader('Shipment Results')
    st.dataframe(df_search)

# DELIVERY PERFORMANCE
if page == '📈 Delivery Performance':
    st.title('📈 Delivery Performance Insights')

    #Avg Delivery time per route
    st.header('Average Delivery Time per Route')
    df_route = fetch_data(''' 
            SELECT origin, destination,
            ROUND(AVG(ABS(DATEDIFF(order_date, delivery_date))), 2) as avg_days FROM shipments
            WHERE delivery_date IS NOT NULL
            GROUP BY origin, destination
            ORDER BY avg_days ASC
            LIMIT 10
            ''')
    st.dataframe(df_route) 
    st.divider()

    #Most Delayed Routes
    st.header('Most Delayed Routes')
    df_delayed = fetch_data('''
            SELECT origin, destination, 
            ROUND(ABS(AVG(DATEDIFF(order_date, delivery_date))), 2) as avg_days FROM shipments
            WHERE delivery_date IS NOT NULL
            GROUP BY origin, destination
            ORDER BY avg_days DESC
            LIMIT 5
            ''')
    st.dataframe(df_delayed)
    st.bar_chart(df_delayed.set_index('origin')['avg_days'])
    st.divider()

    #Delivery Time vs Distance   
    st.header('Delivery Time vs Distance')
    df_distance = fetch_data('''
        SELECT routes.distance_km,
        ROUND(AVG(ABS(DATEDIFF(shipments.order_date, shipments.delivery_date))), 2) as avg_days FROM shipments
        JOIN routes ON shipments.origin = routes.origin
        AND shipments.destination = routes.destination
        WHERE shipments.delivery_date IS NOT NULL
        GROUP BY routes.distance_km
        ORDER BY routes.distance_km
        LIMIT 20
        ''')
    st.dataframe(df_distance)
    st.line_chart(df_distance.set_index('distance_km')['avg_days'])

# COURIER PERFORMANCE                            
if page == '👤 Courier Performance':
    st.title('👤 Courier Performance Insights')

    #Shipments handled per courier
    st.header('Shipment handled per Courier')
    df_courier = fetch_data('''
        SELECT c.name, COUNT(shipments.shipment_id) AS total_shipments FROM shipments
        JOIN courier_staff c ON shipments.courier_id = c.courier_id
        GROUP BY c.name
        ORDER BY total_shipments DESC
        LIMIT 10
        ''')
    st.dataframe(df_courier)
    st.bar_chart(df_courier.set_index('name')['total_shipments'])
    st.divider()

    #On-time delivery %
    st.header('On-Time Delivery %')
    df_ontime = fetch_data('''
        SELECT c.name, ROUND(SUM(CASE WHEN s.status = 'Delivered' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS ontime_percentage
        FROM shipments s
        JOIN courier_staff c ON c.courier_id = s.courier_id
        GROUP BY c.name
        ORDER BY ontime_percentage DESC
        LIMIT 10
        ''')
    st.dataframe(df_ontime)
    st.bar_chart(df_ontime.set_index('name')['ontime_percentage'])
    st.divider()

    #Average rating comparison
    st.header('Avg Rating')
    df_rating = fetch_data('''
        SELECT c.name, rating
        FROM courier_staff c
        ORDER BY rating DESC
        LIMIT 10
        ''')
    st.dataframe(df_rating)
    st.bar_chart(df_rating.set_index('name')['rating'])

#COST ANALYTICS
if page == "💰 Cost Analytics":
    st.title("💰 Cost Analytics")

    #Total Cost per Shipment
    st.header('Total Cost per Shipment')
    df_cost = fetch_data('''
        SELECT s.shipment_id, s.origin, s.destination,
        ROUND(co.fuel_cost + co.labor_cost + co.misc_cost, 2) AS `total_cost (₹)`
        FROM shipments s
        JOIN costs co ON co.shipment_id = s.shipment_id
        ORDER BY `total_cost (₹)` DESC
        LIMIT 10
        ''')
    st.dataframe(df_cost)
    st.divider()

    #Cost per Route
    st.header('Cost per Route')
    df_cost_route = fetch_data('''
        SELECT s.origin, s.destination,
        ROUND(AVG(co.fuel_cost + co.labor_cost + co.misc_cost), 2) AS `avg_cost (₹)`
        FROM shipments s
        JOIN costs co ON s.shipment_id = co.shipment_id
        GROUP BY s.origin, s.destination
        ORDER BY `avg_cost (₹)`
        LIMIT 10
        ''')
    st.dataframe(df_cost_route) 
    st.divider()
    
    #Fuel vs Labor contribution
    st.header('Fuel vs Labor Cost Contribution')
    df_contribution = fetch_data('''
        SELECT 
        ROUND(SUM(fuel_cost) * 100.0 / SUM(fuel_cost + labor_cost + misc_cost), 2) AS fuel_percentage,
        ROUND(SUM(labor_cost) * 100.0 / SUM(fuel_cost + labor_cost + misc_cost), 2) AS labor_percentage FROM costs
        ''')
        
    df_chart = df_contribution.melt(var_name = 'Cost Type', value_name = 'Percentage')
    df_chart['Cost Type'] = df_chart['Cost Type'].str.replace('_percentage', '').str.capitalize()
    st.dataframe(df_chart)
    fig, ax = plt.subplots()
    ax.pie(df_chart['Percentage'], labels = df_chart['Cost Type'], autopct = '%1.2f%%')
    st.pyplot(fig)
    st.divider()

    #High-cost shipments
    st.header('High Cost Shipments')
    df_high_cost = fetch_data('''
        SELECT s.shipment_id, s.origin, s.destination,
        ROUND(co.fuel_cost + co.labor_cost + co.misc_cost, 2) as `total_cost (₹)`
        FROM shipments s
        JOIN costs co ON co.shipment_id = s.shipment_id
        ORDER BY `total_cost (₹)` DESC
        LIMIT 10
        ''')
    st.dataframe(df_high_cost)


#CANCELLATION ANALYSIS
if page == '❌ Cancellation Analysis':
    st.title('❌ Cancellation Analysis')

    #Cancellation Rate by Origin
    st.header('Cancellation Rate by Origin')
    df_cancel_origin = fetch_data('''
        SELECT origin,
        COUNT(*) AS total_shipments,
        SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled,
        ROUND(SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS cancel_rate
        FROM shipments
        GROUP BY origin
        ORDER BY cancel_rate DESC
        LIMIT 10
        ''')
    st.dataframe(df_cancel_origin)
    st.bar_chart(df_cancel_origin.set_index('origin')['cancel_rate'])
    st.divider()

    #Cancellation Rate by Courier 
    st.header('Cancellation Rate by Courier')
    df_cancel_courier = fetch_data('''
        SELECT c.name,
        ROUND(SUM(CASE WHEN s.status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS cancel_rate
        FROM shipments s
        JOIN courier_staff c ON s.courier_id = c.courier_id
        GROUP BY c.name
        ORDER BY cancel_rate DESC
        LIMIT 10
        ''')
    st.dataframe(df_cancel_courier)
    st.bar_chart(df_cancel_courier.set_index('name')['cancel_rate'])
    st.divider()

    #Time to Cancellation 
    st.header('Time to Cancellation Analysis')
    df_time_cancel = fetch_data('''
        SELECT s.origin,s.destination,
        ROUND(AVG(ABS(DATEDIFF(s.order_date, st.timestamp))), 2) AS average_cancellation_time
        FROM shipments s
        JOIN shipment_tracking st ON st.shipment_id = s.shipment_id
        WHERE s.status = 'Cancelled'
        AND st.status =  'Cancelled' 
        GROUP BY s.origin, s.destination
        ORDER BY average_cancellation_time DESC
        LIMIT 10
        ''')
    st.dataframe(df_time_cancel)

#WAREHOUSE INSIGHTS
if page == '🏭 Warehouse Insights':
    st.title('🏭 Warehouse Insights')

    #Warehouse capacity comparison
    st.header('Warehouse Capacity')
    df_capacity = fetch_data('''
        SELECT city, state, capacity
        FROM warehouses
         ORDER BY capacity DESC
         LIMIT 10
         ''')
    st.dataframe(df_capacity)
    st.bar_chart(df_capacity.set_index('city')['capacity'])
    st.divider()

    #High-traffic warehouse cities
    st.header('High-Traffic Warehouse Cities')
    df_traffic = fetch_data('''
        SELECT w.city, COUNT(s.shipment_id) AS total_shipments
        FROM warehouses w
        JOIN shipments s ON w.city = s.origin
        OR w.city = s.destination
        GROUP BY w.city
        ORDER BY total_shipments DESC
        LIMIT 10
    ''')
    st.dataframe(df_traffic)
    st.bar_chart(df_traffic.set_index("city")["total_shipments"])

        

   


        