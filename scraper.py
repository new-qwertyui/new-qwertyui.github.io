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
                if col.lower() not in ["#ffffff", "white"]:
                    color_map[cls_name] = col

    rows = soup.find_all('tr')
    tracker_data = {}
    current_era = "Unknown"
    trash_keywords = ["og file(s)", "full", "tagged", "partial", "snippet(s)", "unavailable", "era", "track name"]

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 2: continue
        
        era_td = cells[0]
        era_text = era_td.get_text().strip()
        track_name = cells[1].get_text().strip()
        
        classes = era_td.get('class', [])
        bg_color = None
        for c in classes:
            if c in color_map:
                bg_color = color_map[c]
                break
                
        img_tag = era_td.find('img')
        if not img_tag and len(cells) > 1: 
            img_tag = cells[1].find('img')
        img_src = img_tag['src'] if img_tag else None

        if era_text and not any(k in era_text.lower() for k in trash_keywords):
            current_era = era_text
            
        if current_era not in tracker_data:
            tracker_data[current_era] = {
                "color": "",
                "image": "",
                "tracks": []
            }
            
        if bg_color and not tracker_data[current_era]["color"]:
            tracker_data[current_era]["color"] = bg_color
        if img_src and not tracker_data[current_era]["image"]:
            tracker_data[current_era]["image"] = img_src

        if not track_name or any(k in track_name.lower() for k in trash_keywords):
            continue
        
        link_tag = row.find('a')
        raw_link = link_tag['href'] if link_tag else ""
        pillows_id = ""
        if "pillows.su" in raw_link:
            match = re.search(r'pillows\.su/f/([a-zA-Z0-9]+)', raw_link)
            if match:
                pillows_id = match.group(1)

        tracker_data[current_era]["tracks"].append({
            "name": track_name,
            "pillows_id": pillows_id,
            "note": cells[2].get_text().strip() if len(cells) > 2 else ""
        })

    with open('data.json', 'w') as f:
        json.dump(tracker_data, f, indent=4)

if __name__ == "__main__":
    scrape()
