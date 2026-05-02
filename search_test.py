from utils.db_functions import search_movies

# Filtreleri kaldırıyoruz, sadece en yüksek puanlı ilk 10 filmi getirsin
results = search_movies()

if not results:
    print(
        "⚠️ Veritabanından film dönmedi kanka. Veritabanı bağlantısını veya tablo isimlerini kontrol etmelisin."
    )
else:
    print(f"✅ Toplam {len(results)} film bulundu. İşte ilk 10 tanesi:\n")
    for movie in results[:10]:  # Sadece ilk 10 tanesini terminale basalım
        print(
            f"🎬 {movie['title']} - Puan: {movie['vote_average']} - Türler: {movie.get('genres', 'Yok')}"
        )
