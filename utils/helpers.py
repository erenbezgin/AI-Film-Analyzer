from utils.db_manager import get_db_connection

def fetch_genre_sections(cursor, genre_limit=8, movie_limit=12):
    """Tür isimlerini genres tablosundan alıp, filmleri movies tablosunda LIKE ile hızlıca arar."""
    # Menü için referans tablosundan türleri çekiyoruz
    cursor.execute("SELECT id, genre_name FROM genres LIMIT %s", (genre_limit,))
    genres = cursor.fetchall()

    genre_sections = []
    for g in genres:
        g_name = g["genre_name"]
        # JOIN kullanmadan, direkt yeni genre sütununda arama yapıyoruz
        cursor.execute(
            """
            SELECT id, title, vote_average, poster_path, release_date
            FROM movies 
            WHERE genre LIKE %s 
            ORDER BY vote_average DESC LIMIT %s
        """,
            (f"%{g_name}%", movie_limit),
        )

        movies = cursor.fetchall()
        if movies:
            genre_sections.append({"id": g["id"], "name": g_name, "movies": movies})

    return genre_sections


def get_ai_related_movies(user_question, limit=8):
    """Kullanıcının sorusuna göre ilgili filmleri getirir."""
    keyword_map = {
        "bilim kurgu": ["bilim kurgu", "science fiction", "sci-fi"],
        "aksiyon": ["aksiyon", "action"],
        "komedi": ["komedi", "comedy"],
        "dram": ["dram", "drama"],
        "korku": ["korku", "horror"],
        "romantik": ["romantik", "romance"],
        "animasyon": ["animasyon", "animation"],
        "macera": ["macera", "adventure"],
        "gerilim": ["gerilim", "thriller"],
        "suç": ["suç", "suc", "crime"],
        "gizem": ["gizem", "mystery"],
        "fantastik": ["fantastik", "fantasy"],
        "belgesel": ["belgesel", "documentary"],
    }

    normalized = (user_question or "").lower().strip()
    matched_aliases = []
    for aliases in keyword_map.values():
        if any(alias in normalized for alias in aliases):
            matched_aliases.extend(aliases)

    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)

    try:
        if matched_aliases:
            like_conditions = " OR ".join(
                ["LOWER(genre) LIKE %s"] * len(matched_aliases)
            )
            query = f"""
                SELECT id, title, vote_average, release_date, poster_path
                FROM movies
                WHERE {like_conditions}
                ORDER BY vote_average DESC
                LIMIT %s
            """
            params = tuple(f"%{alias.lower()}%" for alias in matched_aliases) + (limit,)

            cursor.execute(query, params)
            movies = cursor.fetchall()
            if movies:
                return movies

        cursor.execute(
            """
            SELECT id, title, vote_average, release_date, poster_path
            FROM movies
            WHERE title LIKE %s
            ORDER BY vote_average DESC
            LIMIT %s
            """,
            (f"%{user_question.strip()}%", limit),
        )
        movies = cursor.fetchall()
        if movies:
            return movies

        cursor.execute(
            """
            SELECT id, title, vote_average, release_date, poster_path
            FROM movies
            ORDER BY vote_average DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"AI Film Bulma Hatası: {e}")
        return []
    finally:
        cursor.close()
        conn.close()
