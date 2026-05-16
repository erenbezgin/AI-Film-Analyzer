from utils.db_manager import get_db_connection
import hashlib


def search_movies(title=None, genre=None, min_rating=None, year=None):
    """
    Kriterlere göre veritabanında dinamik arama yapar.
    Tamamen teknik ve ölçeklenebilir bir SQL yapısı kullanır.
    """
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    # Basit yapı: tür bilgisi artık movies.genre sütununda tutuluyor
    query = """
        SELECT m.*, m.genre AS genres
        FROM movies m
        WHERE 1=1
    """
    params = []

    # Dinamik kriter ekleme
    if title:
        query += " AND m.title LIKE %s"
        params.append(f"%{title}%")

    if genre:
        query += " AND LOWER(m.genre) LIKE %s"
        params.append(f"%{genre.lower()}%")

    if min_rating:
        query += " AND m.vote_average >= %s"
        params.append(min_rating)

    if year:
        query += " AND YEAR(m.release_date) = %s"
        params.append(year)

    query += " ORDER BY m.vote_average DESC"

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
        INSERT IGNORE INTO movies (id, title, overview, release_date, vote_average, poster_path, genre)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    val_movie = (
        movie.get("id"),
        movie.get("title"),
        movie.get("overview"),
        movie.get("release_date") if movie.get("release_date") else None,
        movie.get("vote_average"),
        movie.get("poster_path"),
        movie.get("genre") if movie.get("genre") else None,
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
    Güncel model: türleri `movies.genre` sütununa yazar. `genre_ids` verildiğinde
    önce `genres` tablosundan isimleri alır, virgülle ayrılmış biçimde kaydeder.
    """
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)
    try:
        if not genre_ids:
            return
        format_strings = ",".join(["%s"] * len(genre_ids))
        cursor.execute(f"SELECT id, genre_name FROM genres WHERE id IN ({format_strings})", tuple(genre_ids))
        rows = cursor.fetchall()
        names = [r["genre_name"] for r in rows] if rows else []
        genre_str = ", ".join(names)
        cursor2 = conn.cursor()
        cursor2.execute("UPDATE movies SET genre = %s WHERE id = %s", (genre_str, movie_id))
        conn.commit()
        cursor2.close()
    except Exception as e:
        print(f"❌ Tür Eşleme/Güncelleme Hatası (ID: {movie_id}): {e}")
    finally:
        cursor.close()
        conn.close()


def add_to_watch_list(user_id, movie_id):
    """Kullanıcının listesine film ekler."""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT IGNORE INTO watch_list (user_id, movie_id) VALUES (%s, %s)",
            (user_id, movie_id),
        )
        conn.commit()
        print(f"✅ Film listeye eklendi!")
    except Exception as e:
        print(f"❌ Liste hatası: {e}")
    finally:
        cursor.close()
        conn.close()


def get_recommendations(user_id):
    """İzleme listesi ve olumlu değerlendirmelere göre tür tercihlerinden film önerir."""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)

    try:
        # Yeni model: movie_genre_map yok -> watch_list ve reviews'ten gelen film kayıtlarının
        # `movies.genre` sütununu parçalayarak tür sinyallerini sayıyoruz.
        cursor.execute(
            "SELECT m.genre FROM watch_list wl JOIN movies m ON wl.movie_id = m.id WHERE wl.user_id = %s",
            (user_id,),
        )
        watch_rows = cursor.fetchall() or []

        cursor.execute(
            "SELECT m.genre FROM reviews r JOIN movies m ON r.movie_id = m.id WHERE r.user_id = %s AND r.rating >= 7",
            (user_id,),
        )
        review_rows = cursor.fetchall() or []

        genre_scores = {}
        for r in watch_rows:
            g_field = r.get("genre") if isinstance(r, dict) else (r[0] if r else None)
            if not g_field:
                continue
            for part in [p.strip() for p in g_field.split(",") if p.strip()]:
                key = part.lower()
                genre_scores[key] = genre_scores.get(key, 0) + 3

        for r in review_rows:
            g_field = r.get("genre") if isinstance(r, dict) else (r[0] if r else None)
            if not g_field:
                continue
            for part in [p.strip() for p in g_field.split(",") if p.strip()]:
                key = part.lower()
                genre_scores[key] = genre_scores.get(key, 0) + 1

        if not genre_scores:
            return []

        sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
        top_genres = [g for g, _ in sorted_genres[:3]]

        # 2. Bu türlere uyan filmleri çek (movies.genre LIKE kullanarak), izleme listesi ve yorumlu filmleri dışla
        placeholders = ",".join(["%s"] * len(top_genres))
        like_clauses = " OR ".join(["LOWER(m.genre) LIKE %s" for _ in top_genres])
        params = tuple(f"%{g}%" for g in top_genres)

        recommend_query = f"""
            SELECT m.id, m.title, m.vote_average, m.poster_path
            FROM movies m
            WHERE ({like_clauses})
            AND m.id NOT IN (SELECT movie_id FROM watch_list WHERE user_id = %s)
            AND m.id NOT IN (SELECT movie_id FROM reviews WHERE user_id = %s)
            ORDER BY m.vote_average DESC
            LIMIT 15
        """
        params = params + (user_id, user_id)
        cursor.execute(recommend_query, params)
        return cursor.fetchall()

    except Exception as e:
        print(f"❌ Öneri Hatası: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def register_user(username, email, password):
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()

    # Şifreyi SHA-256 ile hashliyoruz
    hashed_pw = hashlib.sha256(password.encode("utf-8")).hexdigest()

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_pw),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Kayıt Hatası: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def login_user(username, password):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)

    # GİRİŞTE DE AYNI ŞEKİLDE HASHLEME YAPILMALI!
    hashed_pw = hashlib.sha256(password.encode("utf-8")).hexdigest()

    try:
        query = "SELECT id, username, is_admin FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, hashed_pw))
        user = cursor.fetchone()

        if user:
            user["is_admin"] = bool(user["is_admin"])
            return user
        return None
    except Exception as e:
        print(f"❌ Login Hatası: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_watch_list(user_id):
    """Kullanıcının izleme listesindeki tüm filmleri getirir."""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT m.id, m.title, m.vote_average, m.release_date, m.poster_path, m.genre as genres
            FROM watch_list wl
            JOIN movies m ON wl.movie_id = m.id
            WHERE wl.user_id = %s
            ORDER BY m.vote_average DESC
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ İzleme Listesi Hatası: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_users_list():
    """Tüm kullanıcıları listeler (Admin için)."""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)

    try:
        query = "SELECT id, username, email, is_admin FROM users ORDER BY id DESC"
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Kullanıcı Listesi Hatası: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_movie_cast(movie_id):
    """Bir filmin oyuncu kadrosunu getirir."""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT a.id, a.name, a.profile_path, mc.character_name
            FROM movie_cast mc
            JOIN actors a ON mc.actor_id = a.id
            WHERE mc.movie_id = %s
            LIMIT 10
        """
        cursor.execute(query, (movie_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Cast Getirme Hatası: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_actor_info_and_movies(actor_id):
    """Bir aktörün temel bilgilerini ve oynadığı filmleri getirir."""
    conn = get_db_connection()
    if not conn:
        return None, []
    cursor = conn.cursor(dictionary=True)

    try:
        # Aktör bilgisi
        cursor.execute("SELECT id, name, profile_path FROM actors WHERE id = %s", (actor_id,))
        actor_info = cursor.fetchone()

        if not actor_info:
            return None, []

        # Oynadığı filmler
        query = """
            SELECT m.id, m.title, m.poster_path, m.vote_average, m.release_date, mc.character_name
            FROM movie_cast mc
            JOIN movies m ON mc.movie_id = m.id
            WHERE mc.actor_id = %s
            ORDER BY m.vote_average DESC
            LIMIT 20
        """
        cursor.execute(query, (actor_id,))
        movies = cursor.fetchall()

        return actor_info, movies
    except Exception as e:
        print(f"❌ Aktör Getirme Hatası: {e}")
        return None, []
    finally:
        cursor.close()
        conn.close()


def get_top_actors(limit=60):
    """Sistemdeki en çok filme sahip (veya popüler) oyuncuları getirir."""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT a.id, a.name, a.profile_path, COUNT(mc.movie_id) as movie_count
            FROM actors a
            JOIN movie_cast mc ON a.id = mc.actor_id
            GROUP BY a.id, a.name, a.profile_path
            ORDER BY movie_count DESC, a.name ASC
            LIMIT %s
        """
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Oyuncu Listesi Hatası: {e}")
        return []
    finally:
        cursor.close()
        conn.close()
