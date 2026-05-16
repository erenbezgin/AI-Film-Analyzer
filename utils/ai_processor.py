from utils.db_manager import get_db_connection
from dotenv import load_dotenv
from utils.ai_engine import generate_gemini_text

# .env dosyasındaki API anahtarlarını yükle
load_dotenv()


def _safe_log(msg):
    """Konsola emoji dahil yazarken codec hatalarina karsi."""
    print(msg.encode("ascii", errors="replace").decode("ascii"))


def analyze_advanced_insight():
    """
    Veritabanındaki filmleri analiz eder ve profesyonel teknik analizler üretir.
    Kişisel veri barındırmaz, tamamen objektif bir mimari kullanır.
    """
    conn = get_db_connection()
    if not conn:
        _safe_log("[error] Veritabanina baglanilamadi.")
        return

    cursor = conn.cursor(dictionary=True)

    # genres artık movies.genre sütununda tutuluyor
    query = """
        SELECT m.id, m.title, m.overview, m.genre as genres
        FROM movies m
        WHERE m.id NOT IN (SELECT movie_id FROM ai_insights)
        LIMIT 1
    """

    try:
        cursor.execute(query)
        movie = cursor.fetchone()

        if not movie:
            _safe_log("[info] Analiz icin yeni film kaydi bulunamadi.")
            return

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

        raw_text = generate_gemini_text(prompt)
        if raw_text.startswith("Hata:"):
            _safe_log(f"[error] Gemini bos veya hatali cevap: {raw_text}")
            return

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
            _safe_log(f"[ok] Analiz basariyla kaydedildi: {movie['title']}")
        else:
            _safe_log("[warn] API yanit formati beklenen yapida degil.")

    except Exception as e:
        _safe_log(f"[error] Analiz hatasi: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    analyze_advanced_insight()
