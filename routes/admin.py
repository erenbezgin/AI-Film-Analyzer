import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.db_manager import get_db_connection
from utils.db_functions import get_users_list, save_movie_to_db, update_movie_genres
from utils.ai_engine import get_quota_status
from utils.ai_processor import analyze_advanced_insight
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/")
@admin_required
def dashboard():
    """Admin kontrol paneli"""
    try:
        users_list = get_users_list()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as count FROM movies")
        movies_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM reviews")
        reviews_count = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT r.id, r.rating, r.comment, r.created_at, u.username, m.title as movie_title
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            JOIN movies m ON r.movie_id = m.id
            ORDER BY r.created_at DESC LIMIT 20
        """)
        recent_reviews = cursor.fetchall()

        cursor.execute("""
            SELECT id, title, vote_average, release_date
            FROM movies
            ORDER BY id DESC
            LIMIT 5
            """)
        recent_added_movies = cursor.fetchall()

        pending_analysis_count = 0
        try:
            cursor.execute("""
                SELECT COUNT(*) AS count
                FROM movies m
                LEFT JOIN ai_insights ai ON ai.movie_id = m.id
                WHERE ai.movie_id IS NULL OR ai.ai_commentary IS NULL OR ai.ai_commentary = ''
                """)
            pending_analysis_count = cursor.fetchone()["count"]
        except Exception:
            pending_analysis_count = 0

        cursor.execute("""
            SELECT r.id, u.username, m.title AS movie_title, r.rating, r.comment, r.created_at
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            JOIN movies m ON r.movie_id = m.id
            WHERE r.rating <= 3 OR LENGTH(TRIM(COALESCE(r.comment, ''))) < 5
            ORDER BY r.created_at DESC
            LIMIT 6
            """)
        problematic_reviews = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "admin_dashboard.html",
            username=session["username"],
            users_count=len(users_list) if users_list else 0,
            movies_count=movies_count,
            reviews_count=reviews_count,
            users=users_list or [],
            recent_reviews=recent_reviews or [],
            recent_added_movies=recent_added_movies or [],
            pending_analysis_count=pending_analysis_count,
            problematic_reviews=problematic_reviews or [],
            ai_quota_status=get_quota_status(),
        )
    except Exception as e:
        flash(f"❌ Hata: {str(e)}", "danger")
        return redirect(url_for("main.dashboard"))


@admin_bp.route("/make_admin/<int:user_id>")
@admin_required
def make_admin(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_admin = 1 WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Kullanıcı başarıyla admin yapıldı.", "success")
    except Exception as e:
        flash(f"Yetkilendirme hatası: {str(e)}", "danger")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/delete_user/<int:user_id>")
@admin_required
def delete_user(user_id):
    if user_id == session.get("user_id"):
        flash("Kendinizi silemezsiniz!", "danger")
        return redirect(url_for("admin.dashboard"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM watch_list WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM reviews WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Kullanıcı silindi.", "success")
    except Exception as e:
        flash(f"Silme hatası: {str(e)}", "danger")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/user_list/<int:user_id>")
@admin_required
def admin_user_list(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
        user_info = cursor.fetchone()

        if not user_info:
            flash("Kullanıcı bulunamadı.", "warning")
            return redirect(url_for("admin.dashboard"))

        cursor.execute(
            """
            SELECT m.* 
            FROM watch_list w
            JOIN movies m ON w.movie_id = m.id
            WHERE w.user_id = %s
            ORDER BY w.added_at DESC
        """,
            (user_id,),
        )
        user_movies = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "admin_user_list.html", target_user=user_info, movies=user_movies
        )
    except Exception as e:
        flash(f"Liste yüklenirken hata oluştu: {str(e)}", "danger")
        return redirect(url_for("admin.dashboard"))


@admin_bp.route("/delete_review/<int:review_id>")
@admin_required
def delete_review(review_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Yorum silindi.", "success")
    except Exception as e:
        flash(f"Silme hatası: {str(e)}", "danger")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/add_movie", methods=["POST"])
@admin_required
def admin_add_movie():
    tmdb_id = request.form.get("tmdb_id")
    if not tmdb_id:
        flash("TMDB ID boş olamaz!", "warning")
        return redirect(url_for("admin.dashboard"))

    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={os.getenv('TMDB_API_KEY')}&language=tr-TR"
        response = requests.get(url)

        if response.status_code == 200:
            movie = response.json()
            movie_data = {
                "id": movie["id"],
                "title": movie.get("title") or movie.get("original_title", "Bilinmeyen"),
                "overview": movie.get("overview", "Açıklama bulunamadı."),
                "release_date": movie.get("release_date"),
                "vote_average": movie.get("vote_average", 0),
                "poster_path": movie.get("poster_path"),
                "backdrop_path": movie.get("backdrop_path"),
            }
            if movie_data["release_date"] and movie_data["poster_path"]:
                save_movie_to_db(movie_data)
                genre_ids = [g["id"] for g in movie.get("genres", [])]
                update_movie_genres(movie_data["id"], genre_ids)

                # Yeni: Oyuncu kadrosunu da çek ve kaydet
                credits_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={os.getenv('TMDB_API_KEY')}&language=tr-TR"
                credits_response = requests.get(credits_url)
                if credits_response.status_code == 200:
                    cast_list = credits_response.json().get("cast", [])[:10]
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    for actor in cast_list:
                        actor_id = actor.get("id")
                        actor_name = actor.get("name")
                        character_name = actor.get("character", "")
                        profile_path = actor.get("profile_path", "")
                        try:
                            cursor.execute("INSERT IGNORE INTO actors (id, name, profile_path) VALUES (%s, %s, %s)", (actor_id, actor_name, profile_path))
                            cursor.execute("INSERT IGNORE INTO movie_cast (movie_id, actor_id, character_name) VALUES (%s, %s, %s)", (tmdb_id, actor_id, character_name))
                        except Exception:
                            pass
                    conn.commit()
                    cursor.close()
                    conn.close()

                flash(f"🎬 '{movie_data['title']}' ve oyuncu kadrosu başarıyla eklendi!", "success")
            else:
                flash("Filmin çıkış tarihi veya afişi eksik olduğu için eklenmedi.", "warning")
        else:
            flash("TMDB'de böyle bir film bulunamadı.", "danger")

    except Exception as e:
        flash(f"Film eklenirken hata oluştu: {str(e)}", "danger")

    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/delete_movie", methods=["POST"])
@admin_required
def admin_delete_movie():
    movie_id = request.form.get("movie_id")
    if not movie_id:
        flash("Film ID boş olamaz!", "warning")
        return redirect(url_for("admin.dashboard"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM movie_genre_map WHERE movie_id = %s", (movie_id,))
        except Exception:
            pass
        cursor.execute("DELETE FROM movie_cast WHERE movie_id = %s", (movie_id,))
        cursor.execute("DELETE FROM watch_list WHERE movie_id = %s", (movie_id,))
        cursor.execute("DELETE FROM reviews WHERE movie_id = %s", (movie_id,))

        cursor.execute("DELETE FROM movies WHERE id = %s", (movie_id,))
        deleted_count = cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        if deleted_count > 0:
            flash("🗑️ Film ve bağlı tüm veriler sistemden silindi.", "success")
        else:
            flash("Veritabanında böyle bir film bulunamadı.", "warning")

    except Exception as e:
        flash(f"Silme işlemi sırasında hata: {str(e)}", "danger")

    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/analyze", methods=["GET", "POST"])
@admin_required
def admin_analyze():
    """Admin - Gemini ile film analizi"""
    if request.method == "POST":
        try:
            analyze_advanced_insight()
            flash("✅ Film analizi tamamlandı!", "success")
        except Exception as e:
            flash(f"❌ Analiz Hatası: {str(e)}", "danger")

        return redirect(url_for("admin.dashboard"))

    return render_template("admin_analyze.html", username=session["username"])
