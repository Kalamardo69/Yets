import requests
import re
import unicodedata

SOURCE_URL = "https://ipfs.io/ipns/k2k4r8lm8tkmuxbc8lkmq1in3v0oya1p6pe9o5bu0hu30br5ko08k2gb/data/listas/lista_fuera_iptv.m3u"
OUTPUT_FILE = "lista2.m3u"
# La URL base que precede al ID
BASE_URL = "http://192.168.18.41:6878/ace/getstream?id="

# Grupos que se eliminan por completo
REMOVE_GROUPS = ["bundesliga","eventos","futbol int","motor","nba","otros","sport tv","tdt","tenis","ufc","liga endesa"]

# Canales específicos que se eliminan
REMOVE_CHANNELS = [
    "teledeporte","FOX PREMIUM UFC","SKY SPORTS ARENA","REAL MADRID TV",
    "SKY SPORTS CRICKET","SKY SPORTS MAIN EVENT","TNT SPORTS","DAZN F1 4K",
    "AMC", "CAZA Y PESCA","DARK","ONETORO","TOROLE TV","TVG EUROPA", 
    "MOVISTAR GOLF", "solo eventos" 
]

ORDER = [
    "dazn bar", "dazn laliga", "movistar laliga", "liga de campeones",
    "hypermotion", "1rfef", "primera federacion", "dazn",                
    "movistar deportes", "movistar vamos", "gol play", "dazn f1",             
    "movistar", "eurosport"            
]

GROUP_DATA = {
    "1rfef": '#EXTGRP: group-title="1RFEF" group-logo="https://static.wikia.nocookie.net/logopedia/images/d/df/Logo_Primera_RFEF_2021.png/revision/latest?cb=20230620215900&path-prefix=es"',
    "primera federacion": '#EXTGRP: group-title="1RFEF" group-logo="https://static.wikia.nocookie.net/logopedia/images/d/df/Logo_Primera_RFEF_2021.png/revision/latest?cb=20230620215900&path-prefix=es"',
    "dazn laliga": '#EXTGRP: título del grupo="LA LIGA" logotipo del grupo="https://i.ibb.co/sp6dD8h2/laliga-logo.png"',
    "movistar laliga": '#EXTGRP: título del grupo="LA LIGA" logotipo del grupo="https://i.ibb.co/sp6dD8h2/laliga-logo.png"',
    "liga de campeones": '#EXTGRP: group-title="LIGA DE CAMPEONES" group-logo="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Liga_de_Campeones_por_Movistar_Plus%2B_2023_Logo.svg/2560px-Liga_de_Campeones_por_Movistar_Plus%2B_2023_Logo.svg.png"',
    "hypermotion": '#EXTGRP: título del grupo="HIPERMOCIÓN" logotipo del grupo="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/LaLiga_Hypermotion_2023_Vertical_Logo.svg/2335px-LaLiga_Hypermotion_2023_Vertical_Logo.svg.png"',
    "dazn bar": '#EXTGRP: título del grupo="DAZN" logotipo del grupo="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Dazn-logo.png/601px-Dazn-logo.png"',
    "dazn": '#EXTGRP: título del grupo="DAZN" logotipo del grupo="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Dazn-logo.png/601px-Dazn-logo.png"',
    "movistar deportes": '#EXTGRP: group-title="MOVISTAR DEPORTES" group-logo="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Deportes_por_Movistar_Plus%2B_2022_logo.svg/2560px-Deportes_por_Movistar_Plus%2B_2022_logo.svg.png"',
    "movistar vamos": '#EXTGRP: group-title="MOVISTAR DEPORTES" group-logo="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Deportes_por_Movistar_Plus%2B_2022_logo.svg/2560px-Deportes_por_Movistar_Plus%2B_2022_logo.svg.png"',
    "dazn f1": '#EXTGRP: título del grupo="FÓRMULA 1" logotipo del grupo="https://i.ibb.co/2Ndmtbp/f1.png"',
    "movistar": '#EXTGRP: título-grupo="MOVISTAR" logotipo-grupo="https://upload.wikimedia.org/wikipedia/commons/d/d9/Movistar%2B_Logo.png"',
    "eurosport": '#EXTGRP: título del grupo="EUROSPORT" logotipo del grupo="https://logos-world.net/wp-content/uploads/2022/05/Eurosport-Logo.png"',
    "gol play": '#EXTGRP: título del grupo="DEPORTES" logotipo del grupo="https://i.ibb.co/6JGvLDWx/deportes-logo.png"'
}

def clean_text(text, no_numbers=False):
    if not text: return ""
    text = text.lower().replace("m+", "movistar")
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")
    text = text.replace(" ", "")
    if no_numbers:
        text = re.sub(r'\d+', '', text)
    return text

def get_priority(extinf_line):
    full_name = extinf_line.split(",")[-1].split("-->")[0].strip()
    name_for_match = clean_text(full_name, no_numbers=True)
    num = int(re.search(r'(\d+)', full_name).group(1)) if re.search(r'(\d+)', full_name) else 0
    
    best_match = None
    max_len = 0
    
    for i, key in enumerate(ORDER):
        clean_key = clean_text(key, no_numbers=True)
        if key == "dazn f1":
            if "f1" in name_for_match and not ("fhd" in name_for_match and "dazn" in name_for_match and "f1" not in name_for_match):
                return (i, num, key)
            continue
        if clean_key in name_for_match:
            if len(clean_key) > max_len:
                max_len = len(clean_key)
                best_match = (i, num, key)
    return best_match if best_match else (None, None, None)

# --- PROCESO ---
try:
    r = requests.get(SOURCE_URL, timeout=15)
    r.raise_for_status()
    lines = r.text.splitlines()
except:
    print("Error al descargar la lista fuente.")
    exit()

channels = []
current_block = []
for line in lines:
    line = line.strip()
    if not line or line.startswith("#EXTM3U"): continue
    if line.startswith("#EXTINF"):
        if current_block: channels.append(current_block)
        current_block = [line]
    else: current_block.append(line)
if current_block: channels.append(current_block)

final_list = []
active_groups = set()

for ch in channels:
    header = ch[0]
    full_name_raw = header.split(",")[-1].split("-->")[0].strip()
    
    if any(clean_text(x) in clean_text(full_name_raw) for x in REMOVE_CHANNELS):
        continue
        
    if any(f'group-title="{g.lower()}' in header.lower() for g in REMOVE_GROUPS):
        continue

    prio, num, g_key = get_priority(header)
    if prio is not None:
        new_block = []
        for l in ch:
            if "acestream://" in l:
                # REEMPLAZAMOS 'acestream://' por la URL de tu servidor
                # Esto deja solo el ID al final de la URL
                new_block.append(l.replace("acestream://", BASE_URL))
            else:
                new_block.append(l)
                
        final_list.append({'block': new_block, 'prio': prio, 'num': num, 'g_key': g_key})
        active_groups.add(g_key)

final_list.sort(key=lambda x: (x['prio'], x['num']))

# --- ESCRITURA ---
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write('#EXTM3U url-tvg="https://raw.githubusercontent.com/davidmuma/EPG_dobleM/refs/heads/master/guiatv.xml,https://epgshare01.online/epgshare01/epg_ripper_NL1.xml.gz,https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiatv.xml" actualizar="3600"\n')
    f.write('#EXTVLCOPT:almacenamiento en caché de red=1000\n')
    
    written_logos = set()
    for key in ORDER:
        if key in active_groups:
            logo_line = GROUP_DATA.get(key)
            if logo_line and logo_line not in written_logos:
                f.write(logo_line + "\n")
                written_logos.add(logo_line)
    
    f.write('\n\n') 
    
    for item in final_list:
        for line in item['block']:
            f.write(line + "\n")

print(f"Lista generada. Ahora los enlaces son: {BASE_URL}[ID]")
