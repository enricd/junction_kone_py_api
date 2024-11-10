import folium.raster_layers
import streamlit as st
import plotly.graph_objects as go
import os
from utils import stl2mesh3d
import requests
import base64
import folium
from streamlit_folium import st_folium


st.set_page_config(layout="wide")

api_url = "http://127.0.0.1:8000"

json_plan = {
    "outer_walls": [(0, 0), (10, 0), (10, 20), (-10, 20), (-10, 10), (0, 10)],
    "inner_walls": [[(-5, 10), (-5, 20)], [(-5, 15), (10, 15)]],
    "elevator": [(5, 12), (7, 12), (7, 14), (5, 14)],
    "floor_height": 3.0,
    "floors": 4,
    "underground_floors": 3,
    "return_glb": False,
}

# validate that the api is running
response = requests.get(f"{api_url}/status")
if response.status_code != 200:
    st.sidebar.error("API is not running")
    st.stop()
else:
    st.sidebar.success("API is running")

floor_height = st.sidebar.slider("Floor height", min_value=1.0, max_value=5.0, value=json_plan["floor_height"]  , step=0.1)
floors = st.sidebar.slider("Floors", min_value=1, max_value=10, value=json_plan["floors"], step=1)
underground_floors = st.sidebar.slider("Underground floors", min_value=1, max_value=10, value=json_plan["underground_floors"], step=1)

json_plan["floor_height"] = floor_height
json_plan["floors"] = floors
json_plan["underground_floors"] = underground_floors

cols0 = st.columns(2)

with cols0[0]:

    if "location" not in st.session_state:
        st.session_state.location = [60.16175, 24.90411]

    # --- Drawing FOLIUM MAP ---
    m = folium.Map(location=st.session_state.location, zoom_start=16)
    folium.Marker(
        st.session_state.location
    ).add_to(m)
    folium.raster_layers.ImageOverlay(
        image="plan.png",
        bounds=[[60.05, 24.85], [60.25, 25.05]],
        opacity=0.5
    ).add_to(m)
    # geovertices = get_building_nodes(*st.session_state.location)["nodes"]
    # folium.Polygon(
    #     locations=[[v["lat"], v["lon"]] for v in geovertices],
    #     fill=True,
    #     fill_color="blue",
    #     fill_opacity=0.2,
    #     color="blue",
    #     weight=3,
    # ).add_to(m)    


    # call to render Folium map in Streamlit
    st_data = st_folium(m, width=700, height=400)

    if st_data:
        if st_data["last_clicked"]:
            st.session_state.location = (st_data["last_clicked"]["lat"], st_data["last_clicked"]["lng"])
            st.write(st.session_state.location)


with cols0[1]:
    if "building_3d_model" not in st.session_state:
        st.session_state.building_3d_model = None

    if st.button("Build 3D model"):
        # get the zip file from the api
        response = requests.post(f"{api_url}/build_3d_model", json=json_plan)

        if response.status_code != 200:
            error_message = response.text  # Parse the error message from JSON
            st.sidebar.error(f"API error: {error_message}")
            st.stop()
        else:
            st.sidebar.success("3D model built successfully")
            # st.sidebar.write({k: v and len(v) for k, v in response.json().items()})

        # save the file contents to files if it's not None
        if response.json()["above_file"]:
            with open("building_above.stl", "wb") as f:
                f.write(base64.b64decode(response.json()["above_file"]))
            building_above = stl2mesh3d("building_above.stl", type="above")
        else:
            building_above = None
        if response.json()["under_file"]:
            with open("building_under.stl", "wb") as f:
                f.write(base64.b64decode(response.json()["under_file"]))
            building_under = stl2mesh3d("building_under.stl", type="under")
        else:
            building_under = None
        if response.json()["elevator_file"]:
            with open("elevator.stl", "wb") as f:
                f.write(base64.b64decode(response.json()["elevator_file"]))
            elevator = stl2mesh3d("elevator.stl", type="elevator")
        else:
            elevator = None


        fig = go.Figure()
        fig.add_trace(stl2mesh3d("building_above.stl", type="above"))
        if building_under:
            fig.add_trace(building_under)
        if elevator:
            fig.add_trace(elevator)

        # adjust height
        fig.update_layout(
            width=600,
            height=500,
            scene=dict(aspectmode='data')
        )
        st.plotly_chart(fig)