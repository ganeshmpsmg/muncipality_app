import streamlit as st
import pickle
import folium
from folium.plugins import Geocoder
from streamlit_folium import st_folium
import streamlit.components.v1 as components

# ---------------- LOAD MODELS ----------------
try:
    with open("model.pkl", "rb") as mf:
        model = pickle.load(mf)
    with open("vectorizer.pkl", "rb") as vf:
        vectorizer = pickle.load(vf)
except FileNotFoundError:
    st.error("Required files `model.pkl` or `vectorizer.pkl` not found.")
    st.info("Run `python train_model.py` to generate them.")
    st.stop()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Smart Municipality Complaint", layout="centered")
st.title("🚰 Smart Municipality Complaint System")

# ---------------- SESSION STATE INITIALIZATION ----------------
if 'latitude' not in st.session_state:
    st.session_state.latitude = 20.5937  # India center
if 'longitude' not in st.session_state:
    st.session_state.longitude = 78.9629
if 'gps_clicked' not in st.session_state:
    st.session_state.gps_clicked = False

# ---------------- BROWSER GPS COMPONENT ----------------
def get_browser_location():
    """JavaScript component to get browser GPS location"""
    html_code = """
    <script>
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(showPosition, showError);
            document.getElementById("status").innerHTML = "Getting location...";
        } else {
            document.getElementById("status").innerHTML = "Geolocation is not supported by this browser.";
        }
    }
    
    function showPosition(position) {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        
        // Send data to Streamlit
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: {lat: lat, lng: lng}
        }, '*');
        
        document.getElementById("status").innerHTML = 
            "✅ Location found: " + lat.toFixed(6) + ", " + lng.toFixed(6);
    }
    
    function showError(error) {
        let errorMsg = "";
        switch(error.code) {
            case error.PERMISSION_DENIED:
                errorMsg = "❌ User denied location permission";
                break;
            case error.POSITION_UNAVAILABLE:
                errorMsg = "❌ Location information unavailable";
                break;
            case error.TIMEOUT:
                errorMsg = "❌ Request timed out";
                break;
            case error.UNKNOWN_ERROR:
                errorMsg = "❌ Unknown error occurred";
                break;
        }
        document.getElementById("status").innerHTML = errorMsg;
    }
    </script>
    
    <button onclick="getLocation()" style="
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
        margin-bottom: 10px;
    ">📍 Use My Current Location (GPS)</button>
    <p id="status" style="font-size: 14px; color: #666;"></p>
    """
    return components.html(html_code, height=100)

# ---------------- COMPLAINT INPUT ----------------
complaint = st.text_area("Describe your complaint", height=100)

st.markdown("---")
st.subheader("📍 Select Location")

# GPS Button with JavaScript
st.markdown("**Option 1: Use GPS**")
location_data = get_browser_location()

# Update session state if GPS data received
if location_data and isinstance(location_data, dict):
    if 'lat' in location_data and 'lng' in location_data:
        st.session_state.latitude = location_data['lat']
        st.session_state.longitude = location_data['lng']
        st.session_state.gps_clicked = True
        st.success(f"GPS Location: {st.session_state.latitude:.6f}, {st.session_state.longitude:.6f}")

st.markdown("**Option 2: Click on Map or Search Location**")

# ---------------- MAP ----------------
# Create map centered on current session state location
m = folium.Map(
    location=[st.session_state.latitude, st.session_state.longitude],
    zoom_start=13 if st.session_state.gps_clicked else 5,
    tiles=None,
    control_scale=True
)

# Add current location marker if GPS was used
if st.session_state.gps_clicked:
    folium.Marker(
        [st.session_state.latitude, st.session_state.longitude],
        popup="Your Current Location",
        tooltip="Current Location",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

# Base maps
folium.TileLayer(
    tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    name="Street",
    attr="OpenStreetMap",
    control=True
).add_to(m)

folium.TileLayer(
    tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    name="Terrain",
    attr="OpenTopoMap (CC-BY-SA)",
    control=True
).add_to(m)

folium.TileLayer(
    tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    name="Dark",
    attr="CartoDB",
    control=True
).add_to(m)

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    name="Satellite",
    attr="Esri",
    control=True
).add_to(m)

# Click popup
m.add_child(folium.LatLngPopup())

# Search bar
Geocoder(collapsed=False, position="topright").add_to(m)

# Layer control
folium.LayerControl(collapsed=False).add_to(m)

# Render map
map_data = st_folium(m, height=450, width=700, key="map")

# ---------------- GET COORDINATES ----------------
# Update coordinates based on map interaction
if map_data and map_data.get("last_clicked"):
    st.session_state.latitude = map_data["last_clicked"]["lat"]
    st.session_state.longitude = map_data["last_clicked"]["lng"]
    st.info(f"Map Location: {st.session_state.latitude:.6f}, {st.session_state.longitude:.6f}")
elif map_data and map_data.get("center") and not st.session_state.gps_clicked:
    # Only update from center if GPS wasn't clicked (for search functionality)
    st.session_state.latitude = map_data["center"]["lat"]
    st.session_state.longitude = map_data["center"]["lng"]

# Display current coordinates
st.markdown(f"**Current Selected Location:** `{st.session_state.latitude:.6f}, {st.session_state.longitude:.6f}`")

# ---------------- SUBMIT COMPLAINT ----------------
st.markdown("---")
if st.button("🚀 Submit Complaint", type="primary"):
    if len(complaint.strip()) < 5:
        st.error("⚠️ Please enter a valid complaint (minimum 5 characters)")
    else:
        # ML Prediction
        vec = vectorizer.transform([complaint])
        prediction = model.predict(vec)[0]

        # Output
        st.success("✅ Complaint Registered Successfully!")
        
        result = {
            "complaint_text": complaint,
            "latitude": st.session_state.latitude,
            "longitude": st.session_state.longitude,
            "category": "Water Issue" if prediction == 1 else "Other Issue"
        }
        
        st.json(result)
        
        # Show on map
        st.markdown("### 📍 Complaint Location on Map")
        confirmation_map = folium.Map(
            location=[st.session_state.latitude, st.session_state.longitude],
            zoom_start=15
        )
        folium.Marker(
            [st.session_state.latitude, st.session_state.longitude],
            popup=f"Category: {result['category']}<br>Location: {st.session_state.latitude:.6f}, {st.session_state.longitude:.6f}",
            tooltip=result['category'],
            icon=folium.Icon(color='blue', icon='tint' if prediction == 1 else 'exclamation-sign')
        ).add_to(confirmation_map)
        st_folium(confirmation_map, height=300, width=700)
