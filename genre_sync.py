import os
import time
import requests
from dotenv import load_dotenv
from utils.db_manager import get_db_connection
from utils.db_functions import update_movie_genres

load_dotenv()


def sync_all_genres():
    api_key = os.getenv("TMDB_API_KEY")
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)
    # Sadece türü henüz eşleşmemiş filmleri çekiyoruz (Performans için)
    cursor.execute("""
        SELECT id FROM movies 
        WHERE id NOT IN (SELECT DISTINCT movie_id FROM movie_genre_map)
    """)
    movies_to_fix = cursor.fetchall()
    conn.close()

    print(f"🔄 {len(movies_to_fix)} film için tür eşleşmesi başlatılıyor...")

    for movie in movies_to_fix:
        m_id = movie["id"]
        url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={api_key}&language=tr-TR"

        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Tür ID'lerini bir liste olarak alıyoruz
                genre_ids = [g["id"] for g in data.get("genres", [])]

                if genre_ids:
                    update_movie_genres(m_id, genre_ids)
                    print(f"✅ Film ID {m_id} türleri eşleşti.")

                time.sleep(0.1)  # API limitine takılmamak için
            else:
                print(f"⚠️ Film ID {m_id} bilgisi çekilemedi.")
        except Exception as e:
            print(f"❌ Hata (ID {m_id}): {e}")
            continue

    print("🏁 Tüm türler mermi gibi dizildi kanka!")


if __name__ == "__main__":
    sync_all_genres()
