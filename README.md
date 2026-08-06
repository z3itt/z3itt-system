# 🤖 Z 3 İ T T Sistem Bot

Gelişmiş, modern ve tamamen Slash Command (Eğik Çizgi Komutları) altyapısına sahip Discord botu. Sunucunuzu daha güvenli, eğlenceli ve etkileşimli hale getirmek için tasarlanmıştır. Güçlü moderasyon araçlarından, detaylı ekonomi sistemine ve dinamik ses/seviye özelliklerine kadar geniş bir yelpazede hizmet sunar.

---

## ✨ Öne Çıkan Özellikler

- **🛡️ Gelişmiş Moderasyon:** Kapsamlı sunucu yönetimi, otomatik ceza sistemleri (spam koruması, vb.), hızlı rol yönetimi ve toplu işlem yetenekleri.
- **💰 Kapsamlı Ekonomi Sistemi:** Kullanıcıların bakiye kazanıp harcayabileceği eğlenceli şans oyunları (Sweet Bonanza, Blackjack, Slot vb.) ve günlük ödüller.
- **🎙️ Gelişmiş Ses Sistemleri:** Özel geçici ses odaları, sesli kanalda geçirilen süreyi takip etme ve detaylı ses sıralaması.
- **📈 Seviye (Level) Sistemi:** Kullanıcıların sohbet aktifliğine göre seviye atlaması ve belirli seviyelere ulaştıklarında otomatik rol kazanmaları.
- **🛡️ Koruma & Güvenlik:** Reklam engelleme, beyaz liste (whitelist) yönetimi, kanal/rol/webhook limit korumaları ve davet (invite) takibi.
- **💾 Yedekleme (Backup):** Sunucu düzenini yedekleyebilme özellikleri.
- **⚡ Modern Altyapı:** `discord.py` kütüphanesi kullanılarak, tamamen etkileşimli (Interaction) slash komutlarına migrate edilmiştir.

---

## 🛠️ Komutlar ve Kullanımları

Sistem içerisindeki tüm komutlar kategorilere ayrılmıştır. Aşagıda kullanabileceğiniz tüm Slash (`/`) komutlarının listesi bulunmaktadır:

### 🛡️ Moderasyon Komutları (`/mod`)
Sunucu düzenini sağlamak için yetkililerin kullanımına sunulan araçlar.
- `/mod ban <kullanıcı> [sebep]` : Belirtilen kullanıcıyı sunucudan yasaklar.
- `/mod kick <kullanıcı> [sebep]` : Belirtilen kullanıcıyı sunucudan atar.
- `/mod unban <kullanıcı_id> [sebep]` : Yasaklanan kullanıcının yasağını kaldırır.
- `/mod sustur <kullanıcı> <süre> [sebep]` : Kullanıcıyı geçici veya kalıcı olarak zaman aşımına (timeout) uğratır.
- `/mod susturkaldir <kullanıcı>` : Kullanıcının zaman aşımını kaldırır.
- `/mod temizle <miktar>` : Kanaldaki belirtilen miktarda mesajı siler.
- `/mod clearall` : Tüm sohbet geçmişini temizlemek için özel toplu silme işlemi.
- `/mod rolver <kullanıcı> <rol>` : Belirtilen kullanıcıya rol verir.
- `/mod rolal <kullanıcı> <rol>` : Belirtilen kullanıcıdan rol alır.
- `/mod rolverall <rol>` : Sunucudaki uygun olan tüm kullanıcılara belirtilen rolü verir.

### 💰 Ekonomi ve Eğlence Komutları (`/ekonomi`)
Kullanıcıların eğlenmesi ve kendi aralarında rekabet etmesi için ekonomi oyunları.
- `/ekonomi bakiye [kullanıcı]` : Sizin veya belirtilen kullanıcının mevcut bakiyesini gösterir.
- `/ekonomi daily` : Günlük bakiye ödülünüzü almanızı sağlar.
- `/ekonomi gonder <kullanıcı> <miktar>` : Başka bir kullanıcıya para transferi yaparsınız.
- `/ekonomi soy <kullanıcı>` : Başka bir kullanıcının bakiyesini çalmayı denersiniz.
- `/ekonomi coinflip <miktar>` : Yazı/tura oyunu oynayarak bahsi ikiye katlama şansı.
- `/ekonomi slot <miktar>` : Klasik slot makinesi oyunu.
- `/ekonomi sweetbonanza <miktar>` : Eğlenceli çark ve kazanç katlama oyunu.
- `/ekonomi blackjack <miktar>` : Dağıtıcıya karşı oynanan popüler iskambil oyunu (21).

### 🎙️ Ses ve Geçici Oda Komutları (`/ses`)
Özel ses kanalları oluşturma ve istatistik takip araçları.
- `/ses gir` : Seste olan kullanıcının durumunu loglar/görüntüler.
- `/ses cik` : Sesten çıkış durumları ile ilgili işlem yapar.
- `/ses sure [kullanıcı]` : Sesli kanallarda toplam ne kadar vakit geçirdiğinizi gösterir.
- `/ses siralama` : Sunucudaki en çok seste duran kullanıcıların liderlik tablosunu gösterir.
- `/ses kilit` : Sahip olduğunuz geçici ses odasını başkalarına kilitler.
- `/ses kilitac` : Kilitli olan geçici ses odanızı herkese veya birisine açar.
- `/ses cek <kullanıcı>` : Belirtilen kullanıcıyı bulunduğunuz ses kanalına çeker.

### 👑 Yönetim ve Admin Komutları (`/admin`)
Sadece üst düzey yetkililerin kullanabileceği bot ayarları ve ekonomi kontrolü.
- `/admin beyazliste <kullanıcı>` : Güvenlik sistemlerinden muaf tutulacak kullanıcıyı beyaz listeye ekler.
- `/admin beyazlisteliste` : Beyaz listedeki kullanıcıları gösterir.
- `/admin parabas <kullanıcı> <miktar>` : Sınırsız bakiye oluşturarak belirtilen kişiye verir (Ekonomi yönetimi).
- `/admin parasil <kullanıcı> <miktar>` : Belirtilen kişiden bakiye siler.

### 📌 Genel ve Tekil Komutlar
Herkesin kullanabileceği istatistik ve bilgi komutları.
- `/rank` : Mevcut seviyenizi, tecrübe puanınızı (XP) ve ilerlemenizi gösterir.
- `/stats` : Botun genel istatistiklerini (sunucu sayısı, ping, çalışma süresi) listeler.
- `/profil [kullanıcı]` : Kullanıcının seviye, bakiye ve genel bot istatistiklerini bir arada gösterir.
- `/owner` : Botun yapımcısı/sahibi hakkında bilgiler verir.
- `/yardim` : Detaylı ve interaktif yardım menüsünü açar.
- `/adminmenu` : Yetkililer için tasarlanmış özel kontrol paneli butonlarını açar.

---

## ⚙️ Kurulum & Başlangıç

1. **Gereksinimler:** Python 3.9 veya daha güncel bir sürümünün kurulu olduğundan emin olun.
2. **Kütüphaneler:** Gerekli modülleri kurmak için konsola aşağıdaki komutu girin:
   ```bash
   pip install -r requirements.txt
   ```
3. **Yapılandırma:** `main.py` içerisindeki TOKEN değerine botunuzun Discord Token'ını girin ve kanal/kategori ID'lerini kendi sunucunuza göre düzenleyin.
4. **Çalıştırma:** 
   ```bash
   python main.py
   ```
   *Bot aktif olduğunda konsolda onay mesajını göreceksiniz ve slash komutları Discord'a senkronize edilecektir.*

---
*Bu bot, Z 3 İ T T tarafından özenle geliştirilmiş ve yönetilmektedir.*
