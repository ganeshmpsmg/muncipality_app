import streamlit as st
import pickle
import spacy
import folium
from folium.plugins import Geocoder, LocateControl
from streamlit_folium import st_folium

# ---------------- LOAD MODELS ----------------
try:
    with open("model.pkl", "rb") as mf:
        
        model = pickle.load(mf)
    with open("vectorizer.pkl", "rb") as vf:
        vectorizer = pickle.load(vf)
except FileNotFoundError:
    st.error("Required files `model.pkl` or `vectorizer.pkl` not found in project root.")
    st.info("Place the files next to `app.py` or run `python train_model.py` to generate them.")
    st.stop()

# NLP
nlp = spacy.load("en_core_web_sm")

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Smart Municipality Complaint", layout="centered")
st.title("🚰 Smart Municipality Complaint System")

# ---------------- COMPLAINT INPUT ----------------
complaint = st.text_area("Describe your complaint")

# ---------------- MAP ----------------
# Default marker location (India center)
default_marker = [20.5937, 78.9629]

# Initialize map
m = folium.Map(location=default_marker, zoom_start=5, tiles=None, control_scale=True)

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

# GPS locate
LocateControl(auto_start=False, position="topleft", flyTo=True).add_to(m)

# Layer control
folium.LayerControl(collapsed=False).add_to(m)

# Render map
map_data = st_folium(m, height=450, width=700)

# ---------------- GET COORDINATES ----------------
# Start with default
lat, lng = default_marker

# Update if user clicked
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lng = map_data["last_clicked"]["lng"]
# Update if GPS or search changed center
elif map_data and map_data.get("center"):
    lat = map_data["center"]["lat"]
    lng = map_data["center"]["lng"]

# ---------------- SUBMIT COMPLAINT ----------------
if st.button("Submit Complaint"):
    if len(complaint.strip()) < 5:
        st.error("Please enter a valid complaint")
    elif lat is None or lng is None:
        st.error("Please select a location on the map")
    else:
        # ML Prediction
        vec = vectorizer.transform([complaint])
        prediction = model.predict(vec)[0]

        # Output
        st.success("Complaint Registered Successfully")
        st.json({
            "complaint_text": complaint,
            "latitude": lat,
            "longitude": lng,
            "category": "Water Issue" if prediction == 1 else "Other Issue"
        })
