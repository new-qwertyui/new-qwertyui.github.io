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
    rows = soup.find_all('tr')
    
    tracker_data = {}
    current_era = "Unknown"
    
    trash_keywords = ["og file(s)", "full", "tagged", "partial", "snippet(s)", "unavailable", "era", "track name"]

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 2: continue
        
        era_text = cells[0].get_text().strip()
        track_name = cells[1].get_text().strip()
        
        if era_text and not any(k in era_text.lower() for k in trash_keywords):
            current_era = era_text
            
        if not track_name or any(k in track_name.lower() for k in trash_keywords):
            continue
        
        link_tag = row.find('a')
        raw_link = link_tag['href'] if link_tag else ""
        
        pillows_id = ""
        if "pillows.su" in raw_link:
            match = re.search(r'pillows\.su/f/([a-zA-Z0-9]+)', raw_link)
            if match:
                pillows_id = match.group(1)

        if current_era not in tracker_data:
            tracker_data[current_era] = []
            
        tracker_data[current_era].append({
            "name": track_name,
            "pillows_id": pillows_id,
            "note": cells[2].get_text().strip() if len(cells) > 2 else ""
        })

    with open('data.json', 'w') as f:
        json.dump(tracker_data, f, indent=4)

if __name__ == "__main__":
    scrape()
