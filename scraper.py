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
    trash_keywords = ["og file(s)", "full", "tagged", "partial", "snippet(s)", "unavailable", "era", "track name", "0 stem bounce"]

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 2: continue
        
        # Check if this row is an Era Header (usually has the description/image)
        # We look at the 2nd cell (index 1) for the Era Name
        pot_era_name = cells[1].get_text().strip()
        
        # If the first cell contains "OG File(s)" or similar stats, it's definitely an Era Header row
        is_era_header = "og file(s)" in cells[0].get_text().lower()

        if is_era_header and pot_era_name:
            current_era = pot_era_name
            if current_era not in tracker_data:
                tracker_data[current_era] = {"color": "", "image": "", "tracks": []}
            
            # 1. Hunt for Image in ANY cell of this row
            for td in cells:
                img = td.find('img')
                if img and img.get('src'):
                    tracker_data[current_era]["image"] = img['src']
                    break
            
            # 2. Hunt for Color in the Era Name cell
            for c in cells[1].get('class', []):
                if c in color_map:
                    tracker_data[current_era]["color"] = color_map[c]
                    break

        # Track Logic (Rows that have a link in them)
        track_name = cells[1].get_text().strip()
        link_tag = row.find('a')
        
        if link_tag and current_era != "Unknown":
            raw_link = link_tag['href']
            pillows_id = ""
            if "pillows.su" in raw_link:
                # Support both /f/ and /api/ paths
                match = re.search(r'(?:f/|download/)([a-zA-Z0-9]+)', raw_link)
                if match: pillows_id = match.group(1)

            # Avoid adding the Header row as a track
            if not any(k in track_name.lower() for k in trash_keywords):
                tracker_data[current_era]["tracks"].append({
                    "name": track_name,
                    "pillows_id": pillows_id,
                    "note": cells[2].get_text().strip() if len(cells) > 2 else ""
                })

    # Clean up empty eras
    final_data = {k: v for k, v in tracker_data.items() if v["tracks"]}

    with open('data.json', 'w') as f:
        json.dump(final_data, f, indent=4)

if __name__ == "__main__":
    scrape()
