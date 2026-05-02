import os
from google import genai
from utils.db_manager import get_db_connection
from dotenv import load_dotenv

# .env dosyasındaki API anahtarlarını yükle
load_dotenv()


def analyze_advanced_insight():
    """
    Veritabanındaki filmleri analiz eder ve profesyonel teknik analizler üretir.
    Kişisel veri barındırmaz, tamamen objektif bir mimari kullanır.
    """
    conn = get_db_connection()
    if not conn:
        print("❌ Veritabanı bağlantısı kurulamadı.")
        return

    cursor = conn.cursor(dictionary=True)

    # 1. Analiz edilmemiş filmi, tür bilgisiyle birlikte çek
    # Veritabanı dökümanındaki ilişkisel yapıya sadık kalınmıştır.
    query = """
        SELECT m.id, m.title, m.overview, 
               GROUP_CONCAT(DISTINCT g.genre_name) as genres
        FROM movies m
        LEFT JOIN movie_genre_map mgm ON m.id = mgm.movie_id
        LEFT JOIN genres g ON mgm.genre_id = g.id
        WHERE m.id NOT IN (SELECT movie_id FROM ai_insights)
        GROUP BY m.id
        LIMIT 1
    """

    try:
        cursor.execute(query)
        movie = cursor.fetchone()

        if not movie:
            print("ℹ️ Analiz edilecek yeni kayıt bulunamadı.")
            return

        # 2. Gemini 2.5 API Yapılandırması (Profesyonel Mod)
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # Tamamen nesnel, teknik ve kurumsal bir prompt yapısı
        prompt = f"""
        GÖREV: Film İçerik Analizi
        FİLM: {movie['title']}
        TÜRLER: {movie['genres'] if movie['genres'] else 'Belirtilmemiş'}
        ÖZET: {movie['overview']}
        
        ANALİZ KRİTERLERİ:
        - Analiz, kıdemli bir yazılım mühendisi ve profesyonel bir sinema eleştirmeni diliyle yapılmalıdır.
        - Üslup: Objektif, teknik derinliği olan, ciddi ve kurumsal.
        - Her türlü kişisel ifade, samimiyet veya öznel yargıdan kaçınılmalıdır.
        
        FORMAT:
        ETİKET: [Max 3 kelimelik teknik/felsefi tanımlama]
        YORUM: [İçeriğin yapısını ve temasını inceleyen 2-3 cümlelik profesyonel analiz]
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        raw_text = response.text

        # Veri ayrıştırma (Parsing)
        if "ETİKET:" in raw_text and "YORUM:" in raw_text:
            tag = raw_text.split("ETİKET:")[1].split("YORUM:")[0].strip()
            commentary = raw_text.split("YORUM:")[1].strip()

            # 3. Sonuçları ai_insights tablosuna kaydet
            insert_query = """
                INSERT INTO ai_insights (movie_id, analysis_tag, ai_commentary)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (movie["id"], tag, commentary))
            conn.commit()
            print(f"✅ Analiz Başarılı: {movie['title']}")
        else:
            print("⚠️ API yanıt formatı beklenen yapıda değil.")

    except Exception as e:
        print(f"❌ Sistem Hatası: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    analyze_advanced_insight()
