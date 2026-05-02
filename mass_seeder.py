import os
import time
import requests
from dotenv import load_dotenv
from utils.db_functions import save_movie_to_db

load_dotenv()


def start_mega_seeding(target_count=1500):
    api_key = os.getenv("TMDB_API_KEY")
    current_count = 0
    # TMDb her sayfada 20 film verir. 1500 / 20 = 75 sayfa.
    pages_needed = target_count // 20

    print(f"🚀 Hedef: {target_count} film. Veri çekme işlemi başlatıldı...")

    for page in range(1, pages_needed + 1):
        # tr-TR diliyle çekiyoruz
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=tr-TR&page={page}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                movies = response.json().get("results", [])
                for movie in movies:
                    # save_movie_to_db fonksiyonun içindeki INSERT IGNORE sayesinde
                    # aynı film ID'si gelirse veritabanı onu otomatik reddeder, hata vermez.
                    save_movie_to_db(movie)
                    current_count += 1

                print(
                    f"📦 Sayfa {page}/75 işlendi. Şu anki işlem sayısı: {current_count}"
                )

                # API banlanmamak için kısa bir bekleme (Profesyonel yaklaşım)
                time.sleep(0.3)
            else:
                print(f"⚠️ Sayfa {page} çekilemedi. Durum kodu: {response.status_code}")

        except Exception as e:
            print(
                f"⚠️ Bağlantı hatası oluştu, 3 saniye bekleyip devam ediliyor... Hata: {e}"
            )
            time.sleep(3)
            continue  # İnternet kopsa da döngüyü kırma, devam et

    print(f"🏁 İşlem bitti! Veritabanını kontrol edebilirsin kanka.")


if __name__ == "__main__":
    start_mega_seeding(1500)
