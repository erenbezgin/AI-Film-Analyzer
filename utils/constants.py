"""
Proje genelinde kullanılan sabit değerler ve yardımcı fonksiyonlar.
"""

# Platformda gösterilmeyecek film türleri (küçük harf)
BLOCKED_GENRES = ["romantik", "romance"]


def blocked_genre_sql(alias=None):
    """
    Engellenen türleri filtreleyen SQL AND koşulu döner.
    Parameterize değil; değerler geliştirici tanımlı sabitlerdir.

    Args:
        alias: Tablo alias'ı (örn: 'm' → LOWER(m.genre) NOT LIKE ...)
               None ise LOWER(genre) NOT LIKE ... şeklinde üretilir.

    Returns:
        str: SQL AND koşulu, örn:
             "LOWER(m.genre) NOT LIKE '%romantik%' AND LOWER(m.genre) NOT LIKE '%romance%'"
    """
    col = f"LOWER({alias}.genre)" if alias else "LOWER(genre)"
    return " AND ".join([f"{col} NOT LIKE '%{g}%'" for g in BLOCKED_GENRES])
