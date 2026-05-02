from utils.db_manager import get_db_connection


def search_movies(title=None, genre=None, min_rating=None, year=None):
    """
    Kriterlere göre veritabanında dinamik arama yapar.
    Tamamen teknik ve ölçeklenebilir bir SQL yapısı kullanır.
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    # Temel sorgu ve JOIN yapısı
    query = """
        SELECT m.*, GROUP_CONCAT(g.genre_name) as genres 
        FROM movies m
        LEFT JOIN movie_genre_map mgm ON m.id = mgm.movie_id
        LEFT JOIN genres g ON mgm.genre_id = g.id
        WHERE 1=1
    """
    params = []

    # Dinamik kriter ekleme
    if title:
        query += " AND m.title LIKE %s"
        params.append(f"%{title}%")

    if genre:
        query += " AND g.genre_name = %s"
        params.append(genre)

    if min_rating:
        query += " AND m.vote_average >= %s"
        params.append(min_rating)

    if year:
        query += " AND YEAR(m.release_date) = %s"
        params.append(year)

    query += " GROUP BY m.id ORDER BY m.vote_average DESC"

    try:
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"❌ Sorgu Hatası: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def save_movie_to_db(movie):
    """
    TMDb'den gelen film verisini 'movies' tablosuna kaydeder.
    Eğer film zaten varsa (ID çakışması), hata vermez ve geçer.
    """
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()

    # 1. Filmi Ana Tabloya Kaydet
    sql_movie = """
        INSERT IGNORE INTO movies (id, title, overview, release_date, vote_average, poster_path)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    val_movie = (
        movie.get("id"),
        movie.get("title"),
        movie.get("overview"),
        movie.get("release_date") if movie.get("release_date") else None,
        movie.get("vote_average"),
        movie.get("poster_path"),
    )

    try:
        cursor.execute(sql_movie, val_movie)
        conn.commit()
    except Exception as e:
        print(f"❌ Film Kayıt Hatası: {e}")
    finally:
        cursor.close()
        conn.close()


def update_movie_genres(movie_id, genre_ids):
    """
    Belirli bir film için tür eşleşmelerini movie_genre_map tablosuna yazar.
    """
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        for g_id in genre_ids:
            cursor.execute(
                "INSERT IGNORE INTO movie_genre_map (movie_id, genre_id) VALUES (%s, %s)",
                (movie_id, g_id),
            )
        conn.commit()
    except Exception as e:
        print(f"❌ Tür Eşleşme Hatası (ID: {movie_id}): {e}")
    finally:
        cursor.close()
        conn.close()
