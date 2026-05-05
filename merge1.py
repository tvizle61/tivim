import requests
import os

m3u_urls = [
    "https://raw.githubusercontent.com/kadirsener1/tivim/main/m3u/hit.m3u",
     "https://raw.githubusercontent.com/kadirsener1/tivim/main/m3u/ulusal.m3u",
    "https://raw.githubusercontent.com/kadirsener1/selcuk/main/5.m3u"
]

output_file = "merged.m3u"

def fetch_m3u(url):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Hata: {url} okunamadı. Detay: {e}")
        return ""

def parse_m3u(content):
    channels = []
    lines = content.splitlines()

    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            extinf = lines[i]
            if i + 1 < len(lines):
                url = lines[i + 1].strip()
                channels.append((extinf, url))
            i += 2
        else:
            i += 1
    return channels

def load_existing():
    if not os.path.exists(output_file):
        return []

    with open(output_file, "r", encoding="utf-8") as f:
        return parse_m3u(f.read())

# #EXTINF satırından sadece kanal adını (virgülden sonrasını) alır
def get_clean_name(extinf_line):
    if "," in extinf_line:
        return extinf_line.split(",")[-1].strip()
    return extinf_line.strip()

def merge():
    existing_channels = load_existing()
    
    # Yeni dosyaları indirip kanal adlarına göre sözlüğe alıyoruz
    new_channels_dict = {}
    new_channels_order = [] # Yeni kanalların geliş sırasını tutmak için
    
    for url in m3u_urls:
        content = fetch_m3u(url)
        parsed = parse_m3u(content)
        for extinf, stream_url in parsed:
            name = get_clean_name(extinf)
            if name not in new_channels_dict:
                new_channels_order.append(name)
            # Anahtarı kanal ismi yapıyoruz, değeri url yapıyoruz
            new_channels_dict[name] = (extinf, stream_url)

    final_list = []
    processed_names = set()

    # 🔥 1. Adım: Eski sıralamayı koru + Eğer link değişmişse linki GÜNCELLE
    for old_extinf, old_url in existing_channels:
        name = get_clean_name(old_extinf)
        
        if name in new_channels_dict:
            # Kanal yeni listede var, o zaman YENİ LİNKİ (new_url) al, mevcut ismi (old_extinf) koru.
            _, new_url = new_channels_dict[name]
            final_list.append((old_extinf, new_url))
        else:
            # Kanal yeni listede yoksa, eskisini olduğu gibi bırak
            final_list.append((old_extinf, old_url))
            
        processed_names.add(name)

    # ➕ 2. Adım: Yepyeni kanallar gelmişse onları listenin en sonuna ekle
    for name in new_channels_order:
        if name not in processed_names:
            extinf, stream_url = new_channels_dict[name]
            final_list.append((extinf, stream_url))

    # Dosyaya yaz
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for extinf, url in final_list:
            f.write(f"{extinf}\n{url}\n")

    print("✅ Sıralama korundu, değişen linkler aynı ismin altına güncellendi.")

if __name__ == "__main__":
    merge()
