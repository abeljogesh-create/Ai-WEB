# Lumnivox.py
# AI assistant with persistent memory, clean Gemini output, news & weather, no visible history

import streamlit as st
import google.generativeai as genai
from streamlit_option_menu import option_menu
import requests
import os

# ---------------- KEYS ---------------- #
genai.configure(api_key="AIzaSyDq-Me3iQZ5Con9rYp3U_yDfZgoOPQfKr0")
OPENWEATHER_API_KEY = "84a22496c83f97c24dd288263ba09f2e"
NEWS_API_KEY = "pub_4924bcaf4a5a4f598f080ac1e57d2e93"

# ---------------- STREAMLIT SETUP ---------------- #
st.set_page_config(
    page_title="Lumnivox AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- CSS THEME ---------------- #
st.markdown("""
<style>
body {background-color: #121212; color: #e0e0e0; font-family: Arial, sans-serif;}
.stTextInput>div>div>input {background-color: #2c2c2c; color:#e0e0e0; border-radius:8px; padding:10px;}
.stButton>button {background-color:#4b6cb7; color:white; border-radius:8px; padding:10px; font-weight:bold; transition:0.2s;}
.stButton>button:hover {background-color:#3a5c96; transform: translateY(-2px);}
div.chat-bubble {background-color:#2c2c2c; padding:15px; border-radius:12px; margin-top:10px; color:#e0e0e0; font-size:1.2rem;}
</style>
""", unsafe_allow_html=True)

# ---------------- MEMORY ---------------- #
MEMORY_FILE = "memory.txt"
if "memory" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.memory = f.read().splitlines()
    else:
        st.session_state.memory = []

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as F:
        F.write("\n".join(st.session_state.memory))

# ---------------- WEATHER ---------------- #
def get_weather(city="Khor Fakkan", country="AE"):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("cod") == 200:
            weather_desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            return f"{weather_desc} with around {temp}°C in {city}."
        else:
            return "I couldn't fetch the weather at the moment."
    except Exception as e:
        return f"Weather error: {e}"

# ---------------- NEWS ---------------- #
def get_news(query="general", country="ae", language="en", page=1):
    try:
        url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&q={query}&country={country}&language={language}&page={page}"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("status") == "success" and "results" in data:
            articles = data["results"][:5]
            news_text = ""
            for article in articles:
                title = article.get("title", "No Title")
                link = article.get("link", "")
                news_text += f"{title} (Read more: {link})\n"
            return news_text.strip()
        else:
            return "News unavailable now."
    except Exception as e:
        return f"News error: {e}"

# ---------------- GEMINI CLEAN TEXT ---------------- #
def extract_gemini_text(response):
    """Safely extract clean text from Gemini API response"""
    try:
        if hasattr(response, "candidates") and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                return "".join([getattr(part, "text", "") for part in candidate.content.parts]).strip()
            elif hasattr(candidate, "content"):
                return str(candidate.content).strip()
        return getattr(response, "text", "Sorry, I got no response.").strip()
    except Exception:
        return "Sorry, I got no response."

# ---------------- GEMINI CHAT ---------------- #
def chat_with_gemini(prompt):
    try:
        lower_prompt = prompt.lower()
        external_info = ""
        if "weather" in lower_prompt:
            external_info = get_weather()
        elif "news" in lower_prompt:
            external_info = get_news()

        memory_text = "\n".join(st.session_state.memory[-50:])
        full_prompt = f"{memory_text}\nUser: {prompt}\n"
        if external_info:
            full_prompt += f"Use this info in your reply: {external_info}\n"
        full_prompt += "AI:"

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(full_prompt)
        answer_text = extract_gemini_text(response)

        # Save memory
        st.session_state.memory.append(f"User: {prompt}")
        st.session_state.memory.append(f"AI: {answer_text}")
        save_memory()

        return answer_text

    except Exception as e:
        st.error(f"Error: {e}")
        return "Sorry, I couldn't get a response."

# ---------------- UI ---------------- #
st.markdown('<h1 style="color:#4b6cb7; text-align:center;">🤖 Lumnivox AI 🤖</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#c0c0c0;">Your AI assistant — ask anything below!</p>', unsafe_allow_html=True)

with st.sidebar:
    selected = option_menu(
        "🎛️ Lumnivox Menu 🎛️",
        ["💬 Chat"],
        icons=["chat-dots-fill"],
        menu_icon="robot",
        default_index=0,
        styles={
            "container": {"background-color": "#121212"},
            "nav-link": {"font-size": "1rem", "color": "#e0e0e0"},
            "nav-link-selected": {"background-color": "#4b6cb7", "color": "white"},
        }
    )

user_input = st.text_input("📝 Type your message:", key="text_input")

if user_input:
    answer = chat_with_gemini(user_input)
    st.markdown(f'<div class="chat-bubble">💬 <strong>Lumnivox:</strong> {answer}</div>', unsafe_allow_html=True)