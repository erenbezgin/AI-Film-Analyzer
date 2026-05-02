import os
import requests
from dotenv import load_dotenv
from utils.db_manager import get_db_connection

load_dotenv()


def seed_official_genres():
    api_key = os.getenv("TMDB_API_KEY")
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}&language=tr-TR"

    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()

    try:
        response = requests.get(url)
        if response.status_code == 200:
            genres = response.json().get("genres", [])
            print(f"📦 {len(genres)} adet tür bulundu, veritabanına işleniyor...")

            for genre in genres:
                cursor.execute(
                    "INSERT IGNORE INTO genres (id, genre_name) VALUES (%s, %s)",
                    (genre["id"], genre["name"]),
                )
            conn.commit()
            print("✅ genres tablosu başarıyla dolduruldu!")
        else:
            print("❌ TMDb'den tür listesi çekilemedi.")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    seed_official_genres()
