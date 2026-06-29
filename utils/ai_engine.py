import os
import re
import time
import google.generativeai as genai
from dotenv import load_dotenv

# .env dosyasındaki API anahtarını güvenli şekilde yükle
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("⚠️ UYARI: GEMINI_API_KEY .env dosyasında bulunamadı!")
    api_key = ""

genai.configure(api_key=api_key)
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
model = genai.GenerativeModel(model_name)
_next_retry_ts = 0.0


def _extract_text(resp):
    # gemini'nin farklı yanıt formatlarını güvenli şekilde işleyerek düz metin çıkarır
    """google-generativeai farklı yanıt tiplerinde .text'i bazen üretmez; güvenli çöz."""
    if not resp:
        return ""
    txt = getattr(resp, "text", None)
    if txt:
        return txt.strip()

    cand = getattr(resp, "candidates", None)
    if not cand:
        return ""

    parts = []
    for c in cand:
        content = getattr(c, "content", None)
        if not content:
            continue
        for p in getattr(content, "parts", []) or []:
            t = getattr(p, "text", None)
            if t:
                parts.append(t)
    return "\n".join(parts).strip()


def generate_gemini_text(prompt: str) -> str:
    #diğer tüm yapay zeka fonksiyonları bu temel metin üretim fonksiyonunu kullanır
    """Gemini'den düz metin üret (boş veya hata durumunda anlamlı mesaj)."""
    global _next_retry_ts
    if not api_key:
        return "Hata: GEMINI_API_KEY tanımlı değil. .env dosyasına anahtarı ekleyip uygulamayı yeniden başlatın."

    now = time.time()
    if _next_retry_ts > now:
        wait = int(_next_retry_ts - now)
        return f"Hata: AI kotasi dolu. Yaklasik {wait} saniye sonra tekrar deneyin."

    try:
        response = model.generate_content(prompt)
        text = _extract_text(response)
        if text:
            return text
        return "Hata: AI yanıtı boş döndü. Model veya kota ayarlarını kontrol edin."
    except Exception as e:
        err = str(e)
        print(f"Gemini API Hatası: {err}")
        if "429" in err or "quota" in err.lower():
            retry_seconds = 60
            match = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)s", err, re.IGNORECASE)
            if match:
                try:
                    retry_seconds = max(1, int(float(match.group(1))))
                except Exception:
                    retry_seconds = 60
            _next_retry_ts = time.time() + retry_seconds
            return f"Hata: AI kotasi dolu. Yaklasik {retry_seconds} saniye sonra tekrar deneyin."
        return f"Hata: AI şu an yanıt veremiyor. ({err})"


def get_ai_movie_analysis(movie_title):
    #dışarıdan verilen film başlığına göre yapay zekadan analiz alır
    """Film hakkında derinlemesine analiz yapar."""
    prompt = f"Bana '{movie_title}' filminin temasını, neden izlenmesi gerektiğini ve varsa gizli detaylarını 3 kısa cümleyle anlat."
    return generate_gemini_text(prompt)


def get_ai_recommendation(user_input):
    #kullanıcının doğal dildeki isteğine göre yapay zekadan film önerisi alır
    """Kullanıcının doğal dil isteğine göre film önerir."""
    prompt = f"Kullanıcı diyor ki: '{user_input}'. Bu isteğe göre en iyi 3 film önerisini kısa gerekçeleriyle yaz."
    return generate_gemini_text(prompt)


def get_ai_chat_response(question):
    #kullanıcının yapay zeka ile sohbet edebileceği basit chat bot fonksiyonu
    """AI ile sohbet: Kullanıcının sorularına yanıt verir ve önerdiği filmleri Türkçe/İngilizce etiketler."""
    prompt = (
        f"Sen sinema konusunda uzmanlaşmış, zeki bir AI Film Asistanısın.\n"
        f"Kullanıcının sorusu: '{question}'\n\n"
        f"Lütfen bu soruya Türkçe, samimi ve profesyonel bir dille yanıt ver. "
        f"Önerdiğin filmler varsa, her birini kalın harflerle belirt (örneğin **Inception**). "
        f"En önemlisi, önerdiğin tüm filmlerin Türkçe ve İngilizce/Orijinal başlıklarını yanıtının en sonuna "
        f"tam olarak şu formatta ekle: [FILMLER: Türkçe İsim / İngilizce İsim, Türkçe İsim / İngilizce İsim]\n"
        f"Örnek: [FILMLER: Başlangıç / Inception, Matrix / The Matrix, Yıldızlararası / Interstellar]\n"
        f"Bu etiket kullanıcıya gösterilmeyecek, arka planda işlenecektir. Yanıtının sonuna mutlaka eklemelisin."
    )
    return generate_gemini_text(prompt)


def get_quota_status():
    #admin paneli için yapay zeka kota durumunu kontrol eder ve uygun mesajı döndürür
    """Basit bir AI kota durumu kontrolü döndürür.

    Dönüş formatı: { 'level': 'green'|'yellow'|'red', 'label': 'Metin', 'detail': 'Açıklama' }
    - Red: API anahtarı yok veya uzun süreli kısıtlama
    - Yellow: Geçici kısıtlama (retry zamanına yakın)
    - Green: Her şey normal
    """
    import time

    now = time.time()
    # API anahtarı yoksa kritik
    if not api_key:
        return {"level": "red", "label": "Kritik", "detail": "GEMINI_API_KEY tanımlı değil."}

    # Eğer sistem daha önce kota hatası alıp retry zamanını belirlediyse
    global _next_retry_ts
    try:
        remaining = max(0, int(_next_retry_ts - now))
    except Exception:
        remaining = 0

    if remaining > 0:
        # Eğer bekleme 1 dakikadan azsa kırmızı, daha uzunsa sarı
        if remaining <= 60:
            return {"level": "red", "label": "Kısıtlı", "detail": f"AI kotası dolu. Yaklaşık {remaining}s bekleyin."}
        return {"level": "yellow", "label": "Sınırlı", "detail": f"AI kotası dolu. Yaklaşık {remaining}s bekleyin."}

    # Varsayılan: yeşil
    return {"level": "green", "label": "Aktif", "detail": "Gemini API erişimi hazır."}
