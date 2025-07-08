import pickle
import pandas as pd
import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Page Configuration ---
st.set_page_config(page_title="🎬 Movie Recommender", page_icon="🍿", layout="wide")

# --- Global setup for requests session with retry ---
session = requests.Session()
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    backoff_factor=1
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)

# --- Simple in-memory cache ---
poster_cache = {}

# --- Function to fetch movie poster from TMDb API ---
def fetch_poster(movie_id):
    if movie_id in poster_cache:
        return poster_cache[movie_id]
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=56561d9a96becbe244161efe7a5505a2&language=en-US"
        response = session.get(url, timeout=8)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        full_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else "https://via.placeholder.com/500?text=No+Poster"
        poster_cache[movie_id] = full_url
        return full_url
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch poster for movie ID {movie_id}: {e}")
        return "https://via.placeholder.com/500?text=Error"

# --- Function to recommend similar movies ---
def recommend(movie):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        recommended_movies = []
        recommended_movies_posters = []
        for i in movies_list:
            movie_id = movies.iloc[i[0]].id
            recommended_movies.append(movies.iloc[i[0]].title)
            recommended_movies_posters.append(fetch_poster(movie_id))
        return recommended_movies, recommended_movies_posters
    except Exception as e:
        print(f"Error during recommendation: {e}")
        return [], []

# --- Load data ---
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

# ✅ Clean titles: remove hashtags like #Horror
movies['title'] = movies['title'].str.replace(r'^#', '', regex=True)

similarity = pickle.load(open('similarity.pkl', 'rb'))

# --- Custom Styling ---
st.markdown("""
    <style>
        .main-title {
            text-align: center;
            font-size: 50px;
            color: #ff4b4b;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            font-size: 20px;
            color: #555;
            margin-bottom: 30px;
        }
        .footer {
            text-align: center;
            font-size: 14px;
            color: gray;
            margin-top: 50px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("<div class='main-title'>🎬 Movie Recommendation System</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Discover similar movies you'll love based on your favorite</div>", unsafe_allow_html=True)

# --- Movie Selection with Placeholder ---
movie_list = sorted(movies['title'].unique())
selected_movie_name = st.selectbox("🎥 Select a movie you like:", ["-- Choose a movie --"] + movie_list)

# --- Recommendation Button ---
if selected_movie_name != "-- Choose a movie --":
    if st.button("🔍 Recommend"):
        with st.spinner("🔎 Finding similar movies..."):
            names, posters = recommend(selected_movie_name)

        st.markdown("---")
        st.markdown(f"<h4 style='text-align: center;'>Top 5 Recommendations for <span style='color:#ff4b4b;'>{selected_movie_name}</span></h4>", unsafe_allow_html=True)

        if names:
            cols = st.columns(5)
            for i in range(5):
                with cols[i]:
                    st.image(posters[i], use_container_width=True)
                    st.markdown(f"<p style='text-align: center; font-weight: bold;'>{names[i]}</p>", unsafe_allow_html=True)
        else:
            st.error("⚠️ Could not generate recommendations. Please try again.")

# --- Footer ---
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div class='footer'>Made with ❤️ | © 2025 MovieMate</div>", unsafe_allow_html=True)
