import streamlit as st
import pickle
import folium
from folium.plugins import Geocoder
from streamlit_folium import st_folium

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
if 'location_set' not in st.session_state:
    st.session_state.location_set = False

# ---------------- COMPLAINT INPUT ----------------
complaint = st.text_area("Describe your complaint", height=100)

st.markdown("---")
st.subheader("📍 Select Location")

# ---------------- LOCATION INPUT OPTIONS ----------------
st.markdown("**Choose a method to set your location:**")

# Method 1: Manual Coordinate Input
with st.expander("🔢 Option 1: Enter Coordinates Manually"):
    col1, col2 = st.columns(2)
    with col1:
        manual_lat = st.number_input("Latitude", value=st.session_state.latitude, format="%.6f")
    with col2:
        manual_lon = st.number_input("Longitude", value=st.session_state.longitude, format="%.6f")
    
    if st.button("Set Manual Location"):
        st.session_state.latitude = manual_lat
        st.session_state.longitude = manual_lon
        st.session_state.location_set = True
        st.success(f"✅ Location set to: {manual_lat:.6f}, {manual_lon:.6f}")
        st.rerun()

# Method 2: Browser Geolocation (Instructions)
with st.expander("📍 Option 2: Browser GPS (Enable in your browser)"):
    st.info("""
    **To use browser GPS:**
    1. Your browser will ask for location permission
    2. Click on the map marker that appears at your location
    3. The coordinates will be automatically set
    
    **Note:** Make sure location services are enabled in your browser settings.
    """)

st.markdown("**Option 3: Click on Map or Search Location**")

# ---------------- MAP WITH GEOLOCATION ----------------
# Create map centered on current session state location
m = folium.Map(
    location=[st.session_state.latitude, st.session_state.longitude],
    zoom_start=13 if st.session_state.location_set else 5,
    tiles=None,
    control_scale=True
)

# Add current location marker if location was set
if st.session_state.location_set:
    folium.Marker(
        [st.session_state.latitude, st.session_state.longitude],
        popup="Selected Location",
        tooltip="Current Selection",
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

# Add geolocation button to map
from folium.plugins import LocateControl
LocateControl(auto_start=False, position='topright').add_to(m)

# Click popup
m.add_child(folium.LatLngPopup())

# Search bar
Geocoder(collapsed=False, position="topright").add_to(m)

# Layer control
folium.LayerControl(collapsed=False).add_to(m)

# Render map
map_data = st_folium(m, height=450, width=700, key="map")

# ---------------- GET COORDINATES FROM MAP ----------------
# Update coordinates based on map interaction
if map_data:
    if map_data.get("last_clicked"):
        st.session_state.latitude = map_data["last_clicked"]["lat"]
        st.session_state.longitude = map_data["last_clicked"]["lng"]
        st.session_state.location_set = True
        st.info(f"📍 Map Location: {st.session_state.latitude:.6f}, {st.session_state.longitude:.6f}")

# Display current coordinates
st.markdown(f"**📌 Current Selected Location:** `{st.session_state.latitude:.6f}, {st.session_state.longitude:.6f}`")

# Display location status
if st.session_state.location_set:
    st.success("✅ Location has been set")
else:
    st.warning("⚠️ Using default location. Please select your actual location.")

# ---------------- SUBMIT COMPLAINT ----------------
st.markdown("---")
if st.button("🚀 Submit Complaint", type="primary"):
    if len(complaint.strip()) < 5:
        st.error("⚠️ Please enter a valid complaint (minimum 5 characters)")
    elif not st.session_state.location_set:
        st.warning("⚠️ Please select your location before submitting")
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