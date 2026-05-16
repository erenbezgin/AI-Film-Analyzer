from utils.db_functions import login_user


def start_app():
    print("\n" + "=" * 30)
    print("🎬  AI FILM ANALYZER - LOGIN")
    print("=" * 30)

    # Kullanıcıdan giriş bilgilerini alıyoruz
    username = input("👤 Username: ")
    password = input("🔑 Password: ")

    # DB fonksiyonumuzu çağırıyoruz
    user = login_user(username, password)

    if user:
        # user['is_admin'] artık bir bool (True/False) gibi davranıyor
        is_admin = user["is_admin"]

        print(f"\n✅ Giriş başarılı! Hoş geldin, {user['username']}.")

        if is_admin:
            print("\n" + "!" * 35)
            print("🛠️  YÖNETİCİ (ADMIN) PANELİ AÇILIYOR")
            print("!" * 35)
            print("- [1] Film Ekle/Düzenle/Sil")
            print("- [2] Kullanıcı Yönetimi")
            print("- [3] Sistem İstatistiklerini Gör")
            print("- [0] Çıkış Yap")
        else:
            print("\n" + "-" * 35)
            print("👤  KULLANICI PROFİL SAYFASI")
            print("-" * 35)
            print("- [1] İzleme Listeme Git")
            print("- [2] Yeni Film Keşfet (AI Önerileri)")
            print("- [3] Film Ara")
            print("- [0] Çıkış Yap")

    else:
        print("\n❌ Hata: Kullanıcı adı veya şifre yanlış! Lütfen tekrar dene.")


if __name__ == "__main__":
    while True:
        start_app()
        secim = input("\nTekrar denemek ister misin? (e/h): ").lower()
        if secim != "e":
            print("Görüşürüz kanka!")
            break
