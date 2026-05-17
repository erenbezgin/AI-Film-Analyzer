# 🧠 3. Kişi — Sorumluluk & Dosya Raporu
**Veritabanı, Yapay Zeka (AI) ve Veri İşleme Sorumlusu**

---

## 📁 Sorumlu Olduğun Dosyalar

```
AI-Film-Analyzer/
├── utils/
│   ├── db_manager.py       ✅ Senin
│   ├── db_functions.py     ✅ Senin
│   ├── ai_engine.py        ✅ Senin
│   ├── ai_processor.py     ✅ Senin
│   ├── helpers.py          ✅ Senin
│   └── constants.py        ✅ Senin
├── scripts/
│   ├── main_seeder.py      ✅ Senin
│   └── check_db.py         ✅ Senin
└── .env                    ✅ Senin (API key yönetimi)
```

---

## 🗄️ utils/db_manager.py — Veritabanı Bağlantısı

**Ne yapar:** MySQL bağlantısını `.env` dosyasından okuyarak kurar.

| Fonksiyon | Açıklama |
|---|---|
| `get_db_connection()` | `.env` ayarlarıyla MySQL bağlantısı açar, hata olursa XAMPP varsayılanını dener |
| `test_db()` | Bağlantıyı test eder, konsola sonuç yazar |

> [!NOTE]
> Tüm diğer utils dosyaları bu modülü import eder. Bağlantı burada yönetilir.

---

## 📋 utils/db_functions.py — CRUD İşlemleri

**Ne yapar:** Tüm veritabanı okuma/yazma fonksiyonlarını içerir. Backend (2. kişi) bu fonksiyonları çağırır.

| Fonksiyon | Açıklama |
|---|---|
| `search_movies(title, genre, min_rating, year)` | Dinamik SQL ile film arama |
| `save_movie_to_db(movie)` | TMDB'den gelen veriyi `movies` tablosuna yazar |
| `update_movie_genres(movie_id, genre_ids)` | Film türlerini günceller |
| `add_to_watch_list(user_id, movie_id)` | Kullanıcı izleme listesine film ekler |
| `get_recommendations(user_id)` | İzleme geçmişine göre film önerir |
| `register_user(username, email, password)` | Yeni kullanıcı kaydeder (SHA-256 hash) |
| `login_user(username, password)` | Giriş doğrular (SHA-256 hash karşılaştırması) |
| `get_watch_list(user_id)` | Kullanıcının tüm izleme listesini çeker |
| `get_users_list()` | Admin paneli için tüm kullanıcıları listeler |
| `get_movie_cast(movie_id)` | Filmin oyuncu kadrosunu getirir |
| `get_actor_info_and_movies(actor_id)` | Aktör bilgisi + filmografisini getirir |
| `get_top_actors(limit)` | En çok filmde oynayan oyuncuları listeler |

> [!IMPORTANT]
> Bu dosyadaki fonksiyonlar, 2. kişinin routes/ dosyalarında doğrudan import edilir. Fonksiyon adlarını değiştirirsen 2. kişiye haber ver.

---

## 🤖 utils/ai_engine.py — Gemini API Entegrasyonu

**Ne yapar:** Google Gemini API ile iletişimi yönetir. Tüm AI çağrıları buradan geçer.

| Fonksiyon | Açıklama |
|---|---|
| `generate_gemini_text(prompt)` | Gemini'ye prompt gönderir, metin döner; kota doluysa hata mesajı döner |
| `get_ai_movie_analysis(movie_title)` | Film başlığına göre 3 cümlelik analiz üretir |
| `get_ai_recommendation(user_input)` | Kullanıcı girdisine göre 3 film önerir |
| `get_ai_chat_response(question)` | Sohbet sorusuna profesyonel yanıt üretir |
| `get_quota_status()` | API kota durumunu `green/yellow/red` olarak döner |
| `_extract_text(resp)` | Gemini yanıtından güvenli metin çıkarımı (iç yardımcı) |

> [!NOTE]
> API anahtarı `.env` dosyasındaki `GEMINI_API_KEY` değişkeninden okunur. Kota aşımında otomatik bekleme mekanizması (`_next_retry_ts`) vardır.

---

## ⚙️ utils/ai_processor.py — AI Analiz İşleyicisi

**Ne yapar:** Veritabanındaki filmleri sırayla Gemini'ye gönderir, üretilen analizi `ai_insights` tablosuna kaydeder.

| Fonksiyon | Açıklama |
|---|---|
| `analyze_advanced_insight()` | DB'de henüz analiz edilmemiş 1 film alır → Gemini prompt üretir → `ETİKET` ve `YORUM` parse eder → `ai_insights` tablosuna yazar |

> [!TIP]
> Bu script tek seferde 1 film analiz eder. Toplu analiz için bir döngüyle çalıştırılabilir veya otomatik zamanlayıcı (cron) kurulabilir.

---

## 🛠️ utils/helpers.py — Yardımcı Fonksiyonlar

**Ne yapar:** Birden fazla modülde kullanılan genel amaçlı fonksiyonlar.

| Fonksiyon | Açıklama |
|---|---|
| `fetch_genre_sections(cursor, genre_limit, movie_limit)` | Dashboard için türlere göre film grupları getirir; engellenen türleri filtreler |
| `get_ai_related_movies(user_question, limit)` | Kullanıcı sorusundaki anahtar kelimelere göre DB'den ilgili filmleri getirir |

---

## 🔒 utils/constants.py — Sabitler

**Ne yapar:** Proje genelinde kullanılan sabit değerleri ve SQL yardımcısını barındırır.

| Öğe | Açıklama |
|---|---|
| `BLOCKED_GENRES` | Platformda gösterilmeyecek tür listesi: `["romantik", "romance"]` |
| `blocked_genre_sql(alias)` | Engellenen türleri filtreleyen SQL `AND` koşulu üretir |

> [!WARNING]
> Bu dosyayı tüm utils ve routes modülleri kullanır. `BLOCKED_GENRES` listesini değiştirirsen tüm sorgular etkilenir.

---

## 🌱 scripts/main_seeder.py — TMDB Veri Çekici

**Ne yapar:** TMDB API'sinden 5000 film + oyuncu kadrosu çekerek veritabanını doldurur.

**Çalıştırma:**
```bash
python scripts/main_seeder.py
```

**Ne Yapar (Adım Adım):**
1. TMDB `popular` endpoint'inden 250 sayfa film çeker
2. Her film için tür isimlerini Türkçeye çevirir (`TMDB_GENRES` sözlüğü)
3. `movies` tablosuna `INSERT IGNORE` ile yazar
4. Her film için `/credits` endpoint'inden oyuncu kadrosunu çeker
5. `actors` ve `movie_cast` tablolarına yazar
6. Ham JSON'ı `api_raw_data` tablosuna arşivler
7. API ban yememek için her istek arasında `0.1s` bekler

> [!CAUTION]
> `.env` dosyasında `TMDB_API_KEY` tanımlı olmalı. Script yaklaşık **15–20 dakika** sürer, terminali kapatma!

---

## 🔍 scripts/check_db.py — Bağlantı Test Scripti

**Ne yapar:** MySQL bağlantısının çalışıp çalışmadığını hızlıca test eder.

```bash
python scripts/check_db.py
```

---

## 🗃️ Veritabanı Tabloları (Senin Sorumluluğunda)

| Tablo | Açıklama |
|---|---|
| `movies` | Film bilgileri (id, title, overview, genre, poster_path, vote_average, release_date) |
| `actors` | Oyuncu bilgileri (id, name, profile_path) |
| `movie_cast` | Film-Oyuncu ilişki tablosu (movie_id, actor_id, character_name) |
| `watch_list` | Kullanıcı izleme listesi (user_id, movie_id) |
| `reviews` | Kullanıcı yorumları (user_id, movie_id, rating, comment) |
| `genres` | Tür listesi (id, genre_name) |
| `ai_insights` | AI analiz sonuçları (movie_id, analysis_tag, ai_commentary) |
| `api_raw_data` | TMDB'den gelen ham JSON arşivi (movie_id, raw_json) |

---

## 📌 .env Dosyası — API Anahtarları

Senin yönetiminde olan ortam değişkenleri:

```env
GEMINI_API_KEY=...       # Google Gemini API
TMDB_API_KEY=...         # The Movie Database API
GEMINI_MODEL=gemini-2.5-flash

DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=film_arsivi_db
```

---

## ✅ Özet Görev Listesi

- [ ] `db_manager.py` — Bağlantı kararlılığını sağla
- [ ] `db_functions.py` — CRUD fonksiyonlarını genişlet / hataları yakala
- [ ] `ai_engine.py` — Gemini prompt kalitesini iyileştir, kota yönetimini güçlendir
- [ ] `ai_processor.py` — Toplu analiz için döngü veya cron desteği ekle
- [ ] `helpers.py` — Yeni yardımcı fonksiyonlar ekle (gerekirse)
- [ ] `constants.py` — Sabit listesini güncel tut
- [ ] `scripts/main_seeder.py` — İlave veri veya TMDB endpoint desteği
- [ ] `scripts/check_db.py` — Tablo varlık kontrolü de eklenebilir
