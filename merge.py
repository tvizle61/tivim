import requests
import re

# Güncellenecek kaynak linkler
urls = [
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/hit.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/ss.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/cafe.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/ulusal.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/cocuk.m3u",
]

def get_channel_name(extinf_line):
    """EXTINF satırından kanal adını çıkar"""
    match = re.search(r',\s*(.+)$', extinf_line)
    return match.group(1).strip().lower() if match else None

def parse_source_m3u(content):
    """Kaynak dosyalardan kanal adı -> (meta_lines, url) eşleştirmesi"""
    channels = {}
    lines = content.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            channel_name = get_channel_name(line)
            meta_lines = [line]
            i += 1
            # EXTVLCOPT ve diğer # ile başlayan satırlar
            while i < len(lines) and lines[i].strip().startswith("#"):
                meta_lines.append(lines[i].strip())
                i += 1
            # URL satırı
            url = lines[i].strip() if i < len(lines) and not lines[i].strip().startswith("#") else ""
            if channel_name and url:
                channels[channel_name] = {
                    "meta": meta_lines,
                    "url": url
                }
            i += 1
        else:
            i += 1
    return channels

def update_merged_m3u(merged_path, source_channels):
    """merged.m3u dosyasını oku, sıralamayı koru, sadece linkleri güncelle"""
    with open(merged_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    updated_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        if line.strip().startswith("#EXTINF"):
            channel_name = get_channel_name(line.strip())
            
            # EXTINF satırını ekle (orijinal haliyle - isim ve logo korunur)
            new_lines.append(line)
            i += 1
            
            # Mevcut meta satırlarını atla, sonra URL'yi bul
            old_meta = []
            while i < len(lines) and lines[i].strip().startswith("#"):
                old_meta.append(lines[i])
                i += 1
            
            # Eski URL satırı
            old_url = lines[i] if i < len(lines) else ""
            
            # Kaynaklarda bu kanal var mı?
            if channel_name and channel_name in source_channels:
                source = source_channels[channel_name]
                # Yeni meta satırlarını ekle (EXTVLCOPT vs.)
                for meta in source["meta"][1:]:  # İlk satır EXTINF, onu zaten ekledik
                    new_lines.append(meta + "\n")
                # Yeni URL'yi ekle
                new_lines.append(source["url"] + "\n")
                if source["url"].strip() != old_url.strip():
                    updated_count += 1
                    print(f"✓ Güncellendi: {channel_name}")
            else:
                # Kaynaklarda yok, orijinal meta ve URL'yi koru
                for meta in old_meta:
                    new_lines.append(meta)
                new_lines.append(old_url)
            
            i += 1
        else:
            new_lines.append(line)
            i += 1
    
    # Dosyayı güncelle
    with open(merged_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    return updated_count

# Ana işlem
print("="*50)
print("MERGED.M3U LINK GÜNCELLEME")
print("="*50)

# 1. Tüm kaynak dosyaları indir ve parse et
all_source_channels = {}

for url in urls:
    print(f"\n📥 İndiriliyor: {url.split('/')[-1]}")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        channels = parse_source_m3u(resp.text)
        print(f"   {len(channels)} kanal bulundu")
        # Sonraki dosyalar önceki linkleri override eder
        all_source_channels.update(channels)
    except Exception as e:
        print(f"   ❌ HATA: {e}")

print(f"\n📊 Toplam {len(all_source_channels)} benzersiz kanal kaynaklardan alındı")

# 2. merged.m3u dosyasını güncelle
print("\n" + "="*50)
print("GÜNCELLEME BAŞLIYOR...")
print("="*50)

try:
    updated = update_merged_m3u("merged.m3u", all_source_channels)
    print(f"\n✅ TAMAMLANDI!")
    print(f"   {updated} kanal linki güncellendi")
    print(f"   Dosya: merged.m3u")
except FileNotFoundError:
    print("\n❌ HATA: merged.m3u dosyası bulunamadı!")
    print("   Bu scripti merged.m3u ile aynı klasörde çalıştırın.")
except Exception as e:
    print(f"\n❌ HATA: {e}")            else:
                channels[channel_name] = {
                    "meta": meta_lines,
                    "url": url
                }
                order.append(channel_name)
            i += 1
        else:
            i += 1
    return channels, order

all_channels = {}
all_order = []

for url in urls:
    print(f"Fetching: {url}")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        content = resp.text
        channels, order = parse_m3u(content)
        
        for name in order:
            if name in all_channels:
                # Sadece URL güncelle
                all_channels[name]["url"] = channels[name]["url"]
            else:
                all_channels[name] = channels[name]
                all_order.append(name)
    except Exception as e:
        print(f"  HATA: {e}")

# merged.m3u yaz
with open("merged.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n\n")
    for name in all_order:
        ch = all_channels[name]
        for meta in ch["meta"]:
            f.write(meta + "\n")
        f.write(ch["url"] + "\n\n")

print(f"\nToplam {len(all_order)} kanal merged.m3u dosyasına yazıldı.")
