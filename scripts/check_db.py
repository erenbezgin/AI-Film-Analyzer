from utils.db_manager import get_db_connection

if __name__ == '__main__':
    conn = get_db_connection()
    if not conn:
        print('❌ Bağlantı başarısız. Lütfen .env ve MySQL servis durumunu kontrol edin.')
        exit(1)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT DATABASE()')
        db = cursor.fetchone()
        print('✅ MySQL bağlantısı başarılı. Kullanılan veritabanı:', db[0])
    except Exception as e:
        print('❌ Sorgu hatası:', e)
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
