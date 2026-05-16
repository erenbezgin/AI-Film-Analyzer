import random
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.db_manager import get_db_connection
from utils.db_functions import (
    get_recommendations,
    add_to_watch_list,
    get_watch_list,
    get_movie_cast,
    get_actor_info_and_movies,
    get_top_actors
)
from utils.helpers import fetch_genre_sections, get_ai_related_movies
from utils.ai_engine import get_ai_chat_response, generate_gemini_text
from utils.decorators import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Kullanıcı ana sayfası - Sadece Sizin İçin ve Popüler"""
    try:
        conn = get_db_connection()
        if not conn:
            flash(
                "❌ Veritabanı bağlantısı kurulamadı. Dashboard yüklenemiyor.", "danger"
            )
            return redirect(url_for("auth.login"))

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT is_admin FROM users WHERE id = %s", (session["user_id"],)
        )
        db_user = cursor.fetchone()
        if db_user:
            session["is_admin"] = bool(db_user["is_admin"])

        recommended = get_recommendations(session["user_id"])
        genre_sections = fetch_genre_sections(cursor, genre_limit=6, movie_limit=12)

        try:
            cursor.execute(
                """
                SELECT m.id, m.title, m.vote_average, m.poster_path, m.release_date
                FROM watch_list wl
                JOIN movies m ON wl.movie_id = m.id
                WHERE wl.user_id = %s
                ORDER BY m.id DESC
                LIMIT 12
                """,
                (session["user_id"],),
            )
            continue_watching = cursor.fetchall()
        except Exception:
            continue_watching = []

        try:
            cursor.execute("""
                SELECT m.id, m.title, m.vote_average, m.poster_path, m.release_date, COUNT(r.id) AS review_hits
                FROM reviews r
                JOIN movies m ON r.movie_id = m.id
                GROUP BY m.id, m.title, m.vote_average, m.poster_path, m.release_date
                ORDER BY review_hits DESC, m.vote_average DESC
                LIMIT 10
                """)
            top_10_week = cursor.fetchall()
        except Exception:
            top_10_week = []

        try:
            cursor.execute("""
                SELECT m.id, m.title, m.vote_average, m.poster_path, m.release_date, COUNT(wl.movie_id) AS trend_score
                FROM watch_list wl
                JOIN movies m ON wl.movie_id = m.id
                GROUP BY m.id, m.title, m.vote_average, m.poster_path, m.release_date
                ORDER BY trend_score DESC, m.vote_average DESC
                LIMIT 12
                """)
            trending_now = cursor.fetchall()
        except Exception:
            trending_now = []

        if not recommended:
            cursor.execute("SELECT * FROM movies ORDER BY vote_average DESC LIMIT 15")
            recommended = cursor.fetchall()

        if not top_10_week:
            cursor.execute("""
                SELECT id, title, vote_average, poster_path, release_date
                FROM movies
                ORDER BY vote_average DESC
                LIMIT 10
                """)
            top_10_week = cursor.fetchall()

        if not trending_now:
            cursor.execute("""
                SELECT id, title, vote_average, poster_path, release_date
                FROM movies
                ORDER BY vote_average DESC
                LIMIT 12
                """)
            trending_now = cursor.fetchall()

        cursor.execute("""
            SELECT id, title, vote_average, poster_path, release_date
            FROM movies 
            WHERE LOWER(genre) LIKE '%bilim kurgu%' 
               OR LOWER(genre) LIKE '%sci-fi%' 
               OR LOWER(genre) LIKE '%science fiction%'
            ORDER BY vote_average DESC
            LIMIT 50
            """)
        sci_fi_pool = cursor.fetchall()

        hero_movie = (
            random.choice(sci_fi_pool)
            if sci_fi_pool
            else (random.choice(recommended) if recommended else None)
        )

        cursor.close()
        conn.close()

        return render_template(
            "dashboard.html",
            username=session.get("username"),
            recommendations=recommended,
            watch_list=continue_watching,
            top_10_week=top_10_week,
            trending_now=trending_now,
            genre_sections=genre_sections,
            hero_movie=hero_movie,
            is_admin=session.get("is_admin", False),
        )
    except Exception as e:
        flash(f"❌ Bir hata oluştu: {str(e)}", "danger")
        return redirect(url_for("auth.login"))


@main_bp.route("/profile")
@login_required
def profile():
    """Kullanıcı Profili ve İzleme Listesi"""
    try:
        watch_list = get_watch_list(session["user_id"])
        return render_template(
            "profile.html", username=session.get("username"), watch_list=watch_list
        )
    except Exception as e:
        flash(f"❌ Bir hata oluştu: {str(e)}", "danger")
        return redirect(url_for("main.dashboard"))


@main_bp.route("/genre/<genre_name>")
@login_required
def genre_page(genre_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        normalized_name = genre_name.replace("-", " ").strip()

        like_val = f"%{normalized_name.lower()}%"
        cursor.execute(
            """
            SELECT * FROM movies m
            WHERE LOWER(m.genre) LIKE %s
            ORDER BY m.vote_average DESC
            """,
            (like_val,),
        )
        movies = cursor.fetchall()

        if not movies and normalized_name.lower() in ("bilimkurgu", "bilim kurgu"):
            cursor.execute(
                """
                SELECT * FROM movies m
                WHERE LOWER(m.genre) LIKE %s OR LOWER(m.genre) LIKE %s OR LOWER(m.genre) LIKE %s
                ORDER BY m.vote_average DESC
                """,
                ("%bilim kurgu%", "%science fiction%", "%sci-fi%"),
            )
            movies = cursor.fetchall()
            normalized_name = "Bilim Kurgu"

        cursor.execute(
            "SELECT genre_name FROM genres WHERE LOWER(genre_name) = LOWER(%s) LIMIT 1",
            (normalized_name,),
        )
        found_genre = cursor.fetchone()
        display_name = found_genre["genre_name"] if found_genre else normalized_name.title()

        cursor.close()
        conn.close()

        return render_template("genre.html", genre_name=display_name, movies=movies)
    except Exception as e:
        flash("Tür bulunamadı veya hata oluştu.", "danger")
        return redirect(url_for("main.dashboard"))


@main_bp.route("/genre/id/<int:genre_id>")
@login_required
def genre_page_by_id(genre_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT genre_name FROM genres WHERE id = %s", (genre_id,))
        genre = cursor.fetchone()

        if not genre:
            flash("Tür bulunamadı.", "warning")
            return redirect(url_for("main.dashboard"))

        g_name = genre["genre_name"]

        if g_name.lower() in ("bilimkurgu", "bilim kurgu", "bilim-kurgu"):
            cursor.execute(
                """
                SELECT * FROM movies 
                WHERE LOWER(genre) LIKE %s OR LOWER(genre) LIKE %s OR LOWER(genre) LIKE %s
                ORDER BY vote_average DESC
                """,
                ("%bilim kurgu%", "%science fiction%", "%sci-fi%"),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM movies 
                WHERE genre LIKE %s 
                ORDER BY vote_average DESC
            """,
                (f"%{g_name}%",),
            )
        movies = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("genre.html", genre_name=g_name, movies=movies)
    except Exception as e:
        flash("Hata oluştu.", "danger")
        return redirect(url_for("main.dashboard"))


@main_bp.route("/movie/<int:movie_id>", methods=["GET", "POST"])
@login_required
def movie_detail(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        rating = request.form.get("rating")
        comment = request.form.get("comment", "").strip()
        user_id = session.get("user_id")

        if rating and rating.isdigit():
            rating = int(rating)
            if 1 <= rating <= 10:
                try:
                    cursor.execute(
                        "INSERT INTO reviews (user_id, movie_id, rating, comment) VALUES (%s, %s, %s, %s)",
                        (user_id, movie_id, rating, comment),
                    )
                    conn.commit()
                    flash("Değerlendirmeniz başarıyla eklendi!", "success")
                except Exception as e:
                    flash("Yorum eklenirken hata oluştu.", "danger")

    try:
        cursor.execute("SELECT * FROM movies WHERE id = %s", (movie_id,))
        movie = cursor.fetchone()

        if not movie:
            flash("Film bulunamadı.", "danger")
            return redirect(url_for("main.dashboard"))

        cursor.execute(
            """
            SELECT r.rating, r.comment, r.created_at, u.username
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.movie_id = %s
            ORDER BY r.created_at DESC
        """,
            (movie_id,),
        )
        reviews = cursor.fetchall()

        if reviews:
            avg_rating = sum([r["rating"] for r in reviews]) / len(reviews)
            movie["site_rating"] = round(avg_rating, 1)
        else:
            movie["site_rating"] = 0

        if movie.get("genre"):
            movie["genre_list"] = [
                g.strip() for g in movie["genre"].split(",") if g.strip()
            ]
        else:
            movie["genre_list"] = []

        cast = get_movie_cast(movie_id)

    except Exception as e:
        flash("Hata oluştu.", "danger")
        return redirect(url_for("main.dashboard"))
    finally:
        cursor.close()
        conn.close()

    return render_template("movie_detail.html", movie=movie, reviews=reviews, cast=cast)


@main_bp.route("/actors")
@login_required
def actors_list():
    actors = get_top_actors(limit=60)
    return render_template("actors_list.html", actors=actors)


@main_bp.route("/actor/<int:actor_id>")
@login_required
def actor_detail(actor_id):
    actor, movies = get_actor_info_and_movies(actor_id)
    if not actor:
        flash("Aktör bulunamadı.", "danger")
        return redirect(url_for("main.dashboard"))
    return render_template("actor.html", actor=actor, movies=movies)


@main_bp.route("/search")
@login_required
def search():
    query = request.args.get("q", "").strip()
    rating = request.args.get("rating", "")
    year = request.args.get("year", "")
    
    conn = get_db_connection()
    if not conn:
        flash("Veritabanı bağlantısı yok.", "danger")
        return redirect(url_for("main.dashboard"))
        
    cursor = conn.cursor(dictionary=True)
    
    sql = "SELECT id, title, vote_average, poster_path, release_date FROM movies WHERE 1=1"
    params = []
    
    if query:
        sql += " AND (LOWER(title) LIKE %s OR LOWER(genre) LIKE %s)"
        params.extend([f"%{query.lower()}%", f"%{query.lower()}%"])
        
    if rating and rating.isdigit():
        sql += " AND vote_average >= %s"
        params.append(float(rating))
        
    if year and year.isdigit():
        sql += " AND YEAR(release_date) = %s"
        params.append(int(year))
        
    sql += " ORDER BY vote_average DESC LIMIT 50"
    
    try:
        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()
    except Exception as e:
        results = []
        flash(f"Arama hatası: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
        
    return render_template("search.html", results=results, query=query)


@main_bp.route("/add-to-watchlist/<int:movie_id>", methods=["POST"])
@login_required
def add_watchlist(movie_id):
    try:
        result = add_to_watch_list(session["user_id"], movie_id)
        if result:
            flash("✅ Film izleme listesine eklendi!", "success")
        else:
            flash("⚠️ Film zaten izleme listesinde!", "info")
    except Exception as e:
        flash(f"❌ Hata: {str(e)}", "danger")

    return redirect(request.referrer or url_for("main.dashboard"))


@main_bp.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    response = None

    if request.method == "POST":
        user_question = request.form.get("question", "").strip()

        if not user_question:
            if request.headers.get("Accept") == "application/json":
                return jsonify({"response": "Lütfen bir soru sorunuz!"})
            flash("❌ Lütfen bir soru sorunuz!", "danger")
        else:
            try:
                response = get_ai_chat_response(user_question)
                related_movies = get_ai_related_movies(user_question, limit=8)
                if response and response.strip().lower().startswith(
                    "hata: ai kotasi dolu"
                ):
                    fallback_lines = []
                    for m in related_movies[:5]:
                        title = m.get("title", "Film")
                        rating = m.get("vote_average", 0)
                        fallback_lines.append(f"- {title} (⭐ {rating})")
                    if fallback_lines:
                        response = (
                            f"{response}\n\nBu arada beklerken veritabanindan senin icin secilen filmler:\n"
                            + "\n".join(fallback_lines)
                        )
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"response": response, "movies": related_movies})
            except Exception as e:
                error_msg = f"AI Hata: {str(e)}"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"response": error_msg}), 500
                flash(f"❌ {error_msg}", "danger")

    return render_template("chat.html", response=response, username=session["username"])


@main_bp.route("/api/analyze/<int:movie_id>")
@login_required
def analyze_film(movie_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Veritabanı bağlantısı başarısız"}), 500

        cursor = conn.cursor(dictionary=True)

        result = None
        try:
            query = "SELECT analysis_tag, ai_commentary FROM ai_insights WHERE movie_id = %s"
            cursor.execute(query, (movie_id,))
            result = cursor.fetchone()
        except Exception:
            pass

        if result:
            cursor.close()
            conn.close()
            return jsonify(
                {"tag": result["analysis_tag"], "analysis": result["ai_commentary"]}
            )
        else:
            cursor.execute(
                "SELECT title, overview FROM movies WHERE id = %s", (movie_id,)
            )
            movie_info = cursor.fetchone()

            cursor.close()
            conn.close()

            if not movie_info:
                return jsonify({"error": "Film bulunamadı."}), 404

            title = movie_info.get("title", "")
            overview = movie_info.get("overview", "")

            prompt = f"'{title}' adlı film hakkında kısaca profesyonel bir sinema eleştirisi yap. Filmin özeti: {overview}. Lütfen cevabını 2-3 cümle ile sınırla."
            response = generate_gemini_text(prompt)

            if response and response.strip().lower().startswith("hata: ai kotasi dolu"):
                snippet = (overview or "").strip()
                if len(snippet) > 420:
                    snippet = snippet[:420].rstrip() + "..."
                fallback_analysis = (
                    "AI kotasi gecici olarak dolu. Bu sirada filmin ozetinden hizli bir degerlendirme:\n\n"
                    f"{snippet if snippet else 'Film ozeti mevcut degil.'}"
                )
                return jsonify({"tag": "Gecici Ozet", "analysis": fallback_analysis})

            if not response or response.strip().lower().startswith("hata:"):
                return (
                    jsonify(
                        {
                            "error": response
                            or "AI analizi şu an kullanılamıyor, lütfen daha sonra tekrar deneyin."
                        }
                    ),
                    500,
                )

            return jsonify({"tag": "Hızlı Analiz", "analysis": response})
    except Exception as e:
        return jsonify({"error": f"Analiz hatası: {str(e)}"}), 500
