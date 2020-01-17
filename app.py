import streamlit as st
import pandas as pd
import numpy as np
from zipfile import ZipFile
import urllib.request, os
from functions.recommendation import find_recommendation
from config import MINI_DATASET_URL
from youtube_search import YoutubeSearch


def isin_genres(df, selected_genres):
    # filter dataframe if there is user input criteria; default to 1 if not.

    if selected_genres:
        df = df.apply(lambda x: 1 if (x >= selected_genres) else 0)
    else:
        df = 1

    return df


def cast_int(value):
    try:
        value = int(value)
    except ValueError:
        value = None
    return value


def make_clickable(title):
    search_str = 'http://www.google.com'
    return f'<a href="{search_str}">{title}</a>'


def process_data(links, movies, ratings):
    # Process Movie Data
    movies['year'] = movies['title'].apply(lambda x: x.split('(')[-1]
                                           .strip(' )')).apply(lambda x: cast_int(x))
    movies['genres'] = movies['genres'].replace("(no genres listed)", None)

    movies['genres_set'] = movies['genres'].apply(lambda x: set(x.split("|")))

    movies['clickable_title'] = movies['title'].apply(lambda x: make_clickable(x))

    return links, movies, ratings


@st.cache
def get_data():
    # Create directory and downlaod data if not exist
    if not os.path.isfile('./data/mini_dataset.zip'):
        os.mkdir('./data')
        urllib.request.urlretrieve(MINI_DATASET_URL, './data/mini_dataset.zip')

    # Load data to pandas
    links = pd.read_csv(ZipFile('./data/mini_dataset.zip').open('ml-latest-small/links.csv'))
    movies = pd.read_csv(ZipFile('./data/mini_dataset.zip').open('ml-latest-small/movies.csv'))
    ratings = pd.read_csv(ZipFile('./data/mini_dataset.zip').open('ml-latest-small/ratings.csv'))

    return links, movies, ratings


def get_min_max_year(year):
    return [int(year.min()), int(year.max())]


def get_genre_set(genres):
    genre_list = []

    # Add individual genre value to to genre list
    for item in genres:
        item = str(item).split("|")
        for i in item:
            genre_list.append(i)

    return np.unique(genre_list)


def main():
    # Load Data
    links, movies, ratings = get_data()
    p_links, p_movies, p_rating = process_data(links.copy(), movies.copy(), ratings.copy())

    # Set Up the Layout
    st.title("Yet Another Movie Recommender")

    add_year_selector = st.sidebar.slider(label="Select Year Range",
                                          min_value=get_min_max_year(p_movies.year)[0],
                                          max_value=get_min_max_year(p_movies.year)[1],
                                          value=(get_min_max_year(p_movies.year)[1] - 20,
                                                 get_min_max_year(p_movies.year)[1]),
                                          step=1)

    add_genre_selector = st.sidebar.multiselect(label="Select the Genre (default to any)",
                                                options=get_genre_set(p_movies.genres))

    st.subheader(f"Your Movie Suggestions from {add_year_selector[0]} to {add_year_selector[1]}")

    # Filter Data
    data = p_movies.loc[(p_movies['year'] >= add_year_selector[0]) &
                (p_movies['year'] <= add_year_selector[1]) &
                (isin_genres(p_movies['genres_set'], set(add_genre_selector)))]\
        .sample(int(5))\
        .sort_values("year", ascending=False)\
        .reset_index()

    try:
        st.table(data[['title', 'genres']])

    except ValueError:
        st.write(f"Not enough results. Here are all.")
        st.table(data[['title', 'genres']])

    st.button("Show Something Else", key=1)

    st.subheader("Movie Trailers")
    for title in data['title']:
        search_term = title + "trailer"
        results = YoutubeSearch(title, max_results=1).to_dict()
        st.video('https://www.youtube.com'+results[0]['link'])

    st.button("Show Something Else", key=2)


if __name__ == '__main__':
    main()
