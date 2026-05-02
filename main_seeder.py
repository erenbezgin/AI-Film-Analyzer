import os
import requests
from dotenv import load_dotenv
from utils.db_functions import save_movie_to_db

load_dotenv()


def seed_popular_movies():
    api_key = os.getenv("TMDB_API_KEY")
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=tr-TR&page=1"

    response = requests.get(url)
    if response.status_code == 200:
        movies = response.json().get("results", [])
        for movie in movies:
            save_movie_to_db(movie)
    else:
        print("❌ TMDb'den veri çekilemedi.")


if __name__ == "__main__":
    seed_popular_movies()
