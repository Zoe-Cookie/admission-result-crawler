#!/usr/bin/env python3
"""
Admission Result Crawler
Monitors websites for admission list announcements and sends notifications.
"""

import os
import sys
import json
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup


class AdmissionCrawler:
    """Web crawler for monitoring admission result announcements."""
    
    def __init__(self, config_path="config.json"):
        """
        Initialize the crawler with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self.load_config(config_path)
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        
    def load_config(self, config_path):
        """Load configuration from JSON file."""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "urls": [],
            "keywords": ["榜單", "放榜", "admission", "result", "錄取"],
            "check_interval": 1200,  # 20 minutes in seconds
        }
    
    def fetch_page(self, url):
        """
        Fetch webpage content.
        
        Args:
            url: Target URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def check_for_admission_info(self, soup, keywords):
        """
        Check if webpage contains admission-related keywords.
        
        Args:
            soup: BeautifulSoup object
            keywords: List of keywords to search for
            
        Returns:
            Boolean indicating if admission info found
        """
        if not soup:
            return False
            
        text_content = soup.get_text().lower()
        
        for keyword in keywords:
            if keyword.lower() in text_content:
                return True
        return False
    
    def find_admission_links(self, soup, keywords):
        """
        Find links related to admission results.
        
        Args:
            soup: BeautifulSoup object
            keywords: List of keywords to search for
            
        Returns:
            List of relevant links
        """
        if not soup:
            return []
            
        relevant_links = []
        
        for link in soup.find_all('a', href=True):
            link_text = link.get_text().strip()
            link_href = link.get('href', '')
            
            for keyword in keywords:
                if keyword in link_text or keyword in link_href:
                    relevant_links.append({
                        'text': link_text,
                        'url': link_href
                    })
                    break
        
        return relevant_links
    
    def send_telegram_notification(self, message):
        """
        Send notification via Telegram.
        
        Args:
            message: Message to send
        """
        if not self.telegram_token or not self.telegram_chat_id:
            print("Telegram credentials not configured")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            print("Notification sent successfully")
            return True
        except requests.RequestException as e:
            print(f"Error sending notification: {e}")
            return False
    
    def check_url(self, url):
        """
        Check a single URL for admission information.
        
        Args:
            url: URL to check
            
        Returns:
            Dictionary with check results
        """
        print(f"Checking {url}...")
        soup = self.fetch_page(url)
        
        if not soup:
            return {
                'url': url,
                'found': False,
                'error': 'Failed to fetch page'
            }
        
        keywords = self.config.get('keywords', [])
        has_info = self.check_for_admission_info(soup, keywords)
        links = self.find_admission_links(soup, keywords) if has_info else []
        
        return {
            'url': url,
            'found': has_info,
            'links': links,
            'checked_at': datetime.now().isoformat()
        }
    
    def run(self):
        """Run the crawler to check all configured URLs."""
        print(f"Starting crawler at {datetime.now()}")
        print(f"Checking {len(self.config.get('urls', []))} URLs...")
        
        results = []
        found_any = False
        
        for url in self.config.get('urls', []):
            result = self.check_url(url)
            results.append(result)
            
            if result.get('found'):
                found_any = True
                message = f"🎓 <b>Admission Information Found!</b>\n\n"
                message += f"URL: {result['url']}\n"
                message += f"Time: {result['checked_at']}\n"
                
                if result.get('links'):
                    message += f"\n<b>Related Links:</b>\n"
                    for link in result['links'][:5]:  # Limit to 5 links
                        message += f"• {link['text']}: {link['url']}\n"
                
                self.send_telegram_notification(message)
        
        # Print summary
        print("\n" + "="*50)
        print(f"Check completed at {datetime.now()}")
        print(f"URLs checked: {len(results)}")
        print(f"Admission info found: {sum(1 for r in results if r.get('found'))}")
        print("="*50 + "\n")
        
        return results


def main():
    """Main entry point."""
    crawler = AdmissionCrawler()
    
    # Check if URLs are configured
    if not crawler.config.get('urls'):
        print("Warning: No URLs configured in config.json")
        print("Please add URLs to monitor in config.json")
        sys.exit(1)
    
    results = crawler.run()
    
    # Exit with status code based on results
    if any(r.get('found') for r in results):
        print("✓ Admission information detected!")
        sys.exit(0)
    else:
        print("No admission information found yet.")
        sys.exit(0)


if __name__ == "__main__":
    main()
