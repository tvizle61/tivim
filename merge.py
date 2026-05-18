import requests
import re
import os

# Kaynak M3U URL'leri
SOURCE_URLS = [
    "https://raw.githubusercontent.com/kadirsener1/avva1/refs/heads/main/playlist.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/hit.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/ss.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/cafe.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/ulusal.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/cocuk.m3u",
]

def m3u_parse(content):
    """M3U içeriğini kanal listesine parse eder. Her kanal: isim, metadata (tüm # satırları), link"""
    channels = []
    current_meta = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('#EXTINF'):
            # Yeni kanal başlangıcı
            current_meta = [line]
        elif line.startswith('#'):
            # Mevcut kanalın metadata satırı (EXTVLCOPT dahil)
            if current_meta:
                current_meta.append(line)
        else:
            # Yayın linki satırı
            if current_meta:
                # Kanal adını EXTINF satırından al (virgülden sonraki kısım)
                extinf_line = current_meta[0]
                name_match = re.search(r',(.+)$', extinf_line)
                channel_name = name_match.group(1).strip() if name_match else extinf_line.strip()
                channels.append({
                    'name': channel_name,
                    'meta': current_meta.copy(),
                    'url': line
                })
                current_meta = []
    return channels

def main():
    merged_path = 'merged.m3u'

    if os.path.exists(merged_path):
        # MEVCUT merged.m3u VAR: Sıralamayı koru, sadece link güncelle
        print(f"Mevcut {merged_path} bulundu. Sıralama korunuyor, sadece linkler güncelleniyor...")
        with open(merged_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        existing_channels = m3u_parse(existing_content)
        print(f"Mevcut {len(existing_channels)} kanal yüklendi.")

        # Kaynaklardan kanal adı -> link sözlüğü oluştur
        source_links = {}
        for url in SOURCE_URLS:
            print(f"Kaynak çekiliyor: {url}")
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                channels = m3u_parse(resp.text)
                for ch in channels:
                    # Aynı kanal birden fazla kaynakta varsa son linki al
                    source_links[ch['name']] = ch['url']
                print(f"  {len(channels)} kanal tarandı.")
            except Exception as e:
                print(f"  HATA: {e}")

        # Mevcut kanalların sadece linklerini güncelle (diğer her şey sabit kalır)
        updated_count = 0
        for ch in existing_channels:
            if ch['name'] in source_links:
                new_url = source_links[ch['name']]
                if ch['url'] != new_url:
                    ch['url'] = new_url
                    updated_count += 1

        # Güncellenmiş dosyayı yaz
        with open(merged_path, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for ch in existing_channels:
                for meta_line in ch['meta']:
                    f.write(meta_line + '\n')
                f.write(ch['url'] + '\n')

        print(f"✅ İşlem tamamlandı. {updated_count} kanalın linki güncellendi. Toplam {len(existing_channels)} kanal kaydedildi.")

    else:
        # merged.m3u YOK: Kaynakları birleştir, tüm içeriği koru
        print(f"{merged_path} bulunamadı. Kaynaklar birleştiriliyor...")
        all_channels = []
        seen_channels = {}  # kanal adı -> listedeki indexi

        for url in SOURCE_URLS:
            print(f"Kaynak çekiliyor: {url}")
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                channels = m3u_parse(resp.text)
                print(f"  {len(channels)} kanal bulundu.")
                for ch in channels:
                    name = ch['name']
                    if name not in seen_channels:
                        # İlk kez görülen kanalı ekle
                        all_channels.append(ch)
                        seen_channels[name] = len(all_channels) - 1
                    else:
                        # Mevcut kanalın sadece linkini güncelle
                        idx = seen_channels[name]
                        all_channels[idx]['url'] = ch['url']
            except Exception as e:
                print(f"  HATA: {e}")

        # Dosyayı yaz
        with open(merged_path, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for ch in all_channels:
                for meta_line in ch['meta']:
                    f.write(meta_line + '\n')
                f.write(ch['url'] + '\n')

        print(f"✅ İşlem tamamlandı. Toplam {len(all_channels)} kanal birleştirildi, tekrar edenler ayıklandı.")

if __name__ == '__main__':
    main()
