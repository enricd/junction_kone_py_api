import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_drawable_canvas import st_canvas
import pandas as pd
from PIL import Image
from get_building_shape import get_building_nodes
import plotly.graph_objects as go
import os

from utils import (
    building_shape_to_meters, 
    create_3d_building,
    stl2mesh3d,
    plan2img,
)


st.set_page_config(
    page_title="Prototype",
    page_icon="🚠",
    layout="wide",
    initial_sidebar_state="expanded",
)

cols0 = st.columns(2)

if "location" not in st.session_state:
    st.session_state.location = [60.16175, 24.90411]

geovertices = get_building_nodes(*st.session_state.location)["nodes"]
rel_geovertices = building_shape_to_meters(geovertices)
st.write(rel_geovertices)
plan2img(rel_geovertices)

# st.write([[v["lat"], v["lon"]] for v in geovertices])

with cols0[0]:
    # --- Drawing FOLIUM MAP ---
    m = folium.Map(location=[60.16175, 24.90411], zoom_start=16)
    folium.Marker(
        st.session_state.location
    ).add_to(m)
    geovertices = get_building_nodes(*st.session_state.location)["nodes"]
    folium.Polygon(
        locations=[[v["lat"], v["lon"]] for v in geovertices],
        fill=True,
        fill_color="blue",
        fill_opacity=0.2,
        color="blue",
        weight=3,
    ).add_to(m)
    if st.button("Refresh"):
        st.rerun()

    # call to render Folium map in Streamlit
    st_data = st_folium(m, width=700, height=400)

    if st_data:
        if st_data["last_clicked"]:
            st.session_state.location = (st_data["last_clicked"]["lat"], st_data["last_clicked"]["lng"])
            st.write(st.session_state.location)


    # --- Drawing CANVAS ---
    # Specify canvas parameters in application
    rel_geovertices = building_shape_to_meters(geovertices)
    drawing_mode = st.selectbox(
        "Drawing tool:", ("line", "rect", "transform")
    )

    bg_image = "plan.png"

    # Create a canvas component
    canvas_result = st_canvas(
        drawing_mode=drawing_mode,
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=3,
        stroke_color="black",
        background_color="#eee",
        background_image=Image.open(bg_image) if bg_image else None,
        update_streamlit=True,
        height=400,
        key="canvas",
        width=400,
    )

    json_plan = {
        "outer_walls": rel_geovertices,
        "inner_walls": [],
        "elevators": [],
    }

# Do something interesting with the image data and paths
if canvas_result.json_data is not None:
    objects = pd.json_normalize(canvas_result.json_data["objects"]) # need to convert obj to str because PyArrow
    for col in objects.select_dtypes(include=['object']).columns:
        objects[col] = objects[col].astype("str")
    st.dataframe(objects)

    cols = ["type", "left", "top", "width", "height", "x1", "y1", "x2", "y2"]
    if len(objects) > 0 and all([col in objects.columns for col in cols]):
        
        st.dataframe(objects[cols])

        for object in objects.iterrows():
            if object[1]["type"] == "line":
                l, t, w, h = map(float, object[1][["left", "top", "width", "height"]])
                _x1, _y1, _x2, _y2 = map(float, object[1][["x1", "y1", "x2", "y2"]])
                x1 = l if _x1 < 0 else l + w
                y1 = t if _y1 < 0 else t + h
                x2 = l if _x2 < 0 else l + w
                y2 = t if _y2 < 0 else t + h
                json_plan["inner_walls"].append(((x1, y1), (x2, y2)))
            elif object[1]["type"] == "rect":
                pass
        
        # st.write(plan_building_rel)


with cols0[1]:

    cols1 = st.columns(3)
    with cols1[0]:
        st.number_input("Wall height", value=3.0, step=0.1, key="floor_height")
    with cols1[1]:
        st.number_input("Floors", value=2, step=1, key="floors")
    with cols1[2]:
        st.number_input("Underground floors", value=1, step=1, key="underground_floors")

    create_3d_building(
        json_plan, 
        st.session_state.floor_height, 
        st.session_state.floors, 
        st.session_state.underground_floors,
    )
    
    fig = go.Figure()
    fig.add_trace(stl2mesh3d("building_above.stl", type="above"))
    if os.path.exists("building_under.stl"):
        fig.add_trace(stl2mesh3d("building_under.stl", type="under"))

    # adjust height
    fig.update_layout(
        height=550,
        scene = dict(aspectmode='data')
    )
    st.plotly_chart(fig)