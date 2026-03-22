import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

#  DB CONNECTION
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="loganWolf@123",
        database="nasa_asteroids"
    )

#  RUN QUERY FUNCTION
def run_query(query, params=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows)


#            STREAMLIT UI STARTS HERE
st.set_page_config(page_title="NASA Asteroid Tracker", layout="wide")

st.title("🚀 NASA Asteroid Tracker")


#     SIDEBAR — QUERY DROPDOWN (15 QUERIES)
st.sidebar.title("📌 Menu")
option = st.sidebar.selectbox(
    "Choose View",
    ["Filter Criteria", "Queries"]
)

predefined_queries = {
    "Count how many times each asteroid has approached Earth":"""SELECT a.name, COUNT(c.neo_reference_id) AS approach_count FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id GROUP BY a.name ORDER BY approach_count DESC;""",
    
    "Average velocity of each asteroid over multiple approaches":"""SELECT a.name, AVG(c.relative_velocity_kmph) AS avg_velocity FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id GROUP BY a.name ORDER BY avg_velocity DESC;""",

    "Top 10 fastest asteroids":"""SELECT a.name, MAX(c.relative_velocity_kmph) AS max_velocity FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id GROUP BY a.name ORDER BY 
max_velocity DESC LIMIT 10;""",

    "Potentially hazardous asteroids that have approached Earth more than 3 times":"""SELECT a.name, COUNT(c.neo_reference_id) AS approach_count FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE a.is_potentially_hazardous_asteroid = TRUE GROUP BY a.name HAVING approach_count > 3;""",
    
    "Find the month with the most asteroid approaches":"""SELECT MONTH(close_approach_date) AS month, COUNT(*) AS total_approaches FROM close_approach GROUP BY MONTH(close_approach_date) ORDER BY total_approaches DESC LIMIT 1;""",
    
    "Get the asteroid with the fastest ever approach speed":"""SELECT a.name, c.relative_velocity_kmph FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id ORDER BY c.relative_velocity_kmph DESC LIMIT 1;""",
    
    "Sort asteroids by maximum estimated diameter":"""SELECT name, estimated_diameter_max_km FROM asteroids ORDER BY estimated_diameter_max_km DESC;""",
    
    "Find an asteroid whose closest approach is getting nearer over time":"""SELECT a.name, c.close_approach_date, c.miss_distance_km FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id ORDER BY a.name, c.close_approach_date;""",
    
    "Display name, date, and miss distance of the closest approach":"""SELECT a.name, c.close_approach_date, c.miss_distance_km FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id ORDER BY c.miss_distance_km ASC LIMIT 10;""",
    
    "asteroids with velocity > 50,000 km/h":"""SELECT a.name, c.relative_velocity_kmph FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE c.relative_velocity_kmph > 50000;""",
    
    "Count how many approaches happened per month":"""SELECT MONTH(close_approach_date) AS month, COUNT(*) AS total_approaches FROM close_approach GROUP BY MONTH(close_approach_date);""",
    
    "Find asteroid with the highest brightness (lowest magnitude)":"""SELECT name, absolute_magnitude_h FROM asteroids ORDER BY absolute_magnitude_h ASC LIMIT 1;""",
    
    "Get count of hazardous vs non-hazardous asteroids":"""SELECT is_potentially_hazardous_asteroid, COUNT(*) AS total FROM asteroids GROUP BY is_potentially_hazardous_asteroid;""",
    
    "Asteroids that passed closer than the Moon (< 1 LD)":"""SELECT a.name, c.close_approach_date, c.miss_distance_lunar FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE c.miss_distance_lunar < 1 ORDER BY c.miss_distance_lunar ASC;""",
    
    "Asteroids that came within 0.05 AU":"""SELECT a.name, c.close_approach_date, c.astronomical FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE c.astronomical < 0.05 ORDER BY c.astronomical ASC;"""
}


if option == "Queries":
    st.header("📊 Predefined SQL Queries")

    selected_query = st.selectbox("Select a Query", list(predefined_queries.keys()))

    if st.button("Run Query"):
        query = predefined_queries[selected_query]
        df = run_query(query)
        st.dataframe(df, use_container_width=True)


#     FILTER CRITERIA PAGE
if option == "Filter Criteria":
    st.header("🔍 Filter Asteroids")

# --- FILTER WIDGETS ---

    start_date = st.date_input("Start Date", date(2024, 1, 1))
    end_date = st.date_input("End Date", date(2025, 4, 13))

    min_mag, max_mag = st.slider("Absolute Magnitude Range", 0.0, 40.0, (10.0, 30.0))
    min_dia, max_dia = st.slider("Estimated Diameter (km)", 0.0, 20.0, (0.1, 5.0))

    rel_min, rel_max = st.slider("Relative Velocity (kmph)", 0.0, 200000.0, (1000.0, 50000.0))

    au_min, au_max = st.slider("Astronomical Units", 0.0, 1.0, (0.01, 0.5))
    lunar_min, lunar_max = st.slider("Lunar Distance", 0.0, 400.0, (0.1, 100.0))

    hazardous = st.selectbox("Show Hazardous Only?", ["All", "Yes", "No"])


# --- SQL FILTER QUERY ----

    filter_sql = """
        SELECT 
            a.id, a.name, a.absolute_magnitude_h,
            a.estimated_diameter_min_km, a.estimated_diameter_max_km,
            a.is_potentially_hazardous_asteroid,
            c.close_approach_date, c.relative_velocity_kmph,
            c.astronomical, c.miss_distance_km, c.miss_distance_lunar
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE c.close_approach_date BETWEEN %s AND %s
          AND a.absolute_magnitude_h BETWEEN %s AND %s
          AND a.estimated_diameter_min_km >= %s
          AND a.estimated_diameter_max_km <= %s
          AND c.relative_velocity_kmph BETWEEN %s AND %s
          AND c.astronomical BETWEEN %s AND %s
          AND c.miss_distance_lunar BETWEEN %s AND %s
    """

    params = [
        start_date, end_date,
        min_mag, max_mag,
        min_dia, max_dia,
        rel_min, rel_max,
        au_min, au_max,
        lunar_min, lunar_max
    ]

    if hazardous == "Yes":
        filter_sql += " AND a.is_potentially_hazardous_asteroid = 1"
    elif hazardous == "No":
        filter_sql += " AND a.is_potentially_hazardous_asteroid = 0"


# --- BUTTON + SHOW RESULT ---

    if st.button("Filter"):
        df = run_query(filter_sql, params)
        st.subheader("Filtered Asteroids")
        st.dataframe(df, use_container_width=True)
