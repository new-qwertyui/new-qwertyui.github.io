import requests
from bs4 import BeautifulSoup
import json
import re

def scrape():
    gid = "34972268"
    url = f"https://yetracker.net/htmlview/sheet?headers=true&gid={gid}"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    color_map = {}
    for style_tag in soup.find_all('style'):
        css_text = style_tag.get_text()
        for match in re.finditer(r'\.(s\d+)[^{]*\{([^}]+)\}', css_text):
            cls_name = match.group(1)
            rules = match.group(2)
            bg_match = re.search(r'background-color:\s*([^;]+)', rules)
            if bg_match:
                col = bg_match.group(1).strip()
                if col.lower() not in ["#ffffff", "white", "transparent"]:
                    color_map[cls_name] = col

    rows = soup.find_all('tr')
    tracker_data = {}
    current_era = "Unknown"
    era_marker = "og file(s)"
    trash_keywords = ["og file(s)", "full", "tagged", "partial", "snippet(s)", "unavailable", "era", "track name"]

    for row in rows:
        cells = row.find_all('td')
        if not cells: continue
        
        first_cell_text = cells[0].get_text().lower()
        
        if era_marker in first_cell_text:
            full_era_text = cells[1].get_text().strip()
            
            # Split Era Name from Alt Names (stuff in parentheses)
            # Regex looks for the first "(" and takes everything before it as the name
            name_match = re.split(r'\s*\(', full_era_text, 1)
            era_main_name = name_match[0].strip()
            era_alt_names = f"({name_match[1]}" if len(name_match) > 1 else ""

            if era_main_name and not any(k in era_main_name.lower() for k in trash_keywords):
                current_era = era_main_name
                if current_era not in tracker_data:
                    tracker_data[current_era] = {
                        "alt_names": era_alt_names,
                        "color": "", 
                        "image": "", 
                        "tracks": []
                    }
                
                if len(cells) > 4:
                    img_tag = cells[4].find('img')
                    if img_tag:
                        src = img_tag.get('src', '')
                        # FIX: Ensure URL starts with https:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif not src.startswith('http'):
                            src = 'https://' + src
                        tracker_data[current_era]["image"] = src
                
                for c in cells[1].get('class', []):
                    if c in color_map:
                        tracker_data[current_era]["color"] = color_map[c]
                        break

        link_tag = row.find('a')
        if link_tag and current_era != "Unknown":
            track_name = cells[1].get_text().strip()
            if track_name and not any(k in track_name.lower() for k in trash_keywords):
                raw_link = link_tag['href']
                pillows_id = ""
                id_match = re.search(r'(?:f/|download/)([a-zA-Z0-9]+)', raw_link)
                if id_match:
                    pillows_id = id_match.group(1)

                tracker_data[current_era]["tracks"].append({
                    "name": track_name,
                    "pillows_id": pillows_id,
                    "note": cells[2].get_text().strip() if len(cells) > 2 else ""
                })

    final_data = {k: v for k, v in tracker_data.items() if v["tracks"]}
    with open('data.json', 'w') as f:
        json.dump(final_data, f, indent=4)

if __name__ == "__main__":
    scrape()
