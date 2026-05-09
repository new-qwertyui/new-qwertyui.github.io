import requests
from bs4 import BeautifulSoup
import json
import re

def clean_url(url):
    if url and "google.com/url?q=" in url:
        return url.split("q=")[1].split("&")[0]
    return url

def scrape():
    gid = "34972268"
    url = f"https://yetracker.net/htmlview/sheet?headers=true&gid={gid}"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr')
    
    tracker_data = {}
    current_era = "Unknown"
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 3: continue
        
        era_text = cells[0].get_text().strip()
        track_name = cells[1].get_text().strip()
        
        if era_text: current_era = era_text
        if not track_name or track_name.lower() == "track name": continue
        
        link = row.find('a')['href'] if row.find('a') else None
        
        if current_era not in tracker_data:
            tracker_data[current_era] = []
            
        tracker_data[current_era].append({
            "name": track_name,
            "link": clean_url(link),
            "note": cells[2].get_text().strip()
        })

    with open('data.json', 'w') as f:
        json.dump(tracker_data, f, indent=4)

if __name__ == "__main__":
    scrape()
