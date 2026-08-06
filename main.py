"""
=============================================================================
  901 SİSTEM BOT — PREFIX'TEN SLASH COMMAND'E TAM MİGRASYON
  Kütüphane : discord.py (app_commands + Cogs)
  Yazar      : Migrasyon Asistanı
=============================================================================

DEĞİŞİKLİK ÖZETİ
─────────────────────────────────────────────────────────────────────────────
  ÖNCE (Prefix)          →   SONRA (Slash)
  @bot.command()         →   @app_commands.command()  (Cog içinde)
  ctx: commands.Context  →   interaction: discord.Interaction
  ctx.send(...)          →   interaction.response.send_message(...)
  ctx.author             →   interaction.user
  ctx.guild              →   interaction.guild
  commands.Greedy[Member]→   member1, member2, ... (ayrı parametreler)
  aliases=[...]          →   Yok — alternatif adlar yorum olarak belirtildi

KOMUT GRUPLARI (Slash Grupları)
─────────────────────────────────────────────────────────────────────────────
  /ekonomi  → bakiye, daily, coinflip, slot, gonder, soy, sweetbonanza,
               blackjack, kumarbaz
  /mod      → ban, kick, unban, sustur, susturkaldir, temizle, clearall,
               rolver, rolal, rolverall
  /ses      → gir, cik, sure, siralama, kilit, kilitac, cek
  /admin    → beyazliste, beyazlisteliste, parabas, parasil
  Tekil     → /rank, /stats, /profil, /owner, /yardim, /adminmenu
=============================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import asyncio
import sys
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View
import re
import time
import asyncio
import random
import json
import os
import datetime
from datetime import datetime, timedelta, timezone, time as dt_time
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Windows konsolunda emoji/unicode karakterlerin hatasız yazdırılması için
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ─────────────────────────────────────────────────────────────────────────────
# AYARLAR  (orijinal sabit değerler korundu)
# ─────────────────────────────────────────────────────────────────────────────
# Botunuzun Discord Developer Portal'dan alınan token değeri. Tırnak içinde yazılmalıdır.
TOKEN = 'BURAYA_BOT_TOKEN_GIRIN'

# Aşağıdaki değişkenlere ilgili kanalların İSİMLERİNİ yazın (örneğin: 'genel-sohbet').
LOG_KANAL_ADI = 'log-kanali-adi'
HOSGELDIN_KANAL_ADI = 'hosgeldin-kanali-adi'
DUYURU_KANAL_ADI = 'duyuru-kanali-adi'  # Hoşgeldin etiketinin atılacağı duyuru kanalı adı
HOSGELDIN_ETIKET_KANAL_ADI = 'duyuru-kanali-adi'  # Girişte kullanıcıya etiket atılacak kanal (4 sn sonra silinir)
SES_SIRALAMA_KANAL_ADI   = 'ses-siralama-kanali-adi'    # Günlük ses sıralamasının atılacağı kanal
LIDERLIK_KANAL_ADI       = 'liderlik-kanali-adi'      # Üçlü sıralamanın atılacağı kanal
MUTE_LOG_KANAL_ADI       = 'mute-log-kanali-adi'         # Susturma/sağırlaştırma loglarının atılacağı kanal

# ─────────────────────────────────────────────────────────────────────────────
# UI & EMBED UTILS
# ─────────────────────────────────────────────────────────────────────────────
class BotUI:
    COLOR_SUCCESS = 0x2ecc71
    COLOR_ERROR   = 0xe74c3c
    COLOR_INFO    = 0x3498db
    COLOR_WARN    = 0xf1c40f
    COLOR_PREMIUM = 0x2b2d31

    @staticmethod
    def embed(title: str = None, desc: str = None, color: int = COLOR_PREMIUM, user: discord.User = None) -> discord.Embed:
        e = discord.Embed(color=color)
        if title: e.title = title
        if desc: e.description = desc
        if user:
            e.set_footer(text=f"Sorgulayan: {user.display_name}", icon_url=user.display_avatar.url)
        else:
            e.set_footer(text="Z 3 İ T T Sistem")
        e.timestamp = discord.utils.utcnow()
        return e

    @staticmethod
    def success(text: str) -> str: return f"> ✅ **Başarılı:** {text}"
    
    @staticmethod
    def error(text: str) -> str: return f"> ❌ **Hata:** {text}"
    
    @staticmethod
    def info(text: str) -> str: return f"> ℹ️ **Bilgi:** {text}"
    
    @staticmethod
    def warn(text: str) -> str: return f"> ⚠️ **Dikkat:** {text}"
DAVET_TAKIP_KANAL_ADI   = 'davet-takip-kanali-adi'      # Davet takip loglarının atılacağı kanal
OTO_ROL_ADI = 'oto-rol-ismi'  # Sunucuya yeni girenlere otomatik verilecek rolün ADI

# Aşağıdaki alanlara Discord üzerinden kopyaladığınız SAYISAL ID değerlerini tırnaksız olarak girin.
# (Geliştirici modunun açık olması gerekir, kullanıcıya/kanala sağ tıklayıp "ID'yi Kopyala" diyebilirsiniz)
OZEL_SAHIP_ID = 0  # Botun özel sahibinin kullanıcı ID'si
BOT_KANAL_ID = 0   # Bot komutlarının kullanılabileceği 1. kanalın ID'si
BOT_KANAL_ID2 = 0  # Bot komutlarının kullanılabileceği 2. kanalın ID'si
MUAF_KANAL_IDLERI = []  # Spam/reklam korumasından muaf tutulacak kanal ID'leri (Örn: [12345, 67890])

REKLAM_UZANTILARI = ["discord.gg/", "discord.com/", ".gg", ".gg/"]
KOMUT_ISARETLERI = ("/", "e!", "s?")

# Seviye rollerini ayarlamak için "Seviye": "Rol İsmi" şeklinde eklemeler yapabilirsiniz.
LEVEL_ROLLER = {"5": "seviye-5-rol-ismi"}

# Otomatik Moderasyon ve Limit Ayarları
SPAM_LIMIT = 10
SPAM_ZAMANI = 5
SUSTURMA_SURESI = 10
BAN_LIMIT_SAYISI = 3
BAN_LIMIT_SURESI = 15
KICK_LIMIT_SAYISI = 3
KICK_LIMIT_SURESI = 15
ZAMAN_ASIMI = 60

# Geçici Ses Odası (Private VC) Ayarları
CREATE_VC_ID = 0    # Odaların açılmasını tetikleyecek ana ses kanalının ID'si (Örn: "Oda Oluştur" kanalı)
# Odaların açılacağı kategorinin ID'si
CATEGORY_ID = 0     # Geçici ses kanallarının açılacağı kategorinin ID'si
PANEL_CHANNEL_ID = 0 # Kontrol paneli vb. özel bir sistem için kullanılacak kanal ID'si
LIMITLER = {
    "Üye Yasaklama (Ban)": 5,
    "Üye Atma (Kick)": 5,
    "Kanal Silme": 3,
    "Kanal Oluşturma": 3,
    "Rol Silme": 5,
    "Webhook Oluşturma": 1,
}
# ─── Korunan Kategoriler ─────────────────────────────────────────────────────
# Bu kategorilerdeki kanallar /mod kilitac all komutundan ETKİLENMEZ.
# Sunucundaki log/yönetim kategorisinin ID'sini buraya ekle.
KORUNAN_KATEGORI_IDLERI = [
    # Örnek: 1234567890123456789,
    # Birden fazla kategori için virgülle ayırarak ekleyebilirsin.
]

# ─────────────────────────────────────────────────────────────────────────────
# RUNTIME STATE  (orijinal değişkenler korundu)
# ─────────────────────────────────────────────────────────────────────────────
spam_takip = {}
spam_ceza_takip = {}
ceza_kilidi = {}
ban_takip = {}
kick_takip = {}
kullanici_takip = {}
ses_giris_takip = {}
yayin_giris_takip = {}
TEMP_ROOMS = {}
gecici_odalar = {}  # Kanal ID : Kurucu ID
silme_gorevleri = {}  # Kanal ID : Sayac Gorevi
ses_data_cache = {}
aktif_cekilisler: dict[int, dict] = {}
BEYAZ_LISTE = []

# ─────────────────────────────────────────────────────────────────────────────
# DOSYA YARDIMCILARI  (iş mantığı değiştirilmedi)
# ─────────────────────────────────────────────────────────────────────────────
BEYAZ_LISTE_FILE = "beyazliste.json"
DAVET_FILE       = "davetler.json"
YEDEK_FILE       = "yedekler.json"
SES_FILE = "ses_verisi.json"
LEVEL_FILE = "levels.json"
ECONOMY_FILE = "economy.json"
SIRALAMA_FILE = "siralama_verileri.json"

levels = {}
economy = {}
siralama_verileri = {
    "mesajlar": {},
    "yayin": {},
    "mesaj_ids": {}
}


def load_white_list():
    global BEYAZ_LISTE
    if os.path.exists(BEYAZ_LISTE_FILE):
        with open(BEYAZ_LISTE_FILE, "r") as f:
            try:
                BEYAZ_LISTE = json.load(f).get("ids", [])
            except:
                BEYAZ_LISTE = []
    else:
        BEYAZ_LISTE = []


def save_white_list():
    with open(BEYAZ_LISTE_FILE, "w") as f:
        json.dump({"ids": BEYAZ_LISTE}, f, indent=4)


# ── Davet Takip ───────────────────────────────────────────────────────────────
invite_cache: dict[int, dict[str, discord.Invite]] = {}  # guild_id -> {code: invite}

def load_davet():
    if os.path.exists(DAVET_FILE):
        with open(DAVET_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_davet(data):
    with open(DAVET_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_yedek():
    if os.path.exists(YEDEK_FILE):
        with open(YEDEK_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_yedek(data):
    with open(YEDEK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_ses():
    if os.path.exists(SES_FILE):
        with open(SES_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}


def save_ses(data):
    with open(SES_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_siralama():
    global siralama_verileri
    if os.path.exists(SIRALAMA_FILE):
        with open(SIRALAMA_FILE, "r", encoding="utf-8") as f:
            try:
                siralama_verileri = json.load(f)
                if "mesaj_ids" not in siralama_verileri:
                    siralama_verileri["mesaj_ids"] = {}
            except:
                pass


def save_siralama():
    with open(SIRALAMA_FILE, "w", encoding="utf-8") as f:
        json.dump(siralama_verileri, f, indent=4, ensure_ascii=False)


def load_levels():
    global levels
    if os.path.exists(LEVEL_FILE):
        with open(LEVEL_FILE, "r") as f:
            try:
                levels = json.load(f)
            except:
                levels = {}
    else:
        levels = {}


def save_levels():
    with open(LEVEL_FILE, "w") as f:
        json.dump(levels, f, indent=4)


def load_economy():
    global economy
    if os.path.exists(ECONOMY_FILE):
        with open(ECONOMY_FILE, "r") as f:
            try:
                economy = json.load(f)
            except:
                economy = {}
    else:
        economy = {}


def save_economy():
    with open(ECONOMY_FILE, "w") as f:
        json.dump(economy, f, indent=4)


def check_user(u_id):
    if u_id not in economy:
        economy[u_id] = {"balance": 100, "last_daily": None}


def sure_formatla(saniye):
    h, r = divmod(int(saniye), 3600)
    m, s = divmod(r, 60)
    parcalar = []
    if h:
        parcalar.append(f"{h} saat")
    if m:
        parcalar.append(f"{m} dakika")
    if s or not parcalar:
        parcalar.append(f"{s} saniye")
    return " ".join(parcalar)
# --- YETKİ KONTROL FONKSİYONU ---


async def check_permissions(interaction: discord.Interaction, channel_id):
    user = interaction.user
    guild = interaction.guild

    target_channel = guild.get_channel(channel_id)
    if not target_channel or not target_channel.category or target_channel.category.id != CATEGORY_ID:
        return False, "❌ Bu kanal özel oda kategorisinde değil."

    if channel_id in TEMP_ROOMS and TEMP_ROOMS[channel_id] == user.id:
        return True, None

    if user.guild_permissions.administrator or user == guild.owner:
        if user.voice and user.voice.channel and user.voice.channel.id == channel_id:
            return True, None
        return False, "❌ Bu odayı yönetmek için bu odanın ses kanalında olmalısınız. (Admin Yetkisi)"

    return False, "❌ Bu oda size ait değil."


# --- MODAL SINIFLARI ---
class RoomNameModal(discord.ui.Modal, title="Oda İsmini Güncelle"):
    name_input = discord.ui.TextInput(
        label="Yeni Oda İsmi", placeholder="Örn: Sohbet Odası", max_length=50, required=True)

    def __init__(self, kanal_id):
        super().__init__()
        self.kanal_id = kanal_id

    async def on_submit(self, interaction: discord.Interaction):
        permitted, reason = await check_permissions(interaction, self.kanal_id)
        if not permitted:
            return await interaction.response.send_message(reason, ephemeral=True)

        kanal = interaction.guild.get_channel(self.kanal_id)
        if not kanal:
            return await interaction.response.send_message("❌ Kanal bulunamadı.", ephemeral=True)

        await kanal.edit(name=self.name_input.value)
        await interaction.response.send_message(f"✅ İsim **{self.name_input.value}** olarak güncellendi.", ephemeral=True)


class RoomLimitModal(discord.ui.Modal, title="Oda Limitini Güncelle"):
    limit_input = discord.ui.TextInput(
        label="Kişi Sayısı (0-99)", placeholder="Örn: 10 (Sınırsız için 0)", max_length=2, required=True)

    def __init__(self, kanal_id):
        super().__init__()
        self.kanal_id = kanal_id

    async def on_submit(self, interaction: discord.Interaction):
        permitted, reason = await check_permissions(interaction, self.kanal_id)
        if not permitted:
            return await interaction.response.send_message(reason, ephemeral=True)

        kanal = interaction.guild.get_channel(self.kanal_id)
        if not kanal:
            return await interaction.response.send_message("❌ Kanal bulunamadı.", ephemeral=True)

        try:
            l = int(self.limit_input.value)
            if not (0 <= l <= 99):
                raise ValueError
            await kanal.edit(user_limit=l)
            await interaction.response.send_message(
                f"✅ Oda limiti **{l if l > 0 else 'Sınırsız'}** olarak güncellendi.", ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message("❌ Lütfen 0 ile 99 arasında bir sayı girin.", ephemeral=True)


# --- USER SELECT VIEW SINIFLARI ---
class UserSelectView(discord.ui.View):
    def __init__(self, kanal_id, action):
        super().__init__(timeout=60)
        self.kanal_id = kanal_id
        self.action = action

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Bir kullanıcı seçin...")
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        permitted, reason = await check_permissions(interaction, self.kanal_id)
        if not permitted:
            return await interaction.response.send_message(reason, ephemeral=True)

        selected_user = select.values[0]
        if selected_user.bot:
            return await interaction.response.send_message("❌ Botlar üzerinde işlem yapamazsınız.", ephemeral=True)

        kanal = interaction.guild.get_channel(self.kanal_id)
        if not kanal:
            return await interaction.response.send_message("❌ Kanal bulunamadı.", ephemeral=True)

        owner_id = TEMP_ROOMS.get(self.kanal_id)

        if self.action == "add":
            await kanal.set_permissions(selected_user, connect=True, view_channel=True)
            await interaction.response.send_message(f"✅ {selected_user.mention} odaya giriş izni verildi.", ephemeral=True)

        elif self.action == "kick":
            if owner_id and selected_user.id == owner_id:
                return await interaction.response.send_message(
                    "❌ Oda sahibini yasaklayamazsınız. Önce sahipliği devredin.", ephemeral=True
                )
            await kanal.set_permissions(selected_user, connect=False, view_channel=True)
            if selected_user in kanal.members:
                await selected_user.move_to(None)
            await interaction.response.send_message(f"✅ {selected_user.mention} odadan yasaklandı.", ephemeral=True)

        elif self.action == "transfer":
            if owner_id and selected_user.id == owner_id:
                return await interaction.response.send_message("❌ Sahipliği zaten bu kullanıcıda.", ephemeral=True)

            # Eski sahibin yetkilerini sıfırla
            eski_sahip = interaction.guild.get_member(owner_id)
            if eski_sahip:
                await kanal.set_permissions(eski_sahip, overwrite=None)

            TEMP_ROOMS[self.kanal_id] = selected_user.id
            await kanal.set_permissions(
                selected_user,
                connect=True,
                view_channel=True,
                manage_channels=True,
                mute_members=True,      # ← YENİ
                deafen_members=True     # ← YENİ
            )
            await interaction.response.send_message(
                f"👑 Oda sahipliği başarıyla {selected_user.mention} kullanıcısına devredildi.", ephemeral=True
            )


# --- ANA PANEL VIEW SINIFI ---
class RoomPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_interacted_room(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator or interaction.user == interaction.guild.owner:
            if (interaction.user.voice and interaction.user.voice.channel
                    and interaction.user.voice.channel.id in TEMP_ROOMS):
                return interaction.user.voice.channel.id

        for r_id, o_id in TEMP_ROOMS.items():
            if o_id == interaction.user.id:
                return r_id
        return None

    @discord.ui.button(label="Gizle & Kilitle", emoji="💀", style=discord.ButtonStyle.danger, custom_id="btn_skull", row=0)
    async def btn_skull(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message(
                "❌ Yetkiniz olan aktif bir oda bulunamadı. (Admin Yetkisi: Odada olun)", ephemeral=True
            )
        kanal = interaction.guild.get_channel(r_id)
        default_perm = kanal.overwrites_for(interaction.guild.default_role)
        view_state = False if default_perm.view_channel is True else True
        connect_state = False if default_perm.connect is True else True
        await kanal.set_permissions(interaction.guild.default_role, view_channel=view_state, connect=connect_state)
        await interaction.response.send_message(
            "👁️🔒 Oda hem gizlendi hem de kilitlendi." if not view_state else "👁️🔓 Oda hem görünür hem de açıldı.",
            ephemeral=True
        )

    @discord.ui.button(label="İsim Değiş", emoji="✏️", style=discord.ButtonStyle.primary, custom_id="btn_edit", row=0)
    async def btn_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ Yetkiniz olan aktif bir oda bulunamadı.", ephemeral=True)
        await interaction.response.send_modal(RoomNameModal(r_id))

    @discord.ui.button(label="Limit Güncelle", emoji="⬆️", style=discord.ButtonStyle.primary, custom_id="btn_limit", row=0)
    async def btn_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ Yetkiniz olan aktif bir oda bulunamadı.", ephemeral=True)
        await interaction.response.send_modal(RoomLimitModal(r_id))

    @discord.ui.button(label="Kilitle", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="btn_lock", row=1)
    async def btn_lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ Yetkiniz olan aktif bir oda bulunamadı.", ephemeral=True)
        kanal = interaction.guild.get_channel(r_id)
        current_connect = kanal.overwrites_for(
            interaction.guild.default_role).connect
        new_state = False if current_connect is True else True
        await kanal.set_permissions(interaction.guild.default_role, connect=new_state)
        await interaction.response.send_message(
            "🔓 Oda dışarı açıldı." if new_state else "🔒 Oda dışarıya kilitlendi.", ephemeral=True
        )

    @discord.ui.button(label="İzin Ver", emoji="👥", style=discord.ButtonStyle.success, custom_id="btn_add", row=1)
    async def btn_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ Yetkiniz olan aktif bir oda bulunamadı.", ephemeral=True)
        await interaction.response.send_message("Giriş izni verilecek kullanıcıyı seçin:", view=UserSelectView(r_id, "add"), ephemeral=True)

    @discord.ui.button(label="Yasakla", emoji="🚫", style=discord.ButtonStyle.danger, custom_id="btn_kick", row=1)
    async def btn_kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ Yetkiniz olan aktif bir oda bulunamadı.", ephemeral=True)
        await interaction.response.send_message("Yasaklamak istediğiniz kullanıcıyı seçin:", view=UserSelectView(r_id, "kick"), ephemeral=True)

    @discord.ui.button(label="Görünmez Yap", emoji="👁️", style=discord.ButtonStyle.secondary, custom_id="btn_hide", row=2)
    async def btn_hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ Yetkiniz olan aktif bir oda bulunamadı.", ephemeral=True)
        kanal = interaction.guild.get_channel(r_id)
        current_view = kanal.overwrites_for(
            interaction.guild.default_role).view_channel
        new_state = False if current_view is True else True
        await kanal.set_permissions(interaction.guild.default_role, view_channel=new_state)
        await interaction.response.send_message(
            "👁️ Oda görünür yapıldı." if new_state else "🙈 Oda görünmez yapıldı.", ephemeral=True
        )

    @discord.ui.button(label="Devret", emoji="👑", style=discord.ButtonStyle.primary, custom_id="btn_crown", row=2)
    async def btn_crown(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ Yetkiniz olan aktif bir oda bulunamadı.", ephemeral=True)

        if TEMP_ROOMS.get(r_id) != interaction.user.id:
            return await interaction.response.send_message(
                "❌ Oda sahipliğini sadece asıl sahip başkasına devredebilir.", ephemeral=True
            )
        await interaction.response.send_message(
            "Oda sahipliğini devretmek istediğiniz kullanıcıyı seçin:",
            view=UserSelectView(r_id, "transfer"),
            ephemeral=True
        )

    @discord.ui.button(label="Odayı Sil", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="btn_delete", row=2)
    async def btn_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ Yetkiniz olan aktif bir oda bulunamadı.", ephemeral=True)

        kanal = interaction.guild.get_channel(r_id)
        if kanal:
            TEMP_ROOMS.pop(r_id, None)
            await interaction.response.send_message("🗑️ Odanız başarıyla silindi.", ephemeral=True)
            await kanal.delete()


# ─────────────────────────────────────────────────────────────────────────────
# BOT + INTENTS
# ─────────────────────────────────────────────────────────────────────────────
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

# ─────────────────────────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR  (iş mantığı değiştirilmedi)
# ─────────────────────────────────────────────────────────────────────────────


async def send_log(guild, message=None, color=discord.Color.blue(), embed=None):
    log_channel = discord.utils.get(guild.text_channels, name=LOG_KANAL_ADI)
    if not log_channel:
        return
    if embed:
        await log_channel.send(embed=embed)
    elif message:
        new_embed = BotUI.embed(
            title="Sistem Logu",
            desc=message, 
            color=color.value if isinstance(color, discord.Color) else color
        )
        await log_channel.send(embed=new_embed)


async def koruma_kontrol(guild, user, islem_tipi):
    if user.id in (guild.owner_id, bot.user.id) or user.id in BEYAZ_LISTE:
        return
    simdi = discord.utils.utcnow()
    user_key = f"{user.id}_{islem_tipi}"
    kullanici_takip.setdefault(user_key, [])
    kullanici_takip[user_key] = [
        t for t in kullanici_takip[user_key]
        if t > simdi - timedelta(seconds=ZAMAN_ASIMI)
    ]
    kullanici_takip[user_key].append(simdi)
    limit = LIMITLER.get(islem_tipi, 3)
    if len(kullanici_takip[user_key]) > limit:
        try:
            await guild.ban(user, reason=f"Anti-Nuke: {islem_tipi} limiti aşıldı! @here")
            await send_log(guild, f"🚨 **SALDIRI ENGELLENDİ:** {user.mention} ({user.id}) **{islem_tipi}** limitini aştığı için sunucudan yasaklandı! @here", discord.Color.red())
        except:
            try:
                await user.edit(roles=[r for r in user.roles if r.is_default()])
                await send_log(guild, f"⚠️ **YETKİ ALINDI:** {user.mention} banlanamadı ama tüm yetkileri alındı. @here", discord.Color.orange())
            except:
                await send_log(guild, f"❌ **KRİTİK:** {user.mention} durdurulamıyor! Yetkim yetersiz! @here", discord.Color.dark_red())

# ─────────────────────────────────────────────────────────────────────────────
# DURUM DÖNGÜSÜ  (değiştirilmedi)
# ─────────────────────────────────────────────────────────────────────────────

durum_index = 0

@tasks.loop(seconds=15)
async def durum_dongusu():
    global durum_index
    durumlar = ["self.durumlar = [
            "made by z3itt 🔥",
            "z3itt ♡ Github 😆",
            "@z3itt 😁"
            ]
    await bot.change_presence(
        activity=discord.Streaming(
            name=durumlar[durum_index % len(durumlar)],
            url="https://www.twitch.tv/901sistem"
        )
    )
    durum_index += 1

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            BotUI.warn(f"Bu komutu tekrar kullanmak için **{error.retry_after:.1f} saniye** bekle!"),
            ephemeral=True
        )
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            BotUI.error("Bu komutu kullanmak için yetkin yok!"), ephemeral=True
        )
    elif isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            BotUI.error("Bu komutu kullanma yetkin yok!"), ephemeral=True
        )
    else:
        print(f"Komut hatası [{interaction.command}]: {error}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(BotUI.error("Beklenmeyen bir hata oluştu!"), ephemeral=True)
            else:
                await interaction.followup.send(BotUI.error("Beklenmeyen bir hata oluştu!"), ephemeral=True)
        except:
            pass
# ─────────────────────────────────────────────────────────────────────────────
# ON_READY — KOMUT AĞACINI SYNC ET
# ─────────────────────────────────────────────────────────────────────────────


@bot.event
async def on_ready():
    """
    SYNC NOTU:
      • Global sync → tüm sunucular (değişiklikler ~1 saat gecikir)
      • Guild sync  → sadece test sunucusu (anlık)

      Test için GUILD_ID'yi kendi sunucunla değiştir, sonra
      canlıya geçerken guild parametresini kaldır (global sync).
    """
    load_levels()
    load_economy()
    load_white_list()
    load_giveaways()
    load_siralama()
    bot.add_view(GiveawayView())  # Bot restart'ta butonlar ölmesin
    if not giveaway_kontrol.is_running():
        giveaway_kontrol.start()
    bot.add_view(RoomPanelView())

    # ── SLASH COMMAND SYNC ────────────────────────────────────────────────
    try:
        # GLOBAL SYNC (canlı ortam)
        synced = await bot.tree.sync()

        # GUILD SYNC (test — anlık):
        # TEST_GUILD = discord.Object(id=YourGuildID)
        # synced = await bot.tree.sync(guild=TEST_GUILD)

        print(f"✅ {len(synced)} slash komutu sync edildi.")
    except Exception as e:
        print(f"❌ Sync hatası: {e}")

    if not durum_dongusu.is_running():
        durum_dongusu.start()
    if not gunluk_ses_siralama.is_running():
        gunluk_ses_siralama.start()

    for guild in bot.guilds:
        for vc in guild.voice_channels:
            for member in vc.members:
                if not member.bot:
                    ses_giris_takip[member.id] = time.time()
                    if member.voice and member.voice.self_stream:
                        yayin_giris_takip[member.id] = time.time()

    # Invite cache'i yükle
    for guild in bot.guilds:
        try:
            invites = await guild.invites()
            invite_cache[guild.id] = {inv.code: inv for inv in invites}
        except Exception as e:
            print(f"Invite cache yüklenemedi ({guild.name}): {e}")

    print(f"✅ {bot.user.name} hazır! Tüm sistemler aktif.")

# ─────────────────────────────────────────────────────────────────────────────
# EVENTS  (değiştirilmedi — iş mantığı aynı)
# ─────────────────────────────────────────────────────────────────────────────


@bot.event
async def on_webhooks_update(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
        if entry.user.id not in BEYAZ_LISTE and entry.user.id != channel.guild.owner_id:
            await koruma_kontrol(channel.guild, entry.user, "Webhook Oluşturma")
            webhooks = await channel.webhooks()
            for webhook in webhooks:
                await webhook.delete(reason="Anti-Nuke: İzinsiz Webhook Silindi. @here")
            await send_log(channel.guild, f"⚠️ **İzinsiz Webhook:** {entry.user.mention} tarafından oluşturulan webhook silindi! @here", discord.Color.red())


@bot.event
async def on_member_ban(guild, user):
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                await koruma_kontrol(guild, entry.user, "Üye Yasaklama (Ban)")
                break
    except:
        pass


@bot.event
async def on_guild_invite_create(invite):
    gid = invite.guild.id
    if gid not in invite_cache:
        invite_cache[gid] = {}
    invite_cache[gid][invite.code] = invite


@bot.event
async def on_guild_invite_delete(invite):
    gid = invite.guild.id
    invite_cache.get(gid, {}).pop(invite.code, None)


@bot.event
async def on_guild_channel_delete(channel):
    guild = channel.guild
    await asyncio.sleep(1)
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            responsible_user = entry.user
            if responsible_user.id in (bot.user.id, guild.owner_id) or responsible_user.id in BEYAZ_LISTE:
                await send_log(guild, f"🗑️ **Kanal Silindi:** #{channel.name} | Güvenli İşlem", discord.Color.blue())
                return
            await koruma_kontrol(guild, responsible_user, "Kanal Silme")
            await send_log(guild, f"🚫 **Kanal Silindi:** #{channel.name} | Sorumlu: {responsible_user.mention}", discord.Color.red())
            break
    except Exception as e:
        print(f"Hata: {e}")


@bot.event
async def on_guild_channel_create(channel):
    guild = channel.guild
    kategori_adi = channel.category.name if channel.category else "Kategorisiz"

    try:
        await asyncio.sleep(1)

        sorumlu = None
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                sorumlu = entry.user
                break
        except Exception as e:
            print(f"[on_guild_channel_create] audit_logs hatası: {e}")

        if sorumlu is None:
            await send_log(guild, f"🆕 Kanal Açıldı: {channel.mention} | Kategori: **{kategori_adi}**", discord.Color.orange())
            return

        if sorumlu.id in (bot.user.id, guild.owner_id) or sorumlu.id in BEYAZ_LISTE:
            await send_log(guild, f"🆕 Kanal Açıldı: {channel.mention} | Kategori: **{kategori_adi}** | {sorumlu.mention} | Güvenli İşlem", discord.Color.orange())
            return

        await koruma_kontrol(guild, sorumlu, "Kanal Oluşturma")
        user_key = f"{sorumlu.id}_Kanal Oluşturma"
        islem_sayisi = len(kullanici_takip.get(user_key, []))
        if islem_sayisi > 3:
            try:
                await channel.delete(reason="Anti-Nuke: Kanal limiti aşıldı.")
                await send_log(guild, f"🚫 Limit Aşımı: {sorumlu.mention}", discord.Color.red())
            except:
                pass
        else:
            await send_log(guild, f"🆕 Kanal Açıldı: {channel.mention} | Kategori: **{kategori_adi}** | {sorumlu.mention} | {islem_sayisi}/3", discord.Color.orange())

    except Exception as e:
        print(f"[on_guild_channel_create] genel hata: {e}")
        try:
            await send_log(guild, f"🆕 Kanal Açıldı: {channel.mention} | Kategori: **{kategori_adi}**", discord.Color.orange())
        except Exception:
            pass


async def _kanal_update_sorumlu(guild, channel_id):
    """channel_update audit log'larından bu kanala ait son işlemi yapan kullanıcıyı bulur."""
    try:
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_update):
            target_id = entry.target.id if entry.target else None
            if target_id == channel_id:
                return entry.user
    except Exception as e:
        print(f"[on_guild_channel_update] audit_logs hatası: {e}")
    return None


@bot.event
async def on_guild_channel_update(before, after):
    guild = after.guild
    await asyncio.sleep(1)

    if before.name != after.name:
        sorumlu = await _kanal_update_sorumlu(guild, after.id)
        ek = f" | {sorumlu.mention}" if sorumlu else ""
        await send_log(guild, f"📑 Kanal Adı Değişti: #{before.name} → #{after.name}{ek}", discord.Color.gold())

    if before.category_id != after.category_id:
        once_kategori = before.category.name if before.category else "Kategorisiz"
        sonra_kategori = after.category.name if after.category else "Kategorisiz"
        sorumlu = await _kanal_update_sorumlu(guild, after.id)
        ek = f" | {sorumlu.mention}" if sorumlu else ""
        await send_log(guild, f"📂 Kanal Taşındı: {after.mention} | **{once_kategori}** → **{sonra_kategori}**{ek}", discord.Color.gold())

    if before.position != after.position and before.category_id == after.category_id:
        sorumlu = await _kanal_update_sorumlu(guild, after.id)
        ek = f" | {sorumlu.mention}" if sorumlu else ""
        await send_log(guild, f"↕️ Kanal Sıralaması Değişti: {after.mention}{ek}", discord.Color.gold())


@bot.event
async def on_guild_update(before, after):
    if before.name != after.name:
        async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
            await send_log(after, f"🏰 Sunucu Adı: {before.name} → {after.name} | {entry.user.mention}", discord.Color.gold())
            break
    if before.icon != after.icon:
        async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
            await send_log(after, f"🖼️ Sunucu Fotoğrafı Değişti | {entry.user.mention}", discord.Color.purple())
            break

    if before.vanity_url_code != after.vanity_url_code:
        eski_kod = before.vanity_url_code
        yeni_kod = after.vanity_url_code

        sorumlu = None
        async for entry in after.audit_logs(limit=5, action=discord.AuditLogAction.guild_update):
            sorumlu = entry.user
            break

        ek = f" | {sorumlu.mention}" if sorumlu else ""
        uyari = ""
        if sorumlu and sorumlu.id not in (after.owner_id,) and sorumlu.id not in BEYAZ_LISTE:
            uyari = "\n⚠️ **Discord API kısıtlaması nedeniyle bot eski linki otomatik geri yükleyemez. Lütfen sunucu ayarlarından manuel olarak geri alın.**"

        await send_log(
            after,
            f"🔗 Davet Koruması: Özel Davet Linki değiştirildi! `{eski_kod}` → `{yeni_kod}`{ek}{uyari}",
            discord.Color.red()
        )


@bot.event
async def on_guild_role_create(role):
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
        await send_log(role.guild, f"✨ Yeni Rol: {role.name} | {entry.user.mention}", discord.Color.green())
        break


@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        await send_log(role.guild, f"🔥 Rol Silindi: {role.name} | {entry.user.mention}", discord.Color.red())
        break


@bot.event
async def on_guild_role_update(before, after):
    guild = after.guild
    if before.permissions != after.permissions:
        kritik_yetkiler = ["administrator",
                           "manage_roles", "manage_guild", "ban_members"]
        added_perms = [p for p, v in after.permissions if v and not dict(
            before.permissions)[p]]
        if any(p in kritik_yetkiler for p in added_perms):
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                sorumlu = entry.user
                sorumlu_member = guild.get_member(sorumlu.id)
                is_whitelisted = sorumlu.id in BEYAZ_LISTE
                is_admin = sorumlu_member is not None and sorumlu_member.guild_permissions.administrator
                if not (is_whitelisted or is_admin):
                    try:
                        await after.edit(permissions=before.permissions, reason="İzinsiz yetki ekleme!")
                        await koruma_kontrol(guild, sorumlu, "Rol Yetkisi Güncelleme")
                        await send_log(guild, f"⚠️ **YETKİ ARTIŞI ENGELLENDİ:** {sorumlu.mention} `{after.name}` rolüne kritik yetkiler ekledi!", discord.Color.dark_red())
                    except:
                        pass
                break

    # --- ROL DEĞİŞİKLİK LOGLARI ---
    isim_degisti = before.name != after.name
    yetki_degisti = before.permissions != after.permissions

    if isim_degisti or yetki_degisti:
        sorumlu_yetkili = "Bilinmiyor"
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
            if entry.target.id == after.id:
                sorumlu_yetkili = entry.user.mention
                break

        log_mesaji = f"🛡️ **Rol Güncellendi: {before.name}**\n"
        log_mesaji += f"👤 **Sorumlu:** {sorumlu_yetkili}\n"

        if isim_degisti:
            log_mesaji += f"📝 **İsim Değişimi:** `{before.name}` ➔ `{after.name}`\n"

        if yetki_degisti:
            log_mesaji += "⚠️ **Yetki Değişiklikleri:**\n"
            old_perms = set(cap for cap, val in before.permissions if val)
            new_perms = set(cap for cap, val in after.permissions if val)
            eklenenler = new_perms - old_perms
            cikarilanlar = old_perms - new_perms
            if eklenenler:
                log_mesaji += f"✅ **Eklenenler:** `{', '.join(eklenenler)}`\n"
            if cikarilanlar:
                log_mesaji += f"❌ **Çıkarılanlar:** `{', '.join(cikarilanlar)}`\n"

        try:
            await send_log(guild, message=log_mesaji, color=discord.Color.blue())
        except Exception as e:
            print(f"Log hatası: {e}")


@bot.event
async def on_member_update(before, after):
    guild = after.guild
    if len(before.roles) < len(after.roles):
        new_role = next(r for r in after.roles if r not in before.roles)
        kritik_yetkiler = ["administrator", "manage_roles",
                           "manage_channels", "ban_members", "kick_members"]
        is_critical = any(dict(new_role.permissions).get(p)
                          for p in kritik_yetkiler)
        if is_critical:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                if entry.target.id == after.id:
                    sorumlu = entry.user
                    sorumlu_member = guild.get_member(sorumlu.id)
                    is_whitelisted = sorumlu.id in BEYAZ_LISTE
                    is_admin = sorumlu_member is not None and sorumlu_member.guild_permissions.administrator
                    if not (is_whitelisted or is_admin):
                        try:
                            await after.remove_roles(new_role, reason="İzinsiz yetkili rolü!")
                            await koruma_kontrol(guild, sorumlu, "Yetkili Rolü Verme")
                            await send_log(guild, f"🚨 İzinsiz Yetki Engellendi: {sorumlu.mention} → {after.mention} | {new_role.name}", discord.Color.red())
                            return
                        except:
                            pass
                    break
        if len(after.roles) > 12:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                if entry.target.id == after.id:
                    sorumlu = entry.user
                    sorumlu_member = guild.get_member(sorumlu.id)
                    is_whitelisted = sorumlu.id in BEYAZ_LISTE
                    is_admin = sorumlu_member is not None and sorumlu_member.guild_permissions.administrator
                    if not (is_whitelisted or is_admin):
                        try:
                            await after.remove_roles(new_role, reason="9 Rol Sınırı")
                            lk = discord.utils.get(
                                guild.text_channels, name="log")
                            if lk:
                                await lk.send(f"⚠️ {after.mention} rol sınırına ulaştı, `{new_role.name}` alındı.")
                        except:
                            pass
                    break
    if len(before.roles) != len(after.roles):
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
            if entry.target.id == after.id:
                sorumlu = entry.user
                if len(before.roles) < len(after.roles):
                    new_role = next(
                        r for r in after.roles if r not in before.roles)
                    if new_role.name != OTO_ROL_ADI:
                        await send_log(guild, f"👤 {after.mention} → `{new_role.name}` verildi. | {sorumlu.mention}", discord.Color.green())
                else:
                    removed_role = next(
                        r for r in before.roles if r not in after.roles)
                    await send_log(guild, f"👤 {after.mention} → `{removed_role.name}` alındı. | {sorumlu.mention}", discord.Color.red())
                break
    if before.display_name != after.display_name:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
            if entry.target.id == after.id:
                await send_log(guild, f"👤 İsim: {before.display_name} → {after.display_name} | {entry.user.mention}", discord.Color.blue())
                break
    if before.timed_out_until != after.timed_out_until:
        yetkili = "Bilinmiyor"
        try:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target.id == after.id:
                    yetkili = entry.user.mention
                    break
        except:
            pass
        if after.timed_out_until is None:
            embed = discord.Embed(title="🔓 Susturma Kaldırıldı",
                                  description=f"**Kullanıcı:** {after.mention}\n**Yetkili:** {yetkili}", color=discord.Color.green(), timestamp=discord.utils.utcnow())
            embed.set_thumbnail(url=after.display_avatar.url)
            await send_log(after.guild, embed=embed)
        else:
            simdi_utc = discord.utils.utcnow()
            saniye = (after.timed_out_until - simdi_utc).total_seconds()
            if saniye > 86400:
                sure_metni = f"{round(saniye/86400)} gün"
            elif saniye > 3600:
                sure_metni = f"{round(saniye/3600)} saat"
            else:
                sure_metni = f"{round(saniye/60)} dakika"
            embed = discord.Embed(
                title="🚫 Manuel Susturma", description=f"**Kullanıcı:** {after.mention}\n**Yetkili:** {yetkili}\n**Süre:** {sure_metni}", color=discord.Color.red(), timestamp=discord.utils.utcnow())
            embed.set_thumbnail(url=after.display_avatar.url)
            await send_log(after.guild, embed=embed)


@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    await send_log(message.guild, f"🗑️ **Mesaj Silindi** | {message.author.mention} | {message.channel.mention} | {message.content}", discord.Color.red())


@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content:
        return
    await send_log(before.guild, f"📝 **Düzenleme** | {before.author.mention} | Eski: {before.content} | Yeni: {after.content}", discord.Color.blue())


@bot.event
async def on_member_join(member):
    if member.bot:
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
            if entry.target.id == member.id:
                davet_eden = entry.user
                if davet_eden.id not in BEYAZ_LISTE and davet_eden.id != member.guild.owner_id:
                    try:
                        await member.ban(reason=f"İzinsiz bot: {davet_eden.name}")
                        await send_log(member.guild, f"🚫 İzinsiz Bot Engellendi: {member.name} | Davet: {davet_eden.mention}", discord.Color.red())
                        return
                    except Exception as e:
                        print(f"Bot engelleme hatası: {e}")
                break
    guild = member.guild
    h_kanal = discord.utils.get(
        member.guild.text_channels, name=HOSGELDIN_KANAL_ADI)
    if h_kanal:
        embed = discord.Embed(title="📥 Aramıza Yeni Biri Katıldı!",
                              description=f"🎉 Hoş geldin {member.mention}! **{guild.member_count}** kişiye ulaştık.", color=discord.Color.green(), timestamp=discord.utils.utcnow())
        embed.add_field(name="👤 Kullanıcı", value=member.name, inline=True)
        embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="🚀 Üye Sırası",
                        value=f"**{guild.member_count}**", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{guild.name} Yönetim Sistemi",
                         icon_url=guild.icon.url if guild.icon else None)
        await h_kanal.send(content=f"🌟 **{member.name}** sunucuya giriş yaptı! {member.mention}", embed=embed)

    # Belirtilen kanala etiket at, 4 saniye sonra silinsin
    etiket_kanal = discord.utils.get(member.guild.text_channels, name=HOSGELDIN_ETIKET_KANAL_ADI)
    if etiket_kanal:
        try:
            await etiket_kanal.send(
                content=f"👋 Hoş geldin {member.mention}! 🎉",
                delete_after=4
            )
        except Exception:
            pass

    rol = discord.utils.get(member.guild.roles, name=OTO_ROL_ADI)
    if rol:
        try:
            await member.add_roles(rol)
            await send_log(member.guild, f"✅ Oto-Rol Verildi: {member.mention}", discord.Color.green())
        except:
            await send_log(member.guild, f"❌ `{OTO_ROL_ADI}` verilemedi!", discord.Color.red())

    # ── Davet Takip ──────────────────────────────────────────────────────────
    if not member.bot:
        guild = member.guild
        davet_data = load_davet()
        davet_eden_id = None

        try:
            yeni_invites = await guild.invites()
            yeni_cache   = {inv.code: inv for inv in yeni_invites}
            eski_cache   = invite_cache.get(guild.id, {})

            for code, yeni_inv in yeni_cache.items():
                eski_inv = eski_cache.get(code)
                if eski_inv and yeni_inv.uses > eski_inv.uses:
                    davet_eden_id = str(yeni_inv.inviter.id) if yeni_inv.inviter else None
                    break

            # Vanity URL ile gelmiş olabilir
            if davet_eden_id is None and guild.vanity_url_code:
                try:
                    vanity = await guild.vanity_invite()
                    eski_vanity = eski_cache.get("__vanity__")
                    if eski_vanity is None or vanity.uses > eski_vanity.uses:
                        davet_eden_id = "__vanity__"
                    yeni_cache["__vanity__"] = vanity
                except Exception:
                    pass

            invite_cache[guild.id] = yeni_cache

        except Exception as e:
            print(f"[davet_takip] invite fetch hatası: {e}")

        if davet_eden_id and davet_eden_id != "__vanity__":
            uid_str = davet_eden_id
            if uid_str not in davet_data:
                davet_data[uid_str] = {"toplam": 0, "getirdikleri": []}
            davet_data[uid_str]["toplam"] += 1
            if str(member.id) not in davet_data[uid_str]["getirdikleri"]:
                davet_data[uid_str]["getirdikleri"].append(str(member.id))
            save_davet(davet_data)

            davet_kanal = discord.utils.get(guild.text_channels, name=DAVET_TAKIP_KANAL_ADI)
            if davet_kanal:
                davet_eden = guild.get_member(int(davet_eden_id))
                davet_eden_mention = davet_eden.mention if davet_eden else f"<@{davet_eden_id}>"
                toplam = davet_data[uid_str]["toplam"]
                await davet_kanal.send(
                    embed=discord.Embed(
                        description=f"📨 {member.mention} sunucuya katıldı!\n👤 Davet eden: {davet_eden_mention} (Toplam: **{toplam}** davet)",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )
                )
        elif davet_eden_id == "__vanity__":
            davet_kanal = discord.utils.get(guild.text_channels, name=DAVET_TAKIP_KANAL_ADI)
            if davet_kanal:
                await davet_kanal.send(
                    embed=discord.Embed(
                        description=f"📨 {member.mention} sunucuya özel davet linki ile katıldı.",
                        color=discord.Color.blurple(),
                        timestamp=discord.utils.utcnow()
                    )
                )


@bot.event
async def on_member_remove(member):
    guild = member.guild
    h_kanal = discord.utils.get(
        member.guild.text_channels, name=HOSGELDIN_KANAL_ADI)
    if h_kanal:
        embed = discord.Embed(title="📤 Bir Üye Ayrıldı", description=f"{member.mention} ayrıldı.\n🆔 `{member.id}`", color=discord.Color.red(
        ), timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{guild.name} Gelen-Giden",
                         icon_url=guild.icon.url if guild.icon else None)
        await h_kanal.send(content=f"📤 **{member.name}** veda etti.", embed=embed)
    await asyncio.sleep(1)
    is_kicked = False
    try:
        async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 15:
                is_kicked = True
                await koruma_kontrol(member.guild, entry.user, "Üye Atma (Kick)")
                await send_log(member.guild, f"👢 Kicklendi: {member.name} | {entry.user.mention}", discord.Color.red())
                break
    except:
        pass
    if not is_kicked:
        await send_log(member.guild, f"📤 Ayrıldı: {member.name}", discord.Color.orange())


@bot.event
async def on_voice_state_update(member, before, after):
    if not ses_data_cache:
        ses_data_cache.update(load_ses())
    ses_data = ses_data_cache
    uid = str(member.id)
    if uid not in ses_data:
        ses_data[uid] = {"toplam_saniye": 0}

    # ── MUTE / DEAF LOG ─────────────────────────────────────────────────────
    async def mute_log_gonder(mesaj, renk):
        mute_kanal = discord.utils.get(member.guild.text_channels, name=MUTE_LOG_KANAL_ADI)
        if mute_kanal:
            try:
                await mute_kanal.send(embed=discord.Embed(
                    description=mesaj,
                    color=renk,
                    timestamp=discord.utils.utcnow()
                ).set_thumbnail(url=member.display_avatar.url))
            except Exception:
                pass

    # Sunucu susturma
    if before.mute != after.mute:
        if after.mute:
            await asyncio.sleep(1)
            sorumlu_mention = ""
            try:
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id:
                        sorumlu_mention = f" | Yetkili: {entry.user.mention}"
                        break
            except Exception:
                pass
            await mute_log_gonder(f"🔇 **Sunucu Susturma:** {member.mention} susturuldu{sorumlu_mention}", discord.Color.red())
        else:
            await asyncio.sleep(1)
            sorumlu_mention = ""
            try:
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id:
                        sorumlu_mention = f" | Yetkili: {entry.user.mention}"
                        break
            except Exception:
                pass
            await mute_log_gonder(f"🔊 **Sunucu Susturma Kaldırıldı:** {member.mention}{sorumlu_mention}", discord.Color.green())

    # Sunucu sağırlaştırma
    if before.deaf != after.deaf:
        if after.deaf:
            await asyncio.sleep(1)
            sorumlu_mention = ""
            try:
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id:
                        sorumlu_mention = f" | Yetkili: {entry.user.mention}"
                        break
            except Exception:
                pass
            await mute_log_gonder(f"🔕 **Sunucu Sağırlaştırma:** {member.mention} sağırlaştırıldı{sorumlu_mention}", discord.Color.red())
        else:
            await asyncio.sleep(1)
            sorumlu_mention = ""
            try:
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id:
                        sorumlu_mention = f" | Yetkili: {entry.user.mention}"
                        break
            except Exception:
                pass
            await mute_log_gonder(f"🔔 **Sunucu Sağırlaştırma Kaldırıldı:** {member.mention}{sorumlu_mention}", discord.Color.green())

    # Kendini susturma
    if before.self_mute != after.self_mute:
        if after.self_mute:
            await mute_log_gonder(f"🎙️ **Kendini Susturdu:** {member.mention}", discord.Color.orange())
        else:
            await mute_log_gonder(f"🎙️ **Kendini Susturmayı Kaldırdı:** {member.mention}", discord.Color.blue())

    # Kendini sağırlaştırma
    if before.self_deaf != after.self_deaf:
        if after.self_deaf:
            await mute_log_gonder(f"🎧 **Kendini Sağırlaştırdı:** {member.mention}", discord.Color.orange())
        else:
            await mute_log_gonder(f"🎧 **Kendini Sağırlaştırmayı Kaldırdı:** {member.mention}", discord.Color.blue())

    # ── YAYIN TAKİBİ ──────────────────────────────────────────────────────
    if not before.self_stream and after.self_stream:
        yayin_giris_takip[member.id] = time.time()
    elif before.self_stream and not after.self_stream:
        if member.id in yayin_giris_takip:
            gecen_sure = int(time.time() - yayin_giris_takip[member.id])
            del yayin_giris_takip[member.id]
            if gecen_sure > 0:
                siralama_verileri.setdefault("yayin", {})
                uid_str = str(member.id)
                siralama_verileri["yayin"][uid_str] = siralama_verileri["yayin"].get(uid_str, 0) + gecen_sure
                save_siralama()

    # ── 1) KANALA GİRDİ ──────────────────────────────────────────────────
    if before.channel is None and after.channel is not None:
        ses_giris_takip[member.id] = time.time()
        # return YOK — aşağıdaki oda oluşturma kodu çalışsın

    # ── 2) KANAL DEĞİŞTİRDİ ─────────────────────────────────────────────
    elif before.channel is not None and after.channel is not None:
        # ← AYNI KANAL İSE HİÇBİR ŞEY YAPMA
        if before.channel.id == after.channel.id:
            pass
        else:
            gecen_sure = 0
            if member.id in ses_giris_takip:
                gecen_sure = int(time.time() - ses_giris_takip[member.id])
            ses_giris_takip[member.id] = time.time()
            if gecen_sure > 0:
                ses_data[uid]["toplam_saniye"] += gecen_sure
                save_ses(ses_data)
                await _ses_embed_gonder(member, before.channel.name, after.channel, gecen_sure, ses_data[uid]["toplam_saniye"])
    # ── 3) KANALDAN ÇIKTI ────────────────────────────────────────────────
    elif before.channel is not None and after.channel is None:
        gecen_sure = 0
        if member.id in ses_giris_takip:
            gecen_sure = int(time.time() - ses_giris_takip[member.id])
            del ses_giris_takip[member.id]
        if gecen_sure > 0:
            ses_data[uid]["toplam_saniye"] += gecen_sure
            save_ses(ses_data)
            await _ses_embed_gonder(member, before.channel.name, None, gecen_sure, ses_data[uid]["toplam_saniye"])

    # ── ODA OLUŞTURMA ────────────────────────────────────────────────────
    if after.channel and after.channel.id == CREATE_VC_ID:
        guild = member.guild
        kategori = guild.get_channel(CATEGORY_ID)
        if not kategori or not isinstance(kategori, discord.CategoryChannel):
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True),
            member: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                manage_channels=True,
                mute_members=True,
                deafen_members=True
            )
        }

        try:
            yeni_kanal = await guild.create_voice_channel(
                name=f"🔊{member.display_name}",
                category=kategori,
                overwrites=overwrites
            )
            await member.move_to(yeni_kanal)
            TEMP_ROOMS[yeni_kanal.id] = member.id
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

    # ── ODA SİLME ────────────────────────────────────────────────────────
    if before.channel and before.channel.id in TEMP_ROOMS:
        if len(before.channel.members) == 0:
            try:
                await before.channel.delete()
                TEMP_ROOMS.pop(before.channel.id, None)
            except (discord.Forbidden, discord.HTTPException):
                pass

async def _ses_embed_gonder(member, onceki_kanal_adi, sonraki_kanal, gecen_sure, toplam):
    sessaat_kanali = discord.utils.get(
        member.guild.text_channels, name="ses-saat")
    if not sessaat_kanali:
        return

    if sonraki_kanal is not None:
        baslik = "🔄 Ses Kanalı Değiştirildi"
        alan_adi = "📢 Kanal Geçişi"
        aciklama = f"`{onceki_kanal_adi}` → `{sonraki_kanal.name}`"
    else:
        baslik = "🎙️ Ses Kanalı Özeti"
        alan_adi = "📢 Ayrılan Kanal"
        aciklama = f"`{onceki_kanal_adi}`"

    embed = discord.Embed(
        title=baslik, color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="👤 Üye",
                    value=member.mention,              inline=True)
    embed.add_field(name=alan_adi,              value=aciklama,
                    inline=True)
    embed.add_field(name="⏱️ Bu Seferki Süre",
                    value=f"**{sure_formatla(gecen_sure)}**", inline=True)
    embed.add_field(name="📊 Toplam Ses Süresi",
                    value=f"**{sure_formatla(toplam)}**",    inline=False)
    embed.set_footer(
        text=f"{member.guild.name} Ses Sistemi",
        icon_url=member.guild.icon.url if member.guild.icon else None
    )
    await sessaat_kanali.send(embed=embed)


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    if message.channel.id in MUAF_KANAL_IDLERI:
        return

    content = message.content.lower()
    u_id = message.author.id
    simdi = datetime.now()
    spam_tespit = False

    # ── REKLAM KONTROLÜ ──────────────────────────────────────────────────────
    if not message.author.guild_permissions.administrator:
        if any(reklam in content for reklam in REKLAM_UZANTILARI):
            try:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention}, reklam yapmak yasaktır!",
                    delete_after=5
                )
                await send_log(
                    message.guild,
                    f"🚫 Reklam Engellendi: {message.author.mention}",
                    discord.Color.red()
                )
                spam_tespit = True
            except Exception as e:
                print(f"Reklam silme hatası: {e}")

    # ── BOT KOMUTU KANAL KONTROLÜ ─────────────────────────────────────────────
    is_command = any(content.startswith(prefix) for prefix in KOMUT_ISARETLERI)
    if is_command:
        is_admin = message.author.guild_permissions.administrator
        is_whitelisted = u_id in BEYAZ_LISTE
        if not (is_admin or is_whitelisted) and message.channel.id not in [BOT_KANAL_ID, BOT_KANAL_ID2]:
            try:
                await message.delete()
                uyari = await message.channel.send(
                    f"⚠️ {message.author.mention}, bot komutlarını sadece "
                    f"<#{BOT_KANAL_ID}> kanalında kullanabilirsin!"
                )
                await asyncio.sleep(5)
                await uyari.delete()
                return
            except Exception as e:
                print(f"Komut kanal hatası: {e}")

    # ── UZUN MESAJ KONTROLÜ ──────────────────────────────────────────────────
    if not message.author.guild_permissions.administrator:
        if len(message.content) > 500:
            try:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention}, çok uzun mesaj!",
                    delete_after=5
                )
                await send_log(
                    message.guild,
                    f"🚫 Uzun Mesaj: {message.author.mention}",
                    discord.Color.orange()
                )
                spam_tespit = True
            except Exception as e:
                print(f"Uzun mesaj silme hatası: {e}")

    # ── KELİME TEKRARI KONTROLÜ ───────────────────────────────────────────────
    if not message.author.guild_permissions.administrator:
        kelimeler = message.content.lower().split()
        if len(kelimeler) > 5:
            for kelime in set(kelimeler):
                tekrar = kelimeler.count(kelime)
                if tekrar > 10 or (tekrar / len(kelimeler)) > 0.5:
                    try:
                        await message.delete()
                        await message.channel.send(
                            f"⚠️ {message.author.mention}, kelime tekrarı yasak!",
                            delete_after=5
                        )
                        await send_log(
                            message.guild,
                            f"🚫 Kelime Tekrarı: {message.author.mention} '{kelime}' {tekrar}x",
                            discord.Color.orange()
                        )
                        spam_tespit = True
                    except Exception as e:
                        print(f"Kelime tekrarı silme hatası: {e}")
                    break

    # ── SPAM SAYACI (total_seconds() ile düzeltildi) ──────────────────────────
    spam_takip.setdefault(u_id, [])
    spam_takip[u_id] = [
        t for t in spam_takip[u_id]
        # .seconds → .total_seconds()
        if (simdi - t).total_seconds() < SPAM_ZAMANI
    ]
    spam_takip[u_id].append(simdi)

    # ── SPAM LİMİT KONTROLÜ (spam_tespit'ten bağımsız çalışır) ───────────────
    if not message.author.guild_permissions.administrator:
        if len(spam_takip[u_id]) > SPAM_LIMIT:
            spam_tespit = True
            try:
                await message.channel.purge(
                    limit=SPAM_LIMIT + 1,
                    check=lambda m: m.author == message.author,
                    bulk=True
                )
            except Exception as e:
                print(f"Purge hatası: {e}")

    # ── CEZA BLOĞU ────────────────────────────────────────────────────────────
    if spam_tespit:
        # Çift ceza kilidini önle
        if u_id in ceza_kilidi and (simdi - ceza_kilidi[u_id]).total_seconds() < 5:
            return
        ceza_kilidi[u_id] = simdi

        spam_ceza_takip.setdefault(u_id, [])
        spam_ceza_takip[u_id] = [
            t for t in spam_ceza_takip[u_id]
            if (simdi - t).total_seconds() < 86400
        ]
        spam_ceza_takip[u_id].append(simdi)
        ihlal_sayisi = len(spam_ceza_takip[u_id])

        if ihlal_sayisi >= 3:
            # 3. ihlalde 7 gün ban
            spam_ceza_takip[u_id] = []
            if u_id in spam_takip:
                spam_takip[u_id] = []
            try:
                await message.author.timeout(timedelta(days=7), reason="3. İhlal")
                await message.channel.send(
                    f"🛑 {message.author.mention}, 3. ihlal — **7 GÜN** susturuldu!"
                )
                await send_log(
                    message.guild,
                    f"🚫 7 Gün Ceza: {message.author.mention}",
                    discord.Color.red()
                )
            except Exception as e:
                print(f"7 gün timeout hatası: {e}")
        else:
            # 1. ve 2. ihlalde 10 dakika
            try:
                await message.author.timeout(timedelta(minutes=10), reason="Spam/İhlal")
                await message.channel.send(
                    f"⚠️ {message.author.mention}, 10 dk susturuldu! ({ihlal_sayisi}/3)",
                    delete_after=10
                )
                await send_log(
                    message.guild,
                    f"⚠️ 10 Dk Ceza: {message.author.mention} ({ihlal_sayisi}/3)",
                    discord.Color.orange()
                )
            except Exception as e:
                print(f"10 dk timeout hatası: {e}")
        return

    # ── BOT CEVAPLARI ─────────────────────────────────────────────────────────
    bot_isimlari = ["bot", "z3ittanistan", bot.user.mention]
    bota_mi_soylendi = any(isim in content for isim in bot_isimlari)

    if content == "sa":
        await message.channel.send(f"cami mi bura oç {message.author.mention}!")

    if any(k in content for k in ["selam", "selamun aleyküm", "sea", "selamlar"]):
        await message.channel.send(f"cami mi bura oç {message.author.mention}!")

    if bota_mi_soylendi:
        if "amina koyim" in content or "amına koyim" in content:
            await message.channel.send(f"Ben senin amına koyim {message.author.mention}")
        if any(k in content for k in ["ananın amı", "anayın amı", "ananin ami", "anayin ami"]):
            await message.channel.send(f"Senin ananın amı {message.author.mention}")
        if any(k in content for k in [
            "ananı sikeyim", "anani sikeyim", "oç", "ananı sikerim", "anani sikerim",
            "orospu evladı", "oc", "orospu çocuğu", "orospu cocugu",
            "ananı sikiyim", "anani sikiyim", "anani sikim", "ananı sikim"
        ]):
            yanit = random.choice([
                f"😤 Gel baş kaldır bana {message.author.mention}!",
                f"👀 Gel bana bakış at {message.author.mention}",
                f"🤫 Konuşma salağın amından çıkma {message.author.mention}",
                f"😂 Yeni yetme orospu evladı seni {message.author.mention}",
                f"🙏 Anan sikilir inşallah {message.author.mention}",
                f"💀 Sevgilimin oğluna bak sen hele {message.author.mention}",
                f"Senin ananı sikeyim orospu evladı {message.author.mention}",
            ])
            await message.channel.send(yanit)
        elif "amk" in content:
            await message.channel.send(f"Senin amk {message.author.mention}")

    # ── LİDERLİK TABLOSU (MESAJ) ──────────────────────────────────────────────
    uid_str = str(message.author.id)
    siralama_verileri.setdefault("mesajlar", {})
    siralama_verileri["mesajlar"][uid_str] = siralama_verileri["mesajlar"].get(uid_str, 0) + 1
    save_siralama()

    # ── LEVEL + EKONOMİ ───────────────────────────────────────────────────────
    levels.setdefault(uid_str, {"xp": 0, "level": 0})
    levels[uid_str]["xp"] += 2
    lvl = levels[uid_str]["level"]
    next_lvl_xp = (lvl + 1) * 70

    if levels[uid_str]["xp"] >= next_lvl_xp:
        levels[uid_str]["level"] += 1
        yeni_lvl = levels[uid_str]["level"]
        check_user(uid_str)
        economy[uid_str]["balance"] += yeni_lvl * 100
        save_economy()
        if str(yeni_lvl) in LEVEL_ROLLER:
            rol_adi = LEVEL_ROLLER[str(yeni_lvl)]
            rol = discord.utils.get(message.guild.roles, name=rol_adi)
            if rol:
                try:
                    await message.author.add_roles(rol, reason="Level Sistemi")
                    await send_log(
                        message.guild,
                        f"🎖️ Level Rolü: {message.author.mention} → {rol_adi}",
                        discord.Color.gold()
                    )
                except Exception as e:
                    print(f"Rol verme hatası: {e}")
        save_levels()

    await bot.process_commands(message)


@bot.event
async def on_audit_log_entry_create(entry):
    if entry.action == discord.AuditLogAction.ban:
        target = entry.target
        user = entry.user
        reason = entry.reason or "Sebep belirtilmedi."
        embed = discord.Embed(title="🔨 Manuel Ban", color=discord.Color.red())
        embed.add_field(name="Yasaklanan",
                        value=f"{target.name} ({target.id})", inline=False)
        embed.add_field(name="Yasaklayan", value=user.mention, inline=False)
        embed.add_field(name="Sebep",      value=reason, inline=False)
        await send_log(entry.guild, embed=embed)


# ─────────────────────────────────────────────────────────────────────────────
# BLACKJACK VIEW  (değiştirilmedi)
# ─────────────────────────────────────────────────────────────────────────────
class BlackjackView(View):
    """
    MİGRASYON NOTU:
      Bu View sınıfı prefix komutundan slash komutuna geçişte tamamen
      korunabilir. Button'lar interaction üzerinden çalışmaya devam eder.
      Tek değişiklik: ctx parametresi yerine 'author' kimliğini saklamak.
    """

    def __init__(self, author_id, oyuncu_el, kasa_el, deck, ranks,
                 get_card, calculate, format_hand, bahis, economy, u_id):
        super().__init__(timeout=60.0)
        self.author_id = author_id       # ← ctx.author.id yerine
        self.oyuncu_el = oyuncu_el
        self.kasa_el = kasa_el
        self.deck = deck
        self.ranks = ranks
        self.get_card = get_card
        self.calculate = calculate
        self.format_hand = format_hand
        self.bahis = bahis
        self.economy = economy
        self.u_id = u_id

    async def finalize_game(self, interaction):
        o_skor = self.calculate(self.oyuncu_el)
        while self.calculate(self.kasa_el) < 17 and o_skor <= 21:
            self.kasa_el.append(self.get_card())
        k_skor = self.calculate(self.kasa_el)

        if o_skor > 21:
            txt = f"💥 **Bust!** -{self.bahis} Coin"
            self.economy[self.u_id]["balance"] -= self.bahis
            final_color = discord.Color.red()
        elif k_skor > 21 or o_skor > k_skor:
            txt = f"🎉 **Kazandın!** +{self.bahis} Coin"
            self.economy[self.u_id]["balance"] += self.bahis
            final_color = discord.Color.green()
        elif o_skor < k_skor:
            txt = f"💀 **Kaybettin!** -{self.bahis} Coin"
            self.economy[self.u_id]["balance"] -= self.bahis
            final_color = discord.Color.red()
        else:
            txt = "🤝 **Beraberlik!**"
            final_color = discord.Color.gold()

        save_economy()

        embed = discord.Embed(title="🃏 Oyun Sonucu", description=txt, color=final_color)
        embed.add_field(name=f"Kasa [{k_skor}]", value=self.format_hand(self.kasa_el), inline=True)
        embed.add_field(name=f"Sen [{o_skor}]", value=self.format_hand(self.oyuncu_el), inline=True)

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="👊 Kart Çek (Hit)", style=discord.ButtonStyle.green)
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Bu senin oyunun değil!", ephemeral=True)

        # Deck boşsa hata vermesin
        if not self.deck:
            return await interaction.response.send_message("❌ Deste bitti!", ephemeral=True)

        self.oyuncu_el.append(self.get_card())
        score = self.calculate(self.oyuncu_el)

        if score >= 21:
            await self.finalize_game(interaction)
        else:
            embed = discord.Embed(title="🃏 Blackjack Masası", color=discord.Color.blue())
            embed.add_field(
                name=f"Kasa [{self.ranks[self.kasa_el[0][0]]}]",
                value=f"`{self.kasa_el[0][0]}{self.kasa_el[0][1]}` ❓",
                inline=True
            )
            embed.add_field(
                name=f"Sen [{score}]",
                value=self.format_hand(self.oyuncu_el),
                inline=True
            )
            await interaction.response.edit_message(embed=embed, view=self)  # ← view=self EKLENDİ

    @discord.ui.button(label="🛑 Dur (Stand)", style=discord.ButtonStyle.red)
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Bu senin oyunun değil!", ephemeral=True)

        await self.finalize_game(interaction)


# ═════════════════════════════════════════════════════════════════════════════
#  COG 1 — YÖNETİM (Whitelist & Para Yönetimi)
# ═════════════════════════════════════════════════════════════════════════════
class AdminCog(commands.Cog):

    admin_group = app_commands.Group(
        name="admin", description="Yönetici komutları")

    @admin_group.command(name="beyazliste", description="Beyaz listeye üye ekler veya çıkarır")
    @app_commands.describe(
        islem="ekle veya cikar",
        hedef="Üye etiketi (@üye) veya ID"
    )
    async def beyazliste(self, interaction: discord.Interaction,
                         islem: str, hedef: str):
        if interaction.user.id != OZEL_SAHIP_ID:
            return await interaction.response.send_message(
                "🚫 **Yetki Reddedildi:** Bu komut sadece bot sahibine özeldir!", ephemeral=True
            )

        # ID veya mention'dan kullanıcı ID'sini çek
        try:
            uid = int(re.sub(r"[<@!>]", "", hedef))
        except ValueError:
            return await interaction.response.send_message("❌ Geçerli bir kullanıcı etiketi veya ID gir!", ephemeral=True)

        # Kullanıcıyı fetch et (sunucuda olmasa bile)
        try:
            user = interaction.guild.get_member(uid) or await interaction.client.fetch_user(uid)
        except discord.NotFound:
            return await interaction.response.send_message("❌ Bu ID'ye ait kullanıcı bulunamadı!", ephemeral=True)

        islem = islem.lower().strip()

        if islem == "ekle":
            if uid in BEYAZ_LISTE:
                return await interaction.response.send_message("❌ Zaten listede.", ephemeral=True)
            BEYAZ_LISTE.append(uid)
            save_white_list()  # ← diske kaydet
            await interaction.response.send_message(f"✅ {user.mention} (`{uid}`) beyaz listeye eklendi.")
            await send_log(interaction.guild, f"🛡️ Beyaz Liste: {user.mention} (`{uid}`) eklendi.", discord.Color.green())

        elif islem in ["cikar", "çıkar", "kaldir", "kaldır"]:
            if uid not in BEYAZ_LISTE:
                return await interaction.response.send_message("❌ Bu kullanıcı listede değil.", ephemeral=True)
            BEYAZ_LISTE.remove(uid)
            save_white_list()  # ← diske kaydet
            await interaction.response.send_message(f"✅ {user.mention} (`{uid}`) beyaz listeden çıkarıldı.")
            await send_log(interaction.guild, f"🛡️ Beyaz Liste: {user.mention} (`{uid}`) çıkarıldı.", discord.Color.red())

        else:
            await interaction.response.send_message("❓ `ekle` veya `cikar` yazmalısın.", ephemeral=True)
    # ── /admin beyazlisteliste ─────────────────────────────────────────────
    # ESKİ: .beyazlisteliste
    @admin_group.command(name="beyazlisteliste", description="Beyaz listedeki üyeleri gösterir")
    async def beyazlisteliste(self, interaction: discord.Interaction):
        if interaction.user.id != OZEL_SAHIP_ID and interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("🚫 Yetkin yok!", ephemeral=True)
        liste_metni = "\n".join(
            [f"• <@{uid}> (`{uid}`)" for uid in BEYAZ_LISTE]) or "Liste boş."
        embed = discord.Embed(title="🛡️ Beyaz Liste Kayıtları",
                              description=liste_metni, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    # ── /admin parabas ─────────────────────────────────────────────────────
    # ESKİ: .parabas / .ekle / .paraver
    @admin_group.command(name="parabas", description="Üyeye coin ekler (Beyaz liste)")
    @app_commands.describe(member="Alıcı üye", miktar="Eklenecek coin miktarı")
    async def parabas(self, interaction: discord.Interaction,
                      member: discord.Member, miktar: int):
        if interaction.user.id not in BEYAZ_LISTE and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("🚫 Yetki Yok!", ephemeral=True)
        SINIR = 10_000_000
        if miktar > SINIR:
            return await interaction.response.send_message(f"⚠️ Tek seferde max {SINIR:,} Coin!", ephemeral=True)
        if miktar <= 0:
            return await interaction.response.send_message("⚠️ Geçerli bir miktar girin!", ephemeral=True)
        u_id = str(member.id)
        check_user(u_id)
        economy[u_id]["balance"] += miktar
        save_economy()
        embed = discord.Embed(
            title="💸 Para Basıldı!", description=f"{interaction.user.mention}, {member.mention} hesabına **{miktar} Coin** ekledi!", color=discord.Color.gold(), timestamp=discord.utils.utcnow())
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, f"💰 Para Basma: {interaction.user.mention} → {member.mention} | {miktar} Coin", discord.Color.gold())

    # ── /admin parasil ─────────────────────────────────────────────────────
    # ESKİ: .parasil / .bakiyesifirla / .paracep
    @admin_group.command(name="parasil", description="Üyeden coin siler (Beyaz liste / Sahip)")
    @app_commands.describe(member="Hedef üye", miktar="Silinecek coin miktarı")
    async def parasil(self, interaction: discord.Interaction,
                      member: discord.Member, miktar: int):
        if interaction.user.id != OZEL_SAHIP_ID and interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("🚫 Yetki Yok!", ephemeral=True)
        u_id = str(member.id)
        check_user(u_id)
        mevcut = economy[u_id]["balance"]
        if miktar > mevcut:
            miktar = mevcut
        economy[u_id]["balance"] -= miktar
        save_economy()
        embed = discord.Embed(
            title="📉 Para Silindi!", description=f"{member.mention} hesabından **{miktar} Coin** silindi.\nYeni Bakiye: `{economy[u_id]['balance']}` Coin", color=discord.Color.red(), timestamp=discord.utils.utcnow())
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, f"🔻 Para Silme: {interaction.user.mention} → {member.mention} | {miktar} Coin", discord.Color.red())

    # ── /duyuru ──────────────────────────────────────────────────────────────
    @app_commands.command(name="duyuru", description="Sunucuya şık bir embed ile duyuru gönderir (@everyone atar)")
    @app_commands.describe(
        mesaj="Duyuru metni (Alt satıra geçmek için \\n kullanabilirsiniz)",
        baslik="Embed başlığı (opsiyonel)"
    )
    async def duyuru(self, interaction: discord.Interaction, mesaj: str, baslik: str = None):
        if not interaction.user.guild_permissions.administrator and interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("🚫 Bu komutu kullanma yetkin yok!", ephemeral=True)
            
        mesaj_temiz = mesaj.replace("\\n", "\n")
        
        embed = BotUI.embed(
            title=baslik,
            desc=mesaj_temiz,
            color=0x5865F2  # Blurple / Mavi renk (örnekteki gibi)
        )
        
        await interaction.response.send_message("✅ Duyuru gönderiliyor...", ephemeral=True)
        await interaction.channel.send(content="@everyone", embed=embed)

    # ── /dm ──────────────────────────────────────────────────────────────────
    @app_commands.command(name="dm", description="Belirli bir kişiye veya sunucudaki herkese DM gönderir")
    @app_commands.describe(
        hedef="DM gönderilecek üye (boş bırakırsan sunucudaki herkese gönderilir)",
        mesaj="Gönderilecek mesaj (Alt satır için \\n kullanabilirsiniz)",
        baslik="Embed başlığı (opsiyonel)"
    )
    async def dm_gonder(self, interaction: discord.Interaction, mesaj: str, hedef: discord.Member = None, baslik: str = None):
        if not interaction.user.guild_permissions.administrator and interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("🚫 Bu komutu kullanma yetkin yok!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        mesaj_temiz = mesaj.replace("\\n", "\n")

        if hedef:
            # Tek kişiye DM
            embed = BotUI.embed(
                title=baslik or "📬 Sunucu Mesajı",
                desc=f"{hedef.mention}\n\n{mesaj_temiz}",
                color=0x5865F2
            )
            embed.set_footer(text=f"{interaction.guild.name} sunucusundan gönderildi")
            try:
                await hedef.send(embed=embed)
                await interaction.followup.send(
                    BotUI.success(f"{hedef.mention} kullanıcısına DM başarıyla gönderildi."),
                    ephemeral=True
                )
                await send_log(interaction.guild,
                    f"📬 DM Gönderildi: {interaction.user.mention} → {hedef.mention}",
                    discord.Color.blurple())
            except discord.Forbidden:
                await interaction.followup.send(
                    BotUI.error(f"{hedef.mention} kullanıcısının DM'leri kapalı, mesaj gönderilemedi."),
                    ephemeral=True
                )
        else:
            # Sunucudaki herkese DM
            await interaction.followup.send(
                BotUI.warn(f"Sunucudaki tüm üyelere DM gönderiliyor... Bu işlem biraz sürebilir."),
                ephemeral=True
            )
            basarili = 0
            basarisiz = 0
            for member in interaction.guild.members:
                if member.bot:
                    continue
                embed = BotUI.embed(
                    title=baslik or "📬 Sunucu Duyurusu",
                    desc=f"{member.mention}\n\n{mesaj_temiz}",
                    color=0x5865F2
                )
                embed.set_footer(text=f"{interaction.guild.name} sunucusundan gönderildi")
                try:
                    await member.send(embed=embed)
                    basarili += 1
                    await asyncio.sleep(0.5)  # Rate limit koruması
                except discord.Forbidden:
                    basarisiz += 1
                except Exception:
                    basarisiz += 1
            await interaction.channel.send(
                BotUI.success(f"Toplu DM tamamlandı! ✅ {basarili} başarılı | ❌ {basarisiz} başarısız (DM kapalı)")
            )
            await send_log(interaction.guild,
                f"📬 Toplu DM: {interaction.user.mention} tarafından gönderildi | ✅ {basarili} | ❌ {basarisiz}",
                discord.Color.blurple())



# ═════════════════════════════════════════════════════════════════════════════
#  COG 2 — EKONOMİ
# ═════════════════════════════════════════════════════════════════════════════
class EkonomiCog(commands.Cog):



    # ── /ekonomi bakiye ────────────────────────────────────────────────────
    # ESKİ: .bakiye [@üye]
    @app_commands.command(name="bakiye", description="Coin bakiyesini gösterir")
    @app_commands.describe(member="Bakiyesine bakılacak üye (boş = sen)")
    async def bakiye(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user  # MİGRASYON: ctx.author → interaction.user
        u_id = str(member.id)
        check_user(u_id)
        embed = BotUI.embed(
            title="💰 Bakiye Bilgisi", 
            desc=f"{member.mention} kullanıcısının mevcut bakiyesi:\n\n🪙 **{economy[u_id]['balance']:,} Coin**",
            color=BotUI.COLOR_INFO,
            user=interaction.user
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # ── /ekonomi daily ─────────────────────────────────────────────────────
    # ESKİ: .daily / .günlük / .gunluk
    # MİGRASYON: commands.cooldown → app_commands.checks.cooldown
    @app_commands.command(name="daily", description="Günlük 5000 Coin ödülü al")
    @app_commands.checks.cooldown(1, 86400, key=lambda i: i.user.id)
    async def daily(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        check_user(u_id)
        odul = 5000
        economy[u_id]["balance"] += odul
        save_economy()
        embed = BotUI.embed(
            title="💸 Günlük Ödül", 
            desc=f"Tebrikler {interaction.user.mention}!\nGünlük giriş ödülü olarak hesabınıza **{odul:,} Coin** eklendi.", 
            color=BotUI.COLOR_SUCCESS,
            user=interaction.user
        )
        await interaction.response.send_message(embed=embed)

    # ── /ekonomi coinflip ──────────────────────────────────────────────────
    # ESKİ: .coinflip / .yt / .yazitura / .cf
    @app_commands.command(name="cf", description="Yazı-Tura oyna")
    @app_commands.describe(miktar="Bahis miktarı veya 'all'")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def coinflip(self, interaction: discord.Interaction, miktar: str):
        u_id = str(interaction.user.id)
        check_user(u_id)
        if miktar.lower() == "all":
            bahis = economy[u_id]["balance"]
        else:
            try:
                bahis = int(miktar)
            except:
                return await interaction.response.send_message(BotUI.error("Geçerli bir miktar gir veya `all` yaz!"), ephemeral=True)
        if bahis <= 0:
            return await interaction.response.send_message(BotUI.error("En az 1 Coin ile oynayabilirsiniz!"), ephemeral=True)
        if economy[u_id]["balance"] < bahis:
            return await interaction.response.send_message(BotUI.error(f"Bakiyen yetersiz! (Mevcut: **{economy[u_id]['balance']} Coin**)"), ephemeral=True)

        await interaction.response.defer()

        # Animasyon kareleri
        animasyon = ["🪙", "✨🪙✨", "💫🪙💫", "⭐🪙⭐", "🌟🪙🌟"]
        embed = discord.Embed(title="🪙 Yazı-Tura", description="Madeni para havaya fırlatıldı...", color=discord.Color.gold())
        embed.add_field(name="Bahis", value=f"**{bahis} Coin**", inline=True)
        mesaj = await interaction.followup.send(embed=embed)

        for kare in animasyon:
            embed.description = f"{kare} Madeni para döndürülüyor... {kare}"
            await mesaj.edit(embed=embed)
            await asyncio.sleep(0.6)

        # Sonuç
        sonuc = random.choice(["kazandın", "kaybettin"])
        if sonuc == "kazandın":
            economy[u_id]["balance"] += bahis
            embed.title = "🎉 KAZANDIN!"
            embed.description = f"**YAZI** geldi!"
            embed.color = discord.Color.green()
            embed.set_field_at(0, name="Kazanç", value=f"**+{bahis} Coin**", inline=True)
            embed.add_field(name="💰 Yeni Bakiye", value=f"**{economy[u_id]['balance']} Coin**", inline=True)
        else:
            economy[u_id]["balance"] -= bahis
            embed.title = "💀 KAYBETTİN!"
            embed.description = f"**TURA** geldi!"
            embed.color = discord.Color.red()
            embed.set_field_at(0, name="Kayıp", value=f"**-{bahis} Coin**", inline=True)
            embed.add_field(name="💰 Kalan Bakiye", value=f"**{economy[u_id]['balance']} Coin**", inline=True)

        save_economy()
        await mesaj.edit(embed=embed)
    # ── /ekonomi slot ──────────────────────────────────────────────────────
    # ESKİ: .slot [miktar]
    @app_commands.command(name="slot", description="Slot makinesini döndür")
    @app_commands.describe(miktar="Bahis miktarı veya 'all'")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def slot(self, interaction: discord.Interaction, miktar: str):
        u_id = str(interaction.user.id)
        check_user(u_id)
        if miktar.lower() == "all":
            bahis = economy[u_id]["balance"]
        else:
            try:
                bahis = int(miktar)
            except:
                return await interaction.response.send_message("❌ Miktar gir veya `all` yaz!", ephemeral=True)
        if bahis <= 0 or economy[u_id]["balance"] < bahis:
            return await interaction.response.send_message("❌ Bakiyen yetersiz!", ephemeral=True)

        emoji_list = ["🍒", "🍋", "🔔", "💎", "🎰", "🍎"]
        await interaction.response.defer()

        # Başlangıç embed
        embed = discord.Embed(title="🎰 SLOT MAKİNESİ", color=discord.Color.gold())
        embed.add_field(name="Bahis", value=f"**{bahis} Coin**", inline=False)
        embed.add_field(name="Teker", value="🎰 | 🎰 | 🎰", inline=False)
        mesaj = await interaction.followup.send(embed=embed)

        # Sonuçları önceden belirle
        a = random.choice(emoji_list)
        b = random.choice(emoji_list)
        c = random.choice(emoji_list)

        # Animasyon — her teker sırayla duruyor
        for i in range(6):
            if i < 3:
                s1 = random.choice(emoji_list)
                s2 = random.choice(emoji_list)
                s3 = random.choice(emoji_list)
                embed.set_field_at(1, name="Teker", value=f"{s1} | {s2} | {s3}", inline=False)
            elif i == 3:
                # İlk teker durdu
                s2 = random.choice(emoji_list)
                s3 = random.choice(emoji_list)
                embed.set_field_at(1, name="Teker", value=f"**{a}** | {s2} | {s3}", inline=False)
            elif i == 4:
                # İkinci teker durdu
                s3 = random.choice(emoji_list)
                embed.set_field_at(1, name="Teker", value=f"**{a}** | **{b}** | {s3}", inline=False)
            else:
                # Üçüncü teker durdu
                embed.set_field_at(1, name="Teker", value=f"**{a}** | **{b}** | **{c}**", inline=False)

            await mesaj.edit(embed=embed)
            await asyncio.sleep(0.5)

        # Sonuç hesapla
        if a == b == c:
            kazanc = bahis * 5
            economy[u_id]["balance"] += kazanc
            embed.title = "🎊 JACKPOT!"
            embed.color = discord.Color.from_rgb(255, 215, 0)
            sonuc_txt = f"✅ **+{kazanc} Coin** (5x)"
        elif a == b or b == c or a == c:
            kazanc = int(bahis * 1.5)
            economy[u_id]["balance"] += kazanc
            embed.title = "✨ İkili!"
            embed.color = discord.Color.green()
            sonuc_txt = f"✅ **+{kazanc} Coin** (1.5x)"
        else:
            economy[u_id]["balance"] -= bahis
            embed.title = "💀 Kaybettin!"
            embed.color = discord.Color.red()
            sonuc_txt = f"❌ **-{bahis} Coin**"

        save_economy()
        embed.set_field_at(1, name=f"[ {a} | {b} | {c} ]", value=sonuc_txt, inline=False)
        embed.add_field(name="💰 Bakiye", value=f"**{economy[u_id]['balance']} Coin**", inline=False)
        await mesaj.edit(embed=embed)

    # ── /ekonomi gonder ────────────────────────────────────────────────────
    # ESKİ: .gonder / .gönder / .send
    @app_commands.command(name="gonder", description="Başka birine coin gönder")
    @app_commands.describe(member="Alıcı üye", miktar="Gönderilecek coin")
    async def gonder(self, interaction: discord.Interaction,
                     member: discord.Member, miktar: int):
        u_id = str(interaction.user.id)
        t_id = str(member.id)
        check_user(u_id)
        check_user(t_id)
        if miktar <= 0 or economy[u_id]["balance"] < miktar:
            return await interaction.response.send_message("❌ Geçersiz miktar veya yetersiz bakiye!", ephemeral=True)
        economy[u_id]["balance"] -= miktar
        economy[t_id]["balance"] += miktar
        save_economy()
        await interaction.response.send_message(f"✅ {member.mention} kişisine **{miktar} Coin** gönderildi.")

    # ── /ekonomi soy ───────────────────────────────────────────────────────
    # ESKİ: .soy @üye
    @app_commands.command(name="soy", description="Birisini soy (dikkat: yakalanabilirsin!)")
    @app_commands.describe(member="Soyulacak üye")
    @app_commands.checks.cooldown(1, 600, key=lambda i: i.user.id)
    async def soy(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("Kendi kendini soyamazsın! 😂", ephemeral=True)
        if member.id in BEYAZ_LISTE:
            return await interaction.response.send_message(f"🛡️ {member.mention} koruma altında!", ephemeral=True)
        u_id = str(interaction.user.id)
        t_id = str(member.id)
        check_user(u_id)
        check_user(t_id)
        if economy[t_id]["balance"] < 100:
            return await interaction.response.send_message("Bu kişide para yok, soymaya değmez.", ephemeral=True)
        await interaction.response.defer()
        if random.randint(1, 100) <= 40:
            ust_limit = int(economy[t_id]["balance"] * 0.2)
            calinan = random.randint(50, ust_limit) if ust_limit > 50 else 50
            economy[t_id]["balance"] -= calinan
            economy[u_id]["balance"] += calinan
            save_economy()
            await interaction.followup.send(f"🥷 {interaction.user.mention}, {member.mention} kişisini soydu! **+{calinan} Coin**")
        else:
            try:
                await interaction.user.timeout(timedelta(minutes=2), reason="Soygun yaparken yakalandı!")
                await interaction.followup.send(f"🚨 **YAKALANDIN!** {interaction.user.mention}, 2 dakika susturuldu!")
            except:
                await interaction.followup.send(f"🚨 Yakalandın! (Yetkim yetmedi.)")
            await send_log(interaction.guild, f"🚫 Soygun Girişimi: {interaction.user.mention} yakalandı.", discord.Color.red())

    # ── /ekonomi sweetbonanza ──────────────────────────────────────────────
    # ESKİ: .sweetbonanza / .sweet / .bonanza / .sb
    @app_commands.command(name="sweetbonanza", description="🍭 Sweet Bonanza slot oyunu")
    @app_commands.describe(miktar="Bahis miktarı veya 'all'")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def sweetbonanza(self, interaction: discord.Interaction, miktar: str):
        u_id = str(interaction.user.id)
        check_user(u_id)
        if miktar.lower() == "all":
            bahis = economy[u_id]["balance"]
        else:
            try:
                bahis = int(miktar)
            except:
                return await interaction.response.send_message("❌ Geçerli bir miktar gir veya `all` yaz!", ephemeral=True)
        if bahis < 10:
            return await interaction.response.send_message("❌ Min 10 Coin!", ephemeral=True)
        if economy[u_id]["balance"] < bahis:
            return await interaction.response.send_message("❌ Bakiyen yetersiz!", ephemeral=True)

        semboller = ["🍎", "🍇", "🍉", "🍌", "🟦", "🟪", "❤️"]
        seker = "🍭"
        await interaction.response.defer()

        # Başlangıç embed
        embed = discord.Embed(title="🍭 SWEET BONANZA", color=discord.Color.from_rgb(255, 20, 147))
        embed.add_field(name="Bahis", value=f"**{bahis} Coin**", inline=False)
        embed.add_field(name="Teker", value="🍭 | 🍭 | 🍭 | 🍭", inline=False)
        mesaj = await interaction.followup.send(embed=embed)

        # Sonuçları önceden belirle
        s1 = random.choice(semboller + [seker])
        s2 = random.choice(semboller + [seker])
        s3 = random.choice(semboller + [seker])
        s4 = random.choice(semboller + [seker])
        sonuc = [s1, s2, s3, s4]

        # Animasyon — tekerlekler sırayla duruyor
        for i in range(7):
            if i < 3:
                # Hepsi dönüyor
                r = [random.choice(semboller + [seker]) for _ in range(4)]
                embed.set_field_at(1, name="Teker", value=f"{r[0]} | {r[1]} | {r[2]} | {r[3]}", inline=False)
            elif i == 3:
                r = [random.choice(semboller + [seker]) for _ in range(3)]
                embed.set_field_at(1, name="Teker", value=f"**{s1}** | {r[0]} | {r[1]} | {r[2]}", inline=False)
            elif i == 4:
                r = [random.choice(semboller + [seker]) for _ in range(2)]
                embed.set_field_at(1, name="Teker", value=f"**{s1}** | **{s2}** | {r[0]} | {r[1]}", inline=False)
            elif i == 5:
                r = random.choice(semboller + [seker])
                embed.set_field_at(1, name="Teker", value=f"**{s1}** | **{s2}** | **{s3}** | {r}", inline=False)
            else:
                embed.set_field_at(1, name="Teker", value=f"**{s1}** | **{s2}** | **{s3}** | **{s4}**", inline=False)

            await mesaj.edit(embed=embed)
            await asyncio.sleep(0.5)

        # Sonuç hesapla
        seker_sayisi = sonuc.count(seker)
        kalp_sayisi = sonuc.count("❤️")
        ayni_sembol = max([sonuc.count(s) for s in semboller]) if semboller else 0
        carpan = 0

        if seker_sayisi >= 3:
            carpan = 10 if seker_sayisi == 3 else 25
            durum = "🍭 **SCATTER! JACKPOT!**"
            embed.color = discord.Color.from_rgb(255, 215, 0)
        elif kalp_sayisi >= 3:
            carpan = 6
            durum = "❤️ **KALPLER PATLADI!**"
            embed.color = discord.Color.red()
        elif ayni_sembol == 4:
            carpan = 5
            durum = "✨ **TAM KOMBO!**"
            embed.color = discord.Color.green()
        elif seker_sayisi == 2 or ayni_sembol == 3:
            carpan = 2
            durum = "🍬 **GÜZEL PATLAMA!**"
            embed.color = discord.Color.green()
        elif seker_sayisi == 1:
            carpan = 1.2
            durum = "🍭 **ŞEKER TESELLİSİ**"
            embed.color = discord.Color.blurple()
        else:
            durum = "💀 **HÜSRAN...**"
            embed.color = discord.Color.red()

        if carpan > 0:
            kazanc = int(bahis * carpan)
            economy[u_id]["balance"] += (kazanc - bahis)
            son_msg = f"✅ **+{kazanc} Coin** ({carpan}x)"
        else:
            economy[u_id]["balance"] -= bahis
            son_msg = f"❌ **-{bahis} Coin**"

        save_economy()

        embed.title = "🍭 SWEET BONANZA"
        embed.set_field_at(1, name=f"[ {s1} | {s2} | {s3} | {s4} ]", value=f"{durum}\n\n{son_msg}", inline=False)
        embed.add_field(name="💰 Cüzdan", value=f"**{economy[u_id]['balance']} Coin**", inline=False)
        await mesaj.edit(embed=embed)

    # ── /ekonomi blackjack ─────────────────────────────────────────────────
    # ESKİ: .blackjackyeni / .bj / .blackjack
    @app_commands.command(name="blackjack", description="🃏 Blackjack masasına otur")
    @app_commands.describe(bahis="Bahis miktarı veya 'all'")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def blackjack(self, interaction: discord.Interaction, bahis: str):
        u_id = str(interaction.user.id)
        check_user(u_id)
        current_balance = economy[u_id]["balance"]
        if bahis.lower() == "all":
            bahis_miktari = current_balance
        else:
            try:
                bahis_miktari = int(bahis)
            except:
                return await interaction.response.send_message("Geçerli bir sayı veya `all` yaz!", ephemeral=True)
        if bahis_miktari < 10:
            return await interaction.response.send_message("Min 10 Coin!", ephemeral=True)
        if current_balance < bahis_miktari:
            return await interaction.response.send_message(f"Paran yok! ({current_balance} Coin)", ephemeral=True)

        ranks = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                 '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}
        suits = ['♠️', '♥️', '♦️', '♣️']
        deck = [(r, s) for r in ranks for s in suits]
        random.shuffle(deck)

        def get_card(): return deck.pop()

        def calculate(hand):
            score = sum(ranks[c[0]] for c in hand)
            aces = sum(1 for c in hand if c[0] == 'A')
            while score > 21 and aces:
                score -= 10
                aces -= 1
            return score

        def format_hand(hand): return " ".join(
            [f"`{c[0]}{c[1]}`" for c in hand])

        oyuncu_el = [get_card(), get_card()]
        kasa_el = [get_card(), get_card()]
        embed = discord.Embed(title="🃏 Blackjack Masası",
                              color=discord.Color.blue())
        embed.add_field(name=f"Kasa [{ranks[kasa_el[0][0]]}]",
                        value=f"`{kasa_el[0][0]}{kasa_el[0][1]}` ❓", inline=True)
        embed.add_field(name=f"Sen [{calculate(oyuncu_el)}]",  value=format_hand(
            oyuncu_el), inline=True)

        # MİGRASYON: ctx.author.id yerine interaction.user.id gönderiyoruz
        view = BlackjackView(
            interaction.user.id, oyuncu_el, kasa_el, deck,
            ranks, get_card, calculate, format_hand, bahis_miktari, economy, u_id
        )
        await interaction.response.send_message(embed=embed, view=view)

    # ── /ekonomi kumarbaz ──────────────────────────────────────────────────
    # ESKİ: .kumarbaz
    @app_commands.command(name="kumarbaz", description="50.000 Coin ile SWEETBONANZA rolü satın al")
    async def kumarbaz(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        check_user(u_id)
        fiyat = 50_000
        rol_adi = "SWEETBONANZA"
        if economy[u_id]["balance"] < fiyat:
            kalan = fiyat - economy[u_id]["balance"]
            return await interaction.response.send_message(f"❌ Daha **{kalan} Coin** lazım!", ephemeral=True)
        rol = discord.utils.get(interaction.guild.roles, name=rol_adi)
        if not rol:
            return await interaction.response.send_message(f"❌ `{rol_adi}` rolü bulunamadı!", ephemeral=True)
        if rol in interaction.user.roles:
            return await interaction.response.send_message("Zaten kumarbazsın!", ephemeral=True)
        try:
            economy[u_id]["balance"] -= fiyat
            save_economy()
            await interaction.user.add_roles(rol)
            embed = discord.Embed(title="🎰 YENİ BİR KUMARBAZ!",
                                  description=f"{interaction.user.mention} **{fiyat} Coin** ödeyerek `{rol_adi}` rolünü aldı!", color=discord.Color.purple())
            await interaction.response.send_message(embed=embed)
            await send_log(interaction.guild, f"💸 Market: {interaction.user.mention} `{rol_adi}` satın aldı.", discord.Color.purple())
        except:
            await interaction.response.send_message("🚨 Rol verilemedi!", ephemeral=True)


# ═════════════════════════════════════════════════════════════════════════════
#  COG 3 — MODERASYON
# ═════════════════════════════════════════════════════════════════════════════
class ModerasyonCog(commands.Cog):
    mod_group = app_commands.Group(
        name="mod", description="Moderasyon komutları")

    @mod_group.command(name="ban", description="Birden fazla üyeyi yasaklar (ID veya Mention)")
    @app_commands.describe(targets="Yasaklanacak üyeler (ID veya Etiket, boşlukla ayırın)", sebep="Yasak sebebi")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction,
                  targets: str,
                  sebep: str = "Z 3 İ T T Sistem Tarafından Yasaklandı"):

        await interaction.response.defer(ephemeral=True)

        user_ids = list(set(re.findall(r'\d+', targets)))

        if not user_ids:
            return await interaction.followup.send(BotUI.error("Geçerli bir Kullanıcı ID veya Etiket bulunamadı."))

        author_id = interaction.user.id
        simdi = datetime.now()

        if author_id not in BEYAZ_LISTE:
            ban_takip.setdefault(author_id, [])
            ban_takip[author_id] = [t for t in ban_takip[author_id]
                                    if (simdi - t).total_seconds() < BAN_LIMIT_SURESI * 60]

            if len(ban_takip[author_id]) + len(user_ids) > BAN_LIMIT_SAYISI:
                return await interaction.followup.send(BotUI.warn(f"İşlem iptal edildi. Ban limiti ({BAN_LIMIT_SAYISI}) aşılacak."))

        success_count = 0
        failed_targets = []

        for uid in user_ids:
            try:
                target_id = int(uid)
                member = interaction.guild.get_member(target_id) or await interaction.client.fetch_user(target_id)

                # OZEL_SAHIP_ID her şeyi banlayabilir
                if author_id != OZEL_SAHIP_ID:
                    if target_id in BEYAZ_LISTE or target_id == interaction.client.user.id:
                        failed_targets.append(f"{uid} (Beyaz Liste)")
                        continue

                    if isinstance(member, discord.Member):
                        if interaction.user != interaction.guild.owner and interaction.user.top_role.position <= member.top_role.position:
                            failed_targets.append(f"{member.name} (Rol Hiyerarşisi)")
                            continue
                else:
                    # OZEL_SAHIP_ID bile olsa botu banlayamaz
                    if target_id == interaction.client.user.id:
                        failed_targets.append(f"{uid} (Bot)")
                        continue

                await interaction.guild.ban(member, reason=sebep)
                success_count += 1

                if author_id not in BEYAZ_LISTE:
                    ban_takip[author_id].append(datetime.now())

            except Exception as e:
                failed_targets.append(f"{uid} (Hata: {str(e)})")

        report = f"**{success_count}** üye yasaklandı."
        if failed_targets:
            report += f"\n> ❌ **Başarısız:** {', '.join(failed_targets)}"

        await interaction.followup.send(BotUI.success(report))
        if success_count > 0:
            if success_count == 1:
                # Tek ban — isim ve ID yaz
                basarili_id = next(
                    uid for uid in user_ids
                    if f"{uid} (" not in " ".join(failed_targets)
                )
                try:
                    basarili_user = await interaction.client.fetch_user(int(basarili_id))
                    log_msg = f"🔨 Ban: **{basarili_user.name}** (`{basarili_id}`) | Sebep: {sebep} | Yetkili: {interaction.user.mention}"
                except:
                    log_msg = f"🔨 Ban: `{basarili_id}` | Sebep: {sebep} | Yetkili: {interaction.user.mention}"
            else:
                # Toplu ban — sadece sayı yaz
                log_msg = f"🔨 Toplu Ban: **{success_count}** üye | Sebep: {sebep} | Yetkili: {interaction.user.mention}"

            await send_log(interaction.guild, log_msg, discord.Color.red())
    @mod_group.command(name="unban", description="Birden fazla üyenin yasağını kaldırır (ID veya Mention)")
    @app_commands.describe(targets="Yasağı kaldırılacak üyeler (ID, boşlukla ayırın)", sebep="Sebep")
    @app_commands.default_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction,
                    targets: str,
                    sebep: str = "Z 3 İ T T Sistem Tarafından Yasak Kaldırıldı"):
        await interaction.response.defer(ephemeral=True)

        user_ids = list(set(re.findall(r'\d+', targets)))
        if not user_ids:
            return await interaction.followup.send(BotUI.error("Geçerli bir Kullanıcı ID bulunamadı."))

        success_count = 0
        failed_targets = []

        for uid in user_ids:
            try:
                target_id = int(uid)
                user = await interaction.client.fetch_user(target_id)
                await interaction.guild.unban(user, reason=sebep)
                success_count += 1
            except discord.NotFound:
                failed_targets.append(f"{uid} (Zaten banlı değil)")
            except discord.Forbidden:
                failed_targets.append(f"{uid} (Yetki yetersiz)")
            except Exception as e:
                failed_targets.append(f"{uid} (Hata: {str(e)})")

        report = f"**{success_count}** üyenin yasağı kaldırıldı."
        if failed_targets:
            report += f"\n> ❌ **Başarısız:** {', '.join(failed_targets)}"

        await interaction.followup.send(BotUI.success(report))
        if success_count > 0:
            await send_log(
                interaction.guild,
                f"🔓 Toplu Unban: {success_count} üye | Yetkili: {interaction.user.mention}",
                discord.Color.green()
            )
    # ── /mod kick ──────────────────────────────────────────────────────────
    # ESKİ: .kick @üye [sebep]

    @mod_group.command(name="kick", description="Üyeyi sunucudan atar")
    @app_commands.describe(member="Atılacak üye", sebep="Sebep")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction,
                   member: discord.Member,
                   sebep: str = "Z 3 İ T T Sistem Tarafından Atıldı"):
        if interaction.user.id not in BEYAZ_LISTE:
            simdi = datetime.now()
            kick_takip.setdefault(interaction.user.id, [])
            kick_takip[interaction.user.id] = [t for t in kick_takip[interaction.user.id] if (
                simdi - t).total_seconds() < KICK_LIMIT_SURESI * 60]
            if len(kick_takip[interaction.user.id]) >= KICK_LIMIT_SAYISI:
                return await interaction.response.send_message(BotUI.warn(f"Kick limiti ({KICK_LIMIT_SAYISI}) aşıldı!"), ephemeral=True)
        if member.id in BEYAZ_LISTE or member.id == bot.user.id:
            return await interaction.response.send_message(BotUI.warn(f"{member.name} Beyaz Listede!"), ephemeral=True)
        if interaction.user != interaction.guild.owner and interaction.user.top_role.position <= member.top_role.position:
            return await interaction.response.send_message(BotUI.error(f"{member.name} seninle aynı veya üst rolde!"), ephemeral=True)
        try:
            await interaction.guild.kick(member, reason=f"{interaction.user} | {sebep}")
            if interaction.user.id not in BEYAZ_LISTE:
                kick_takip[interaction.user.id].append(datetime.now())
            await interaction.response.send_message(BotUI.success(f"**{member.name}** sunucudan atıldı."))
        except Exception as e:
            await interaction.response.send_message(BotUI.error(f"Hata: {e}"), ephemeral=True)

    # ── /mod sustur ────────────────────────────────────────────────────────
    # ESKİ: .sustur / .mute @üye1 @üye2 [dakika] [sebep]
    @mod_group.command(name="sustur", description="Üyeyi geçici susturur")
    @app_commands.describe(member="Susturulacak üye", sure="Dakika cinsinden süre", sebep="Sebep")
    @app_commands.default_permissions(moderate_members=True)
    async def sustur(self, interaction: discord.Interaction,
                     member: discord.Member,
                     sure: int = 10,
                     sebep: str = "Kural İhlali"):
        if member.id in BEYAZ_LISTE:
            return await interaction.response.send_message(BotUI.warn(f"{member.mention} Beyaz Listede!"), ephemeral=True)
        if interaction.user != interaction.guild.owner and interaction.user.top_role.position <= member.top_role.position:
            return await interaction.response.send_message(BotUI.error(f"{member.name} seninle aynı veya üst rolde!"), ephemeral=True)
        try:
            await member.timeout(timedelta(minutes=sure), reason=sebep)
            await interaction.response.send_message(BotUI.success(f"**{member.name}** {sure} dakika susturuldu."))
        except Exception as e:
            await interaction.response.send_message(BotUI.error(f"Hata: {e}"), ephemeral=True)

    # ── /mod susturkaldir ──────────────────────────────────────────────────
    # ESKİ: .susturkaldir / .unmute / .susturkaldır
    @mod_group.command(name="susturkaldir", description="Üyenin susturmasını kaldırır")
    @app_commands.describe(member="Susturması kaldırılacak üye")
    @app_commands.default_permissions(moderate_members=True)
    async def susturkaldir(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user != interaction.guild.owner and interaction.user.top_role.position <= member.top_role.position:
            return await interaction.response.send_message(BotUI.warn(f"Hiyerarşi engeli: {member.mention}"), ephemeral=True)
        try:
            await member.timeout(None)
            await interaction.response.send_message(BotUI.success(f"**{member.name}** susturması kaldırıldı."))
            await send_log(interaction.guild, f"🔊 Susturma Kaldırıldı: {member.name} | {interaction.user.mention}", discord.Color.green())
        except Exception as e:
            await interaction.response.send_message(BotUI.error(f"Hata: {e}"), ephemeral=True)

    # ── /mod temizle ───────────────────────────────────────────────────────
    # ESKİ: .temizle / .sil / .purge / .clear [sayı]
    @mod_group.command(name="sil", description="Kanaldan mesaj siler (max 100)")
    @app_commands.describe(miktar="Silinecek mesaj sayısı (1-100)")
    @app_commands.default_permissions(manage_messages=True)
    async def sil(self, interaction: discord.Interaction, miktar: int):
        if not 1 <= miktar <= 100:
            return await interaction.response.send_message(BotUI.warn("1-100 arası bir sayı girmelisin!"), ephemeral=True)
        # defer: purge uzun sürebilir
        await interaction.response.defer(ephemeral=True)
        try:
            deleted = await interaction.channel.purge(limit=miktar)
            await interaction.followup.send(BotUI.success(f"**{len(deleted)}** mesaj başarıyla silindi!"), ephemeral=True)
            await send_log(interaction.guild, f"🧹 Temizleme: {interaction.channel.mention} | {len(deleted)} mesaj | {interaction.user.mention}", discord.Color.blue())
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {e}", ephemeral=True)
    @mod_group.command(name="sil_uye", description="Belirlenen üye/üyelerin kanaldaki son X adet mesajını siler")
    @app_commands.describe(
        hedefler="Mesajları silinecek üyelerin etiketleri veya ID'leri (boşluk bırakarak)",
        miktar="Silinecek mesaj sayısı (Maksimum 100)"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def siluye(self, interaction: discord.Interaction, hedefler: str, miktar: int):
        if not 1 <= miktar <= 100:
            return await interaction.response.send_message(BotUI.warn("1-100 arası bir sayı girmelisin!"), ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        # O(1) Performans için ID Set'i oluşturma
        hedef_ids = set()
        for hedef in hedefler.split():
            try:
                uid = int(re.sub(r"[<@!>]", "", hedef))
                hedef_ids.add(uid)
            except ValueError:
                continue

        if not hedef_ids:
            return await interaction.followup.send(BotUI.error("Geçerli bir kullanıcı etiketi veya ID girmedin!"), ephemeral=True)

        silinen_sayac = 0

        # purge içindeki check fonksiyonunu dinamik bir sayaçla yönetiyoruz
        def kontrol(message: discord.Message):
            nonlocal silinen_sayac
            # Eğer hedef sayımıza ulaştıysak artık true dönme (silmeyi durdur)
            if silinen_sayac >= miktar:
                return False

            if message.author.id in hedef_ids:
                silinen_sayac += 1
                return True
            return False

        try:
            # Taranacak derinliği (limit) yüksek tutuyoruz (örn: 500 mesaj geriye kadar tara)
            # Ama `check` fonksiyonu `miktar` değerine ulaştığı an silme listesi dolmuş olacak.
            deleted = await interaction.channel.purge(limit=500, check=kontrol)

            etiketler_str = ", ".join([f"<@{uid}>" for uid in hedef_ids])
            await interaction.followup.send(BotUI.success(f"Belirtilen üyelerin son **{len(deleted)}** adet mesajı geçmişten bulunarak temizlendi!"), ephemeral=True)

            asyncio.create_task(send_log(
                interaction.guild, 
                f"🧹 Üye Mesajı Temizleme: {interaction.channel.mention} | Hedefler: {etiketler_str} | Silinen: {len(deleted)} mesaj | Yetkili: {interaction.user.mention}", 
                discord.Color.red()
            ))
        except discord.Forbidden:
            await interaction.followup.send(BotUI.error("Mesajları silmek için gerekli yetkim yok!"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(BotUI.error(f"Hata: {e}"), ephemeral=True)
    # ── /mod clearall ──────────────────────────────────────────────────────
    # ESKİ: .clearall / .kanalisifirla / .nuke
    @mod_group.command(name="nuke", description="Kanalı sıfırlar (nuke) — Beyaz liste gerekli")
    @app_commands.default_permissions(administrator=True)
    async def nuke(self, interaction: discord.Interaction):
        if interaction.user.id not in BEYAZ_LISTE and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(BotUI.warn("Beyaz liste gerekli!"), ephemeral=True)
        kanal = interaction.channel
        pozisyon = kanal.position
        kategori = kanal.category
        izinler = kanal.overwrites
        isim = kanal.name
        await interaction.response.send_message(BotUI.warn(f"**{isim}** sıfırlanıyor..."))
        try:
            await kanal.delete(reason="Nuke")
            yeni_kanal = await interaction.guild.create_text_channel(
                name=isim, category=kategori,
                overwrites=izinler, position=pozisyon, reason="Kanal sıfırlandı"
            )
            embed = BotUI.embed(
                title="✨ Kanal Sıfırlandı", desc=f"{interaction.user.mention} tarafından başarıyla temizlendi.", color=BotUI.COLOR_SUCCESS)
            await yeni_kanal.send(embed=embed)
            await yeni_kanal.send("https://tenor.com/view/kaboom-boom-gif-4090446168494834371")
            await send_log(interaction.guild, f"💥 KANAL SIFIRLANDI: #{isim} | {interaction.user.mention}", discord.Color.dark_red())
        except Exception as e:
            print(f"Clear All Hatası: {e}")

    # ── /mod rolver ────────────────────────────────────────────────────────
    # ESKİ: .rolver @üye @rol
    @mod_group.command(name="rolver", description="Üyeye rol ver")
    @app_commands.describe(member="Hedef üye", role="Verilecek rol")
    @app_commands.default_permissions(manage_roles=True)
    async def rolver(self, interaction: discord.Interaction,
                     member: discord.Member, role: discord.Role):
        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(BotUI.error("Botun yetkisi bu rolü vermeye yetmiyor!"), ephemeral=True)
        if interaction.user.top_role <= role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message(BotUI.error("Kendi rolünden yüksek veya eşit bir rol veremezsin!"), ephemeral=True)
        await member.add_roles(role)
        await interaction.response.send_message(BotUI.success(f"{member.mention} kullanıcısına `{role.name}` rolü verildi."))

    # ── /mod rolal ─────────────────────────────────────────────────────────
    # ESKİ: .rolal @üye @rol  veya  .rolal @üye all
    @mod_group.command(name="rolal", description="Üyeden rol al (veya all ile hepsini al)")
    @app_commands.describe(member="Hedef üye", secim="Rol etiketle ya da 'all' yaz")
    @app_commands.default_permissions(manage_roles=True)
    async def rolal(self, interaction: discord.Interaction,
                    member: discord.Member, secim: str):
        if member.id in BEYAZ_LISTE:
            return await interaction.response.send_message(BotUI.warn("Beyaz listedeki bir kullanıcının rollerine dokunamazsın!"), ephemeral=True)
        if interaction.user.id != interaction.guild.owner_id and interaction.user.top_role <= member.top_role:
            return await interaction.response.send_message(BotUI.error("Yetki yetersiz! Senden üstün veya eşit pozisyondaki birine işlem yapamazsın."), ephemeral=True)
        if secim.lower() == "all":
            await interaction.response.defer()
            alinanlar = 0
            for role in member.roles:
                if role.name == "@everyone" or role >= interaction.guild.me.top_role:
                    continue
                try:
                    await member.remove_roles(role)
                    alinanlar += 1
                except:
                    pass
            return await interaction.followup.send(f"🧹 {member.mention} tüm rolleri temizlendi! ({alinanlar} rol)")
        try:
            ctx_fake_role = discord.utils.get(interaction.guild.roles, name=secim) or \
                interaction.guild.get_role(int(secim.strip("<@&>")))
            if not ctx_fake_role:
                return await interaction.response.send_message("❌ Rol bulunamadı!", ephemeral=True)
            if ctx_fake_role >= interaction.guild.me.top_role:
                return await interaction.response.send_message("❌ Bot yetkisi yetmiyor!", ephemeral=True)
            await member.remove_roles(ctx_fake_role)
            await interaction.response.send_message(f"✅ {member.mention} → `{ctx_fake_role.name}` alındı.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

    # ── /mod rolverall ─────────────────────────────────────────────────────
    # ESKİ: .rolverall @rol
    @mod_group.command(name="rolverall", description="Herkese belirtilen rolü ver (Beyaz liste)")
    @app_commands.describe(role="Verilecek rol")
    async def rolverall(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.user.id not in BEYAZ_LISTE and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ Beyaz listede değilsin!", ephemeral=True)
        await interaction.response.defer()
        basarili = 0
        for uye in interaction.guild.members:
            if not uye.bot and role not in uye.roles:
                try:
                    await uye.add_roles(role)
                    basarili += 1
                except:
                    pass
        await interaction.followup.send(f"✅ **{basarili}** kişiye `{role.name}` verildi.")

# ── /mod kilit ─────────────────────────────────────────────────────────
    @mod_group.command(name="kilit", description="Kanalı kilitler ve gizler")
    @app_commands.default_permissions(manage_channels=True)
    async def kilit(self, interaction: discord.Interaction):
        everyone_role = interaction.guild.default_role
        ozel_rol = discord.utils.get(interaction.guild.roles, name=OTO_ROL_ADI)

        # @everyone için kanal görüntülemeyi kapat, mesaj göndermeyi sıfırla
        overwrite = interaction.channel.overwrites_for(everyone_role)
        overwrite.view_channel = False
        overwrite.send_messages = None
        await interaction.channel.set_permissions(everyone_role, overwrite=overwrite)

        # Özel rol için kanal görüntülemeyi kapat, mesaj göndermeyi sıfırla
        if ozel_rol:
            ow2 = interaction.channel.overwrites_for(ozel_rol)
            ow2.view_channel = False
            ow2.send_messages = None
            await interaction.channel.set_permissions(ozel_rol, overwrite=ow2)

        embed = discord.Embed(
            title="🔒 Kanal Gizlendi ve Kilitlendi",
            description=f"@everyone ve {OTO_ROL_ADI} rolü için erişim kapatıldı.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, f"🔒 Kanal Gizlendi/Kilitlendi: {interaction.channel.mention} | {interaction.user.mention}", discord.Color.orange())
    @mod_group.command(name="rename", description="Birden fazla üyenin sunucu ismini değiştirir")
    @app_commands.describe(
        hedefler="Üye etiketleri (@üye1 @üye2) veya ID'leri (boşluk bırakarak yazın)",
        yeni_isim="Yeni sunucu ismi (boş bırakırsan orijinal ismine döner)"
    )
    @app_commands.default_permissions(manage_nicknames=True)
    async def rename(self, interaction: discord.Interaction, hedefler: str, yeni_isim: str = None):
        # İşlem uzun sürebileceği için etkileşimi defer ediyoruz (API timeout engelleme)
        await interaction.response.defer(ephemeral=True)

        # Girdiyi boşluklara göre böl ve temizle
        hedef_listesi = [h.strip() for h in hedefler.split() if h.strip()]
        if not hedef_listesi:
            return await interaction.followup.send("❌ En az bir geçerli kullanıcı etiketi veya ID girmelisin!")

        basarili = []
        hatali = []
        is_admin_or_whitelisted = interaction.user == interaction.guild.owner or interaction.user.id in BEYAZ_LISTE

        for hedef in hedef_listesi:
            try:
                uid = int(re.sub(r"[<@!>]", "", hedef))
            except ValueError:
                hatali.append(f"{hedef} (Geçersiz format)")
                continue

            member = interaction.guild.get_member(uid)
            if not member:
                hatali.append(f"<@{uid}> (Sunucuda bulunamadı)")
                continue

            # Hiyerarşi kontrolü
            if not is_admin_or_whitelisted:
                if interaction.user.top_role.position <= member.top_role.position:
                    hatali.append(f"{member.mention} (Yetersiz yetki/Hiyerarşi)")
                    continue

            eski_isim = member.display_name
            try:
                await member.edit(nick=yeni_isim)
                basarili.append(f"✅ {member.mention} (`{eski_isim}` → `{yeni_isim or member.name}`)")

                # Log gönderme işlemini asenkron arka plana atıyoruz (Döngüyü yavaşlatmaması için)
                asyncio.create_task(send_log(
                    interaction.guild,
                    f"✏️ Toplu İsim Değişti: {member.mention} | `{eski_isim}` → `{yeni_isim or member.name}` | Yetkili: {interaction.user.mention}",
                    discord.Color.blue()
                ))
            except discord.Forbidden:
                hatali.append(f"{member.mention} (Botun yetkisi yetersiz)")
            except Exception as e:
                hatali.append(f"{member.mention} (Hata: {str(e)})")

        # Raporlama Aşaması
        rapor = []
        if basarili:
            rapor.append("**Başarılı İşlemler:**\n" + "\n".join(basarili))
        if hatali:
            rapor.append("**Başarısız İşlemler:**\n" + "\n".join(hatali))

        # Discord 2000 karakter sınırını aşmamak için join
        tam_rapor = "\n\n".join(rapor)
        if len(tam_rapor) > 2000:
            tam_rapor = tam_rapor[:1990] + "\n...ve dahası"

        await interaction.followup.send(tam_rapor)
    # ── /mod kilitac ───────────────────────────────────────────────────────
    @mod_group.command(name="kilitac", description="Kanal kilidini açar. 'all' yazarsan log kategorisi hariç tüm kanalları açar")
    @app_commands.describe(hedef="Açılacak kanal (boş = bu kanal) veya 'all' (tüm kanallar)")
    @app_commands.default_permissions(manage_channels=True)
    async def kilitac(self, interaction: discord.Interaction, hedef: str = None):
        await interaction.response.defer(ephemeral=True)

        everyone_role = interaction.guild.default_role
        ozel_rol = discord.utils.get(interaction.guild.roles, name=OTO_ROL_ADI)

        # Log kategorisini bul
        log_kategori = None
        for kategori in interaction.guild.categories:
            if LOG_KANAL_ADI.lower() in kategori.name.lower():
                log_kategori = kategori
                break

        async def kanal_ac(kanal: discord.TextChannel):
            """Verilen kanalı aç: görüntüleme + geçmiş mesajları görme izni ver"""
            overwrite = kanal.overwrites_for(everyone_role)
            overwrite.view_channel = True
            overwrite.read_message_history = True
            await kanal.set_permissions(everyone_role, overwrite=overwrite)

            if ozel_rol:
                ow2 = kanal.overwrites_for(ozel_rol)
                ow2.view_channel = True
                ow2.read_message_history = True
                await kanal.set_permissions(ozel_rol, overwrite=ow2)

        if hedef and hedef.strip().lower() == "all":
            # Tüm metin ve ses kanallarını aç (korunan kategoriler hariç)
            acilan = []

            # Metin kanalları
            for kanal in interaction.guild.text_channels:
                # Sabit korunan kategori listesindeki kanalları atla
                if kanal.category_id and kanal.category_id in KORUNAN_KATEGORI_IDLERI:
                    continue
                # İsme göre log kanalını da atla (kategorisi yoksa)
                if kanal.name == LOG_KANAL_ADI:
                    continue
                try:
                    await kanal_ac(kanal)
                    acilan.append(kanal.mention)
                except Exception:
                    pass

            embed = discord.Embed(
                title="🔓 Tüm Kanallar Açıldı",
                description=(
                    f"Korunan kategoriler hariç **{len(acilan)}** kanal erişime açıldı.\n"
                    f"Görüntüleme ve geçmiş mesaj okuma izni verildi."
                ),
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            await send_log(
                interaction.guild,
                f"🔓 Toplu Kanal Açma: **{len(acilan)}** kanal açıldı (korunan kategoriler hariç) | {interaction.user.mention}",
                discord.Color.green()
            )

        else:
            # Tek kanal: belirtilen kanal ya da mevcut kanal
            if hedef:
                # Kanal etiketinden ID çıkar veya isimle bul
                try:
                    kanal_id = int(re.sub(r"[<#>]", "", hedef))
                    kanal = interaction.guild.get_channel(kanal_id)
                except ValueError:
                    kanal = discord.utils.get(interaction.guild.text_channels, name=hedef.strip())
                if not kanal:
                    return await interaction.followup.send("❌ Kanal bulunamadı!", ephemeral=True)
            else:
                kanal = interaction.channel

            await kanal_ac(kanal)

            embed = discord.Embed(
                title="🔓 Kanal Erişime Açıldı",
                description=f"{kanal.mention} kanalı görüntüleme kısıtlamaları kaldırıldı.\nGörüntüleme ve geçmiş mesaj okuma izni verildi.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            await send_log(
                interaction.guild,
                f"🔓 Kanal Erişime Açıldı: {kanal.mention} | {interaction.user.mention}",
                discord.Color.green()
            )

    # ── /mod kilitacanc ────────────────────────────────────────────────────
    @mod_group.command(name="kilitacanc", description="Duyuru kanalı modunu açar: mesaj gönderme kapalı, görüntüleme + geçmiş açık")
    @app_commands.describe(hedef="Duyuru moduna alınacak kanal (boş = bu kanal)")
    @app_commands.default_permissions(manage_channels=True)
    async def kilitacanc(self, interaction: discord.Interaction, hedef: str = None):
        await interaction.response.defer(ephemeral=True)

        everyone_role = interaction.guild.default_role
        ozel_rol = discord.utils.get(interaction.guild.roles, name=OTO_ROL_ADI)

        # Hedef kanalı belirle
        if hedef:
            try:
                kanal_id = int(re.sub(r"[<#>]", "", hedef))
                kanal = interaction.guild.get_channel(kanal_id)
            except ValueError:
                kanal = discord.utils.get(interaction.guild.text_channels, name=hedef.strip())
            if not kanal:
                return await interaction.followup.send("❌ Kanal bulunamadı!", ephemeral=True)
        else:
            kanal = interaction.channel

        # @everyone: mesaj gönderme kapalı, görüntüleme + geçmiş açık
        overwrite = kanal.overwrites_for(everyone_role)
        overwrite.send_messages = False
        overwrite.view_channel = True
        overwrite.read_message_history = True
        await kanal.set_permissions(everyone_role, overwrite=overwrite)

        # Özel rol da aynı şekilde
        if ozel_rol:
            ow2 = kanal.overwrites_for(ozel_rol)
            ow2.send_messages = False
            ow2.view_channel = True
            ow2.read_message_history = True
            await kanal.set_permissions(ozel_rol, overwrite=ow2)

        embed = discord.Embed(
            title="📢 Duyuru Modu Aktif",
            description=(
                f"{kanal.mention} kanalı **duyuru moduna** alındı.\n\n"
                "✅ Kanalı görüntüleme → **Açık**\n"
                "✅ Geçmiş mesajları görme → **Açık**\n"
                "❌ Mesaj gönderme → **Kapalı**"
            ),
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        await send_log(
            interaction.guild,
            f"📢 Duyuru Modu: {kanal.mention} | Görüntüleme+Geçmiş açık, Mesaj gönderme kapalı | {interaction.user.mention}",
            discord.Color.orange()
        )
# ═════════════════════════════════════════════════════════════════════════════
#  COG 4 — SES SİSTEMİ
# ═════════════════════════════════════════════════════════════════════════════


class SesCog(commands.Cog):

    ses_group = app_commands.Group(
        name="ses", description="Ses kanalı komutları")

    # ── /ses gir ───────────────────────────────────────────────────────────
    # ESKİ: .gir
    @ses_group.command(name="gir", description="Botu ses kanalına bağlar (Beyaz liste)")
    async def gir(self, interaction: discord.Interaction):
        if interaction.user.id not in BEYAZ_LISTE and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("🚫 Beyaz liste gerekli!", ephemeral=True)
        if interaction.guild.voice_client:
            return await interaction.response.send_message(
                f"❌ Zaten `{interaction.guild.voice_client.channel.name}` kanalındayım!", ephemeral=True
            )
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Önce bir ses kanalına gir!", ephemeral=True)

        await interaction.response.defer()  # ← 3 saniyelik süreyi uzatır
        await interaction.user.voice.channel.connect()
        await interaction.followup.send(f"🔊 `{interaction.user.voice.channel.name}` kanalına bağlandım!")

    @ses_group.command(name="cik", description="Botu ses kanalından çıkarır (Beyaz liste)")
    async def cik(self, interaction: discord.Interaction):
        if interaction.user.id not in BEYAZ_LISTE and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("🚫 Beyaz liste gerekli!", ephemeral=True)
        if not interaction.guild.voice_client:
            return await interaction.response.send_message("❌ Zaten bir ses kanalında değilim!", ephemeral=True)

        await interaction.response.defer()  # ← burada da
        await interaction.guild.voice_client.disconnect()
        await interaction.followup.send("👋 Sesten çıktım.")

    # ── /ses sure ──────────────────────────────────────────────────────────
    # ESKİ: .sessurem / .vctime [@üye]
    @ses_group.command(name="sure", description="Ses kanalı toplam süresini gösterir")
    @app_commands.describe(member="Süresine bakılacak üye (boş = sen)")
    async def sure(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user   # MİGRASYON: ctx.author → interaction.user
        ses_data = load_ses()
        toplam = ses_data.get(str(target.id), {}).get("toplam_saniye", 0)
        if target.id in ses_giris_takip:
            toplam += int(time.time() - ses_giris_takip[target.id])
        embed = discord.Embed(title="🎙️ Ses Kanalı Süresi",
                              color=discord.Color.blurple())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name=target.display_name,
                        value=f"**{sure_formatla(toplam)}**")
        await interaction.response.send_message(embed=embed)

    # ── /ses siralama ──────────────────────────────────────────────────────
    # ESKİ: .sessıralama / .seslb [top]
    @ses_group.command(name="siralama", description="Ses kanalı liderboard")
    @app_commands.describe(top="Gösterilecek kişi sayısı (varsayılan 10)")
    async def siralama(self, interaction: discord.Interaction, top: int = 10):
        await interaction.response.defer()
        ses_data = load_ses()
        skorlar = []
        for uid_str, info in ses_data.items():
            toplam = info["toplam_saniye"]
            uid = int(uid_str)
            if uid in ses_giris_takip:
                toplam += int(time.time() - ses_giris_takip[uid])
            skorlar.append((uid, toplam))
        skorlar.sort(key=lambda x: x[1], reverse=True)
        madalyalar = ["🥇", "🥈", "🥉"]
        satirlar = []
        i = 0
        for uid, sn in skorlar:
            if i >= top:
                break
            m = interaction.guild.get_member(uid)
            if not m:
                continue  # Sunucuda olmayan kullanıcılar gösterilmez
            ikon = madalyalar[i] if i < 3 else f"`{i+1}.`"
            satirlar.append(f"{ikon} {m.mention} — {sure_formatla(sn)}")
            i += 1
        embed = discord.Embed(title="🏆 Ses Kanalı Sıralaması", description="\n".join(
            satirlar) or "Veri yok.", color=discord.Color.gold())
        await interaction.followup.send(embed=embed)

    # ── /ses kilit ─────────────────────────────────────────────────────────
    # ESKİ: .seskilit all/#kanal
    @ses_group.command(name="kilit", description="Ses kanallarını kilitler (Beyaz liste)")
    @app_commands.describe(hedef="'all' veya kanal ID'si")
    async def seskilit(self, interaction: discord.Interaction, hedef: str = "all"):
        if interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("❌ Beyaz liste gerekli!", ephemeral=True)
        await interaction.response.defer()
        everyone = interaction.guild.default_role
        oto_rol = discord.utils.get(interaction.guild.roles, name=OTO_ROL_ADI)
        overwrites = {everyone: discord.PermissionOverwrite(
            view_channel=False, connect=False)}
        if oto_rol:
            overwrites[oto_rol] = discord.PermissionOverwrite(
                view_channel=False, connect=False)
        if hedef == "all":
            count = 0
            for channel in interaction.guild.voice_channels:
                await channel.edit(overwrites=overwrites)
                count += 1
            await interaction.followup.send(f"🔇 **{count}** ses kanalı kilitlendi!")
        else:
            try:
                cid = int(hedef.replace("<#", "").replace(">", ""))
                channel = interaction.guild.get_channel(cid)
                if isinstance(channel, discord.VoiceChannel):
                    await channel.edit(overwrites=overwrites)
                    await interaction.followup.send(f"🔒 **{channel.name}** kilitlendi.")
                else:
                    await interaction.followup.send("O bir ses kanalı değil.", ephemeral=True)
            except:
                await interaction.followup.send("Geçerli bir kanal ID'si veya `all` yaz!", ephemeral=True)

    # ── /ses kilitac ───────────────────────────────────────────────────────
    # ESKİ: .seskilitac all/#kanal
    @ses_group.command(name="kilitac", description="Ses kanalı kilidini açar (Beyaz liste)")
    @app_commands.describe(hedef="'all' veya kanal ID'si")
    async def seskilitac(self, interaction: discord.Interaction, hedef: str = "all"):
        if interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
        await interaction.response.defer()
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                view_channel=None, connect=None)
        }
        oto_rol = discord.utils.get(interaction.guild.roles, name=OTO_ROL_ADI)
        if oto_rol:
            overwrites[oto_rol] = discord.PermissionOverwrite(
                view_channel=None, connect=None)
        if hedef == "all":
            for channel in interaction.guild.voice_channels:
                await channel.edit(overwrites=overwrites)
            await interaction.followup.send("🔓 Tüm ses kanalları açıldı!")
        else:
            try:
                cid = int(hedef.replace("<#", "").replace(">", ""))
                channel = interaction.guild.get_channel(cid)
                if isinstance(channel, discord.VoiceChannel):
                    await channel.edit(overwrites=overwrites)
                    await interaction.followup.send(f"🔓 **{channel.name}** açıldı.")
                else:
                    await interaction.followup.send("O bir ses kanalı değil.", ephemeral=True)
            except:
                await interaction.followup.send("Geçerli bir kanal ID'si veya `all` yaz!", ephemeral=True)

    # ── /ses cek ───────────────────────────────────────────────────────────
    # ESKİ: .cek all / .cek @üye
    @ses_group.command(name="cek", description="Üyeleri senin ses kanalına çeker")
    @app_commands.describe(hedef="'all' veya @üye etiket")
    async def cek(self, interaction: discord.Interaction,
                  hedef: str = "all",
                  member: discord.Member = None):
        if not (interaction.user.id == interaction.guild.owner_id or
                interaction.user.guild_permissions.adminastator):
            return await interaction.response.send_message("Yetkin yetersiz! ❌", ephemeral=True)
        if not interaction.user.voice:
            return await interaction.response.send_message("Önce bir ses kanalına gir! ❌", ephemeral=True)
        kanal = interaction.user.voice.channel
        cekilen_sayisi = 0
        await interaction.response.defer()
        if hedef == "all":
            for uye in interaction.guild.members:
                if not uye.bot and uye.voice and uye.voice.channel != kanal:
                    try:
                        await uye.move_to(kanal)
                        cekilen_sayisi += 1
                    except:
                        pass
            await interaction.followup.send(f"🚀 **{cekilen_sayisi}** üye çekildi!")
        elif member:
            if member.voice and member.voice.channel != kanal:
                try:
                    await member.move_to(kanal)
                    await interaction.followup.send(f"✅ {member.mention} çekildi.")
                except:
                    await interaction.followup.send(f"❌ {member.mention} çekilemedi.")
            else:
                await interaction.followup.send(f"{member.mention} seste değil ya da zaten seninle.", ephemeral=True)
        else:
            await interaction.followup.send("Kullanım: `/ses cek all` veya `/ses cek member:@üye`", ephemeral=True)

class DynamicHelpSelect(discord.ui.Select):
    def __init__(self, mapping: dict[str, list[str]], is_admin: bool = False) -> None:
        self.mapping = mapping
        self.is_admin = is_admin
        
        # Maps raw database/tree terms to production-grade UI presentation layers
        self.meta = {
            "Ekonomi": {"emoji": "💰", "desc": "Bakiye, casino oyunları ve transferler"},
            "Mod": {"emoji": "🛡️", "desc": "Sunucu yönetim ve moderasyon araçları"},
            "Ses": {"emoji": "🎙️", "desc": "Ses istatistikleri ve özel oda kilitleri"},
            "Genel Komutlar": {"emoji": "👤", "desc": "Profil, davet sıralaması ve kullanıcı verileri"},
            "Admin": {"emoji": "👑", "desc": "Para basma, silme ve beyaz liste yönetimi"}
        }

        options = []
        for category, cmds in mapping.items():
            info = self.meta.get(category, {"emoji": "📁", "desc": f"{len(cmds)} adet komut içerir."})
            options.append(
                discord.SelectOption(
                    label=category if category != "Mod" else "Moderasyon",
                    description=info["desc"],
                    value=category,
                    emoji=info["emoji"]
                )
            )
        
        super().__init__(
            placeholder="İncelemek istediğiniz kategoriyi seçin..." if not is_admin else "Yönetici panelini seçin...",
            min_values=1,
            max_values=1,
            options=options[:25]
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        selected: str = self.values[0]
        cmds: list[str] = self.mapping[selected]
        
        color = 0x8B0000 if selected == "Admin" else 0x2b2d31
        title = f"{self.meta.get(selected, {}).get('emoji', '📁')} {selected} Kategorisi"
        
        embed = discord.Embed(
            title=title,
            description="\n".join(cmds),
            color=color
        )
        embed.set_footer(text=f"Sorgulayan: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.edit_message(embed=embed)


class DynamicHelpView(discord.ui.View):
    def __init__(self, mapping: dict[str, list[str]], is_admin: bool = False) -> None:
        super().__init__(timeout=90)
        self.add_item(DynamicHelpSelect(mapping, is_admin))
            
# ═════════════════════════════════════════════════════════════════════════════
#  COG 5 — BİLGİ (rank, stats, profil, owner, yardım, adminmenu)
# ═════════════════════════════════════════════════════════════════════════════
class BilgiCog(commands.Cog):

    # ── /rank ──────────────────────────────────────────────────────────────
    # ESKİ: .rank [@üye]
    @app_commands.command(name="rank", description="Seviye ve XP durumunu gösterir")
    @app_commands.describe(member="Bakılacak üye (boş = sen)")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        u_id = str(member.id)
        user_data = levels.get(u_id, {"xp": 0, "level": 0})
        xp = user_data["xp"]
        lvl = user_data["level"]
        next_xp = (lvl + 1) * 70
        embed = BotUI.embed(
            title=f"📊 {member.display_name} İstatistikleri", color=BotUI.COLOR_INFO, user=interaction.user)
        embed.add_field(name="Seviye", value=f"**{lvl}**", inline=True)
        embed.add_field(name="XP",    value=f"**{xp}/{next_xp}**", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # ── /stats ─────────────────────────────────────────────────────────────
    # ESKİ: .stats
    @app_commands.command(name="stats", description="Sunucu istatistiklerini gösterir")
    async def stats(self, interaction: discord.Interaction):
        guild = interaction.guild
        toplam_uye = guild.member_count
        online = len(
            [m for m in guild.members if m.status != discord.Status.offline])
        botlar = len([m for m in guild.members if m.bot])
        insanlar = toplam_uye - botlar
        kurulus = guild.created_at.strftime("%d %B %Y")
        embed = BotUI.embed(title=f"📊 {guild.name} İstatistikleri",
                              color=BotUI.COLOR_WARN, user=interaction.user)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(
            name="👥 Üyeler", value=f"Toplam: **{toplam_uye}**\nİnsan: **{insanlar}**\nBot: **{botlar}**", inline=True)
        embed.add_field(
            name="🟢 Durum",  value=f"Çevrimiçi: **{online}**\nÇevrimdışı: **{toplam_uye-online}**", inline=True)
        embed.add_field(
            name="💬 Kanallar", value=f"Metin: **{len(guild.text_channels)}**\nSes: **{len(guild.voice_channels)}**", inline=True)
        embed.add_field(name="📅 Kuruluş", value=f"**{kurulus}**", inline=False)
        embed.add_field(name="👑 Sunucu Sahibi",
                        value=f"{guild.owner.mention}", inline=True)
        embed.add_field(
            name="🛡️ Güvenlik", value=f"**{str(guild.verification_level).upper()}**", inline=True)

        await interaction.response.send_message(embed=embed)

    # ── /profil ────────────────────────────────────────────────────────────
    # ESKİ: .profil / .userinfo / .me / .p [@üye]
    @app_commands.command(name="profil", description="Üye profil bilgilerini gösterir")
    @app_commands.describe(member="Profili görüntülenecek üye (boş = sen)")
    async def profil(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        u_id = str(member.id)
        bakiye = economy.get(u_id, {}).get("balance", 0)
        xp = levels.get(u_id, {}).get("xp", 0)
        level = levels.get(u_id, {}).get("level", 1)
        next_xp = level * 100
        embed = BotUI.embed(title=f"👤 {member.display_name} Profili",
                              color=BotUI.COLOR_INFO, user=interaction.user)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="💰 Bakiye",
                        value=f"`{bakiye}` Coin", inline=True)
        embed.add_field(name="⭐ Seviye",
                        value=f"`{level}`. Seviye", inline=True)
        embed.add_field(name="📈 İlerleme",
                        value=f"`{xp}/{next_xp}` XP", inline=True)
        embed.add_field(name="📅 Katılım", value=member.joined_at.strftime(
            "%d/%m/%Y"), inline=True)
        embed.add_field(name="🚀 Discord", value=member.created_at.strftime(
            "%d/%m/%Y"), inline=True)
        roller = [r.mention for r in reversed(
            member.roles) if r.name != "@everyone"]
        if roller:
            embed.add_field(name=f"🛡️ Roller ({len(roller)})", value=" ".join(
                roller[:5]) + ("..." if len(roller) > 5 else ""), inline=False)

        await interaction.response.send_message(embed=embed)

    # ── /owner ─────────────────────────────────────────────────────────────
    # ESKİ: .owner / .kurucu / .sahip
    @app_commands.command(name="owner", description="Sunucu sahibinin bilgilerini gösterir")
    async def owner(self, interaction: discord.Interaction):
        owner = interaction.guild.owner or await interaction.guild.fetch_member(interaction.guild.owner_id)
        durum = "✅ Güvenli (Beyaz Listede)" if owner.id in BEYAZ_LISTE else "⚠️ Beyaz Listede Değil"
        embed = discord.Embed(title="👑 Sunucu Sahibi", description=f"{owner.mention} tacı taşıyor!", color=discord.Color.gold(
        ), timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=owner.display_avatar.url)
        embed.set_image(url=owner.display_avatar.url)
        embed.add_field(name="🏷️ Kullanıcı Adı",
                        value=f"`{owner.name}`", inline=True)
        embed.add_field(name="🆔 ID",
                        value=f"`{owner.id}`", inline=True)
        embed.add_field(name="📅 Sunucuya Katılım",
                        value=owner.joined_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="🚀 Discord'a Katılım",
                        value=owner.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="🛡️ Koruma Durumu",
                        value=f"`{durum}`", inline=False)
        embed.set_footer(text=f"{interaction.guild.name}",
                         icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        await interaction.response.send_message(embed=embed)

    # ── /yardim ────────────────────────────────────────────────────────────
    # ESKİ: .yardım / .yardim
    # ── /yardim ────────────────────────────────────────────────────────────
    @app_commands.command(name="yardim", description="Botun tüm güncel ve aktif komutlarını listeler.")
    async def yardim(self, interaction: discord.Interaction) -> None:
        mapping: dict[str, list[str]] = {}
        
        # Safely walk through the entire live command tree at runtime
        for cmd in interaction.client.tree.walk_commands():
            # Enforce Zero-Trust isolation: Isolate admin commands entirely from public eyes
            if cmd.name == "admin" or (cmd.parent and cmd.parent.name == "admin"):
                continue
                
            if isinstance(cmd, app_commands.Command):
                # Parse structural group naming logic
                if cmd.parent:
                    category = cmd.parent.name.capitalize()
                    cmd_name = f"{cmd.parent.name} {cmd.name}"
                else:
                    category = "Genel Komutlar"
                    cmd_name = cmd.name
                    
                if category not in mapping:
                    mapping[category] = []
                    
                desc = cmd.description or "Açıklama girilmemiş."
                mapping[category].append(f"`/{cmd_name}` - {desc}")

        embed = discord.Embed(
            title="🤖 Z 3 İ T T Sistem Bot | Kullanıcı Yardım Menüsü",
            description="Aşağıdaki açılır menüyü kullanarak tüm aktif alt modülleri, casino oyunlarını ve istatistik komutlarını inceleyebilirsiniz.",
            color=0x2b2d31
        )
        await interaction.response.send_message(embed=embed, view=DynamicHelpView(mapping, is_admin=False), ephemeral=True)


    @app_commands.command(name="adminmenu", description="Sistem yöneticileri için dinamik yetki paneli.")
    @app_commands.default_permissions(administrator=True)
    async def adminmenu(self, interaction: discord.Interaction) -> None:
        admin_mapping: dict[str, list[str]] = {"Admin": []}
        
        for cmd in interaction.client.tree.walk_commands():
            # Capture only grouped admin logic or explicit endpoints tied to admin rights
            if cmd.name == "admin" or (cmd.parent and cmd.parent.name == "admin"):
                if isinstance(cmd, app_commands.Command):
                    cmd_name = f"{cmd.parent.name} {cmd.name}" if cmd.parent else cmd.name
                    desc = cmd.description or "Yetkili sistem müdahalesi."
                    admin_mapping["Admin"].append(f"`/{cmd_name}` - {desc}")

        embed = discord.Embed(
            title="⚙️ Z 3 İ T T Sistem | Yetkili Kontrol Paneli",
            description="Bu panel yalnızca **Yönetici** yetkisine sahip hesaplar tarafından görüntülenebilir.\nArz ve beyaz liste manipülasyon araçları aşağıdadır:",
            color=0x8B0000
        )
        await interaction.response.send_message(embed=embed, view=DynamicHelpView(admin_mapping, is_admin=True), ephemeral=True)

    @app_commands.command(name="ship", description="Eşleştirme komutu 💘")
    @app_commands.describe(
        uye="Eşleştirmek istediğin üye",
        rastgele="Üyeyi rastgele biriyle eşleştirmek için 'rastgele' yaz"
    )
    async def ship(
        self,
        interaction: discord.Interaction,
        uye: discord.Member = None,
        rastgele: str = None
    ):
        # ✅ defer() EN BAŞA ALINDI — Discord 3 sn içinde cevap ister
        await interaction.response.defer()

        adaylar = [m for m in interaction.guild.members if not m.bot]

        try:
            if uye is None:
                kisi1 = interaction.user
                havuz = [m for m in adaylar if m.id != kisi1.id]
                if not havuz:
                    return await interaction.followup.send("😢 Eşleştirebileceğim başka kimse yok!", ephemeral=True)
                kisi2 = random.choice(havuz)

            elif rastgele is None:
                if uye.id == interaction.user.id:
                    return await interaction.followup.send("😅 Kendinle ship olamazsın!", ephemeral=True)
                kisi1 = interaction.user
                kisi2 = uye

            else:
                kisi1 = uye
                havuz = [m for m in adaylar if m.id != kisi1.id]
                if not havuz:
                    return await interaction.followup.send("😢 Eşleştirebileceğim başka kimse yok!", ephemeral=True)
                kisi2 = random.choice(havuz)

            uyum_puani = random.randint(1, 100)

            if uyum_puani >= 90:
                kalpler = "💞💞💞"
                yorum = "Mükemmel bir çift! Evlenin artık 💍"
                bar_renk = discord.Color.from_rgb(255, 20, 147)
            elif uyum_puani >= 70:
                kalpler = "💖💖"
                yorum = "Harika bir uyum var aranızda! 🥰"
                bar_renk = discord.Color.from_rgb(255, 105, 180)
            elif uyum_puani >= 50:
                kalpler = "💕"
                yorum = "Fena sayılmaz, bir şansınız var! 😊"
                bar_renk = discord.Color.from_rgb(255, 182, 193)
            elif uyum_puani >= 30:
                kalpler = "💔"
                yorum = "Biraz zorlu ama imkansız değil... 😬"
                bar_renk = discord.Color.orange()
            else:
                kalpler = "🖤"
                yorum = "Bu birliktelik... felaket olur. 💀"
                bar_renk = discord.Color.red()

            dolu = round(uyum_puani / 10)
            bar = "█" * dolu + "░" * (10 - dolu)
            isim1 = kisi1.display_name
            isim2 = kisi2.display_name
            ship_adi = isim1[:max(1, len(isim1) // 2)] + \
                isim2[max(0, len(isim2) // 2):]

            # ── Görsel ────────────────────────────────────────────────────────────
            # ✅ Tek bir session ile her iki avatarı çek (daha hızlı, daha güvenli)
            AV = 160  # avatar boyutu

            async def fetch_avatar(session: aiohttp.ClientSession, url: str) -> Image.Image:
                async with session.get(url) as resp:
                    data = await resp.read()
                img = Image.open(BytesIO(data)).convert("RGBA").resize((AV, AV), Image.LANCZOS)
                mask = Image.new("L", (AV, AV), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, AV, AV), fill=255)
                result = Image.new("RGBA", (AV, AV), (0, 0, 0, 0))
                result.paste(img, (0, 0), mask)
                return result

            async with aiohttp.ClientSession() as session:
                av1, av2 = await asyncio.gather(
                    fetch_avatar(session, kisi1.display_avatar.with_format("png").with_size(256).url),
                    fetch_avatar(session, kisi2.display_avatar.with_format("png").with_size(256).url),
                )

            # Renk
            if uyum_puani >= 70:
                bg_color = (255, 225, 235)
                accent   = (210, 60, 100)
            elif uyum_puani >= 40:
                bg_color = (255, 240, 220)
                accent   = (200, 110, 50)
            else:
                bg_color = (220, 220, 235)
                accent   = (90, 90, 150)

            # Canvas boyutları — her şey sığsın diye hesapla
            # Layout: [20px pad] [AV=160] [20px gap] [orta=120] [20px gap] [AV=160] [20px pad] = 520px
            # Yükseklik: 20 pad + 160 avatar + 20 isim alanı + 16 isim yazısı + 20 bar alanı + 14 bar + 20 pad = 270px
            W, H = 520, 270

            canvas = Image.new("RGB", (W, H), bg_color)
            draw = ImageDraw.Draw(canvas)

            # Font yükle
            try:
                font_pct  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
                font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
                font_bar  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
            except:
                font_pct = font_name = font_bar = ImageFont.load_default()

            # Pozisyonlar
            AV_Y    = 20                      # avatar üst kenar
            AV1_X   = 20                      # sol avatar sol kenar
            AV2_X   = W - 20 - AV            # sağ avatar sol kenar
            MID_X   = W // 2                  # orta nokta
            NAME_Y  = AV_Y + AV + 10         # isim y (avatar altı + 10px boşluk)
            BAR_Y   = NAME_Y + 22            # bar y (isim altı + 22px)
            BAR_H   = 12
            BAR_X   = 20
            BAR_W   = W - 40

            # Avatar gölgeleri
            shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow)
            sd.ellipse((AV1_X+4, AV_Y+4, AV1_X+AV+4, AV_Y+AV+4), fill=(0, 0, 0, 50))
            sd.ellipse((AV2_X+4, AV_Y+4, AV2_X+AV+4, AV_Y+AV+4), fill=(0, 0, 0, 50))
            canvas.paste(Image.alpha_composite(
                Image.new("RGBA", (W, H), (*bg_color, 255)), shadow
            ).convert("RGB"), (0, 0))
            draw = ImageDraw.Draw(canvas)

            # Avatarları yapıştır
            canvas.paste(av1, (AV1_X, AV_Y), av1)
            canvas.paste(av2, (AV2_X, AV_Y), av2)
            draw = ImageDraw.Draw(canvas)

            # Orta kalp
            try:
                font_heart = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except:
                font_heart = ImageFont.load_default()

            HEART_Y = AV_Y + AV // 2 - 30
            draw.text((MID_X+2, HEART_Y+2), "♥", font=font_heart, fill=(*accent, 60), anchor="mt")
            draw.text((MID_X, HEART_Y), "♥", font=font_heart, fill=accent, anchor="mt")

            # Puan pill
            pct_txt = f"%{uyum_puani}"
            pb = draw.textbbox((0, 0), pct_txt, font=font_pct)
            pw, ph = pb[2]-pb[0], pb[3]-pb[1]
            pill_pad = 10
            pill_x1 = MID_X - pw//2 - pill_pad
            pill_y1 = HEART_Y + 54
            pill_x2 = MID_X + pw//2 + pill_pad
            pill_y2 = pill_y1 + ph + 8
            draw.rounded_rectangle((pill_x1, pill_y1, pill_x2, pill_y2), radius=12, fill=accent)
            draw.text((MID_X, pill_y1 + 4), pct_txt, font=font_pct, fill=(255, 255, 255), anchor="mt")

            # İsimler — avatar altında ortalı
            name1 = kisi1.display_name[:16]
            name2 = kisi2.display_name[:16]
            draw.text((AV1_X + AV//2, NAME_Y), name1, font=font_name, fill=accent, anchor="mt")
            draw.text((AV2_X + AV//2, NAME_Y), name2, font=font_name, fill=accent, anchor="mt")

            # Bar arka plan
            draw.rounded_rectangle((BAR_X, BAR_Y, BAR_X+BAR_W, BAR_Y+BAR_H), radius=6, fill=(0,0,0,40))
            # Bar doluluk
            dolu_w = max(int(BAR_W * uyum_puani / 100), BAR_H)
            draw.rounded_rectangle((BAR_X, BAR_Y, BAR_X+dolu_w, BAR_Y+BAR_H), radius=6, fill=accent)

            buf = BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            file = discord.File(buf, filename="ship.png")

            # ── Embed ─────────────────────────────────────────────────────────────
            embed = discord.Embed(
                title=f"💘 Ship: {ship_adi}", color=bar_renk, timestamp=discord.utils.utcnow())
            embed.add_field(
                name="Çift",       value=f"{kisi1.mention} {kalpler} {kisi2.mention}", inline=False)
            embed.add_field(
                name="Uyum Puanı", value=f"`{bar}` **{uyum_puani}%**",                 inline=False)
            embed.add_field(name="Yorum",      value=yorum,
                            inline=False)
            embed.set_image(url="attachment://ship.png")
            embed.set_footer(
                text=f"Kader seni seçti! | {interaction.guild.name}", icon_url=kisi2.display_avatar.url)

            await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            # ✅ Hata olursa interaction asılı kalmaz, kullanıcıya bilgi verilir
            print(f"Ship komutu hatası: {e}")
            await interaction.followup.send("❌ Bir hata oluştu, tekrar dene!", ephemeral=True)

@bot.tree.command(name="panelkur", description="Özel oda panelini kanalda oluşturur 🎙️")
@app_commands.checks.has_permissions(administrator=True)
async def panelkur(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    kanal = bot.get_channel(PANEL_CHANNEL_ID)
    if not kanal or not isinstance(kanal, discord.TextChannel):
        return await interaction.followup.send("❌ Panel kanalı ID'si geçersiz.", ephemeral=True)

    embed = BotUI.embed(title="⚔️ ÖZEL ODA KONTROLÜ", color=BotUI.COLOR_PREMIUM)
    embed.description = (
        "Merhaba değerli **Z 3 İ T T** üyeleri,\n"
        "Sunucumuzda kendinize özel bir ses kanalı oluşturabilirsiniz! 🎵✨\n\n"
        "> 🔊 **Özel oda oluştur👑** ses kanalına giriş yaparak kendi ses kanalınızı hemen oluşturabilirsiniz.\n"
        "Kanalınızı oluşturduktan sonra, aşağıdaki butonları kullanarak odanızı dilediğiniz gibi yönetebilirsiniz.\n\n"
    )

    embed.add_field(name="⚙️ Odanızı Güncelleyin", value=(
        "💀 **Gizle & Kilitle:** Odayı hem gizler hem de girişleri kapatır.\n"
        "✏️ **İsim Değiş:** Oda isminizi günceller.\n"
        "⬆️ **Limit Güncelle:** Odanızın kapasitesini ayarlar."
    ), inline=False)

    embed.add_field(name="🛡️ Erişim Kontrolü", value=(
        "🔒 **Kilitle:** Odanızı dışarıya tamamen kapatır.\n"
        "👥 **İzin Ver:** Belirttiğiniz bir kullanıcının odaya girmesini sağlar.\n"
        "🚫 **Yasakla:** Belirttiğiniz bir kullanıcının odaya girişini yasaklar."
    ), inline=False)

    embed.add_field(name="✨ Diğer Ayarlar", value=(
        "👁️ **Görünmez Yap:** Odanızı listeden gizler.\n"
        "👑 **Devret:** Oda sahipliğini odadaki başka birine aktarır.\n"
        "🗑️ **Odayı Sil:** Odanızı kalıcı olarak siler."
    ), inline=False)

    embed.set_footer(text="Özel Oda Sistemi #z3ittANİSTAN")

    await kanal.send(embed=embed, view=RoomPanelView())
    await interaction.followup.send(BotUI.success("Oda kontrol paneli başarıyla kuruldu."), ephemeral=True)
# ─────────────────────────────────────────────────────────────────────────────
# ÇEKİLİŞ SİSTEMİ
# ─────────────────────────────────────────────────────────────────────────────

GIVEAWAY_FILE = "cekilisler.json"


def save_giveaways():
    """Çekilişleri diske kaydet (bot restart'ta kaybolmasın)."""
    kayit = {}
    for mid, v in aktif_cekilisler.items():
        kayit[str(mid)] = {**v, "bitis": v["bitis"].isoformat()}
    with open(GIVEAWAY_FILE, "w") as f:
        json.dump(kayit, f, indent=4)


def load_giveaways():
    """Diskten çekilişleri yükle."""
    if not os.path.exists(GIVEAWAY_FILE):
        return
    with open(GIVEAWAY_FILE, "r") as f:
        try:
            kayit = json.load(f)
        except:
            return
    for mid_str, v in kayit.items():
        v["bitis"] = datetime.fromisoformat(v["bitis"])
        aktif_cekilisler[int(mid_str)] = v


def sure_parse(sure: str) -> int | None:
    """Süre stringini saniyeye çevirir. Hatalıysa None döner."""
    sure_map = {"s": 1, "d": 60, "h": 3600, "m": 86400}
    sure = sure.strip().lower()
    if len(sure) < 2 or sure[-1] not in sure_map:
        return None
    try:
        deger = int(sure[:-1])
        return deger * sure_map[sure[-1]] if deger > 0 else None
    except ValueError:
        return None


def build_giveaway_embed(veri: dict, bitti: bool = False) -> discord.Embed:
    renk = discord.Color.red() if bitti else discord.Color.green()
    baslik = f"🎉 ÇEKİLİŞ {'SONA ERDİ' if bitti else 'BAŞLADI'}!"
    embed = discord.Embed(title=baslik, color=renk, timestamp=discord.utils.utcnow())
    embed.add_field(name="🏆 Ödül", value=f"**{veri['odul']}**", inline=False)
    embed.add_field(name="🎟️ Kazanan Sayısı", value=f"**{veri['kazanan_sayisi']}** kişi", inline=True)
    embed.add_field(name="👥 Katılımcı", value=f"**{len(veri['katilimcilar'])}** kişi", inline=True)

    if not bitti:
        bitis_ts = int(veri["bitis"].timestamp())
        embed.add_field(name="⏰ Bitiş", value=f"<t:{bitis_ts}:R>", inline=False)
        embed.add_field(name="📅 Bitiş Tarihi", value=f"<t:{bitis_ts}:F>", inline=False)

    embed.set_footer(text=f"Düzenleyen: {veri['duzenleyen']} | Çekiliş Sistemi")
    return embed


async def cekilisi_bitir(mesaj_id: int, veri: dict):
    """Çekilişi sonlandırır, kazananları seçer, embed'i günceller."""
    kanal = bot.get_channel(veri["kanal_id"])
    if not kanal:
        return

    try:
        mesaj = await kanal.fetch_message(mesaj_id)
    except (discord.NotFound, discord.HTTPException):
        return

    katilimcilar = veri["katilimcilar"]
    k_sayisi = min(veri["kazanan_sayisi"], len(katilimcilar))

    if katilimcilar and k_sayisi > 0:
        kazananlar = random.sample(katilimcilar, k_sayisi)
        k_mentions = " ".join([f"<@{uid}>" for uid in kazananlar])
        sonuc_txt = f"🎊 Tebrikler! **{veri['odul']}** kazandılar:\n{k_mentions}"
    else:
        k_mentions = "—"
        sonuc_txt = "😔 Yeterli katılımcı olmadığı için kazanan seçilemedi."

    bitis_embed = build_giveaway_embed(veri, bitti=True)
    bitis_embed.add_field(name="🏅 Kazananlar", value=k_mentions, inline=False)

    bitis_view = discord.ui.View()
    bitis_view.add_item(discord.ui.Button(
        label="🎉 Çekiliş Bitti", style=discord.ButtonStyle.grey, disabled=True
    ))

    try:
        await mesaj.edit(embed=bitis_embed, view=bitis_view)
        await kanal.send(
            content=f"🎉 **ÇEKİLİŞ SONA ERDİ!** — {sonuc_txt}",
            reference=mesaj
        )
    except (discord.NotFound, discord.HTTPException):
        pass

    await send_log(
        kanal.guild,
        f"🎉 Çekiliş bitti: **{veri['odul']}** | Kazananlar: {k_mentions} | Düzenleyen: {veri['duzenleyen']}",
        discord.Color.gold()
    )


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎉 Katıl",
        style=discord.ButtonStyle.green,
        custom_id="giveaway_join"
    )
    async def katil(self, interaction: discord.Interaction, button: discord.ui.Button):
        mesaj_id = interaction.message.id
        if mesaj_id not in aktif_cekilisler:
            return await interaction.response.send_message(
                "❌ Bu çekiliş artık aktif değil.", ephemeral=True
            )

        veri = aktif_cekilisler[mesaj_id]
        katilimci = str(interaction.user.id)

        if katilimci in veri["katilimcilar"]:
            veri["katilimcilar"].remove(katilimci)
            mesaj = "💨 Çekilişten **ayrıldın**."
        else:
            veri["katilimcilar"].append(katilimci)
            mesaj = "✅ Çekilişe **katıldın!** Bol şans 🍀"

        save_giveaways()

        # Buton + Embed ikisini de güncelle
        button.label = f"🎉 Katıl ({len(veri['katilimcilar'])})"
        yeni_embed = build_giveaway_embed(veri)
        await interaction.response.send_message(mesaj, ephemeral=True)
        await interaction.message.edit(embed=yeni_embed, view=self)

    @discord.ui.button(
        label="👥 Katılımcılar",
        style=discord.ButtonStyle.blurple,
        custom_id="giveaway_list"
    )
    async def liste(self, interaction: discord.Interaction, button: discord.ui.Button):
        mesaj_id = interaction.message.id
        if mesaj_id not in aktif_cekilisler:
            return await interaction.response.send_message("❌ Çekiliş bulunamadı.", ephemeral=True)

        veri = aktif_cekilisler[mesaj_id]
        if not veri["katilimcilar"]:
            return await interaction.response.send_message("📭 Henüz kimse katılmadı.", ephemeral=True)

        # 25'ten fazla kişi varsa hepsini gösterme, Discord limiti var
        kisiler = "\n".join([f"• <@{uid}>" for uid in veri["katilimcilar"][:25]])
        if len(veri["katilimcilar"]) > 25:
            kisiler += f"\n... ve {len(veri['katilimcilar']) - 25} kişi daha"

        embed = discord.Embed(
            title=f"👥 Katılımcılar ({len(veri['katilimcilar'])} kişi)",
            description=kisiler,
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@tasks.loop(seconds=15)
async def giveaway_kontrol():
    biten = [mid for mid, v in list(aktif_cekilisler.items())
             if discord.utils.utcnow() >= v["bitis"]]
    for mesaj_id in biten:
        veri = aktif_cekilisler.pop(mesaj_id)
        save_giveaways()
        await cekilisi_bitir(mesaj_id, veri)


@tasks.loop(time=dt_time(hour=21, minute=0, tzinfo=timezone.utc))  # Türkiye saatiyle gece yarısı (UTC+3 = 21:00 UTC)
async def gunluk_ses_siralama():
    """Her gün gece yarısı (TSİ 00:00) 3 ayrı tabloyu leaderboard kanalında günceller."""
    ses_data = load_ses()
    
    # Güncel tarih (TSİ)
    tz = timezone(timedelta(hours=3))
    simdi = datetime.now(tz).strftime("%d.%m.%Y %H:%M")

    for guild in bot.guilds:
        kanal = discord.utils.get(guild.text_channels, name=LIDERLIK_KANAL_ADI)
        if not kanal:
            continue
            
        thumb_url = guild.icon.url if guild.icon else None

        # 1. SES SIRALAMASI
        ses_skorlar = []
        for uid_str, info in ses_data.items():
            toplam = info["toplam_saniye"]
            uid = int(uid_str)
            if uid in ses_giris_takip:
                toplam += int(time.time() - ses_giris_takip[uid])
            ses_skorlar.append((uid, toplam))
        ses_skorlar.sort(key=lambda x: x[1], reverse=True)

        ses_satirlar = []
        i = 1
        for uid, sn in ses_skorlar:
            if i > 10: break
            m = guild.get_member(uid)
            if not m: continue
            dakika = sn // 60
            saat = dakika // 60
            kalan_dakika = dakika % 60
            sure_str = f"{saat} saat {kalan_dakika} dk" if saat > 0 else f"{kalan_dakika} dk"
            ses_satirlar.append(f"`{i}.` {m.mention}: `{sure_str}`")
            i += 1

        embed_ses = BotUI.embed(
            title="🔊 Ses Liderlik Tablosu",
            desc="\n".join(ses_satirlar) or "Henüz veri yok.",
            color=0x2b2d31
        )
        if thumb_url: embed_ses.set_thumbnail(url=thumb_url)
        embed_ses.add_field(name="Son düzenleme", value=f"`{simdi}`", inline=False)

        # 2. MESAJ SIRALAMASI
        mesaj_skorlar = []
        mesaj_verileri = siralama_verileri.get("mesajlar", {})
        for uid_str, sayi in mesaj_verileri.items():
            mesaj_skorlar.append((int(uid_str), sayi))
        mesaj_skorlar.sort(key=lambda x: x[1], reverse=True)

        mesaj_satirlar = []
        i = 1
        for uid, sayi in mesaj_skorlar:
            if i > 10: break
            m = guild.get_member(uid)
            if not m: continue
            mesaj_satirlar.append(f"`{i}.` {m.mention}: `{sayi} mesaj`")
            i += 1

        embed_mesaj = BotUI.embed(
            title="💬 Mesaj Liderlik Tablosu",
            desc="\n".join(mesaj_satirlar) or "Henüz veri yok.",
            color=0x2b2d31
        )
        if thumb_url: embed_mesaj.set_thumbnail(url=thumb_url)
        embed_mesaj.add_field(name="Son düzenleme", value=f"`{simdi}`", inline=False)

        # 3. YAYIN SIRALAMASI
        yayin_skorlar = []
        yayin_verileri = siralama_verileri.get("yayin", {})
        for uid_str, sn in yayin_verileri.items():
            toplam = sn
            uid = int(uid_str)
            if uid in yayin_giris_takip:
                toplam += int(time.time() - yayin_giris_takip[uid])
            yayin_skorlar.append((uid, toplam))
        yayin_skorlar.sort(key=lambda x: x[1], reverse=True)

        yayin_satirlar = []
        i = 1
        for uid, sn in yayin_skorlar:
            if i > 10: break
            m = guild.get_member(uid)
            if not m: continue
            dakika = sn // 60
            saat = dakika // 60
            kalan_dakika = dakika % 60
            sure_str = f"{saat} saat {kalan_dakika} dk" if saat > 0 else f"{kalan_dakika} dk"
            yayin_satirlar.append(f"`{i}.` {m.mention}: `{sure_str}`")
            i += 1

        embed_yayin = BotUI.embed(
            title="💻 Yayın Liderlik Tablosu",
            desc="\n".join(yayin_satirlar) or "Henüz veri yok.",
            color=0x2b2d31
        )
        if thumb_url: embed_yayin.set_thumbnail(url=thumb_url)
        embed_yayin.add_field(name="Son düzenleme", value=f"`{simdi}`", inline=False)

        # MESAJLARI GÖNDER / GÜNCELLE
        siralama_verileri.setdefault("mesaj_ids", {})
        
        async def mesaj_isleme(mesaj_tipi, embed_obj):
            mesaj_id = siralama_verileri["mesaj_ids"].get(mesaj_tipi)
            if mesaj_id:
                try:
                    msg = await kanal.fetch_message(mesaj_id)
                    await msg.edit(embed=embed_obj)
                    return
                except discord.NotFound:
                    siralama_verileri["mesaj_ids"].pop(mesaj_tipi, None)
                except Exception as e:
                    print(f"Liderlik mesajı güncellenemedi ({mesaj_tipi}): {e}")
            # Bulunamadıysa veya hata verirse yeni at
            try:
                msg = await kanal.send(embed=embed_obj)
                siralama_verileri["mesaj_ids"][mesaj_tipi] = msg.id
                save_siralama()
            except Exception as e:
                print(f"Liderlik mesajı gönderilemedi ({mesaj_tipi}): {e}")

        await mesaj_isleme("mesaj", embed_mesaj)
        await mesaj_isleme("ses", embed_ses)
        await mesaj_isleme("yayin", embed_yayin)


@bot.tree.command(name="leaderboard", description="Anlık sıralamayı (ses, mesaj, yayın) leaderboard kanalına atar")
async def leaderboard_komut(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator and interaction.user.id not in BEYAZ_LISTE:
        return await interaction.response.send_message("🚫 Bu komutu kullanma yetkin yok!", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    kanal = discord.utils.get(guild.text_channels, name=LIDERLIK_KANAL_ADI)
    if not kanal:
        return await interaction.followup.send(
            BotUI.error(f"`{LIDERLIK_KANAL_ADI}` adlı bir kanal bulunamadı! Lütfen sunucuda bu isimde bir kanal oluşturun."),
            ephemeral=True
        )

    ses_data = load_ses()
    tz = timezone(timedelta(hours=3))
    simdi = datetime.now(tz).strftime("%d.%m.%Y %H:%M")
    thumb_url = guild.icon.url if guild.icon else None

    # SES
    ses_skorlar = []
    for uid_str, info in ses_data.items():
        toplam = info["toplam_saniye"]
        uid = int(uid_str)
        if uid in ses_giris_takip:
            toplam += int(time.time() - ses_giris_takip[uid])
        ses_skorlar.append((uid, toplam))
    ses_skorlar.sort(key=lambda x: x[1], reverse=True)

    ses_satirlar = []
    i = 1
    for uid, sn in ses_skorlar:
        if i > 10: break
        m = guild.get_member(uid)
        if not m: continue
        dakika = sn // 60; saat = dakika // 60; kalan_dakika = dakika % 60
        sure_str = f"{saat} saat {kalan_dakika} dk" if saat > 0 else f"{kalan_dakika} dk"
        ses_satirlar.append(f"`{i}.` {m.mention}: `{sure_str}`")
        i += 1

    lb_embed_ses = BotUI.embed(title="🔊 Ses Liderlik Tablosu", desc="\n".join(ses_satirlar) or "Henüz veri yok.", color=0x2b2d31)
    if thumb_url: lb_embed_ses.set_thumbnail(url=thumb_url)
    lb_embed_ses.add_field(name="Son düzenleme", value=f"`{simdi}`", inline=False)

    # MESAJ
    mesaj_skorlar = sorted([(int(k), v) for k, v in siralama_verileri.get("mesajlar", {}).items()], key=lambda x: x[1], reverse=True)
    mesaj_satirlar = []
    i = 1
    for uid, sayi in mesaj_skorlar:
        if i > 10: break
        m = guild.get_member(uid)
        if not m: continue
        mesaj_satirlar.append(f"`{i}.` {m.mention}: `{sayi} mesaj`")
        i += 1

    lb_embed_mesaj = BotUI.embed(title="💬 Mesaj Liderlik Tablosu", desc="\n".join(mesaj_satirlar) or "Henüz veri yok.", color=0x2b2d31)
    if thumb_url: lb_embed_mesaj.set_thumbnail(url=thumb_url)
    lb_embed_mesaj.add_field(name="Son düzenleme", value=f"`{simdi}`", inline=False)

    # YAYIN
    yayin_skorlar = []
    for uid_str, sn in siralama_verileri.get("yayin", {}).items():
        toplam = sn
        uid = int(uid_str)
        if uid in yayin_giris_takip:
            toplam += int(time.time() - yayin_giris_takip[uid])
        yayin_skorlar.append((uid, toplam))
    yayin_skorlar.sort(key=lambda x: x[1], reverse=True)

    yayin_satirlar = []
    i = 1
    for uid, sn in yayin_skorlar:
        if i > 10: break
        m = guild.get_member(uid)
        if not m: continue
        dakika = sn // 60; saat = dakika // 60; kalan_dakika = dakika % 60
        sure_str = f"{saat} saat {kalan_dakika} dk" if saat > 0 else f"{kalan_dakika} dk"
        yayin_satirlar.append(f"`{i}.` {m.mention}: `{sure_str}`")
        i += 1

    lb_embed_yayin = BotUI.embed(title="💻 Yayın Liderlik Tablosu", desc="\n".join(yayin_satirlar) or "Henüz veri yok.", color=0x2b2d31)
    if thumb_url: lb_embed_yayin.set_thumbnail(url=thumb_url)
    lb_embed_yayin.add_field(name="Son düzenleme", value=f"`{simdi}`", inline=False)

    siralama_verileri.setdefault("mesaj_ids", {})

    async def lb_gonder(mesaj_tipi, embed_obj):
        mesaj_id = siralama_verileri["mesaj_ids"].get(mesaj_tipi)
        if mesaj_id:
            try:
                msg = await kanal.fetch_message(mesaj_id)
                await msg.edit(embed=embed_obj)
                return
            except discord.NotFound:
                siralama_verileri["mesaj_ids"].pop(mesaj_tipi, None)
            except Exception:
                pass
        try:
            msg = await kanal.send(embed=embed_obj)
            siralama_verileri["mesaj_ids"][mesaj_tipi] = msg.id
            save_siralama()
        except Exception as e:
            print(f"[/leaderboard] Mesaj gönderilemedi ({mesaj_tipi}): {e}")

    await lb_gonder("mesaj", lb_embed_mesaj)
    await lb_gonder("ses", lb_embed_ses)
    await lb_gonder("yayin", lb_embed_yayin)

    await interaction.followup.send(
        BotUI.success(f"Liderlik tabloları <#{kanal.id}> kanalına gönderildi / güncellendi."),
        ephemeral=True
    )


@bot.tree.command(name="cekilis", description="Yeni çekiliş başlatır (Admin / Beyaz Liste)")
@app_commands.describe(
    odul="Çekiliş ödülü",
    sure="Süre: 30s=saniye, 5d=dakika, 2h=saat, 1m=gün",
    kazanan="Kaç kişi kazanacak (varsayılan 1)",
    kanal="Çekilişin yapılacağı kanal (boş = bu kanal)"
)
async def giveaway(
    interaction: discord.Interaction,
    odul: str,
    sure: str,
    kazanan: int = 1,
    kanal: discord.TextChannel = None
):
    if (interaction.user.id != OZEL_SAHIP_ID
            and interaction.user.id not in BEYAZ_LISTE
            and not interaction.user.guild_permissions.administrator):
        return await interaction.response.send_message("🚫 Yetkin yok!", ephemeral=True)
    toplam_sn = sure_parse(sure)
    if not toplam_sn:
        return await interaction.response.send_message(
            "❌ Geçersiz süre!\nÖrnekler: `30s` (saniye) `5d` (dakika) `2h` (saat) `1m` (gün)",
            ephemeral=True
        )

    if kazanan < 1:
        return await interaction.response.send_message("❌ Kazanan sayısı en az 1 olmalı!", ephemeral=True)

    hedef_kanal = kanal or interaction.channel
    veri = {
        "odul": odul,
        "bitis": discord.utils.utcnow() + timedelta(seconds=toplam_sn),
        "kazanan_sayisi": kazanan,
        "katilimcilar": [],
        "kanal_id": hedef_kanal.id,
        "duzenleyen": interaction.user.display_name,
    }

    embed = build_giveaway_embed(veri)
    mesaj = await hedef_kanal.send(embed=embed, view=GiveawayView())

    aktif_cekilisler[mesaj.id] = veri
    save_giveaways()

    await interaction.response.send_message(
        f"✅ Çekiliş **{hedef_kanal.mention}** kanalında başlatıldı!", ephemeral=True
    )
    await send_log(
        interaction.guild,
        f"🎉 Yeni Çekiliş: **{odul}** | Süre: `{sure}` | Kazanan: {kazanan} | {interaction.user.mention}",
        discord.Color.gold()
    )


@bot.tree.command(name="cekilisiptal", description="Aktif çekilişi iptal eder")
@app_commands.describe(mesaj_id="İptal edilecek çekilişin mesaj ID'si")
async def giveaway_iptal(interaction: discord.Interaction, mesaj_id: str):
    if (interaction.user.id != OZEL_SAHIP_ID
            and interaction.user.id not in BEYAZ_LISTE
            and not interaction.user.guild_permissions.administrator):
        return await interaction.response.send_message("🚫 Yetkin yok!", ephemeral=True)

    try:
        mid = int(mesaj_id)
    except ValueError:
        return await interaction.response.send_message("❌ Geçerli bir mesaj ID'si gir!", ephemeral=True)

    if mid not in aktif_cekilisler:
        return await interaction.response.send_message("❌ Aktif çekiliş bulunamadı!", ephemeral=True)

    veri = aktif_cekilisler.pop(mid)
    save_giveaways()

    kanal = bot.get_channel(veri["kanal_id"])
    if kanal:
        try:
            mesaj = await kanal.fetch_message(mid)
            iptal_embed = build_giveaway_embed(veri, bitti=True)
            iptal_embed.title = "🚫 ÇEKİLİŞ İPTAL EDİLDİ"
            iptal_embed.color = discord.Color.red()
            iptal_view = discord.ui.View()
            iptal_view.add_item(discord.ui.Button(
                label="❌ İptal Edildi", style=discord.ButtonStyle.grey, disabled=True
            ))
            await mesaj.edit(embed=iptal_embed, view=iptal_view)
            await kanal.send(
                f"🚫 **{veri['odul']}** çekilişi {interaction.user.mention} tarafından iptal edildi.",
                reference=mesaj
            )
        except (discord.NotFound, discord.HTTPException):
            pass

    await interaction.response.send_message("✅ Çekiliş iptal edildi.", ephemeral=True)
    await send_log(
        interaction.guild,
        f"🚫 Çekiliş İptal: **{veri['odul']}** | {interaction.user.mention}",
        discord.Color.red()
    )


@bot.tree.command(name="cekilislistele", description="Aktif çekilişleri listeler")
async def giveaway_listele(interaction: discord.Interaction):
    if not aktif_cekilisler:
        return await interaction.response.send_message("📭 Şu an aktif çekiliş yok.", ephemeral=True)

    embed = discord.Embed(
        title="🎉 Aktif Çekilişler",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    for mid, v in aktif_cekilisler.items():
        embed.add_field(
            name=f"🏆 {v['odul']}",
            value=(
                f"Katılımcı: **{len(v['katilimcilar'])}**\n"
                f"Kazanan: **{v['kazanan_sayisi']}**\n"
                f"Bitiş: <t:{int(v['bitis'].timestamp())}:R>\n"
                f"[Mesaja Git](https://discord.com/channels/{interaction.guild.id}/{v['kanal_id']}/{mid})"
            ),
            inline=True
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="cekilisyeniden", description="Biten çekilişi yeniden çeker")
@app_commands.describe(
    mesaj_id="Yeniden çekilecek mesajın ID'si",
    kanal="Mesajın bulunduğu kanal (boş = bu kanal)"
)
async def giveaway_yeniden(
    interaction: discord.Interaction,
    mesaj_id: str,
    kanal: discord.TextChannel = None
):
    if (interaction.user.id != OZEL_SAHIP_ID
            and interaction.user.id not in BEYAZ_LISTE
            and not interaction.user.guild_permissions.administrator):
        return await interaction.response.send_message("🚫 Yetkin yok!", ephemeral=True)

    # Aktif çekilişlerde ara
    try:
        mid = int(mesaj_id)
    except ValueError:
        return await interaction.response.send_message("❌ Geçerli bir mesaj ID'si gir!", ephemeral=True)

    if mid not in aktif_cekilisler:
        return await interaction.response.send_message(
            "❌ Bu ID'ye ait aktif çekiliş yok. Sadece aktif çekilişlerde yeniden çekim yapılabilir.",
            ephemeral=True
        )

    veri = aktif_cekilisler[mid]
    katilimcilar = veri["katilimcilar"]
    k_sayisi = min(veri["kazanan_sayisi"], len(katilimcilar))

    if not katilimcilar or k_sayisi == 0:
        return await interaction.response.send_message("❌ Yeterli katılımcı yok!", ephemeral=True)

    kazananlar = random.sample(katilimcilar, k_sayisi)
    k_mentions = " ".join([f"<@{uid}>" for uid in kazananlar])

    await interaction.response.send_message(
        f"🔁 **Yeniden Çekim!** — **{veri['odul']}** için yeni kazananlar:\n{k_mentions}"
    )
    await send_log(
        interaction.guild,
        f"🔁 Yeniden Çekim: **{veri['odul']}** | Kazananlar: {k_mentions} | {interaction.user.mention}",
        discord.Color.gold()
    )





# ══════════════════════════════════════════════════════════════════════════════
# YEDEK COG
# ══════════════════════════════════════════════════════════════════════════════
class YedekCog(commands.Cog):
    yedek_group = app_commands.Group(name="yedek", description="Sunucu yedekleme sistemi (Beyaz Liste)")

    def _beyaz_liste_kontrol(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id in BEYAZ_LISTE or interaction.user.id == interaction.guild.owner_id

    # ── /yedek al ─────────────────────────────────────────────────────────────
    @yedek_group.command(name="al", description="Sunucunun kanal, kategori ve rol yapısını yedekler")
    async def yedek_al(self, interaction: discord.Interaction):
        if not self._beyaz_liste_kontrol(interaction):
            return await interaction.response.send_message("🚫 Bu komutu kullanma yetkin yok!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        # Rolleri kaydet (yönetilebilir olanlar)
        roller = []
        for rol in guild.roles:
            if rol.is_default() or rol.managed:
                continue
            roller.append({
                "id": rol.id,
                "name": rol.name,
                "color": rol.color.value,
                "hoist": rol.hoist,
                "mentionable": rol.mentionable,
                "position": rol.position,
                "permissions": rol.permissions.value
            })

        # Kategoriler ve kanalları kaydet
        kategoriler = []
        for kat in guild.categories:
            kat_izinler = []
            for target, overwrite in kat.overwrites.items():
                allow, deny = overwrite.pair()
                kat_izinler.append({
                    "id": target.id,
                    "type": "role" if isinstance(target, discord.Role) else "member",
                    "allow": allow.value,
                    "deny": deny.value
                })
            kanallar = []
            for kanal in kat.channels:
                kanal_izinler = []
                for target, overwrite in kanal.overwrites.items():
                    allow, deny = overwrite.pair()
                    kanal_izinler.append({
                        "id": target.id,
                        "type": "role" if isinstance(target, discord.Role) else "member",
                        "allow": allow.value,
                        "deny": deny.value
                    })
                kanallar.append({
                    "id": kanal.id,
                    "name": kanal.name,
                    "type": str(kanal.type),
                    "position": kanal.position,
                    "overwrites": kanal_izinler,
                    "topic": getattr(kanal, "topic", None),
                    "slowmode": getattr(kanal, "slowmode_delay", 0),
                    "nsfw": getattr(kanal, "nsfw", False)
                })
            kategoriler.append({
                "id": kat.id,
                "name": kat.name,
                "position": kat.position,
                "overwrites": kat_izinler,
                "kanallar": kanallar
            })

        # Kategorisiz kanalları kaydet
        kategorisiz = []
        for kanal in guild.channels:
            if kanal.category is not None:
                continue
            if isinstance(kanal, discord.CategoryChannel):
                continue
            kanal_izinler = []
            for target, overwrite in kanal.overwrites.items():
                allow, deny = overwrite.pair()
                kanal_izinler.append({
                    "id": target.id,
                    "type": "role" if isinstance(target, discord.Role) else "member",
                    "allow": allow.value,
                    "deny": deny.value
                })
            kategorisiz.append({
                "id": kanal.id,
                "name": kanal.name,
                "type": str(kanal.type),
                "position": getattr(kanal, "position", 0),
                "overwrites": kanal_izinler
            })

        yedek_id = str(int(discord.utils.utcnow().timestamp()))
        yedek = {
            "tarih": discord.utils.utcnow().strftime("%d.%m.%Y %H:%M"),
            "alan": interaction.user.name,
            "roller": roller,
            "kategoriler": kategoriler,
            "kategorisiz": kategorisiz
        }

        data = load_yedek()

        # Max 5 yedek tut
        if len(data) >= 5:
            en_eski = sorted(data.keys())[0]
            del data[en_eski]

        data[yedek_id] = yedek
        save_yedek(data)

        embed = discord.Embed(
            title="✅ Yedek Alındı",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Yedek ID", value=f"`{yedek_id}`", inline=True)
        embed.add_field(name="Rol Sayısı", value=str(len(roller)), inline=True)
        embed.add_field(name="Kategori Sayısı", value=str(len(kategoriler)), inline=True)
        embed.add_field(name="Kanal Sayısı", value=str(sum(len(k["kanallar"]) for k in kategoriler) + len(kategorisiz)), inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)
        await send_log(guild, f"💾 Sunucu Yedeği Alındı | ID: `{yedek_id}` | {interaction.user.mention}", discord.Color.green())

    # ── /yedek liste ──────────────────────────────────────────────────────────
    @yedek_group.command(name="liste", description="Kayıtlı yedekleri listeler")
    async def yedek_liste(self, interaction: discord.Interaction):
        if not self._beyaz_liste_kontrol(interaction):
            return await interaction.response.send_message("🚫 Bu komutu kullanma yetkin yok!", ephemeral=True)

        data = load_yedek()
        if not data:
            return await interaction.response.send_message("📭 Kayıtlı yedek yok.", ephemeral=True)

        embed = discord.Embed(title="💾 Kayıtlı Yedekler", color=discord.Color.blurple())
        for yid, yedek in sorted(data.items(), reverse=True):
            rol_say = len(yedek.get("roller", []))
            kat_say = len(yedek.get("kategoriler", []))
            kanal_say = sum(len(k["kanallar"]) for k in yedek.get("kategoriler", [])) + len(yedek.get("kategorisiz", []))
            embed.add_field(
                name=f"📅 {yedek['tarih']} | ID: `{yid}`",
                value=f"Alan: **{yedek['alan']}** | {rol_say} rol, {kat_say} kategori, {kanal_say} kanal",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /yedek yukle ──────────────────────────────────────────────────────────
    @yedek_group.command(name="yukle", description="Seçilen yedeği yükler (eksik/değişmiş kanal ve rolleri düzeltir)")
    @app_commands.describe(
        yedek_id="Yüklenecek yedeğin ID'si (/yedek liste ile görüntüle)",
        eski_kanallari_sil="Eski kanallar silinsin mi?"
    )
    @app_commands.choices(eski_kanallari_sil=[
        app_commands.Choice(name="Evet", value="evet"),
        app_commands.Choice(name="Hayır", value="hayir")
    ])
    async def yedek_yukle(self, interaction: discord.Interaction, yedek_id: str, eski_kanallari_sil: str = "hayir"):
        if not self._beyaz_liste_kontrol(interaction):
            return await interaction.response.send_message("🚫 Bu komutu kullanma yetkin yok!", ephemeral=True)

        data = load_yedek()
        if yedek_id not in data:
            return await interaction.response.send_message("❌ Bu ID'ye ait yedek bulunamadı!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        yedek = data[yedek_id]

        olusturulan_rol = 0
        olusturulan_kat = 0
        olusturulan_kanal = 0
        duzeltilen_izin = 0

        # ── KANALLARI SİL (İSTEĞE BAĞLI) ──────────────────────────────────
        if eski_kanallari_sil == "evet":
            for c in guild.channels:
                if c.id != interaction.channel.id:
                    try:
                        await c.delete()
                    except:
                        pass
            await asyncio.sleep(2)

        # ── ROLLERİ YÜKLE ─────────────────────────────────────────────────
        mevcut_rol_isimleri = {r.name for r in guild.roles}
        rol_id_map = {r.id: r for r in guild.roles}

        for rol_data in sorted(yedek.get("roller", []), key=lambda x: x["position"], reverse=True):
            mevcut = discord.utils.get(guild.roles, name=rol_data["name"])
            if mevcut is None:
                try:
                    await guild.create_role(
                        name=rol_data["name"],
                        color=discord.Color(rol_data["color"]),
                        hoist=rol_data["hoist"],
                        mentionable=rol_data["mentionable"],
                        permissions=discord.Permissions(rol_data["permissions"])
                    )
                    olusturulan_rol += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"[yedek_yukle] Rol oluşturma hatası ({rol_data['name']}): {e}")
            else:
                # İzinler farklıysa düzelt
                if mevcut.permissions.value != rol_data["permissions"]:
                    try:
                        await mevcut.edit(permissions=discord.Permissions(rol_data["permissions"]))
                        duzeltilen_izin += 1
                        await asyncio.sleep(0.3)
                    except Exception:
                        pass

        # Guild rollerini yenile
        await asyncio.sleep(1)
        rol_isim_map = {r.name: r for r in guild.roles}

        def overwrite_olustur(izin_listesi):
            overwrites = {}
            for izin in izin_listesi:
                target = guild.get_role(izin["id"]) or guild.get_member(izin["id"])
                if target is None:
                    target = rol_isim_map.get(next(
                        (r["name"] for r in yedek.get("roller", []) if r["id"] == izin["id"]), None
                    ))
                if target is None:
                    continue
                allow = discord.Permissions(izin["allow"])
                deny = discord.Permissions(izin["deny"])
                ow = discord.PermissionOverwrite.from_pair(allow, deny)
                overwrites[target] = ow
            return overwrites

        # ── KATEGORİLERİ YÜKLE ────────────────────────────────────────────
        mevcut_kat_isimleri = {c.name: c for c in guild.categories}

        for kat_data in sorted(yedek.get("kategoriler", []), key=lambda x: x["position"]):
            overwrites = overwrite_olustur(kat_data["overwrites"])

            if kat_data["name"] not in mevcut_kat_isimleri:
                try:
                    yeni_kat = await guild.create_category(
                        name=kat_data["name"],
                        overwrites=overwrites
                    )
                    olusturulan_kat += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"[yedek_yukle] Kategori oluşturma hatası ({kat_data['name']}): {e}")
                    yeni_kat = None
            else:
                yeni_kat = mevcut_kat_isimleri[kat_data["name"]]
                # Kategorinin izinlerini güncelle
                try:
                    await yeni_kat.edit(overwrites=overwrites)
                    duzeltilen_izin += 1
                    await asyncio.sleep(0.3)
                except Exception:
                    pass

            if yeni_kat is None:
                continue

            # Kategorideki kanalları yükle
            mevcut_kanal_isimleri = {c.name: c for c in yeni_kat.channels}
            for kanal_data in sorted(kat_data.get("kanallar", []), key=lambda x: x["position"]):
                kanal_overwrites = overwrite_olustur(kanal_data["overwrites"])

                if kanal_data["name"] not in mevcut_kanal_isimleri:
                    try:
                        tip = kanal_data["type"]
                        if "voice" in tip:
                            await guild.create_voice_channel(
                                name=kanal_data["name"],
                                category=yeni_kat,
                                overwrites=kanal_overwrites
                            )
                        elif "forum" in tip:
                            await guild.create_forum(
                                name=kanal_data["name"],
                                category=yeni_kat,
                                overwrites=kanal_overwrites
                            )
                        else:
                            await guild.create_text_channel(
                                name=kanal_data["name"],
                                category=yeni_kat,
                                overwrites=kanal_overwrites,
                                topic=kanal_data.get("topic"),
                                slowmode_delay=kanal_data.get("slowmode", 0),
                                nsfw=kanal_data.get("nsfw", False)
                            )
                        olusturulan_kanal += 1
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"[yedek_yukle] Kanal oluşturma hatası ({kanal_data['name']}): {e}")
                else:
                    # Kanal var, izinleri düzelt
                    mevcut_kanal = mevcut_kanal_isimleri[kanal_data["name"]]
                    try:
                        await mevcut_kanal.edit(overwrites=kanal_overwrites)
                        duzeltilen_izin += 1
                        await asyncio.sleep(0.3)
                    except Exception:
                        pass

        embed = discord.Embed(
            title="✅ Yedek Yüklendi",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Oluşturulan Rol", value=str(olusturulan_rol), inline=True)
        embed.add_field(name="Oluşturulan Kategori", value=str(olusturulan_kat), inline=True)
        embed.add_field(name="Oluşturulan Kanal", value=str(olusturulan_kanal), inline=True)
        embed.add_field(name="Düzeltilen İzin", value=str(duzeltilen_izin), inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)
        await send_log(guild, f"♻️ Yedek Yüklendi | ID: `{yedek_id}` | {interaction.user.mention}\n✅ {olusturulan_rol} rol, {olusturulan_kat} kategori, {olusturulan_kanal} kanal oluşturuldu | {duzeltilen_izin} izin düzeltildi", discord.Color.orange())

    # ── /yedek sil ────────────────────────────────────────────────────────────
    @yedek_group.command(name="sil", description="Belirtilen yedeği siler")
    @app_commands.describe(yedek_id="Silinecek yedeğin ID'si")
    async def yedek_sil(self, interaction: discord.Interaction, yedek_id: str):
        if not self._beyaz_liste_kontrol(interaction):
            return await interaction.response.send_message("🚫 Bu komutu kullanma yetkin yok!", ephemeral=True)

        data = load_yedek()
        if yedek_id not in data:
            return await interaction.response.send_message("❌ Bu ID'ye ait yedek bulunamadı!", ephemeral=True)

        tarih = data[yedek_id]["tarih"]
        del data[yedek_id]
        save_yedek(data)

        await interaction.response.send_message(f"🗑️ `{tarih}` tarihli yedek silindi.", ephemeral=True)
        await send_log(interaction.guild, f"🗑️ Yedek Silindi | ID: `{yedek_id}` | {interaction.user.mention}", discord.Color.red())

# ─────────────────────────────────────────────────────────────────────────────
# COG'LARI KAYDET VE BAŞLAT
# ─────────────────────────────────────────────────────────────────────────────

async def setup_cogs():
    await bot.add_cog(AdminCog())
    await bot.add_cog(EkonomiCog())
    await bot.add_cog(ModerasyonCog())
    await bot.add_cog(SesCog())
    await bot.add_cog(BilgiCog())
    await bot.add_cog(DavetCog())
    await bot.add_cog(YedekCog())

# ══════════════════════════════════════════════════════════════════════════════
# DAVET TAKİP COG
# ══════════════════════════════════════════════════════════════════════════════
class DavetCog(commands.Cog):


    @app_commands.command(name="davet", description="Davet istatistiklerini gösterir")
    @app_commands.describe(uye="Görmek istediğin üye (boş = kendin)")
    async def davet(self, interaction: discord.Interaction, uye: discord.Member = None):
        hedef = uye or interaction.user
        davet_data = load_davet()
        uid_str = str(hedef.id)
        bilgi = davet_data.get(uid_str, {"toplam": 0, "getirdikleri": []})
        toplam = bilgi["toplam"]
        getirdikleri = bilgi["getirdikleri"]

        getirilen_list = []
        for mid in getirdikleri[-10:]:
            m = interaction.guild.get_member(int(mid))
            if m:
                getirilen_list.append(m.mention)

        embed = discord.Embed(
            title=f"📨 {hedef.display_name} — Davet İstatistikleri",
            color=discord.Color.green() if hedef == interaction.user else discord.Color.blurple()
        )
        embed.add_field(name="Toplam Davet", value=f"**{toplam}**", inline=True)
        embed.add_field(name="Getirilen Üyeler (son 10)", value=", ".join(getirilen_list) or "Yok", inline=False)
        embed.set_thumbnail(url=hedef.display_avatar.url)
        ephemeral = hedef == interaction.user
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @app_commands.command(name="davet_siralama", description="En çok davet eden ilk 10 kişiyi gösterir")
    async def davet_siralama(self, interaction: discord.Interaction):
        davet_data = load_davet()
        skorlar = []
        for uid_str, bilgi in davet_data.items():
            m = interaction.guild.get_member(int(uid_str))
            if not m:
                continue
            skorlar.append((m, bilgi["toplam"]))
        skorlar.sort(key=lambda x: x[1], reverse=True)

        madalyalar = ["🥇", "🥈", "🥉"]
        satirlar = []
        for i, (m, toplam) in enumerate(skorlar[:10]):
            ikon = madalyalar[i] if i < 3 else f"`{i+1}.`"
            satirlar.append(f"{ikon} {m.mention} — **{toplam}** davet")

        embed = discord.Embed(
            title="🏆 Davet Sıralaması (İlk 10)",
            description="\n".join(satirlar) or "Henüz davet verisi yok.",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed)

# Cog'ları on_ready öncesinde setup et


async def main():
    async with bot:
        await setup_cogs()
        await bot.start(TOKEN)

asyncio.run(main())