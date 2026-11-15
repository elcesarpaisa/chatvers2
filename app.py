import requests
import streamlit as st

# Configuración de la página pública
st.set_page_config(page_title="Asistente Virtual", page_icon="💬")
st.title("Asistente de Consultas")
st.caption("Respuestas basadas exclusivamente en nuestra documentación oficial.")

# 1. ID de tu documento de Google Drive
GOOGLE_DOC_ID = "AQ.Ab8RN6K-PePxEGemVWLXQEd2QjiJcdwy4gas-Dm9Nnentd9x9g"


# Función para leer el Google Doc en tiempo real
@st.cache_data(ttl=60)
def cargar_datos_drive(doc_id):
  url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
  respuesta = requests.get(url)
  if respuesta.status_code == 200:
    return respuesta.text
  return ""


base_conocimiento = cargar_datos_drive(GOOGLE_DOC_ID)

# 2. Conexión segura con tu API Key desde los secretos de Streamlit
api_key = st.secrets.get("AQ.Ab8RN6K-PePxEGemVWLXQEd2QjiJcdwy4gas-Dm9Nnentd9x9g", "")

if not api_key:
  st.error("Falta configurar la clave del sistema en los secretos.")
  st.stop()

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
    
    Pregunta del usuario: {prompt}
    """

  with st.chat_message("assistant"):
    with st.spinner("Consultando..."):
      try:
        # Llamada directa a la API de Gemini mediante solicitudes HTTP estándar
        url_api = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": instrucciones_sistema}]}]}

        response = requests.post(url_api, json=payload, headers=headers)

        if response.status_code == 200:
          data = response.json()
          bot_respuesta = (
              data.get("candidates", [{}])[0]
              .get("content", {})
              .get("parts", [{}])[0]
              .get("text", "No se obtuvo respuesta.")
          )
        else:
          bot_respuesta = (
              f"Error de conexión con la IA (Código {response.status_code})"
          )
      except Exception as e:
        bot_respuesta = f"Ocurrió un error al procesar la respuesta: {e}"

      st.markdown(bot_respuesta)
      st.session_state.messages.append(
          {"role": "assistant", "content": bot_respuesta}
      )
