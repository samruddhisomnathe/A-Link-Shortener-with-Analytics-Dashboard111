import sqlite3
import random
import string
import urllib.parse
from datetime import datetime
import pandas as pd

DB_FILE = "analytics.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create urls table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            short_code TEXT PRIMARY KEY,
            long_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create clicks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT NOT NULL,
            click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            country TEXT DEFAULT 'Unknown',
            city TEXT DEFAULT 'Unknown',
            device TEXT DEFAULT 'Unknown',
            os TEXT DEFAULT 'Unknown',
            browser TEXT DEFAULT 'Unknown',
            FOREIGN KEY (short_code) REFERENCES urls (short_code) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

def generate_short_code(length=6):
    """Generates a random unique alphanumeric short code."""
    characters = string.ascii_letters + string.digits
    conn = get_db_connection()
    cursor = conn.cursor()
    
    while True:
        code = "".join(random.choices(characters, k=length))
        cursor.execute("SELECT 1 FROM urls WHERE short_code = ?", (code,))
        if not cursor.fetchone():
            conn.close()
            return code

def shorten_url(long_url, custom_code=None):
    """
    Shortens a long URL.
    Returns the short code if successful.
    Raises ValueError if custom_code is taken or URL is invalid.
    """
    # Basic URL validation
    parsed = urllib.parse.urlparse(long_url)
    if not parsed.scheme or not parsed.netloc:
        # Try prepending http:// if it's missing a scheme
        if not long_url.startswith(("http://", "https://")):
            long_url = "http://" + long_url
            parsed = urllib.parse.urlparse(long_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format. Please include http:// or https://")
        else:
            raise ValueError("Invalid URL format. Please include a valid domain.")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if long URL is already shortened without custom code
    if not custom_code:
        cursor.execute("SELECT short_code FROM urls WHERE long_url = ?", (long_url,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return row["short_code"]

    # Use or generate short code
    if custom_code:
        # Validate custom code format (alphanumeric and underscores/hyphens only)
        custom_code = custom_code.strip()
        if not all(c.isalnum() or c in "-_" for c in custom_code):
            conn.close()
            raise ValueError("Custom alias must only contain alphanumeric characters, hyphens (-), and underscores (_).")
        
        # Check if already taken
        cursor.execute("SELECT 1 FROM urls WHERE short_code = ?", (custom_code,))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"The alias '{custom_code}' is already in use. Please choose another one.")
        code = custom_code
    else:
        code = generate_short_code()

    # Insert into database
    cursor.execute("INSERT INTO urls (short_code, long_url) VALUES (?, ?)", (code, long_url))
    conn.commit()
    conn.close()
    return code

def get_long_url(short_code):
    """Retrieves the long URL for a given short code."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT long_url FROM urls WHERE short_code = ?", (short_code,))
    row = cursor.fetchone()
    conn.close()
    return row["long_url"] if row else None

def log_click(short_code, country="Unknown", city="Unknown", device="Unknown", os="Unknown", browser="Unknown"):
    """Logs details of a click on a shortened link."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if the short code actually exists
    cursor.execute("SELECT 1 FROM urls WHERE short_code = ?", (short_code,))
    if not cursor.fetchone():
        conn.close()
        return False
        
    cursor.execute("""
        INSERT INTO clicks (short_code, country, city, device, os, browser)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (short_code, country or "Unknown", city or "Unknown", device or "Unknown", os or "Unknown", browser or "Unknown"))
    
    conn.commit()
    conn.close()
    return True

def delete_url(short_code):
    """Deletes a short URL and all its associated clicks."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM urls WHERE short_code = ?", (short_code,))
    cursor.execute("DELETE FROM clicks WHERE short_code = ?", (short_code,))
    conn.commit()
    conn.close()

def get_all_links():
    """Returns a Pandas DataFrame of all links and their click counts."""
    conn = get_db_connection()
    query = """
        SELECT u.short_code, u.long_url, u.created_at, COUNT(c.id) as clicks
        FROM urls u
        LEFT JOIN clicks c ON u.short_code = c.short_code
        GROUP BY u.short_code
        ORDER BY u.created_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_analytics(short_code=None):
    """
    Returns a dictionary of dataframes representing analytics.
    If short_code is specified, filters data for that link.
    """
    conn = get_db_connection()
    
    where_clause = ""
    params = ()
    if short_code:
        where_clause = "WHERE short_code = ?"
        params = (short_code,)
        
    # 1. Total Summary
    cursor = conn.cursor()
    if short_code:
        cursor.execute("SELECT COUNT(*) FROM clicks WHERE short_code = ?", params)
        total_clicks = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT country) FROM clicks WHERE short_code = ?", params)
        unique_countries = cursor.fetchone()[0]
    else:
        cursor.execute("SELECT COUNT(*) FROM clicks")
        total_clicks = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM urls")
        total_links = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT country) FROM clicks")
        unique_countries = cursor.fetchone()[0]

    # 2. Clicks over time
    clicks_time_query = f"""
        SELECT datetime(click_time) as click_time
        FROM clicks
        {where_clause}
        ORDER BY click_time ASC
    """
    df_clicks = pd.read_sql_query(clicks_time_query, conn, params=params)
    
    # 3. Device distribution
    device_query = f"""
        SELECT device, COUNT(*) as count
        FROM clicks
        {where_clause}
        GROUP BY device
        ORDER BY count DESC
    """
    df_device = pd.read_sql_query(device_query, conn, params=params)
    
    # 4. OS distribution
    os_query = f"""
        SELECT os, COUNT(*) as count
        FROM clicks
        {where_clause}
        GROUP BY os
        ORDER BY count DESC
    """
    df_os = pd.read_sql_query(os_query, conn, params=params)

    # 5. Browser distribution
    browser_query = f"""
        SELECT browser, COUNT(*) as count
        FROM clicks
        {where_clause}
        GROUP BY browser
        ORDER BY count DESC
    """
    df_browser = pd.read_sql_query(browser_query, conn, params=params)

    # 6. Country distribution
    country_query = f"""
        SELECT country, COUNT(*) as count
        FROM clicks
        {where_clause}
        GROUP BY country
        ORDER BY count DESC
    """
    df_country = pd.read_sql_query(country_query, conn, params=params)

    # 7. City distribution
    city_query = f"""
        SELECT city, country, COUNT(*) as count
        FROM clicks
        {where_clause}
        GROUP BY city, country
        ORDER BY count DESC
        LIMIT 10
    """
    df_city = pd.read_sql_query(city_query, conn, params=params)

    conn.close()
    
    summary = {
        "total_clicks": total_clicks,
        "unique_countries": unique_countries,
        "clicks_df": df_clicks,
        "device_df": df_device,
        "os_df": df_os,
        "browser_df": df_browser,
        "country_df": df_country,
        "city_df": df_city
    }
    
    if not short_code:
        summary["total_links"] = total_links
        
    return summary
