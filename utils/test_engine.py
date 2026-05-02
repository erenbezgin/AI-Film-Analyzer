import os
import requests
from google import genai
from dotenv import load_dotenv

load_dotenv()


def run_test():
    print("\n--- 🛠️ SİSTEM BAĞLANTI TESTİ BAŞLATILDI ---")

    # 1. TMDB TESTİ
    tmdb_key = os.getenv("TMDB_API_KEY")
    tmdb_url = (
        f"https://api.themoviedb.org/3/movie/577922?api_key={tmdb_key}&language=tr-TR"
    )
    try:
        tmdb_res = requests.get(tmdb_url)
        if tmdb_res.status_code == 200:
            print(
                f"✅ TMDb Bağlantısı: Başarılı! (Film: {tmdb_res.json().get('title')})"
            )
    except Exception as e:
        print(f"❌ TMDb Hatası: {e}")

    # -- AI TESTİ -
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ Gemini AI Hatası: .env dosyasında anahtar bulunamadı!")
    else:
        try:
            client = genai.Client(api_key=gemini_key)

            print("🔍 Anahtarının erişebildiği modeller taranıyor...")
            model_listesi = []
            for m in client.models.list():
                model_listesi.append(m.name)
                print(f"   -> Bulunan Model: {m.name}")

            if model_listesi:
                # Listeden ilk uygun model
                secilen_model = model_listesi[0]
                print(f"🚀 Otomatik seçilen modelle test ediliyor: {secilen_model}")

                response = client.models.generate_content(
                    model=secilen_model, contents="Bağlantı başarılı mı kaptan?"
                )
                print(f"✅ Gemini Bağlantısı: Başarılı! (Cevap: {response.text})")
            else:
                print("❌ Hata: Bu anahtarla erişilebilen hiçbir model bulunamadı!")

        except Exception as e:
            print(f"❌ Gemini AI Teknik Hata: {e}")


if __name__ == "__main__":
    run_test()
