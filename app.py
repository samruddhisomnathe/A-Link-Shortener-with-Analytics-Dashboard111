import streamlit as st
import database as db
import pandas as pd
import altair as alt
import time
import threading
import urllib.request
import json

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Link Shortener & Analytics",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the database on startup
db.init_db()

# CSS for modern premium dashboard styling (dark theme, glassmorphism, glowing accents)
st.markdown("""
<style>
    /* Styling headers and fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Title text gradient */
    .title-text {
        background: linear-gradient(90deg, #8A2387 0%, #E94057 50%, #F27121 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .subtitle-text {
        color: #a0aec0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Glassmorphic cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 24px;
        border: 1px rgba(255, 255, 255, 0.08) solid;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
    }
    
    /* Metrics panel */
    .metric-card {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 18px;
        border-left: 4px solid #E94057;
        border-top: 1px rgba(255, 255, 255, 0.05) solid;
        border-right: 1px rgba(255, 255, 255, 0.05) solid;
        border-bottom: 1px rgba(255, 255, 255, 0.05) solid;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 600;
        color: #ffffff;
        margin: 5px 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* QR code and Copy Link container */
    .result-card {
        background: rgba(138, 35, 135, 0.05);
        border-radius: 12px;
        padding: 20px;
        border: 1px rgba(138, 35, 135, 0.2) solid;
        margin-top: 15px;
    }
    
    /* Custom button styling */
    .stButton>button {
        background: linear-gradient(135deg, #8A2387 0%, #E94057 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(233, 64, 87, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(233, 64, 87, 0.5);
        background: linear-gradient(135deg, #9C27B0 0%, #FF4081 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def get_base_url():
    """Dynamically resolves the base URL of the Streamlit server."""
    base = "http://localhost:8501"
    try:
        from streamlit.web.server.websocket_headers import _get_websocket_headers
        headers = _get_websocket_headers()
        if headers:
            host = headers.get("Host")
            proto = headers.get("X-Forwarded-Proto", "http")
            if host:
                base = f"{proto}://{host}"
    except Exception:
        pass
    
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            host = st.context.headers.get("Host")
            proto = st.context.headers.get("X-Forwarded-Proto", "http")
            if host:
                base = f"{proto}://{host}"
    except Exception:
        pass
        
    return base

def perform_geo_and_log(short_code, ip, os_name, browser_name, device_name):
    """Fetches geolocation details asynchronously and records the click."""
    country = "Unknown"
    city = "Unknown"
    
    # Handle localhost
    if ip == "127.0.0.1" or ip == "localhost":
        country = "Local Network"
        city = "Localhost"
    elif ip:
        # 1. Try ip-api.com (free, fast, no API key needed)
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,country,city"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                data = json.loads(response.read().decode())
                if data.get("status") == "success":
                    country = data.get("country", "Unknown")
                    city = data.get("city", "Unknown")
        except Exception:
            # 2. Try ipapi.co as a fallback
            try:
                url = f"https://ipapi.co/{ip}/json/"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=1.5) as response:
                    data = json.loads(response.read().decode())
                    if not data.get("error"):
                        country = data.get("country_name", "Unknown")
                        city = data.get("city", "Unknown")
            except Exception:
                pass
                
    db.log_click(
        short_code=short_code,
        country=country,
        city=city,
        device=device_name,
        os=os_name,
        browser=browser_name
    )

# --- REDIRECTION ROUTING ENGINE ---
# Check query parameters to see if this is a redirect request
params = st.query_params

if "s" in params:
    short_code = params["s"]
    if isinstance(short_code, list):
        short_code = short_code[0]
        
    long_url = db.get_long_url(short_code)
    
    # Hide the default Streamlit UI elements for a clean redirect screen
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stSidebar"] {display: none;}
            [data-testid="stHeader"] {display: none;}
            [data-testid="stSidebarCollapseButton"] {display: none;}
            .stApp {
                background: radial-gradient(circle at center, #1e1b4b 0%, #09090b 100%);
            }
        </style>
    """, unsafe_allow_html=True)
    
    if not long_url:
        # Invalid short link - Beautiful 404 page
        st.markdown("""
            <div style="text-align: center; margin-top: 15vh; padding: 20px;">
                <h1 style="font-size: 6rem; background: linear-gradient(90deg, #E94057 0%, #F27121 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;">404</h1>
                <h2 style="color: white; font-size: 2rem; margin-bottom: 20px;">Link Not Found or Expired</h2>
                <p style="color: #a0aec0; max-width: 500px; margin: 0 auto 30px auto; font-size: 1.1rem;">
                    The short link you are trying to access doesn't exist or has been deleted.
                </p>
            </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("Go to Admin Dashboard", use_container_width=True):
                st.query_params.clear()
                st.rerun()
    else:
        # 1. Parse client agent headers directly in Python (Instant, no reloads)
        headers = {}
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = st.context.headers
            
        ua = headers.get("User-Agent", "")
        ip_header = headers.get("X-Forwarded-For", "127.0.0.1")
        # Handle multiple proxies if present
        ip = ip_header.split(",")[0].strip() if ip_header else "127.0.0.1"
        
        # Parse OS
        os_name = "Unknown"
        if "Windows" in ua: os_name = "Windows"
        elif "Macintosh" in ua or "Mac OS X" in ua: os_name = "MacOS"
        elif "Linux" in ua: os_name = "Linux"
        elif "Android" in ua: os_name = "Android"
        elif "iPhone" in ua or "iPad" in ua or "iPod" in ua: os_name = "iOS"
        
        # Parse Device Type
        device_name = "Desktop"
        if any(m in ua.lower() for m in ["mobi", "android", "iphone", "ipod"]):
            if "ipad" in ua.lower():
                device_name = "Tablet"
            else:
                device_name = "Mobile"
        else:
            device_name = "Desktop"
                
        # Parse Browser
        browser_name = "Unknown"
        if "Edge" in ua or "Edg" in ua: browser_name = "Edge"
        elif "Chrome" in ua or "CriOS" in ua:
            if "OPR" in ua: browser_name = "Opera"
            else: browser_name = "Chrome"
        elif "Safari" in ua: browser_name = "Safari"
        elif "Firefox" in ua: browser_name = "Firefox"
        elif "Opera" in ua or "OPR" in ua: browser_name = "Opera"
        
        # 2. Trigger asynchronous click logger in the background (0ms latency for user redirect)
        threading.Thread(
            target=perform_geo_and_log,
            args=(short_code, ip, os_name, browser_name, device_name),
            daemon=True
        ).start()
        
        # 3. Render quick loading redirect page and navigate parent page instantly
        st.markdown(f"""
            <div style="text-align: center; margin-top: 20vh; color: white;">
                <div style="font-size: 4rem; margin-bottom: 20px;">🚀</div>
                <h2 style="font-weight: 600; margin-bottom: 10px;">Taking you to your destination</h2>
                <p style="color: #a0aec0; margin-bottom: 30px;">Redirecting you to: <br><strong style="color: #E94057;">{long_url}</strong></p>
                <p style="font-size: 0.9rem; color: #718096;">
                    If you are not redirected automatically in a moment, 
                    <a href="{long_url}" target="_parent" style="color: #F27121; text-decoration: underline; font-weight: 600;">click here</a>.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.components.v1.html(f"""
            <script>
                window.parent.location.href = "{long_url}";
            </script>
        """, height=10)

# --- ADMIN ANALYTICS DASHBOARD ---
else:
    # Sidebar Navigation and Configuration
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; font-weight: 800; background: linear-gradient(90deg, #8A2387, #E94057); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🔗 LINK SHIELD</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #a0aec0; font-size: 0.85rem; margin-top: -10px; margin-bottom: 30px;'>Premium Link Shortening & Analytics</p>", unsafe_allow_html=True)
        
        st.sidebar.subheader("Navigation")
        menu = st.sidebar.radio(
            "Go To",
            ["Shorten a Link", "Analytics Dashboard", "Links Manager"],
            index=0
        )
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### System Info")
        base_url = get_base_url()
        st.sidebar.info(f"**Short URL Base:**\n`{base_url}`")
        
        if st.sidebar.button("Clear database (Reset)"):
            import os
            if os.path.exists("analytics.db"):
                os.remove("analytics.db")
            db.init_db()
            st.sidebar.success("Database cleared successfully!")
            st.rerun()

    # Dashboard Banner
    st.markdown("<div class='title-text'>Link Shield</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle-text'>Transform long URLs into short links with enterprise-grade analytics tracking.</div>", unsafe_allow_html=True)

    # --- TAB 1: SHORTEN A LINK ---
    if menu == "Shorten a Link":
        st.markdown("### ⚡ Shorten a URL")
        
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            
            long_url_input = st.text_input("Enter your long URL here:", placeholder="https://example.com/some/very/long/path/to/resource")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                custom_alias_input = st.text_input("Custom alias (Optional):", placeholder="promo2026", help="Only alphanumeric, hyphens, and underscores allowed.")
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                shorten_btn = st.button("Shorten URL", use_container_width=True)
                
            st.markdown('</div>', unsafe_allow_html=True)
            
        if shorten_btn:
            if not long_url_input:
                st.error("Please enter a valid URL.")
            else:
                try:
                    custom_code = custom_alias_input.strip() if custom_alias_input.strip() else None
                    short_code = db.shorten_url(long_url_input, custom_code)
                    
                    full_short_url = f"{base_url}/?s={short_code}"
                    
                    st.success("🎉 Short link generated successfully!")
                    
                    # Result Display Panel
                    st.markdown(f"""
                        <div class="result-card">
                            <h4 style="margin: 0 0 10px 0; color: white;">Your Short URL:</h4>
                            <div style="display: flex; align-items: center; background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; border: 1px rgba(255,255,255,0.05) solid;">
                                <code style="font-size: 1.1rem; color: #F27121; flex-grow: 1; word-break: break-all;">{full_short_url}</code>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Display QR Code & Details
                    col_qr, col_details = st.columns([1, 2])
                    with col_qr:
                        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={full_short_url}"
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.image(qr_url, caption="Scan QR Code", width=150)
                    with col_details:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(f"**Original Destination:**\n`{long_url_input}`")
                        st.markdown(f"**Short Code:** `{short_code}`")
                        st.markdown(f"**Preview Clicks Page:** [Open Link]({full_short_url})")
                        
                except ValueError as ve:
                    st.error(str(ve))
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

    # --- TAB 2: ANALYTICS DASHBOARD ---
    elif menu == "Analytics Dashboard":
        # Load fresh analytics data
        links_df = db.get_all_links()
        
        if links_df.empty:
            st.warning("No shortened links found in database. Create one in the 'Shorten a Link' tab first!")
        else:
            # Let the user filter by a specific link or select overall
            link_options = ["Overall Analytics"] + [f"{row['short_code']} ({row['long_url'][:35]}...)" for _, row in links_df.iterrows()]
            selected_option = st.selectbox("Select a Link to Analyze:", link_options)
            
            selected_code = None
            if selected_option != "Overall Analytics":
                selected_code = selected_option.split(" ")[0]
                
            # Query analytics data
            analytics = db.get_analytics(selected_code)
            
            # 1. Dashboard Metrics Banner
            col1, col2, col3, col4 = st.columns(4)
            
            if not selected_code:
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Total Links</div>
                            <div class="metric-value">{analytics['total_links']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                        <div class="metric-card" style="border-left-color: #8A2387;">
                            <div class="metric-label">Total Clicks</div>
                            <div class="metric-value">{analytics['total_clicks']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col3:
                    # Find the link with the most clicks
                    most_popular = "N/A"
                    max_clicks = 0
                    if not links_df.empty and links_df['clicks'].max() > 0:
                        top_link = links_df.sort_values(by="clicks", ascending=False).iloc[0]
                        most_popular = f"/{top_link['short_code']}"
                        max_clicks = top_link['clicks']
                    st.markdown(f"""
                        <div class="metric-card" style="border-left-color: #F27121;">
                            <div class="metric-label">Top Link ({most_popular})</div>
                            <div class="metric-value">{max_clicks} <span style="font-size: 1rem; color: #a0aec0;">clicks</span></div>
                        </div>
                    """, unsafe_allow_html=True)
                with col4:
                    st.markdown(f"""
                        <div class="metric-card" style="border-left-color: #10B981;">
                            <div class="metric-label">Unique Countries</div>
                            <div class="metric-value">{analytics['unique_countries']}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                # Single link metrics
                link_row = links_df[links_df["short_code"] == selected_code].iloc[0]
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Clicks</div>
                            <div class="metric-value">{analytics['total_clicks']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                        <div class="metric-card" style="border-left-color: #8A2387;">
                            <div class="metric-label">Unique Countries</div>
                            <div class="metric-value">{analytics['unique_countries']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                        <div class="metric-card" style="border-left-color: #F27121;">
                            <div class="metric-label">Short Code</div>
                            <div class="metric-value" style="font-size: 1.5rem; line-height: 2.2rem; padding: 4px 0;">/{selected_code}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col4:
                    created_date = pd.to_datetime(link_row['created_at']).strftime("%Y-%m-%d")
                    st.markdown(f"""
                        <div class="metric-card" style="border-left-color: #10B981;">
                            <div class="metric-label">Created Date</div>
                            <div class="metric-value" style="font-size: 1.5rem; line-height: 2.2rem; padding: 4px 0;">{created_date}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # If there are no clicks, display a placeholder
            if analytics['total_clicks'] == 0:
                st.info("This link hasn't been clicked yet! Share it to start collecting analytics data.")
            else:
                # 2. Clicks Over Time Chart
                st.markdown("### 📈 Click Trends Over Time")
                clicks_df = analytics['clicks_df']
                if not clicks_df.empty:
                    clicks_df['click_time'] = pd.to_datetime(clicks_df['click_time'])
                    clicks_df['date'] = clicks_df['click_time'].dt.strftime('%Y-%m-%d %H:00') # group by hour
                    chart_data = clicks_df.groupby('date').size().reset_index(name='Clicks')
                    
                    # Render Altair line chart
                    line_chart = alt.Chart(chart_data).mark_area(
                        line={'color': '#E94057'},
                        color=alt.Gradient(
                            gradient='linear',
                            stops=[alt.GradientStop(color='rgba(233,64,87,0.3)', offset=0),
                                   alt.GradientStop(color='rgba(233,64,87,0.0)', offset=1)],
                            x1=1, y1=1, x2=1, y2=0
                        )
                    ).encode(
                        x=alt.X('date:T', title='Time (Hour/Day)'),
                        y=alt.Y('Clicks:Q', title='Number of Clicks'),
                        tooltip=['date:T', 'Clicks:Q']
                    ).properties(height=350).configure_axis(
                        grid=True,
                        gridColor='rgba(255,255,255,0.05)'
                    )
                    st.altair_chart(line_chart, use_container_width=True)
                
                # 3. Devices & Browsers Split (Donut & Bar charts)
                st.markdown("---")
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.markdown("#### 💻 Devices used")
                    device_df = analytics['device_df']
                    if not device_df.empty:
                        donut_chart = alt.Chart(device_df).mark_arc(innerRadius=50).encode(
                            theta=alt.Theta(field="count", type="quantitative"),
                            color=alt.Color(field="device", type="nominal", scale=alt.Scale(range=['#8A2387', '#E94057', '#F27121', '#10B981'])),
                            tooltip=['device', 'count']
                        ).properties(height=280)
                        st.altair_chart(donut_chart, use_container_width=True)
                    else:
                        st.write("No device data available")
                        
                with col_right:
                    st.markdown("#### 🌐 Browser & OS Split")
                    browser_df = analytics['browser_df']
                    os_df = analytics['os_df']
                    
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1:
                        st.markdown("**Browsers**")
                        if not browser_df.empty:
                            browser_chart = alt.Chart(browser_df).mark_bar(color='#E94057').encode(
                                x=alt.X('count:Q', title=None),
                                y=alt.Y('browser:N', sort='-x', title=None),
                                tooltip=['browser', 'count']
                            ).properties(height=200)
                            st.altair_chart(browser_chart, use_container_width=True)
                        else:
                            st.write("No browser data")
                    with sub_col2:
                        st.markdown("**OS**")
                        if not os_df.empty:
                            os_chart = alt.Chart(os_df).mark_bar(color='#F27121').encode(
                                x=alt.X('count:Q', title=None),
                                y=alt.Y('os:N', sort='-x', title=None),
                                tooltip=['os', 'count']
                            ).properties(height=200)
                            st.altair_chart(os_chart, use_container_width=True)
                        else:
                            st.write("No OS data")

                # 4. Geolocation Distribution
                st.markdown("---")
                col_geo_left, col_geo_right = st.columns(2)
                
                with col_geo_left:
                    st.markdown("#### 🌍 Top Countries")
                    country_df = analytics['country_df']
                    if not country_df.empty:
                        country_chart = alt.Chart(country_df).mark_bar(color='#8A2387').encode(
                            x=alt.X('count:Q', title='Clicks'),
                            y=alt.Y('country:N', sort='-x', title=None),
                            tooltip=['country', 'count']
                        ).properties(height=280)
                        st.altair_chart(country_chart, use_container_width=True)
                    else:
                        st.write("No country data available")
                        
                with col_geo_right:
                    st.markdown("#### 🏢 Top Cities")
                    city_df = analytics['city_df']
                    if not city_df.empty:
                        st.dataframe(
                            city_df.rename(columns={"city": "City", "country": "Country", "count": "Clicks"}),
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.write("No city data available")

                # 5. Raw Click Stream Logs
                st.markdown("---")
                st.markdown("#### 📋 Recent Click Activity (Real-time Stream)")
                
                raw_clicks_query = """
                    SELECT click_time, short_code, country, city, device, os, browser
                    FROM clicks
                """
                if selected_code:
                    raw_clicks_query += f" WHERE short_code = '{selected_code}'"
                raw_clicks_query += " ORDER BY click_time DESC LIMIT 15"
                
                conn = db.get_db_connection()
                df_logs = pd.read_sql_query(raw_clicks_query, conn)
                conn.close()
                
                if not df_logs.empty:
                    df_logs['click_time'] = pd.to_datetime(df_logs['click_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
                    st.dataframe(
                        df_logs.rename(columns={
                            "click_time": "Timestamp",
                            "short_code": "Code",
                            "country": "Country",
                            "city": "City",
                            "device": "Device",
                            "os": "Operating System",
                            "browser": "Browser"
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.write("No click logs found.")

    # --- TAB 3: LINKS MANAGER ---
    elif menu == "Links Manager":
        st.markdown("### 📋 Active Links Manager")
        
        links_df = db.get_all_links()
        
        if links_df.empty:
            st.info("No shortened links found in database. Go to 'Shorten a Link' to create one!")
        else:
            # Search / Filter
            search_query = st.text_input("Search links by short code or destination URL:", placeholder="Type to filter...")
            
            filtered_df = links_df
            if search_query:
                filtered_df = links_df[
                    links_df['short_code'].str.contains(search_query, case=False) | 
                    links_df['long_url'].str.contains(search_query, case=False)
                ]
                
            if filtered_df.empty:
                st.warning("No matches found for your search query.")
            else:
                # Render table with action buttons
                for idx, row in filtered_df.iterrows():
                    full_short = f"{base_url}/?s={row['short_code']}"
                    
                    with st.container():
                        st.markdown(f"""
                            <div class="glass-card" style="padding: 18px; margin-bottom: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                    <div style="flex-grow: 1; min-width: 250px;">
                                        <span style="font-size: 1.25rem; font-weight: 600; color: #E94057;">/{row['short_code']}</span>
                                        <span style="margin-left: 10px; padding: 2px 8px; border-radius: 4px; background: rgba(255,255,255,0.05); font-size: 0.8rem; color: #a0aec0;">
                                            {row['clicks']} clicks
                                        </span>
                                        <div style="margin-top: 5px; font-size: 0.9rem; color: #718096; word-break: break-all;">
                                            Destination: <a href="{row['long_url']}" target="_blank" style="color: #4A5568; text-decoration: none;">{row['long_url']}</a>
                                        </div>
                                    </div>
                                    <div style="margin-top: 10px; display: flex; gap: 10px; align-items: center;">
                                        <a href="{full_short}" target="_blank" style="padding: 6px 12px; background: rgba(242,113,33,0.1); border: 1px rgba(242,113,33,0.2) solid; color: #F27121; border-radius: 6px; text-decoration: none; font-size: 0.85rem; font-weight: 600;">Visit Link</a>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Add a delete button using Streamlit elements inside columns
                        c1, c2, c3 = st.columns([6, 1, 1])
                        with c2:
                            if st.button("Delete", key=f"del_{row['short_code']}", use_container_width=True):
                                db.delete_url(row['short_code'])
                                st.toast(f"Link /{row['short_code']} deleted!")
                                time.sleep(0.5)
                                st.rerun()
                        with c3:
                            if st.button("Analytics", key=f"an_{row['short_code']}", use_container_width=True):
                                st.info("Switch to 'Analytics Dashboard' tab above to view details for this link.")
