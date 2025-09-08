import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import time

# --- 1. PERFORMANCE IMPROVEMENT: Caching ---
# By caching the results, Streamlit won't re-run the expensive API calls
# every time the user interacts with the app. The cache is cleared only
# when the input arguments (api_key, search_term) change.
@st.cache_data
def search_youtube_content(api_key, search_term):
    """
    Searches YouTube for videos and their comments containing questions.
    Returns a list of dictionaries with video data.
    """
    youtube = build("youtube", "v3", developerKey=api_key)
    # Search for videos
    search_request = youtube.search().list(
        part="snippet",
        maxResults=10,
        q=search_term,
        type="video"
    )
    search_response = search_request.execute()
    processed_data = []

    if "items" in search_response:
        for item in search_response["items"]:
            try:
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                thumbnail = snippet["thumbnails"]["high"]["url"]
                title = snippet["title"]

                # Get comments for the video
                comments_request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=40,
                    order="relevance"
                )
                comments_response = comments_request.execute()

                # Filter for comments that are questions
                comments = [
                    comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    for comment in comments_response.get("items", [])
                    if "?" in comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                ]

                # Only include videos that have question-comments
                if comments:
                    processed_data.append({
                        "thumbnail": thumbnail,
                        "title": title,
                        "comments": comments
                    })
            except Exception:
                # Silently skip videos that cause errors
                continue
    return processed_data

# --- App Configuration ---
st.set_page_config(
    page_title="Contenido Ilimitado",
    page_icon="🎬",
    layout="wide"
)

try:
    st.logo("estudiose.png")
except FileNotFoundError:
    st.warning("Logo image 'estudiose.png' not found.")

st.title("🎬 Contenido Ilimitado")
st.markdown("Encuentra ideas de contenido analizando preguntas en los comentarios de videos de YouTube.")


# --- Sidebar for API Keys ---
with st.sidebar:
    st.header("🔑 Claves de Acceso")
    google_api_key = st.text_input("Escribe tu clave de API de Google", type="password")
    st.info("Si no sabes cómo obtener tu clave de API de Google, sigue [este enlace](https://youtu.be/jH5kknrti00).", icon="💡")

    # Secret key validation
    try:
        secret_key = st.secrets["SECRET_KEY"]
    except (FileNotFoundError, KeyError):
        st.error("SECRET_KEY not found in Streamlit secrets.")
        st.stop()
    secret_key_match = st.text_input("Escribe tu clave secreta", type="password")
    st.info("Si no tienes una clave secreta, solicítala al administrador de la comunidad.", icon="🔒")


# --- Main App Logic ---
if not google_api_key or not secret_key_match:
    st.info("Por favor, ingresa tu clave de API de Google y tu Clave Secreta en la barra lateral para empezar.")
elif secret_key != secret_key_match:
    st.warning("La clave secreta es incorrecta. Por favor, inténtalo de nuevo.")
else:
    # --- 2. UX IMPROVEMENT: Using a Form ---
    # A form allows the user to press 'Enter' in the text box to submit,
    # which is a more intuitive experience than forcing a button click.
    with st.form("search_form"):
        search_term = st.text_input(
            "Ingresa tu término de búsqueda:",
            placeholder="Ej: marketing digital, recetas saludables..."
        )
        submitted = st.form_submit_button("Buscar Contenido")

    if submitted and search_term:
        with st.spinner("Buscando videos y analizando comentarios... (La primera búsqueda puede tardar un momento)"):
            results = search_youtube_content(google_api_key, search_term)

        st.subheader(f"Resultados para: \"{search_term}\"")

        if not results:
            st.info("Búsqueda completada. No se encontraron videos con comentarios que contengan preguntas.")
        else:
            # --- ADDITION: Prepare data and add a download button for CSV ---
            # We flatten the results to create a list of dictionaries suitable for a CSV.
            csv_data = []
            for result in results:
                for comment in result['comments']:
                    csv_data.append({
                        "Video Title": result['title'],
                        "Question in Comment": comment
                    })
            
            if csv_data:
                df_download = pd.DataFrame(csv_data)
                # Convert DataFrame to CSV string for the download button
                csv = df_download.to_csv(index=False).encode('utf-8')

                st.download_button(
                   label="Descargar preguntas como CSV",
                   data=csv,
                   file_name=f'preguntas_{search_term.replace(" ", "_")}.csv',
                   mime='text/csv',
                )

            # --- 3. UI IMPROVEMENT: Card Layout ---
            # Instead of a dense table, we display each result in a visually
            # separate "card". This is cleaner and easier to read, especially
            # for media-focused content.
            for result in results:
                with st.container(border=True):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        # --- FIX: Deprecation Warning ---
                        # Changed `use_column_width` to `use_container_width` to align with
                        # recent Streamlit updates and remove the warning.
                        st.image(result["thumbnail"], use_container_width=True)
                    with col2:
                        st.subheader(result["title"])
                        # An expander keeps the UI clean by hiding long lists of comments
                        with st.expander(f"Ver {len(result['comments'])} preguntas encontradas"):
                            for comment in result["comments"]:
                                st.markdown(f"- *{comment}*")
                                st.divider()

