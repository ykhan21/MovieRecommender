import streamlit as st
import pandas as pd
import numpy as np

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

# Load rating matrix and similarity matrix
@st.cache_data
def load_recommendation_data():
    # Paths to be updated based on your file locations
    R = pd.read_csv('Rmat.csv', index_col=0)
    S = pd.read_csv('movie_similarity_matrix.csv', index_col=0)
    
    # Remove prefixes
    R.index = R.index.str.lstrip('u').astype(int)
    R.columns = R.columns.str.lstrip('m').astype(int)
    
    return R, S

# System I: Recommendation Based on Popularity
def get_popular_movies(top_n=10):
    R = pd.read_csv('Rmat.csv', index_col=0)
    R.index = R.index.str.lstrip('u').astype(int)
    R.columns = R.columns.str.lstrip('m').astype(int)

    rating_counts = R.notna().sum()
    avg_ratings = R.mean()
    popular_movies = rating_counts[(rating_counts >= 50) & (avg_ratings >= 3.5)]
    popular_movies_sorted = popular_movies.sort_values(ascending=False).head(top_n)

    # Convert to DataFrame with movie details
    popular_movies_df = movies_df[movies_df["id"].isin(popular_movies_sorted.index)]
    popular_movies_df = popular_movies_df.copy()  # Avoid SettingWithCopyWarning
    popular_movies_df["score"] = popular_movies_sorted.values
    return popular_movies_df

def recommender(ratings_dict, movies_df, top_n=10):
    # Create new_user Series with integer index, allowing NaN values
    new_user = pd.Series(dtype=float, index=movies_df['id'])
    
    # Add rated movies to new_user
    for title, rating in ratings_dict.items():
        matching_movies = movies_df[movies_df['title'] == title]
        if not matching_movies.empty and rating > 0:
            new_user[matching_movies.iloc[0]['id']] = rating

    try:
        R, S = load_recommendation_data()
        
        # Remove any NaN values from new_user
        new_user = new_user.dropna()
        
        # Ensure S is using string column labels
        S.columns = S.columns.astype(str)
        
        # Call myIBCF with modified function
        recommendations = myIBCF(new_user, S, R)

        # If no recommendations, fall back to popular movies
        if recommendations.empty:
            print(f"Recommendations is empty.")
            return get_popular_movies(top_n)

        # Merge recommendations with movie details
        recommended_movies = recommendations.merge(movies_df, on="id", how="left")
        return recommended_movies
    except Exception as e:
        print(f"Error in recommendation: {e}")
        return get_popular_movies(top_n)

def myIBCF(new_user, S, R):
    """
    Compute movie recommendations for a new user using Item-Based Collaborative Filtering.
    """
    # Ensure new_user index is clean
    new_user = new_user[new_user.notna()]
    
    predictions = {}
    for movie_id in S.columns:
        # Convert movie_id to integer
        movie_id = int(movie_id)
        
        # Check if the movie is not already rated by the user
        if movie_id not in new_user.index:
            # Get similar movies
            neighbors = S.loc[:, str(movie_id)].dropna()
            
            # Find rated neighbors
            rated_neighbors = [
                int(r) for r in neighbors.index 
                if int(r) in new_user.index and not pd.isna(new_user[int(r)])
            ]
            
            if rated_neighbors:
                numerator = sum(
                    neighbors[str(r)] * new_user[r] 
                    for r in rated_neighbors
                )
                denominator = sum(neighbors[str(r)] for r in rated_neighbors)
                
                if denominator > 0:
                    predictions[movie_id] = numerator / denominator

    # Convert to DataFrame and sort
    if predictions:
        predictions_df = pd.DataFrame.from_dict(predictions, orient='index', columns=['score'])
        predictions_df.index.name = 'id'
        predictions_df.reset_index(inplace=True)
        predictions_df.sort_values(by='score', ascending=False, inplace=True)
        return predictions_df.head(10)
    else:
        return pd.DataFrame(columns=['id', 'score'])  # Return empty DataFrame with correct columns

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
    print(recommendations)
    
    # Display the recommendations
    for idx, row in recommendations.iterrows():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(get_image_url(row["id"]), width=100)
        with col2:
            st.write(f"**{row['title']}**")
