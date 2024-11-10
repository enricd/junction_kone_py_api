# Junction Hackathon 2024 - KONE's Challenge

# Backend Python 3D Model and Sells Conversation AI Assistant

Main Technologies:
- Python
- FastAPI
- Streamlit


## Serve the FastAPI API:

![alt text](image-2.png)

```bash
cd api
uvicorn app:app --reload
```

## Serve the Streamlit UI (developed to be embedded in the main Frontend app as an iframe):

![alt text](image-1.png)

```bash
cd streamlit_ui
streamlit run viz3d_server.py
```

## Serve the Dev Streamlit UI:

![alt text](image.png)

```bash
cd streamlit_ui
streamlit run viz3d_client.py
```
