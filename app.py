import os
import requests
import streamlit as st
from google import genai

# Configuración de la página pública
st.set_page_config(page_title="Asistente Virtual", page_icon="💬")
st.title("Asistente de Consultas")
st.caption("Respuestas basadas exclusivamente en nuestra documentación oficial.")

# 1. ID de tu documento de Google Drive (Reemplaza el texto entre comillas)
GOOGLE_DOC_ID = "1hrZLnqVqmsUz0n0FwKCrDJ7XQOILrO42"


# Función para leer el Google Doc en tiempo real
@st.cache_data(ttl=60)  # Se actualiza cada 60 segundos si editas el Drive
def cargar_datos_drive(doc_id):
  url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
  respuesta = requests.get(url)
  if respuesta.status_code == 200:
    return respuesta.text
  return ""


base_conocimiento = cargar_datos_drive(GOOGLE_DOC_ID)

# 2. Conexión oculta y segura con tu API Key (se configurará en el Paso 4)
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
  st.error("Falta configurar la clave del sistema.")
  st.stop()

client = genai.Client(api_key=api_key)

# Historial de conversación
if "messages" not in st.session_state:
  st.session_state.messages = []

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# Caja de chat para el usuario público
if prompt := st.chat_input("Escribe tu consulta aquí..."):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  # Regla estricta de comportamiento
  instrucciones_sistema = f"""
    Eres un asistente virtual estricto. Tu única fuente de conocimiento es el siguiente texto extraído de Google Drive:
    ---
    {base_conocimiento}
    ---
    REGLAS OBLIGATORIAS:
    1. Responde ÚNICAMENTE utilizando la información proporcionada arriba.
    2. Si el usuario hace una pregunta cuya respuesta NO está en el texto de arriba, responde exactamente: "Lo siento, solo estoy autorizado para responder consultas específicas sobre nuestra información oficial y no tengo datos sobre ese tema."
    3. No inventes, no supongas y no uses conocimientos externos bajo ninguna circunstancia.
    """

  with st.chat_message("assistant"):
    with st.spinner("Consultando..."):
      try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[instrucciones_sistema, f"Pregunta del usuario: {prompt}"],
        )
        bot_respuesta = response.text
      except Exception:
        bot_respuesta = (
            "En este momento hay mucha demanda. Por favor intenta de nuevo en"
            " unos segundos."
        )

      st.markdown(bot_respuesta)
      st.session_state.messages.append(
          {"role": "assistant", "content": bot_respuesta}
      )
