from flask import Flask, request, jsonify
import sqlite3
import requests
import user_agents
import datetime

app = Flask(__name__)

# Engedélyezett CORS beállítások (hogy a weboldalad tudjon adatot küldeni ide)
from flask_cors import CORS
CORS(app)

# Adatbázis inicializálása
def init_db():
    conn = sqlite3.connect("visitors.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            country TEXT,
            city TEXT,
            latitude REAL,
            longitude REAL,
            user_agent TEXT,
            device_type TEXT,
            os TEXT,
            browser TEXT,
            gender TEXT,
            age_range TEXT,
            visit_time TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# IP alapján földrajzi hely meghatározása (MaxMind vagy ipinfo.io API használatával)
def get_geo_info(ip):
    try:
        response = requests.get(f"http://ipinfo.io/{ip}/json")
        data = response.json()
        loc = data.get("loc", "0,0").split(",")  # Lat, Lon
        return {
            "country": data.get("country", "Unknown"),
            "city": data.get("city", "Unknown"),
            "latitude": float(loc[0]),
            "longitude": float(loc[1])
        }
    except:
        return {"country": "Unknown", "city": "Unknown", "latitude": 0, "longitude": 0}

# Felhasználó eszközének elemzése
def get_device_info(user_agent_string):
    ua = user_agents.parse(user_agent_string)
    return {
        "device_type": "Mobile" if ua.is_mobile else "PC",
        "os": ua.os.family,
        "browser": ua.browser.family
    }

@app.route('/track', methods=['POST'])
def track_visitor():
    user_ip = request.remote_addr  # Látogató IP-címe
    user_agent = request.headers.get("User-Agent", "")
    visit_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    geo_info = get_geo_info(user_ip)
    device_info = get_device_info(user_agent)

    # Egyszerű példa a nem és kor meghatározására egy későbbi AI modell helyett
    gender = "Unknown"
    age_range = "Unknown"

    conn = sqlite3.connect("visitors.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO visitors (ip, country, city, latitude, longitude, user_agent, device_type, os, browser, gender, age_range, visit_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_ip, geo_info["country"], geo_info["city"], geo_info["latitude"], geo_info["longitude"],
          user_agent, device_info["device_type"], device_info["os"], device_info["browser"], gender, age_range, visit_time))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "message": "Visitor tracked"}), 200


@app.route('/get_visitors', methods=['GET'])
def get_visitors():
    conn = sqlite3.connect("visitors.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM visitors")
    data = cursor.fetchall()
    conn.close()
    
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

