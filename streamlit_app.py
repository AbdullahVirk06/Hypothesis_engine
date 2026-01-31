import streamlit as st
import os
from google import genai
from google.genai import types
from groq import Groq

# --- Configuration & Styling ---
st.set_page_config(page_title="Gemini 3 + Groq: Hypothesis Engine", layout="wide")
st.title("🔬 Advanced Scientific Hypothesis Engine")
st.caption("Dual-Engine: Gemini 3 for Research | Groq for Speed")

# --- SECURE API KEYS ---
GEMINI_KEY = os.environ.get("gemini_api")
GROQ_KEY = os.environ.get("groq_api")

if not GEMINI_KEY or not GROQ_KEY:
    st.error("Please add 'gemini_api' and 'groq_api' to your Secrets.")
    st.stop()

# --- Initialize Clients ---
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = genai.Client(api_key=GEMINI_KEY)
if "groq_client" not in st.session_state:
    st.session_state.groq_client = Groq(api_key=GROQ_KEY)

SYSTEM_INSTRUCTIONS = "You are a Senior Scientific Discovery Agent. Be precise and ground claims in evidence."

# --- Sidebar: Engine Selection & Research Corpus ---
with st.sidebar:
    st.header("⚙️ Engine Settings")
    engine = st.radio("Select Primary Brain:", ["Groq (Fast/No Limits)", "Gemini 3 (Deep Search/Code)"])
    
    st.header("📚 Research Corpus")
    uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    
    if st.button("Reset Lab State"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- Initialize Messages ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Main Interaction Loop ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Enter your research objective..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if engine == "Groq (Fast/No Limits)":
            with st.spinner("Groq is thinking..."):
                chat_completion = st.session_state.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                response_text = chat_completion.choices[0].message.content
                st.markdown(response_text)
        
        else:
            with st.status("Gemini 3 Researching...", expanded=True) as status:
                try:
                    config = types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTIONS,
                        thinking_config=types.ThinkingConfig(include_thoughts=True, thinking_level=types.ThinkingLevel.LOW),
                        tools=[types.Tool(google_search=types.GoogleSearchRetrieval()), types.Tool(code_execution=types.ToolCodeExecution())]
                    )
                    # Send message using Gemini
                    response = st.session_state.gemini_client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=prompt,
                        config=config
                    )
                    
                    # Display Reasoning/Code
                    for part in response.candidates[0].content.parts:
                        if part.thought:
                            st.info(f"**Reasoning:** {part.text}")
                        if part.executable_code:
                            st.code(part.executable_code.code, language="python")
                    
                    response_text = response.text
                    st.markdown(response_text)
                    status.update(label="Research Complete", state="complete")
                except Exception as e:
                    st.error(f"Gemini Error: {e}")
                    response_text = "Error occurred."

        st.session_state.messages.append({"role": "assistant", "content": response_text})