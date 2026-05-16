from utils.db_functions import register_user, add_to_watch_list

# 1. Kendimizi kaydedelim
print("🚀 Kullanıcı kaydı deneniyor...")
success = register_user("ErenBezgin", "eren@email.com", "sifre123")

if success:
    print("👤 Kullanıcı başarıyla oluşturuldu!")
    # 2. Listemize bir film ekleyelim (ID'si 1 olan filmi varsayıyoruz)
    # user_id genelde 1 olur çünkü ilk kaydolan sensin
    add_to_watch_list(1, 155)  # 155 Dark Knight falan olabilir, 1500 filmden birini seç
else:
    print("⚠️ Kayıt başarısız (Belki bu kullanıcı zaten var?)")
from utils.db_functions import get_recommendations

print("\n🤖 Senin için seçtiğimiz bazı filmler:")
recs = get_recommendations(user_id=1)
for r in recs:
    print(f"🌟 {r['title']} (Puan: {r['vote_average']})")
