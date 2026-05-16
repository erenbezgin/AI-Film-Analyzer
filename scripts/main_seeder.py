import os
import sys
import requests
import json
import time

# PROJE ANA DİZİNİNİ KESİN OLARAK BUL VE YOLA (PATH) EKLE
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
from utils.db_manager import get_db_connection

load_dotenv()


# TMDb'nin sabit tür ID -> İsim haritası
TMDB_GENRES = {
    28: "Aksiyon",
    12: "Macera",
    16: "Animasyon",
    35: "Komedi",
    80: "Suç",
    99: "Belgesel",
    18: "Dram",
    10751: "Aile",
    14: "Fantastik",
    36: "Tarih",
    27: "Korku",
    10402: "Müzik",
    9648: "Gizem",
    10749: "Romantik",
    878: "Bilim Kurgu",
    10770: "TV Film",
    53: "Gerilim",
    10752: "Savaş",
    37: "Vahşi Batı",
}


def seed_movies():
    conn = get_db_connection()
    if not conn:
        print("❌ Veritabanı bağlantısı kurulamadı!")
        return
    cursor = conn.cursor()

    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("❌ .env dosyasında TMDB_API_KEY bulunamadı!")
        return

    total_pages = 250  # 250 sayfa * 20 film = 5000 film
    print(
        f"🎬 TMDb'den toplam {total_pages * 20} film ve oyuncu kadroları çekiliyor..."
    )
    print(
        "⏳ Bu işlem API limitleri nedeniyle yaklaşık 15-20 dakika sürebilir. Lütfen terminali kapatmayın...\n"
    )

    for page in range(1, total_pages + 1):
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=tr-TR&page={page}"
        response = requests.get(url)

        if response.status_code == 200:
            movies = response.json().get("results", [])
            for movie in movies:
                movie_id = movie.get("id")

                # 1. Türleri ayarla
                g_names = [
                    TMDB_GENRES.get(gid, "") for gid in movie.get("genre_ids", [])
                ]
                genre_str = ", ".join(filter(None, g_names))

                # 2. Filmi Ana Tabloya Kaydet
                sql_movie = """
                    INSERT IGNORE INTO movies (id, title, overview, release_date, vote_average, poster_path, genre)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                val_movie = (
                    movie_id,
                    movie.get("title") or movie.get("original_title", "Bilinmeyen"),
                    movie.get("overview", ""),
                    movie.get("release_date") if movie.get("release_date") else None,
                    movie.get("vote_average", 0),
                    movie.get("poster_path", ""),
                    genre_str,
                )

                try:
                    cursor.execute(sql_movie, val_movie)

                    # --- OYUNCU KADROSU (CREDITS) ÇEKİMİ ---
                    credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={api_key}&language=tr-TR"
                    credits_response = requests.get(credits_url)
                    cast_data = []

                    if credits_response.status_code == 200:
                        credits_json = credits_response.json()
                        cast_list = credits_json.get("cast", [])[:5]

                        for actor in cast_list:
                            actor_id = actor.get("id")
                            actor_name = actor.get("name")
                            character_name = actor.get("character", "")
                            profile_path = actor.get("profile_path", "")

                            sql_actor = "INSERT IGNORE INTO actors (id, name, profile_path) VALUES (%s, %s, %s)"
                            cursor.execute(
                                sql_actor, (actor_id, actor_name, profile_path)
                            )

                            sql_cast = "INSERT IGNORE INTO movie_cast (movie_id, actor_id, character_name) VALUES (%s, %s, %s)"
                            cursor.execute(
                                sql_cast, (movie_id, actor_id, character_name)
                            )

                            cast_data.append(actor)

                    # 3. Arşiv (api_raw_data) için JSON oluştur
                    movie["cast"] = cast_data
                    raw_json_str = json.dumps(movie)

                    # 4. Ham veriyi arşive kaydet
                    sql_raw = "INSERT IGNORE INTO api_raw_data (movie_id, raw_json) VALUES (%s, %s)"
                    cursor.execute(sql_raw, (movie_id, raw_json_str))

                    conn.commit()

                except Exception as e:
                    conn.rollback()

                # Ban yememek için çok kritik bekleme süresi!
                time.sleep(0.1)

            print(
                f"✅ Sayfa {page}/{total_pages} tamamlandı! (Şu ana kadar {page * 20} film tarandı)"
            )

        else:
            print(f"❌ {page}. sayfa çekilemedi! API Hatası: {response.status_code}")
            time.sleep(1)  # Hata alırsak biraz daha uzun bekle

    cursor.close()
    conn.close()
    print("\n🚀 TÜM 5000 FİLM, OYUNCULAR VE ARŞİV BAŞARIYLA SİSTEME EKLENDİ!")


if __name__ == "__main__":
    seed_movies()
