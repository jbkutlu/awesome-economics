import requests
from bs4 import BeautifulSoup
import yaml
import os
import re
import time
from datetime import datetime

def load_existing_events(filename="events.yaml"):
    """Load existing events from a YAML file. Returns a list of events. If file doesn't exist, returns an empty list."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data else []
    except Exception as e:
        print(f"⚠️ File read error: {e}")
        return []

def scrape_inomics():
    base_url = "https://inomics.com/top/conferences"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Arch Linux; Linux x86_64) AppleWebKit/537.36"}
    
    existing_events = load_existing_events()
    existing_links = {event['link'] for event in existing_events if 'link' in event}
    
    # --- STEP 1: FETCH FIRST PAGE AND DETECT TOTAL PAGES ---
    try:
        first_page_res = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(first_page_res.text, 'html.parser')
        
        # Look for links containing "page=" inside pagination items
        pagination_links = soup.select('li.pager__item a[href*="page="]')
        
        page_numbers = []
        for link in pagination_links:
            href = link.get('href', '')
            # Extract digits following "page="
            match = re.search(r'page=(\d+)', href)
            if match:
                page_numbers.append(int(match.group(1)))
        
        # INOMICS is 0-indexed. If we find up to page=10, total pages to loop is 10.
        total_pages = max(page_numbers) if page_numbers else 0
        print(f"📊 Max page index detected: {total_pages}. Starting crawl from page 0...")
    except Exception as e:
        print(f"❌ Could not determine total pages: {e}")
        return

    new_entries_count = 0

    # --- STEP 2: LOOP THROUGH ALL PAGES ---
    for current_page in range(0, total_pages + 1):
        url = base_url if current_page == 0 else f"{base_url}?page={current_page}"
        print(f"🔎 Scanning page {current_page}/{total_pages}...")

        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            posts = soup.select('ul.posts li')
            
            if not posts: 
                break # Stop if the page is empty
            
            for post in posts:
                try:
                    link_tag = post.find('a', class_='post-link')
                    if not link_tag: continue
                    
                    link = "https://inomics.com" + link_tag['href']
                    if link in existing_links: 
                        continue

                    # Data Extraction
                    title = post.find('h2').get_text(strip=True)
                    event_type = post.find('span', class_='type-badge').get_text(strip=True)
                    
                    location_tag = post.select_one('.location.bold')
                    location = " ".join(location_tag.get_text(strip=True).split()) if location_tag else "Remote"
                    
                    # Smart Date Extraction from hidden content
                    date_element = post.select_one('span[content*="-2026"]')
                    raw_date = date_element['content'] if date_element else None
                    
                    # Convert DD-MM-YYYY to YYYY-MM-DD
                    if raw_date:
                        formatted_date = datetime.strptime(raw_date, "%d-%m-%Y").strftime("%Y-%m-%d")
                    else:
                        formatted_date = str(datetime.now().date())

                    new_event = {
                        'title': title,
                        'date': formatted_date,
                        'type': event_type,
                        'location': location,
                        'link': link,
                        'description': f"{event_type} event located in {location}."
                    }
                    
                    existing_events.append(new_event)
                    existing_links.add(link)
                    new_entries_count += 1
                    print(f"✨ Newly added: {title[:40]}...")

                except Exception:
                    continue
            
            # Short sleep to avoid being rate-limited
            time.sleep(1.2)
            
        except Exception as e:
            print(f"⚠️ Error scanning page {current_page}: {e}")
            continue

    # --- STEP 3: SAVE TO FILE ---
    if new_entries_count > 0:
        with open('events.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(existing_events, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print(f"\n✅ Process complete! {new_entries_count} new events added.")
    else:
        print("\nℹ️ No new events found, existing list is already up to date.")

if __name__ == "__main__":
    scrape_inomics()