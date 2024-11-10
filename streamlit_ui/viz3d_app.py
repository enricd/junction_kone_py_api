import streamlit as st
import plotly.graph_objects as go
import os
from utils import stl2mesh3d


fig = go.Figure()
fig.add_trace(stl2mesh3d("../tmp/building_above.stl", type="above"))
if os.path.exists("../tmp/building_under.stl"):
    fig.add_trace(stl2mesh3d("../tmp/building_under.stl", type="under"))
if os.path.exists("../tmp/elevator.stl"):
    fig.add_trace(stl2mesh3d("../tmp/elevator.stl", type="elevator"))

# adjust height
fig.update_layout(
    width=800,
    height=700,
    scene=dict(aspectmode='data')
)
st.plotly_chart(fig)