import os
import time
import requests
from dotenv import load_dotenv
from utils.db_manager import get_db_connection

load_dotenv()


def start_mega_mapping():
    api_key = os.getenv("TMDB_API_KEY")
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)
    # Sadece eşleşmesi olmayan filmleri seçiyoruz
    cursor.execute(
        "SELECT id FROM movies WHERE id NOT IN (SELECT DISTINCT movie_id FROM movie_genre_map)"
    )
    movies = cursor.fetchall()

    print(f"🔗 {len(movies)} film için tür köprüleri kuruluyor...")

    for movie in movies:
        m_id = movie["id"]
        url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={api_key}&language=tr-TR"

        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                genre_ids = [g["id"] for g in data.get("genres", [])]

                for g_id in genre_ids:
                    cursor.execute(
                        "INSERT IGNORE INTO movie_genre_map (movie_id, genre_id) VALUES (%s, %s)",
                        (m_id, g_id),
                    )
                conn.commit()
                print(f"✅ Film ID {m_id} eşleşti.")

            # TMDb hız limitine takılmamak için çok kısa bekleme
            time.sleep(0.05)

        except Exception as e:
            print(f"❌ Hata (ID {m_id}): {e}")

    print("🏁 Köprüler kuruldu! Artık None yazısı tarih oldu kanka.")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    start_mega_mapping()
