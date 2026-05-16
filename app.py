import os
import sys
from flask import Flask, render_template, session
from dotenv import load_dotenv
from utils.db_manager import get_db_connection

# .env dosyasındaki değişkenleri yükle
load_dotenv()

def _configure_console_utf8():
    """Windows'ta konsol yazdiriminde Unicode hatalarını azaltmak için stdout/stderr UTF-8."""
    for stream in (getattr(sys, "stdout", None), getattr(sys, "stderr", None)):
        if stream is None:
            continue
        reconf = getattr(stream, "reconfigure", None)
        if callable(reconf):
            try:
                reconf(encoding="utf-8", errors="replace")
            except Exception:
                pass

_configure_console_utf8()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")

# Blueprint'leri import et ve kaydet
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.main import main_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(main_bp)


@app.context_processor
def inject_nav_genres():
    """Navbar için kategorileri referans 'genres' tablosundan doldurur."""
    if "user_id" not in session:
        return {"nav_genres": []}

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, genre_name FROM genres ORDER BY genre_name ASC LIMIT 10"
        )
        nav_genres = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"nav_genres": nav_genres}
    except Exception:
        return {"nav_genres": []}

@app.route("/")
def index():
    """Anasayfa - Eğer login ise dashboard'a, değilse auth.login e yönlendir"""
    if "user_id" in session:
        from flask import redirect, url_for
        return redirect(url_for("main.dashboard"))
    
    # Eskiden anasayfada genre_sections çekiliyordu. Artık doğrudan login'e yönlendiriyoruz veya
    # basit bir index page gösteriyoruz. Biz auth.login'e yönlendirelim veya dashboard'a.
    from flask import redirect, url_for
    return redirect(url_for("auth.login"))


@app.errorhandler(404)
def page_not_found(error):
    """404 Hatası"""
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(error):
    """500 Hatası"""
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)
