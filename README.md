# Darun Tourism Itinerary App

A Streamlit app for generating editable Andaman travel itineraries with a Google AI Studio Gemini API key.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
streamlit run app.py
```

Add your free Google AI Studio API key in the sidebar, or set it before running:

```powershell
$env:GEMINI_API_KEY="your-google-ai-studio-key"
streamlit run app.py
```

The generated itinerary can be edited inside the app and downloaded as a text file.
