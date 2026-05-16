import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Veritabanı bağlantısını .env'den alınan ayarlarla kurar. Varsayılanlar XAMPP'ye uyumludur.

    Çalışma ortamına göre `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` ortam değişkenlerini ayarlayın.
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "film_arsivi_db"),
            autocommit=False,
        )
        return connection
    except Exception as e:
        # Eğer .env'de placeholder veya yanlış bir şifre varsa, XAMPP'nin varsayılan
        # (root, boş şifre) kombinasyonunu otomatik deneyelim — hızlı kurtarma.
        print(f"❌ Veritabanı Bağlantı Hatası: {e}")
        try:
            fallback = mysql.connector.connect(host=os.getenv("DB_HOST", "localhost"), user=os.getenv("DB_USER", "root"), password="", database=os.getenv("DB_NAME", "film_arsivi_db"), autocommit=False)
            print("⚠️ Uyarı: .env ayarlarıyla bağlanılamadı; boş şifre ile XAMPP varsayılanına geri dönüldü.")
            return fallback
        except Exception as e2:
            print(f"❌ Fallback bağlantı da başarısız: {e2}")
            return None


def test_db():
    conn = get_db_connection()
    if conn:
        print("✅ MySQL Bağlantısı Başarılı!")
        conn.close()


if __name__ == "__main__":
    test_db()
