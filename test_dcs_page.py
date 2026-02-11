#!/usr/bin/env python3
"""
Test script for DCS NTHU page
"""

import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

url = "https://dcs.site.nthu.edu.tw/p/404-1174-162488.php"
keyword = "【115學年度碩士班甄試入學】"

print(f"Fetching {url}...")

# Setup Selenium
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = None
try:
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    
    # Wait a bit for dynamic content
    import time
    time.sleep(3)
    
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Save HTML for inspection
    with open('dcs_page.html', 'w', encoding='utf-8') as f:
        f.write(page_source)
    print("✓ Saved page HTML to dcs_page.html")
    
    # Search for keyword in links
    print(f"\nSearching for '{keyword}' in links...")
    found_links = []
    for link in soup.find_all('a', href=True):
        text = link.get_text(" ", strip=True)
        if keyword in text:
            found_links.append({
                'text': text,
                'href': link.get('href'),
                'title': link.get('title', '')
            })
    
    if found_links:
        print(f"✓ Found {len(found_links)} matching link(s):")
        for link in found_links:
            print(f"  Text: {link['text'][:100]}")
            print(f"  URL: {link['href']}")
            print(f"  Title: {link['title']}")
            print()
    else:
        print("✗ Keyword not found in any link")
        
        # Check if keyword exists anywhere on page
        if keyword in soup.get_text():
            print(f"✓ But keyword exists somewhere in page text")
        else:
            print(f"✗ Keyword not found anywhere on page")
        
        # Show all links with "115" or "碩士"
        print("\nLinks containing '115' or '碩士':")
        for link in soup.find_all('a', href=True)[:20]:
            text = link.get_text(" ", strip=True)
            if '115' in text or '碩士' in text:
                print(f"  - {text[:80]}")
                print(f"    {link.get('href')}")
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
finally:
    if driver:
        driver.quit()
