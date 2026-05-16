from functools import wraps
from flask import session, flash, redirect, url_for
from utils.db_manager import get_db_connection

def login_required(f):
    """Giriş yapılmış kullanıcı kontrolü"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("⚠️ Lütfen önce giriş yapınız!", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Admin kullanıcı kontrolü"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("⚠️ Lütfen önce giriş yapınız!", "warning")
            return redirect(url_for("auth.login"))

        # Anlık veritabanı kontrolü (Kullanıcıya sonradan yetki verildiyse görebilsin diye)
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT is_admin FROM users WHERE id = %s", (session["user_id"],)
            )
            db_user = cursor.fetchone()
            cursor.close()
            conn.close()

            if db_user:
                session["is_admin"] = bool(db_user["is_admin"])
        except Exception:
            pass

        if not session.get("is_admin"):
            flash("❌ Bu sayfaya erişim yetkiniz yok!", "danger")
            return redirect(url_for("main.dashboard"))

        return f(*args, **kwargs)

    return decorated_function
