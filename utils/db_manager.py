import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",  # XAMPP varsayılan kullanıcı
            password="",  # XAMPP varsayılan şifre boştur
            database="film_arsivi_db",
        )
        return connection
    except Exception as e:
        print(f"❌ Veritabanı Bağlantı Hatası: {e}")
        return None


def test_db():
    conn = get_db_connection()
    if conn:
        print("✅ MySQL Bağlantısı Başarılı!")
        conn.close()


if __name__ == "__main__":
    test_db()
