import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import os
import time

# Get the secret key from the loaded environment variables
secret_key = st.secrets["SECRET_KEY"]


# Set the page configuration
st.set_page_config(
    page_title="Contenido Ilimitado",
    page_icon="e.png",
    layout="wide"
)
st.logo("estudiose.png")
st.title("Contenido Ilimitado")

# Set the sidebar configuration and key
with st.sidebar:
    st.sidebar.title("Claves")
    google_api_key = st.text_input("Escribe tu clave de API de Google", type="password")
    st.write(f"Si no sabes cómo obtener tu clave de API de Google, sigue [este enlace](https://youtu.be/jH5kknrti00)")
    secret_key_match = st.text_input("Escribe tu clave secreta", type="password")
    st.write(f"Si no tienes una clave secreta, por favor, solicítala al administrador de la comunidad")

# Check if the user has entered a Google API key and display the search box
if google_api_key and secret_key == secret_key_match:
    search_term = st.text_input("Ingresa tu término de búsqueda")
    # Build the youtube service
    if search_term:
        youtube = build("youtube", "v3", developerKey=google_api_key)
        # Make the youtube request
        request = youtube.search().list(
            part="snippet",
            maxResults=10,
            q=search_term
        )
        response = request.execute()
        # Wait for the response
        with st.spinner("Buscando contenido..."):
            time.sleep(5)

        # Check if the response has items
        try:
            if "items" in response:
                items = response["items"]
                table_data = []
                for item in items:
                    try:
                        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
                        title = item["snippet"]["title"]
                        video_id = item["id"]["videoId"]
                        # Get the comments for the video
                        comments_request = youtube.commentThreads().list(
                            part="snippet",
                            videoId=video_id,
                            maxResults=40
                        )
                        comments_response = comments_request.execute()
                        comments = [comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for comment in comments_response["items"] if "?" in comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]]
                        table_data.append([thumbnail, title, comments])
                    except Exception as e:
                        pass
            else:
                st.warning("No se encontraron resultados")
        except Exception as e:
            st.error(f"Ocurrió algún error con alguno de los videos. Los siguientes son los únicos que se pudieron obtener:")
        
        # Create a pandas DataFrame
        df = pd.DataFrame(table_data, columns=["Thumbnail", "Title", "Comments"])
        # Display the DataFrame
        st.dataframe(df, 
                    width=None,
                    height=None,
                        column_config={
                            "Thumbnail": st.column_config.ImageColumn(width="medium"),
                                "Title": st.column_config.TextColumn(),
                                "Comments": st.column_config.ListColumn()
                        })

else:
    st.warning("Por favor, ingresa tu clave de API de Google y tu Clave Secreta para empezar a buscar contenido ilimitado")

