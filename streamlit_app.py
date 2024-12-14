import streamlit as st
import pandas as pd

# Function to load movies from the movies.dat file
@st.cache_data
def load_movies(dat_file_path):
    movies_data = []
    with open(dat_file_path, "r", encoding="ISO-8859-1") as file:
        for line in file:
            parts = line.strip().split("::")
            if len(parts) >= 3:
                movie_id, title, genres = parts[0], parts[1], parts[2]
                movies_data.append({"id": int(movie_id), "title": title, "genres": genres})
    return pd.DataFrame(movies_data)

# Generate image URL for a movie ID
def get_image_url(movie_id):
    return f"https://liangfgithub.github.io/MovieImages/{movie_id}.jpg"

# Abstracted recommender function
def recommender(ratings_dict, movies_df, top_n=10):
    """
    Placeholder recommendation function.
    Replace this with your own recommendation algorithm.
    """
    unrated_movies = movies_df[
        ~movies_df["title"].isin([title for title, rating in ratings_dict.items() if rating > 0])
    ]
    recommendations = unrated_movies.head(top_n)
    return recommendations

# Load movies
MOVIE_DAT_PATH = "movies.dat"
movies_df = load_movies(MOVIE_DAT_PATH)

# Unique genres
unique_genres = [
    "Action", 
    "Adventure", 
    "Animation", 
    "Children's", 
    "Comedy", 
    "Crime", 
    "Documentary", 
    "Drama", 
    "Fantasy", 
    "Film-Noir", 
    "Horror", 
    "Musical", 
    "Mystery", 
    "Romance", 
    "Sci-Fi", 
    "Thriller", 
    "War", 
    "Western"
]

# Page setup
st.title("Movie Recommender")

# Initialize session state variables
if "ratings" not in st.session_state:
    st.session_state["ratings"] = {}
if "show_recommendations" not in st.session_state:
    st.session_state["show_recommendations"] = False
if "page_number" not in st.session_state:
    st.session_state["page_number"] = 0
if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""
if "selected_genres" not in st.session_state:
    st.session_state["selected_genres"] = []

# Pagination settings
PAGE_SIZE = 12  # Number of movies per page

st.subheader("Step 1: Search, Filter, and Rate Movies")

# Search bar with automatic rerun
search_query = st.text_input(
    "Search for a movie:", 
    value=st.session_state["search_query"],
    key="movie_search_input"  # Adding a key to help Streamlit track changes
)

# Check if search query has changed and reset page number
if search_query != st.session_state["search_query"]:
    st.session_state["search_query"] = search_query
    st.session_state["page_number"] = 0  # Reset to first page when search changes
    st.rerun()

# Genre filter with automatic rerun
selected_genres = st.multiselect(
    "Filter by genre(s):", 
    unique_genres, 
    default=st.session_state["selected_genres"],
    key="genre_multiselect"  # Adding a key to help Streamlit track changes
)

# Check if genres have changed and reset page number
if selected_genres != st.session_state["selected_genres"]:
    st.session_state["selected_genres"] = selected_genres
    st.session_state["page_number"] = 0  # Reset to first page when filter changes
    st.rerun()

# Function to check if all selected genres are in the movie's genre list (AND logic)
def genre_filter(genre_list, selected_genres):
    movie_genres = set(genre_list.split("|"))  # Split the pipe-delimited genres into a set
    return all(genre in movie_genres for genre in selected_genres)

# Filter movies based on search query and selected genres
filtered_movies = movies_df
if search_query:
    filtered_movies = filtered_movies[filtered_movies["title"].str.contains(search_query, case=False, na=False)]
if selected_genres:
    filtered_movies = filtered_movies[filtered_movies["genres"].apply(genre_filter, selected_genres=selected_genres)]

# Pagination calculations
total_movies = len(filtered_movies)
max_page_number = (total_movies - 1) // PAGE_SIZE

# Ensure the page number is within bounds
if st.session_state["page_number"] > max_page_number:
    st.session_state["page_number"] = max_page_number
if st.session_state["page_number"] < 0:
    st.session_state["page_number"] = 0

# Calculate current page movies
start_idx = st.session_state["page_number"] * PAGE_SIZE
end_idx = start_idx + PAGE_SIZE
current_page_movies = filtered_movies.iloc[start_idx:end_idx]

# Display movies with ratings
for idx, row in current_page_movies.iterrows():
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(get_image_url(row["id"]), caption=row["title"], width=100)
    with col2:
        rating = st.slider(f"Rate {row['title']}", 0, 5, 0, key=f"rating_{row['id']}")
        st.session_state["ratings"][row["title"]] = rating

# Pagination buttons with improved navigation
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("Previous") and st.session_state["page_number"] > 0:
        st.session_state["page_number"] -= 1
        st.rerun()
with col3:
    if st.button("Next") and st.session_state["page_number"] < max_page_number:
        st.session_state["page_number"] += 1
        st.rerun()

# Display current page information
st.write(f"Page {st.session_state['page_number'] + 1} of {max_page_number + 1}")

# Step 2: Get recommendations
st.subheader("Step 2: Discover movies you might like")
if st.button("Click here to get your recommendations"):
    st.session_state["show_recommendations"] = True

# Display recommendations
if st.session_state["show_recommendations"]:
    st.subheader("Here are 10 movies you might like:")
    
    # Call the abstracted recommender function
    recommendations = recommender(st.session_state["ratings"], movies_df, top_n=10)
    
    # Display the recommendations
    for idx, row in recommendations.iterrows():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(get_image_url(row["id"]), width=100)
        with col2:
            st.write(f"**{row['title']}**")
