#!/usr/bin/env python3
"""
Admission Result Crawler
Monitors websites for admission list announcements and sends notifications.
"""

import os
import sys
import json
import time
import re
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
            "keywords": [],
            "check_interval": 1200,  # 20 minutes in seconds
        }
    
    def fetch_page_requests(self, url, verify_ssl=True):
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
            if not verify_ssl:
                try:
                    from urllib3.exceptions import InsecureRequestWarning
                    import urllib3
                    urllib3.disable_warnings(InsecureRequestWarning)
                except Exception:
                    pass

            response = requests.get(
                url,
                headers=headers,
                timeout=30,
                verify=verify_ssl
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def fetch_page_selenium(
        self,
        url,
        wait_selector=None,
        wait_timeout=15,
        click_selector=None,
        click_text=None,
        click_text_contains=None
    ):
        """
        Fetch webpage content using Selenium (for dynamic pages).

        Args:
            url: Target URL to fetch
            wait_selector: Optional CSS selector to wait for
            wait_timeout: Seconds to wait for selector
            click_selector: Optional CSS selector to click before wait
            click_text: Optional exact text to click before wait
            click_text_contains: Optional substring text to click before wait

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
        except Exception as e:
            print(f"Selenium not available: {e}")
            return None

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            
            # Give dynamic content time to load if no wait_selector specified
            if not wait_selector and not click_text and not click_text_contains:
                import time
                time.sleep(3)
            
            if click_text:
                text_xpath = f"//*[normalize-space()='{click_text}']"
                WebDriverWait(driver, wait_timeout).until(
                    EC.element_to_be_clickable((By.XPATH, text_xpath))
                ).click()
            elif click_text_contains:
                text_xpath = (
                    f"//*[contains(normalize-space(), '{click_text_contains}')]"
                )
                WebDriverWait(driver, wait_timeout).until(
                    EC.element_to_be_clickable((By.XPATH, text_xpath))
                ).click()
            elif click_selector:
                WebDriverWait(driver, wait_timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, click_selector))
                ).click()
            if wait_selector:
                WebDriverWait(driver, wait_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                )
            page_source = driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url} with Selenium: {e}")
            return None
        finally:
            if driver:
                driver.quit()

    def text_contains_any(self, text, keywords):
        """Check if any keyword exists in text."""
        if not text:
            return False

        lowered = text.lower()
        for keyword in keywords:
            if keyword.lower() in lowered:
                return True
        return False
    
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
            
        text_content = soup.get_text(" ", strip=True)
        return self.text_contains_any(text_content, keywords)
    
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
            link_text = link.get_text().strip().lower()
            link_href = link.get('href', '').lower()
            
            for keyword in keywords:
                if keyword.lower() in link_text or keyword.lower() in link_href:
                    relevant_links.append({
                        'text': link.get_text().strip(),
                        'url': link.get('href', '')
                    })
                    break
        
        return relevant_links

    def evaluate_rule(self, soup, rule, keywords):
        """
        Evaluate a parser rule for a page.

        Returns:
            Tuple(found: bool, links: list)
        """
        if not soup:
            return False, []

        rule_type = (rule or {}).get('type', 'keyword')
        rule_keywords = (rule or {}).get('keywords', keywords)

        if rule_type == 'keyword':
            has_info = self.check_for_admission_info(soup, rule_keywords)
            links = self.find_admission_links(soup, rule_keywords) if has_info else []
            return has_info, links

        if rule_type == 'css_text_contains':
            selector = (rule or {}).get('selector', '')
            if selector:
                elements = soup.select(selector)
                text_content = " ".join(
                    [el.get_text(" ", strip=True) for el in elements]
                )
            else:
                text_content = soup.get_text(" ", strip=True)
            has_info = self.text_contains_any(text_content, rule_keywords)
            links = self.find_admission_links(soup, rule_keywords) if has_info else []
            return has_info, links

        if rule_type == 'css_exists':
            selector = (rule or {}).get('selector', '')
            return bool(selector and soup.select_one(selector)), []

        if rule_type == 'table_text_contains':
            selector = (rule or {}).get('selector', 'table')
            elements = soup.select(selector)
            text_content = " ".join(
                [el.get_text(" ", strip=True) for el in elements]
            )
            has_info = self.text_contains_any(text_content, rule_keywords)
            return has_info, []

        if rule_type == 'link_text_regex':
            pattern = (rule or {}).get('pattern', '')
            if not pattern:
                return False, []
            try:
                compiled = re.compile(pattern)
            except re.error as e:
                print(f"Invalid regex pattern: {e}")
                return False, []

            matched_links = []
            for link in soup.find_all('a', href=True):
                link_text = link.get_text().strip()
                link_href = link.get('href', '')
                if compiled.search(link_text) or compiled.search(link_href):
                    matched_links.append({
                        'text': link_text,
                        'url': link_href
                    })
            return bool(matched_links), matched_links

        if rule_type == 'link_text_contains':
            matched_links = []
            for link in soup.find_all('a', href=True):
                link_text = link.get_text().strip()
                link_href = link.get('href', '')
                combined = f"{link_text} {link_href}"
                if self.text_contains_any(combined, rule_keywords):
                    matched_links.append({
                        'text': link_text,
                        'url': link_href
                    })
            return bool(matched_links), matched_links

        has_info = self.check_for_admission_info(soup, rule_keywords)
        links = self.find_admission_links(soup, rule_keywords) if has_info else []
        return has_info, links

    def build_targets(self):
        """Build target list with optional per-URL overrides."""
        targets = []
        seen_urls = set()

        for target in self.config.get('targets', []):
            url = target.get('url')
            if not url:
                continue
            targets.append(target)
            seen_urls.add(url)

        for url in self.config.get('urls', []):
            if url in seen_urls:
                continue
            targets.append({
                'url': url,
                'fetcher': 'requests',
                'parser': {
                    'type': 'keyword'
                }
            })

        return targets
    
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
    
    def check_url(self, target):
        """
        Check a single URL for admission information.
        
        Args:
            url: URL to check
            
        Returns:
            Dictionary with check results
        """
        url = target.get('url')
        fetcher = target.get('fetcher', 'requests')
        parser = target.get('parser', {'type': 'keyword'})
        wait_selector = target.get('wait_selector')
        click_selector = target.get('click_selector')
        click_text = target.get('click_text')
        click_text_contains = target.get('click_text_contains')

        print(f"Checking {url}... (fetcher={fetcher})")
        if fetcher == 'selenium':
            soup = self.fetch_page_selenium(
                url,
                wait_selector=wait_selector,
                click_selector=click_selector,
                click_text=click_text,
                click_text_contains=click_text_contains
            )
        else:
            verify_ssl = target.get('verify_ssl', True)
            soup = self.fetch_page_requests(url, verify_ssl=verify_ssl)
        
        if not soup:
            return {
                'url': url,
                'found': False,
                'error': 'Failed to fetch page'
            }
        
        keywords = target.get('keywords', self.config.get('keywords', []))
        has_info, links = self.evaluate_rule(soup, parser, keywords)
        
        return {
            'url': url,
            'found': has_info,
            'links': links,
            'fetcher': fetcher,
            'rule_type': parser.get('type', 'keyword'),
            'checked_at': datetime.now().isoformat()
        }
    
    def run(self):
        """Run the crawler to check all configured URLs."""
        print(f"Starting crawler at {datetime.now()}")
        targets = self.build_targets()
        print(f"Checking {len(targets)} URLs...")
        
        results = []
        found_any = False
        
        for target in targets:
            result = self.check_url(target)
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
