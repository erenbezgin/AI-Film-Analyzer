from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.db_manager import get_db_connection
from utils.db_functions import login_user, register_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Giriş sayfası"""
    if request.method == "POST":
        test_conn = get_db_connection()
        if not test_conn:
            flash(
                "❌ Veritabanı bağlantısı kurulamadı. Lütfen DB ayarlarınızı kontrol edin.",
                "danger",
            )
            return render_template("login.html")
        try:
            test_conn.close()
        except Exception:
            pass

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("❌ Kullanıcı adı ve şifre zorunludur!", "danger")
            return redirect(url_for("auth.login"))

        user = login_user(username, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = user["is_admin"]
            flash(f"✅ Hoşgeldin {user['username']}!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("❌ Hatalı kullanıcı adı veya şifre!", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Kayıt sayfası"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        password_confirm = request.form.get("password_confirm", "").strip()

        if not username or not email or not password:
            flash("❌ Tüm alanları doldurunuz!", "danger")
            return redirect(url_for("auth.register"))

        if password != password_confirm:
            flash("❌ Şifreler eşleşmiyor!", "danger")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("❌ Şifre en az 6 karakter olmalıdır!", "danger")
            return redirect(url_for("auth.register"))

        result = register_user(username, email, password)
        if result:
            flash("✅ Kayıt başarılı! Şimdi giriş yapabilirsiniz.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("❌ Bu kullanıcı adı veya email zaten kayıtlı!", "danger")

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    """Çıkış"""
    session.clear()
    flash("👋 Çıkış yaptınız. Hoşça kalınız!", "info")
    return redirect(url_for("auth.login"))
