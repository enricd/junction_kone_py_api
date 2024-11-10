import folium.raster_layers
import streamlit as st
import plotly.graph_objects as go
import os
from utils import stl2mesh3d
import requests
import base64
import folium
from streamlit_folium import st_folium
import zipfile
import json
import sys
from voice_methods import transcribe_audio_assemblyai
from openai import OpenAI
from markdown_pdf import MarkdownPdf
from datetime import datetime

st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
)

api_url = "http://127.0.0.1:8000"

tabs = st.tabs(["🏢 3D Model", "🤖 Sells Voice Assistant"])

with tabs[0]:
    if os.path.exists("../tmp/building_above.stl"):
        building_above = stl2mesh3d("../tmp/building_above.stl", type="above")
    else:
        building_above = None
    if os.path.exists("../tmp/building_under.stl"):
        building_under = stl2mesh3d("../tmp/building_under.stl", type="under")
    else:
        building_under = None
    if os.path.exists("../tmp/elevator.stl"):
        elevator = stl2mesh3d("../tmp/elevator.stl", type="elevator")
    else:
        elevator = None


    fig = go.Figure()
    if building_above:
        fig.add_trace(building_above)
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

    cols0 = st.columns(2)

    with cols0[0]:
        # download the json plan
        if os.path.exists("../tmp/plan.json"):
            st.download_button(label="📄 Building Plan", data=open("../tmp/plan.json", "rb").read(), file_name="building_plan.json", use_container_width=True)

        # for each file, if it exists, open it and download it to the client
        if building_above:
            st.download_button(label="📄 Building Above", data=open("../tmp/building_above.stl", "rb").read(), file_name="building_above.stl", use_container_width=True)

    with cols0[1]:
        if building_under:
            st.download_button(label="📄 Building Under", data=open("../tmp/building_under.stl", "rb").read(), file_name="building_under.stl", use_container_width=True)
        if elevator:
            st.download_button(label="📄 Elevator", data=open("../tmp/elevator.stl", "rb").read(), file_name="elevator.stl", use_container_width=True)


with tabs[1]:

    transcribe_audio = transcribe_audio_assemblyai

    FILE_URL = "https://github.com/AssemblyAI-Examples/audio-examples/raw/main/20230607_me_canadian_wildfires.mp3"
    FILE_URL = None
    DEMO_TRANSCRIPT_PATH = "../tmp/sales_transcript_example.txt"

    client = OpenAI()

    audio_value = st.audio_input("Record a voice message")
    transcript = None

    if audio_value:
        st.audio(audio_value)

        # save the audio to a file
        with open("audio.mp3", "wb") as f:
            f.write(audio_value.getvalue())

        # transcribe the audio
        transcript = transcribe_audio(file_path="audio.mp3")

        # write a streamlit chat from the transcript
        for utterance in transcript or []:
            st.chat_message(utterance.speaker).markdown(utterance.text)

    if FILE_URL:
        transcript = transcribe_audio(file_url=FILE_URL)

        # write a streamlit chat from the transcript
        for utterance in transcript or []:
            st.chat_message(utterance.speaker).markdown(utterance.text)

    if DEMO_TRANSCRIPT_PATH:
        transcript = open(DEMO_TRANSCRIPT_PATH, "r").read()

        # transform the transcript string into a list of utterances
        transcript = [{"speaker":line.split(":")[0], "text":line.split(":")[1]} for line in transcript.split("\n") if ":" in line]

        # write a streamlit chat from the transcript
        for utterance in transcript or []:
            st.chat_message(utterance["speaker"][-1]).markdown(utterance["text"])

    if transcript:
        instructions = """
        You are a helpful assistant from the KONE elevators company expert in selling elevators.
        You are given a transcript of a conversation with a customer.
        Your task is to answer the customer's questions and help them choose the best elevator for their needs.
        """

        # join the transcript into a single string with newlines and speaker labels in the format "Speaker X: <utterance>"
        if isinstance(transcript[0], dict):
            transcript_text = "\n".join([f"Speaker {utterance['speaker']}: {utterance['text']}" for utterance in transcript])
        else:
            transcript_text = "\n".join([f"Speaker {utterance.speaker}: {utterance.text}" for utterance in transcript])

        if DEMO_TRANSCRIPT_PATH:
            response = """
Hello John! It's great to hear you're considering adding an elevator to your building. Here’s a summary of what we discussed and the next steps:

Building Details: You have a four-story building from the 1920s with both residential and commercial tenants, and you're looking for a solution that fits within limited space while preserving the building's aesthetic.

Elevator Options: We offer compact elevator models that are designed for tight spaces and can be customized to blend with your building's architecture. Additionally, our elevators are energy-efficient, which can help reduce your operating costs.

Installation Process: Typically, our installations are completed within a few months, and we make a concerted effort to minimize disruption to your tenants. We coordinate closely with your management to ensure a smooth process.

Maintenance and Support: Our after-sales support includes comprehensive maintenance packages, 24/7 emergency availability, and regular check-ups for optimal performance.

Cost Estimation: I will prepare a detailed proposal with cost estimates, and we offer financing options to make the investment manageable.

As discussed, I'll arrange for one of our specialists to assess your building this week. This will help us provide a more accurate quote and finalize the project details.

If you have any further questions or specific requirements before the site visit, feel free to reach out. Looking forward to working with you!
"""
        else:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": transcript_text},
                ],
            )
            response = response.choices[0].message.content

        st.chat_message("assistant").markdown(response)

        # Create a pdf from the response
        pdf = MarkdownPdf(toc_level=2)
        from markdown_pdf import Section

        pdf.add_section(Section(f"# Sells Conversation Recommendation - Date: {datetime.now().strftime('%Y-%m-%d')}", toc=False))
        pdf.add_section(Section(response))
        pdf.save("guide.pdf")

        # download the response as a pdf
        st.download_button(label="📄 Download Recommendation", data=open("guide.pdf", "rb").read(), file_name="sells_recommendation.pdf", use_container_width=True)
