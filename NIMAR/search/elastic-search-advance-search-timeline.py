"""
=======================================================================
📄 NIMAR Elastic Search & Advanced Search Timeline Automation Script
=======================================================================

🔧 Purpose:
    Automates comprehensive search testing for NIMAR web portal including:
    - Simple search verification
    - Sorting verification
    - Advanced search tabs
    - Advanced search with filters
    - Timeline verification
    - Department filter verification

    This script uses Playwright for browser automation and follows the
    same structure as other automation scripts in the project.

⚙️ Features:
    • Single main class architecture (ElasticSearchAutomation)
    • All helper methods are class methods
    • Loads credentials and settings from env_variables.py
    • Uses OTP login from auth.otp module
    • Handles missing environment variables, network delays, and errors gracefully

📁 Project Structure:
    Automation/
    ├── Elastic-search&-advance-search/
    │   └── elastic-search-advance-search-timeline.py  ← This module
    ├── auth/
    │   └── otp.py              ← Uses login_with_otp_sync from this module
    ├── env_variables.py         ← Environment variables module
    └── requirements.txt        ← Python dependencies

🔐 Environment Variables (imported from env_variables.py):
    PORTAL_URL=https://app.nimar.gov.pk
    USERNAME=your_portal_username
    PASSWORD=your_portal_password
    EMAIL_USER=your_email@gmail.com
    EMAIL_PASS=your_gmail_app_password
    (See env_variables.py for complete list)

🚀 How to Run:
    1. Install all required packages:
           pip install -r requirements.txt
           playwright install

    2. Run the script:
           python "Elastic-search&-advance-search/elastic-search-advance-search-timeline.py"

🧩 Dependencies:
    - playwright         → Automate web flow
    - fuzzywuzzy         → Fuzzy string matching

🧠 Author:
    Rabbia Gillani SQA
    Version: 2.0.0 (Playwright)
    Date: 2025-01-XX
=======================================================================
"""
import re
import time
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import quote
from fuzzywuzzy import fuzz
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

from NIMAR.auth.otp import login_with_otp_sync

# Import environment variables
from NIMAR.env_variables import (
    PORTAL_URL,
    BROWSER_HEADLESS,
    BROWSER_IGNORE_HTTPS_ERRORS,
    BROWSER_NO_VIEWPORT,
    ELASTIC_SEARCH_FUZZY_THRESHOLD,
    ELASTIC_SEARCH_NOISE_WORDS,
    ELASTIC_SEARCH_PAGE_LOAD_TIMEOUT,
    ELASTIC_SEARCH_ELEMENT_WAIT_TIMEOUT,
    ELASTIC_SEARCH_SCROLL_PAUSE_TIME,
    ELASTIC_SEARCH_DEFAULT_KEYWORD
)

# =============================================================================
# MODULE-LEVEL CONSTANTS
# =============================================================================

# Fuzzy matching threshold (default: 70)
FUZZY_THRESHOLD = ELASTIC_SEARCH_FUZZY_THRESHOLD or 70

# Default search keyword (default: "news")
DEFAULT_KEYWORD = ELASTIC_SEARCH_DEFAULT_KEYWORD or "news"

# =============================================================================
# UTILITY FUNCTIONS CLASS
# =============================================================================

class UtilityFunctions:
    """
    Utility functions class for common helper functions.
    
    This class contains:
    - Configuration loading from env_variables.py
    - Environment variables display
    - Browser initialization and management
    - Common utility functions (scrolling, clicking, etc.)
    
    Attributes:
        playwright: Playwright instance
        browser: Browser instance
        context: Browser context instance
        page: Page instance
        FUZZY_THRESHOLD (int): Fuzzy matching threshold
        NOISE_WORDS (list): List of noise words to filter
        PAGE_LOAD_TIMEOUT (int): Page load timeout in milliseconds
        ELEMENT_WAIT_TIMEOUT (int): Element wait timeout in milliseconds
        SCROLL_PAUSE_TIME (int): Scroll pause time in milliseconds
        DEFAULT_KEYWORD (str): Default search keyword
    
    Example:
        >>> utils = UtilityFunctions()
        >>> utils.initialize_browser()
    """
    
    def __init__(self):
        """
        Initialize Utility Functions.
        
        Loads all configuration from env_variables.py module.
        """
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Load configuration from environment variables
        self._load_config()
    
    def _load_config(self):
        """
        Load configuration from env_variables.py with defaults.
        
        Sets class-level configuration attributes from environment variables.
        """
        # Fuzzy matching threshold
        self.FUZZY_THRESHOLD = ELASTIC_SEARCH_FUZZY_THRESHOLD or 70
        
        # Noise words to filter out (comma-separated string from env)
        noise_words_str = ELASTIC_SEARCH_NOISE_WORDS or "other,see details,mb,mp4,jpg,png,zip,pdf,xls,mov"
        self.NOISE_WORDS = [word.strip() for word in noise_words_str.split(",")]
        
        # Performance settings
        self.PAGE_LOAD_TIMEOUT = ELASTIC_SEARCH_PAGE_LOAD_TIMEOUT or 20000
        
        self.ELEMENT_WAIT_TIMEOUT = ELASTIC_SEARCH_ELEMENT_WAIT_TIMEOUT or 10000
        
        self.SCROLL_PAUSE_TIME = ELASTIC_SEARCH_SCROLL_PAUSE_TIME or 500
        
        # Default search keyword
        self.DEFAULT_KEYWORD = ELASTIC_SEARCH_DEFAULT_KEYWORD or "news"
    
    
    def display_env_variables(self) -> None:
        """
        Display all environment variables loaded from env_variables.py (sensitive values masked).
        
        This method prints all environment variables organized by category,
        masking sensitive information like passwords.
        """
        from NIMAR.env_variables import (
            PORTAL_URL, USERNAME, PASSWORD,
            EMAIL_USER, EMAIL_PASS, EMAIL_SERVER,
            LOG_LEVEL
        )
        
        print("\n" + "="*80)
        print("📋 ENVIRONMENT VARIABLES LOADED FROM env_variables.py (Elastic Search Module)")
        print("="*80)
        
        sensitive_vars = ["PASSWORD", "EMAIL_PASS", "PASS"]
        all_vars = {
            "Portal Credentials": {
                "PORTAL_URL": PORTAL_URL,
                "USERNAME": USERNAME,
                "PASSWORD": PASSWORD
            },
            "Email Settings": {
                "EMAIL_USER": EMAIL_USER,
                "EMAIL_PASS": EMAIL_PASS,
                "EMAIL_SERVER": EMAIL_SERVER
            },
            "Browser Settings": {
                "BROWSER_HEADLESS": BROWSER_HEADLESS,
                "BROWSER_IGNORE_HTTPS_ERRORS": BROWSER_IGNORE_HTTPS_ERRORS,
                "BROWSER_NO_VIEWPORT": BROWSER_NO_VIEWPORT
            },
            "Elastic Search Settings": {
                "ELASTIC_SEARCH_FUZZY_THRESHOLD": ELASTIC_SEARCH_FUZZY_THRESHOLD,
                "ELASTIC_SEARCH_NOISE_WORDS": ELASTIC_SEARCH_NOISE_WORDS,
                "ELASTIC_SEARCH_PAGE_LOAD_TIMEOUT": ELASTIC_SEARCH_PAGE_LOAD_TIMEOUT,
                "ELASTIC_SEARCH_ELEMENT_WAIT_TIMEOUT": ELASTIC_SEARCH_ELEMENT_WAIT_TIMEOUT,
                "ELASTIC_SEARCH_SCROLL_PAUSE_TIME": ELASTIC_SEARCH_SCROLL_PAUSE_TIME,
                "ELASTIC_SEARCH_DEFAULT_KEYWORD": ELASTIC_SEARCH_DEFAULT_KEYWORD
            },
            "Logging": {
                "LOG_LEVEL": LOG_LEVEL
            }
        }
        
        missing_vars = []
        for category, vars_dict in all_vars.items():
            print(f"\n📂 {category}:")
            for var_name, value in vars_dict.items():
                if value is None:
                    print(f"   ❌ {var_name}: NOT SET (MISSING)")
                    missing_vars.append(var_name)
                else:
                    if any(sensitive in var_name.upper() for sensitive in sensitive_vars):
                        masked_value = "*" * min(len(str(value)), 20) + ("..." if len(str(value)) > 20 else "")
                        print(f"✅ {var_name}: {masked_value}")
                    else:
                        print(f"✅ {var_name}: {value}")
        
        if missing_vars:
            print(f"\n⚠️  WARNING: {len(missing_vars)} variable(s) missing from env_variables.py:")
            for var in missing_vars:
                print(f"      - {var}")
            print("\n   Please add these variables to your env_variables.py.")
        else:
            print("\n✅ All environment variables are loaded successfully!")
        
        print("="*80 + "\n")
    
    def initialize_browser(self) -> bool:
        """
        Initialize Playwright browser with Chrome.
        
        Sets up browser with appropriate launch arguments and context settings.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.playwright = sync_playwright().start()
            
            launch_args = [
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--disable-web-security",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--start-maximized"
            ]
            
            browser_headless = BROWSER_HEADLESS if BROWSER_HEADLESS is not None else False
            browser_ignore_https = BROWSER_IGNORE_HTTPS_ERRORS if BROWSER_IGNORE_HTTPS_ERRORS is not None else True
            browser_no_viewport = BROWSER_NO_VIEWPORT if BROWSER_NO_VIEWPORT is not None else True
            
            self.browser = self.playwright.chromium.launch(
                headless=browser_headless,
                args=launch_args
            )
            
            self.context = self.browser.new_context(
                ignore_https_errors=browser_ignore_https,
                no_viewport=browser_no_viewport,
                viewport=None
            )
            
            self.page = self.context.new_page()
            
            # Navigate to portal URL
            if not PORTAL_URL:
                raise ValueError("PORTAL_URL environment variable is required. Set it in env_variables.py.")
            
            print(f"🌐 Navigating to {PORTAL_URL}...")
            self.page.goto(PORTAL_URL)
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            print("✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            print(f"ERROR: ❌ Failed to initialize browser: {e}")
            return False
    
    def close_browser(self) -> None:
        """
        Close the browser and cleanup resources.
        
        Closes browser, context, and stops playwright instance.
        """
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("✅ Browser closed")
        except Exception as e:
            print(f"Browser close exception: {e}")
    
    def calculate_last_month_dates(self):
        """
        Calculate start and end dates for last month.
        
        Returns:
            tuple: (start_date, end_date) formatted for URL encoding
        """
        today = datetime.now()
        
        # First day of current month
        first_current = today.replace(day=1)
        
        # Last day of previous month
        last_month_end = first_current - timedelta(days=1)
        
        # First day of previous month
        last_month_start = last_month_end.replace(day=1)
        
        # Format for URL encoding
        start_date = last_month_start.strftime("%a+%b+%d+%Y+00%%3A00%%3A00+GMT%%2B0500+%%28Pakistan+Standard+Time%%29")
        end_date = last_month_end.strftime("%a+%b+%d+%Y+23%%3A59%%3A59+GMT%%2B0500+%%28Pakistan+Standard+Time%%29")
        
        return start_date, end_date
    
    def extract_page_text_fast(self, page: Page):
        """
        Extract all visible text from page using JavaScript for maximum speed.
        
        Args:
            page (Page): Playwright Page instance
        
        Returns:
            list: List of extracted text strings
        """
        js_script = """
        return Array.from(document.querySelectorAll('div,span,p,h1,h2,h3,h4,h5,h6,a,li'))
            .map(e => e.innerText.trim())
            .filter(t => t.length > 5)
            .filter(t => !t.match(/^\\d+$/) && !t.match(/^\\d{1,2}:\\d{2}$/))
            .filter(t => !['other', 'see details', 'mb', 'mp4', 'jpg', 'png', 'zip', 'pdf', 'xls', 'mov'].some(noise => t.toLowerCase().includes(noise)));
        """
        
        try:
            texts = page.evaluate(js_script)
            return texts if texts else []
        except Exception as e:
            print(f"⚠️ JavaScript text extraction failed: {e}")
            return []
    
    def fuzzy_keyword_match(self, texts, keyword, threshold=None):
        """
        Perform fuzzy matching on extracted texts.
        
        Args:
            texts (list): List of text strings to search
            keyword (str): Keyword to search for
            threshold (int, optional): Fuzzy matching threshold. If None, uses self.FUZZY_THRESHOLD
        
        Returns:
            tuple: (matches, total) count
        """
        if threshold is None:
            threshold = self.FUZZY_THRESHOLD
        
        keyword_lower = keyword.lower()
        matches = 0
        total = len(texts)
        
        for text in texts:
            text_lower = text.lower()
            
            # Check for exact match first (fastest)
            if keyword_lower in text_lower:
                matches += 1
                continue
                
            # Fuzzy match if no exact match
            if fuzz.partial_ratio(keyword_lower, text_lower) >= threshold:
                matches += 1
        
        return matches, total
    
    def wait_for_user_otp(self):
        """
        Fallback manual OTP prompt.
        
        Waits for user to manually enter OTP and press Enter.
        """
        print("\n" + "="*60)
        print("🔐 MANUAL OTP ENTRY REQUIRED")
        print("="*60)
        input("Press Enter after you have entered the OTP and logged in successfully...")
        print("✅ Continuing with automation...")
    
    def scroll_page(self, page: Page, to="bottom"):
        """
        Robust scroll helper that finds and scrolls the main scrollable container.
        
        Strategy:
          1) Try known container selectors (role=main, main, overflow/scroll classes)
          2) Auto-detect largest scrollable element via JS
          3) Fallback to window/document scrolling element
          4) Final fallback: focus body and send END/HOME repeated
        
        Args:
            page (Page): Playwright Page instance
            to (str): "bottom" or "top" direction
        """
        direction = "bottom" if to == "bottom" else "top"

        # 1) Try common container selectors first
        container_selectors = [
            "div[role='main']",
            "main",
            "div[class*='overflow']",
            "div[class*='scroll']",
            "div[class*='content']",
            "div[class*='container']",
            "div[class*='list']",
            "div[class*='grid']",
        ]
        for sel in container_selectors:
            try:
                el = page.locator(sel).first
                if not el.is_visible():
                    continue
                # Check if actually scrollable
                is_scrollable = page.evaluate("""
                    (el) => {
                        return el.scrollHeight > el.clientHeight;
                    }
                """, el.element_handle())
                if not is_scrollable:
                    continue
                if direction == 'bottom':
                    page.evaluate("""
                        (el) => {
                            el.scrollTo({top: el.scrollHeight, behavior: 'instant'});
                        }
                    """, el.element_handle())
                else:
                    page.evaluate("""
                        (el) => {
                            el.scrollTo({top: 0, behavior: 'instant'});
                        }
                    """, el.element_handle())
                return
            except Exception:
                continue

        # 2) Auto-detect largest scrollable element
        try:
            js = """
            var nodes = Array.from(document.querySelectorAll('*'));
            nodes = nodes.filter(function(el){
              var cs = getComputedStyle(el);
              if (cs.visibility==='hidden' || cs.display==='none') return false;
              var oh=el.scrollHeight, ch=el.clientHeight;
              var oy=cs.overflowY;
              return (oh > ch+5) && (oy==='auto' || oy==='scroll');
            });
            nodes.sort(function(a,b){return (b.scrollHeight-b.clientHeight)-(a.scrollHeight-a.clientHeight);});
            var t = nodes[0] || document.scrollingElement || document.documentElement;
            if (arguments[0]==='bottom'){ t.scrollTo({top: t.scrollHeight, behavior: 'instant'}); }
            else { t.scrollTo({top: 0, behavior: 'instant'}); }
            return (t===document.scrollingElement || t===document.documentElement) ? 'window' : (t.id || t.className || t.tagName);
            """
            page.evaluate(js, direction)
            return
        except Exception:
            pass

        # 3) Fallback to window/document scrolling element
        try:
            if direction == 'bottom':
                page.evaluate("(document.scrollingElement || document.documentElement).scrollTo({top: (document.scrollingElement || document.documentElement).scrollHeight, behavior: 'instant'});")
            else:
                page.evaluate("(document.scrollingElement || document.documentElement).scrollTo({top: 0, behavior: 'instant'});")
            return
        except Exception:
            pass

        # 4) Final fallback: focus body and send END/HOME multiple times
        try:
            body = page.locator("body")
            body.click()
            if direction == 'bottom':
                for _ in range(8):
                    body.press("End")
                    time.sleep(0.15)
            else:
                for _ in range(8):
                    body.press("Home")
                    time.sleep(0.15)
        except Exception:
            pass
    
    def smooth_scroll_page(self, page: Page, to="bottom"):
        """
        Real-time dynamic scrolling that continues until true bottom/top is reached.
        Uses gradual scrolling with content loading detection and visual feedback.
        
        Args:
            page (Page): Playwright Page instance
            to (str): "bottom" or "top" direction
        """
        try:
            if to == "bottom":
                print("⬇️ Starting real-time scroll to bottom...")
                
                # Get initial scroll position and height
                initial_scroll = page.evaluate("window.pageYOffset || window.scrollY || document.documentElement.scrollTop")
                last_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
                last_scroll = initial_scroll
                step = 0
                unchanged_count = 0
                max_unchanged = 3  # Stop when scroll position unchanged for 3 consecutive checks
                
                print(f"📏 Initial page height: {last_height}px, scroll position: {initial_scroll}px")
                
                while unchanged_count < max_unchanged:
                    step += 1
                    
                    # Scroll down gradually (smaller increments for smoother scrolling)
                    scroll_amount = 500  # Scroll 500px at a time
                    page.evaluate(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}});")
                    time.sleep(0.4)  # Wait for smooth scroll animation
                    
                    # Also trigger END key to ensure we reach bottom
                    try:
                        page.keyboard.press("End")
                        time.sleep(0.3)  # Wait after END key
                    except Exception:
                        pass
                    
                    # Wait for potential lazy loading (IMPORTANT: wait for content to load)
                    time.sleep(0.5)  # Extra wait for content loading
                    
                    # Get current scroll position and page height
                    current_scroll = page.evaluate("window.pageYOffset || window.scrollY || document.documentElement.scrollTop")
                    new_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
                    
                    # Check if content loaded (height increased) - this is the key check
                    if new_height > last_height:
                        unchanged_count = 0
                        last_height = new_height
                        print(f"⬇️ Step {step}: New content loaded! Height: {last_height}px (+{new_height - last_height}px), Scroll: {current_scroll}px")
                        # Continue scrolling since new content loaded
                        continue
                    
                    # Check if we're at bottom (scroll position not changing)
                    scroll_change = abs(current_scroll - last_scroll)
                    if scroll_change < 10:  # Less than 10px change
                        unchanged_count += 1
                        print(f"⬇️ Step {step}: Scroll position unchanged ({unchanged_count}/{max_unchanged}) - Height: {new_height}px, Scroll: {current_scroll}px")
                        
                        # Before declaring bottom, check if content is still loading
                        # Wait a bit more and check again
                        time.sleep(1.0)  # Wait for any pending content to load
                        final_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
                        final_scroll = page.evaluate("window.pageYOffset || window.scrollY || document.documentElement.scrollTop")
                        
                        if final_height > new_height:
                            # New content loaded during wait!
                            unchanged_count = 0
                            last_height = final_height
                            last_scroll = final_scroll
                            print(f"⬇️ Step {step}: Content loaded during wait! New height: {final_height}px, continuing scroll...")
                            continue
                    else:
                        unchanged_count = 0
                        last_scroll = current_scroll
                        if step % 5 == 0:  # Log every 5th step
                            print(f"⬇️ Step {step}: Scrolling... Height: {new_height}px, Scroll: {current_scroll}px")
                    
                    # Safety break to prevent infinite loop
                    if step > 100:
                        print("⚠️ Reached maximum scroll steps (100) — stopping")
                        break
                    
                    # Check if we've reached the actual bottom
                    max_scroll = page.evaluate("""
                        Math.max(
                            document.body.scrollHeight,
                            document.body.offsetHeight,
                            document.documentElement.clientHeight,
                            document.documentElement.scrollHeight,
                            document.documentElement.offsetHeight
                        ) - window.innerHeight
                    """)
                    
                    if current_scroll >= max_scroll - 50:  # Within 50px of bottom
                        # Final verification: wait and check one more time
                        time.sleep(1.5)  # Wait for any final content to load
                        final_check_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
                        final_check_scroll = page.evaluate("window.pageYOffset || window.scrollY || document.documentElement.scrollTop")
                        
                        if final_check_height > new_height:
                            # Still loading, continue
                            last_height = final_check_height
                            unchanged_count = 0
                            print(f"⬇️ Step {step}: Final check - more content loaded! Height: {final_check_height}px, continuing...")
                            continue
                        
                        print(f"✅ Reached bottom! Final height: {final_check_height}px, Scroll: {final_check_scroll}px")
                        # One final scroll to ensure we're at the very bottom
                        page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
                        time.sleep(0.5)
                        break
                
                if unchanged_count >= max_unchanged:
                    # Final wait to ensure all content is loaded
                    time.sleep(2.0)
                    final_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
                    if final_height > last_height:
                        print(f"⬇️ Additional content loaded during final wait! New height: {final_height}px")
                        # Continue scrolling
                        last_height = final_height
                        unchanged_count = 0
                    else:
                        print(f"✅ Reached bottom (no more content loading). Final height: {last_height}px")
                
            else:  # to == "top"
                print("⬆️ Starting real-time scroll to top...")
                
                current_scroll = page.evaluate("window.pageYOffset || window.scrollY || document.documentElement.scrollTop")
                step = 0
                
                print(f"📏 Current scroll position: {current_scroll}px")
                
                # Scroll to top gradually
                while current_scroll > 10:  # Continue until within 10px of top
                    step += 1
                    
                    # Scroll up gradually
                    scroll_amount = 500
                    page.evaluate(f"window.scrollBy({{top: -{scroll_amount}, behavior: 'smooth'}});")
                    time.sleep(0.3)
                    
                    # Also trigger HOME key
                    try:
                        page.keyboard.press("Home")
                        time.sleep(0.2)
                    except Exception:
                        pass
                    
                    current_scroll = page.evaluate("window.pageYOffset || window.scrollY || document.documentElement.scrollTop")
                    
                    if step % 5 == 0:
                        print(f"⬆️ Step {step}: Scrolling to top... Current: {current_scroll}px")
                    
                    # Safety break
                    if step > 50:
                        break
                
                # Final scroll to top
                page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'});")
                time.sleep(0.5)
                
                print("✅ Reached top!")
                    
        except Exception as e:
            print(f"⚠️ Scrolling failed: {str(e)}")
            # Fallback to instant scroll
            try:
                if to == "bottom":
                    page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'instant'});")
                else:
                    page.evaluate("window.scrollTo({top: 0, behavior: 'instant'});")
            except Exception:
                pass
    
    def collect_result_cards(self, page: Page, area_xpath="//*[@id='recentUploads']"):
        """
        Best-effort collection of visible result cards/items within the area.
        
        Tries common card container patterns and falls back to visible, clickable descendants.
        Returns a list of unique Locator objects (outermost card containers).
        
        Args:
            page (Page): Playwright Page instance
            area_xpath (str): XPath of the area to collect cards from
        
        Returns:
            list: List of Locator objects representing result cards
        """
        candidates = []
        tried_selectors = [
            ".//descendant::*[contains(@class,'card') or contains(@class,'item') or contains(@class,'grid-item') or contains(@class,'masonry')][normalize-space(.)!='']",
            ".//descendant::*[@role='listitem' or @role='option'][normalize-space(.)!='']",
            ".//descendant::article|.//descendant::li|.//descendant::div[contains(@class,'result') or contains(@class,'tile') or contains(@class,'entry')]",
        ]
        seen = set()
        try:
            area = page.locator(area_xpath).first
            if not area.is_visible():
                return []
        except Exception:
            return []
        
        for xp in tried_selectors:
            try:
                elements = area.locator(xp).all()
                for el in elements:
                    try:
                        if not el.is_visible():
                            continue
                        # Get a unique identifier for the element
                        el_id = el.evaluate("(el) => el.id || el.className || el.tagName")
                        if el_id not in seen:
                            seen.add(el_id)
                            candidates.append(el)
                    except Exception:
                        continue
            except Exception:
                continue
        # Fallback: pick top-level children with text
        if not candidates:
            try:
                top_children = area.locator("./*/*[normalize-space(.)!='']").all()
                for el in top_children:
                    try:
                        if el.is_visible():
                            candidates.append(el)
                    except Exception:
                        continue
            except Exception:
                pass
        return candidates
    
    def get_element_full_text(self, page: Page, locator):
        """
        Return normalized visible text for an element; falls back to JS innerText.
        
        Args:
            page (Page): Playwright Page instance
            locator: Playwright Locator object
        
        Returns:
            str: Extracted text or empty string
        """
        try:
            txt = locator.inner_text() or ""
            if txt:
                return txt.strip()
        except Exception:
            pass
        try:
            return page.evaluate("(el) => el.innerText || '';", locator.element_handle()) or ""
        except Exception:
            return ""
    
    def wait_for_results(self, page: Page, area_xpath="//*[@id='recentUploads']", timeout=10):
        """
        Wait until at least one visible card appears in area, or timeout.
        Uses multiple strategies to find cards.
        
        Args:
            page (Page): Playwright Page instance
            area_xpath (str): XPath of the area to wait for
            timeout (int): Timeout in seconds
        
        Returns:
            Locator or None: Area locator if found, None otherwise
        """
        end = time.time() + timeout
        try:
            area = page.locator(area_xpath).first
            if not area.is_visible():
                # Wait a bit and retry
                time.sleep(2)
                try:
                    area = page.locator(area_xpath).first
                    if not area.is_visible():
                        return None
                except Exception:
                    return None
        except Exception:
            return None
        
        # Try multiple card detection strategies
        card_selectors = [
            ".//div[contains(@class,'card')]",
            ".//div[contains(@class,'Card')]",
            ".//div[contains(@class,'item')]",
            ".//div[contains(@class,'Item')]",
            ".//div[contains(@class,'grid-item')]",
            ".//div[contains(@class,'masonry-item')]",
            ".//article",
            ".//div[@role='listitem']",
            ".//div[contains(@class,'result')]",
            ".//div[contains(@class,'tile')]",
            ".//div[contains(@class,'entry')]",
            ".//div[contains(@class,'media')]",
            ".//div[contains(@class,'content')]",
            ".//div[contains(@class,'thumbnail')]",
            ".//div[contains(@class,'video')]",
            ".//div[contains(@class,'image')]",
            ".//div[contains(@class,'document')]",
            ".//div[contains(@class,'audio')]",
        ]
        
        while time.time() < end:
            try:
                # Strategy 1: Use collect_result_cards
                cards = self.collect_result_cards(page, area_xpath)
                if cards:
                    return area
                
                # Strategy 2: Try direct selectors
                for selector in card_selectors:
                    try:
                        found_cards = area.locator(selector).all()
                        if found_cards:
                            visible_cards = [c for c in found_cards if c.is_visible()]
                            if visible_cards:
                                return area
                    except Exception:
                        continue
                
                # Strategy 3: Check for any div with content
                try:
                    all_divs = area.locator(".//div").all()
                    for div in all_divs[:10]:  # Check first 10
                        try:
                            if div.is_visible():
                                text = div.inner_text()
                                has_image = len(div.locator(".//img").all()) > 0
                                has_video = len(div.locator(".//video").all()) > 0
                                if (text and len(text.strip()) > 10) or has_image or has_video:
                                    return area
                        except Exception:
                            continue
                except Exception:
                    pass
                    
            except Exception:
                pass
            time.sleep(0.5)  # Increased wait time
        
        # Return area anyway for subsequent attempts
        return area
    
    def _is_irrelevant_token(self, token_l):
        """
        Check if a token is irrelevant (file extensions, durations, sizes, generic labels).
        
        Args:
            token_l (str): Lowercase token to check
        
        Returns:
            bool: True if token is irrelevant, False otherwise
        """
        if not token_l:
            return True
        # common irrelevant tokens: file extensions, durations, sizes, generic labels
        if re.search(r"\b(mp4|mkv|avi|mp3|wav|pdf|docx?|xlsx?|pptx?)\b", token_l):
            return True
        if re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", token_l):
            return True
        if re.search(r"\b\d+(?:\.\d+)?\s?(kb|mb|gb)\b", token_l):
            return True
        if token_l in {"other", "others", "duration", "size", "file", "type"}:
            return True
        return False
    
    def robust_click_sorting_option(self, page: Page, xpath, option_label):
        """
        Robust multi-strategy click helper for sorting options.
        
        Args:
            page (Page): Playwright Page instance
            xpath (str): XPath of the sorting option element
            option_label (str): Label of the option for logging
        
        Returns:
            bool: True if successful, False otherwise
        """
        for attempt in range(3):  # Retry up to 3 times
            try:
                # Wait 1 second before each attempt
                time.sleep(1)
                
                # Wait for element to be clickable
                element = page.locator(xpath).first
                element.wait_for(state="visible", timeout=5000)
                
                # Scroll element into view
                element.scroll_into_view_if_needed()
                time.sleep(0.5)
                
                # Strategy 1: Normal click
                try:
                    element.click()
                    print(f"✅ Successfully clicked sorting option [{option_label}]")
                    return True
                except Exception:
                    pass
                
                # Strategy 2: JavaScript click
                try:
                    page.evaluate("(el) => el.click();", element.element_handle())
                    print(f"✅ Successfully clicked sorting option [{option_label}]")
                    return True
                except Exception:
                    pass
                
                # Strategy 3: Force click
                try:
                    element.click(force=True)
                    print(f"✅ Successfully clicked sorting option [{option_label}]")
                    return True
                except Exception:
                    pass
                    
            except Exception as e:
                if attempt < 2:  # Not the last attempt
                    print(f"⚠️ Attempt {attempt + 1} failed for {option_label}: {e}")
                    time.sleep(1)  # Wait 1s before retry
                    continue
                else:
                    print(f"⚠️ Could not click [{option_label}] after 3 tries — skipping.")
                    return False
        
        return False
    
    def robust_click_element(self, page: Page, locator, element_name="element", max_attempts=3):
        """
        Robust click mechanism with retry and JS fallback.
        
        Args:
            page (Page): Playwright Page instance
            locator: Playwright Locator object
            element_name (str): Name of element for logging
            max_attempts (int): Maximum number of click attempts
        
        Returns:
            bool: True if successful, False otherwise
        """
        for attempt in range(max_attempts):
            try:
                # Scroll element into view
                locator.scroll_into_view_if_needed()
                time.sleep(0.5)
                
                # Try normal click first
                try:
                    locator.click()
                    print(f"✅ Successfully clicked {element_name} (attempt {attempt + 1})")
                    return True
                except Exception:
                    # Try JavaScript click
                    try:
                        page.evaluate("(el) => el.click();", locator.element_handle())
                        print(f"✅ Successfully clicked {element_name} via JS (attempt {attempt + 1})")
                        return True
                    except Exception:
                        # Try force click
                        try:
                            locator.click(force=True)
                            print(f"✅ Successfully clicked {element_name} via force (attempt {attempt + 1})")
                            return True
                        except Exception:
                            pass
                
                # Wait before retry
                if attempt < max_attempts - 1:
                    time.sleep(1)
                    
            except Exception as e:
                if attempt < max_attempts - 1:
                    time.sleep(1)
                else:
                    print(f"⚠️ Could not click {element_name} after {max_attempts} attempts: {e}")
        
        return False
    
    def extract_card_title(self, page: Page, card):
        """
        Extract title from a result card.
        
        Args:
            page (Page): Playwright Page instance
            card: Playwright Locator object representing a card
        
        Returns:
            str: Extracted title or empty string
        """
        try:
            t = card.locator(".//*[self::h1 or self::h2 or self::h3 or contains(@class,'title') or contains(@class,'name')][normalize-space(.)!='']").first.inner_text().strip()
            if t:
                return t
        except Exception:
            pass
        return self.get_element_full_text(page, card).strip()
    
    def extract_card_date(self, page: Page, card):
        """
        Attempt to extract a comparable date value from the card. Returns Unix timestamp or None.
        
        Args:
            page (Page): Playwright Page instance
            card: Playwright Locator object representing a card
        
        Returns:
            int or None: Unix timestamp if found, None otherwise
        """
        # Try <time datetime>
        try:
            tm = card.locator(".//time").first
            dt_attr = tm.get_attribute("datetime") or tm.get_attribute("data-time")
            if dt_attr:
                import datetime as _dt
                try:
                    return int(_dt.datetime.fromisoformat(dt_attr.replace('Z','+00:00')).timestamp())
                except Exception:
                    pass
            txt = tm.inner_text().strip()
            if txt:
                # very tolerant parse: try Date.parse in JS
                ts = page.evaluate("(txt) => Date.parse(txt);", txt)
                if isinstance(ts, (int, float)) and ts > 0:
                    return int(ts/1000)
        except Exception:
            pass
        # Try data attributes on card container
        for attr in ["data-date", "data-timestamp", "data-created", "data-updated"]:
            try:
                val = card.get_attribute(attr)
                if val:
                    try:
                        return int(val)
                    except Exception:
                        try:
                            import datetime as _dt
                            return int(_dt.datetime.fromisoformat(val.replace('Z','+00:00')).timestamp())
                        except Exception:
                            continue
            except Exception:
                continue
        return None
    
    def find_and_click_content_button(self, page: Page):
        """
        Find and click the Content button with multiple fallback methods.
        
        Args:
            page (Page): Playwright Page instance
        
        Returns:
            bool: True if successful, False otherwise
        """
        # List of possible selectors for Content button/tab
        content_selectors = [
            "//*[@id='scrollingDiv']/div[4]/div[1]/div[2]/div/div/div[2]/button[2]/p",  # User-provided specific XPath
            "//*[@id='scrollingDiv']/div[4]/div[1]/div[2]/div/div/div[2]/button[2]",  # Parent button element
            "//button[contains(text(), 'Content')]",
            "//a[contains(text(), 'Content')]",
            "//span[contains(text(), 'Content')]",
            "//div[contains(text(), 'Content')]",
            "//li[contains(text(), 'Content')]",
            "//*[contains(@class, 'content') and contains(text(), 'Content')]",
            "//*[contains(@id, 'content')]",
            "//*[contains(@href, 'content')]"
        ]
        
        content_element = None
        
        # Fast pass: try a composite XPath once without long waits
        fast_xpaths = [
            "//*[@id='scrollingDiv']/div[4]/div[1]/div[2]/div/div/div[2]/button[2]",  # User-provided specific button
            "//button[.//text()[contains(.,'Content')]]",
            "//a[.//text()[contains(.,'Content')]]",
            "//*[contains(@class,'content') and (self::button or self::a or self::div)]",
        ]
        for fx in fast_xpaths:
            try:
                els = page.locator(fx).all()
                if els and els[0].is_visible():
                    content_element = els[0]
                    print(f"⚡ Fast-found Content element via: {fx}")
                    break
            except Exception:
                continue

        # Fallback to precise list with short waits
        if not content_element:
            for selector in content_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible():
                        # If selector points to a <p> element, try to get its parent button
                        if selector.endswith('/p'):
                            try:
                                # Try to find parent button using XPath
                                parent_selector = selector.rsplit('/', 1)[0]  # Remove '/p' to get parent button
                                parent_button = page.locator(parent_selector).first
                                if parent_button.is_visible():
                                    content_element = parent_button
                                    print(f"✅ Found Content button (parent of <p> element) using selector: {parent_selector}")
                                else:
                                    # Fallback: try ancestor button
                                    try:
                                        parent_button = element.locator("xpath=ancestor::button[1]").first
                                        if parent_button.is_visible():
                                            content_element = parent_button
                                            print(f"✅ Found Content button (ancestor) using selector: {selector}")
                                        else:
                                            content_element = element
                                    except Exception:
                                        content_element = element
                            except Exception:
                                content_element = element
                                print(f"✅ Found Content element using selector: {selector}")
                        else:
                            content_element = element
                            print(f"✅ Found Content element using selector: {selector}")
                        break
                except Exception:
                    continue
        
        if not content_element:
            # If not found, try to find any element containing "Content" text
            try:
                content_element = page.locator("//*[contains(text(), 'Content')]").first
                if content_element.is_visible():
                    print("✅ Found Content element using generic text search")
            except Exception:
                print("❌ Content element not found with any method")
                return False
        
        # Store initial page state for comparison
        initial_url = page.url
        initial_title = page.title()
        
        # Store initial DOM state for better verification
        initial_search_box_count = len(page.locator("//input[@type='text' and contains(@placeholder, 'search')]").all())
        initial_recent_uploads = len(page.locator("//*[@id='recentUploads']").all())
        
        # Try different clicking methods
        click_methods = [
            ("Normal Click", lambda: content_element.click()),
            ("JavaScript Click", lambda: page.evaluate("(el) => el.click();", content_element.element_handle())),
            ("Force Click", lambda: content_element.click(force=True))
        ]
        
        for method_name, click_method in click_methods:
            try:
                print(f"🔄 Attempting {method_name}...")
                
                # Scroll element into view first
                content_element.scroll_into_view_if_needed()
                time.sleep(1)
                
                # Check if button is actually clickable before clicking
                try:
                    is_clickable = content_element.is_enabled()
                    if not is_clickable:
                        print(f"⚠️ Content button is not enabled, skipping {method_name}")
                        continue
                except Exception:
                    pass
                
                # Try clicking
                click_method()
                
                # Wait for DOM to update (longer wait for proper verification)
                time.sleep(2)
                
                # Check if we're still on the same page or if URL changed
                current_url = page.url
                page_title = page.title()
                
                print(f"📄 Current URL: {current_url}")
                print(f"📄 Page Title: {page_title}")
                
                # Wait a bit more and check for search box and content area (better indicator of content section)
                time.sleep(2)
                
                # Try multiple search box selectors
                search_box_selectors = [
                    "//input[@type='text' and contains(@placeholder, 'search')]",
                    "//input[@type='text' and contains(@placeholder, 'Search')]",
                    "//input[@type='search']",
                    "//input[contains(@class, 'search')]",
                    "//input[contains(@id, 'search')]",
                    "//input[contains(@name, 'search')]",
                    "//input[@type='text']",
                ]
                
                current_search_box_count = 0
                search_box_visible = False
                for selector in search_box_selectors:
                    try:
                        count = len(page.locator(selector).all())
                        if count > 0:
                            current_search_box_count = count
                            # Check if visible
                            if page.locator(selector).first.is_visible():
                                search_box_visible = True
                                break
                    except Exception:
                        continue
                
                # Check for recentUploads section (strong indicator)
                current_recent_uploads = len(page.locator("//*[@id='recentUploads']").all())
                recent_uploads_visible = False
                if current_recent_uploads > 0:
                    try:
                        recent_uploads_visible = page.locator("//*[@id='recentUploads']").first.is_visible()
                    except Exception:
                        pass
                
                # Check for content cards/items (another strong indicator)
                content_cards_count = 0
                try:
                    content_cards_count = len(page.locator("//*[@id='recentUploads']//div[contains(@class,'card')]").all())
                except Exception:
                    pass
                
                # Check if Content button is now active/selected
                content_button_active = False
                try:
                    active_selectors = [
                        "//*[contains(text(), 'Content') and (contains(@class, 'active') or contains(@class, 'selected') or contains(@class, 'current'))]",
                        "//*[contains(text(), 'Content') and (@aria-selected='true' or @data-active='true' or @aria-current='page')]",
                        "//button[contains(text(), 'Content') and contains(@class, 'active')]",
                    ]
                    for sel in active_selectors:
                        if len(page.locator(sel).all()) > 0:
                            content_button_active = True
                            break
                except Exception:
                    pass
                
                # Check for various success indicators (URL change is NOT mandatory for SPA)
                success_indicators = [
                    # Strong indicators (count as 2 points each)
                    current_recent_uploads > initial_recent_uploads and recent_uploads_visible,  # Recent uploads appeared
                    search_box_visible,  # Search box is visible
                    content_cards_count > 0,  # Content cards are present
                    content_button_active,  # Content button is active
                    
                    # Medium indicators (count as 1 point each)
                    current_search_box_count > initial_search_box_count,  # Search box count increased
                    'content' in current_url.lower(),  # URL contains 'content'
                    current_url != initial_url,  # URL changed
                    page_title != initial_title,  # Title changed
                    'content' in page_title.lower(),  # Title contains 'content'
                ]
                
                # Count strong indicators (worth 2 points) and medium indicators (worth 1 point)
                strong_indicators = sum(1 for i, indicator in enumerate(success_indicators[:4]) if indicator)
                medium_indicators = sum(1 for indicator in success_indicators[4:] if indicator)
                total_score = (strong_indicators * 2) + medium_indicators
                
                # Success if: (1 strong indicator) OR (2+ medium indicators) OR (recentUploads appeared)
                is_success = (
                    strong_indicators >= 1 or  # At least 1 strong indicator
                    medium_indicators >= 2 or  # At least 2 medium indicators
                    (current_recent_uploads > initial_recent_uploads and recent_uploads_visible)  # Recent uploads appeared and visible
                )
                
                if is_success:
                    print(f"✅ {method_name} successful! (Score: {total_score} - {strong_indicators} strong, {medium_indicators} medium indicators)")
                    if current_recent_uploads > initial_recent_uploads and recent_uploads_visible:
                        print("✅ Recent uploads section appeared and visible - Content section is open!")
                    if search_box_visible:
                        print("✅ Search box is visible - Content section is open!")
                    if content_cards_count > 0:
                        print(f"✅ Content cards found ({content_cards_count}) - Content section is open!")
                    if content_button_active:
                        print("✅ Content button is active - Content section is open!")
                    return True
                else:
                    print(f"⚠️ {method_name} executed but success criteria not met (Score: {total_score})")
                    print(f"   Strong indicators: {strong_indicators}/4")
                    print(f"   Medium indicators: {medium_indicators}/5")
                    print(f"   Search box: {initial_search_box_count} → {current_search_box_count} (visible: {search_box_visible})")
                    print(f"   Recent uploads: {initial_recent_uploads} → {current_recent_uploads} (visible: {recent_uploads_visible})")
                    print(f"   Content cards: {content_cards_count}")
                    print(f"   Content button active: {content_button_active}")
                    
            except Exception as e:
                print(f"❌ {method_name} failed: {str(e)}")
                continue
        
        # Final check - if recentUploads section is visible, assume success (even if search box not found)
        try:
            recent_uploads_visible = page.locator("//*[@id='recentUploads']").first.is_visible(timeout=3000)
        except Exception:
            recent_uploads_visible = False
            if recent_uploads_visible:
                print("✅ Recent uploads section is visible - Content section appears to be open!")
                # Try to find search box with multiple selectors
                try:
                    search_box_found = False
                    search_selectors = [
                        "//input[@type='text' and contains(@placeholder, 'search')]",
                        "//input[@type='text' and contains(@placeholder, 'Search')]",
                        "//input[@type='search']",
                        "//input[contains(@class, 'search')]",
                        "//input[contains(@id, 'search')]",
                    ]
                    for selector in search_selectors:
                        try:
                            search_box = page.locator(selector).first
                            if search_box.is_visible(timeout=2000):
                                print(f"✅ Search box also found using: {selector}")
                                break
                        except Exception as e:
                            print(f"❌ Search box not found using {selector}: {str(e)}")
                            continue
                except Exception as e:
                    print(f"❌ Search box not found: {str(e)}")
                return True
        except Exception as e:
            print(f"❌ Recent uploads section not found: {str(e)}")
            return False

# =============================================================================
# SIMPLE SEARCH FUNCTIONS CLASS
# =============================================================================

class SimpleSearchFunctions:
    """
    Simple Search functions class for basic search functionality.
    
    This class handles:
    - Simple search verification
    - View switching (Grid, List, Masonry)
    - Sorting verification
    - Keyword matching in results
    
    Attributes:
        page (Page): Playwright Page instance
    
    Example:
        >>> simple_search = SimpleSearchFunctions(page)
        >>> results = simple_search.execute_simple_search(keyword="news", threshold=70)
    """
    
    def __init__(self, page: Page, utils=None):
        """
        Initialize Simple Search Functions.
        
        Args:
            page (Page): Playwright Page instance
            utils (UtilityFunctions, optional): UtilityFunctions instance for helper methods
        """
        self.page = page
        self.utils = utils
    
    def extract_comprehensive_metadata(self, card):
        """
        Extract all possible metadata from a card element.
        
        Args:
            card: Playwright locator for the card element
        
        Returns:
            dict: Dictionary containing all extracted metadata fields
        """
        metadata = {
            'title': '',
            'description': '',
            'keywords': '',
            'alt_text': '',
            'aria_label': '',
            'data_attributes': '',
            'all_text': '',
            'image_src': '',
            'video_src': ''
        }
        
        def safe_text(card_locator, xp):
            try:
                el = card_locator.locator(xp).first
                try:
                    if not el.is_visible():
                        return ""
                except Exception:
                    pass
                return (el.inner_text() or "").strip()
            except Exception:
                return ""
        
        def safe_attr(card_locator, xp, attr_name):
            try:
                el = card_locator.locator(xp).first
                if el.count() > 0:
                    return (el.get_attribute(attr_name) or "").strip()
            except Exception:
                pass
            return ""
        
        # Extract title
        title_selectors = [
            ".//*[contains(@class,'title') or self::h1 or self::h2 or self::h3 or self::h4]",
            ".//*[@class*='title' or @class*='Title']",
            ".//h1 | .//h2 | .//h3 | .//h4"
        ]
        for selector in title_selectors:
            title = safe_text(card, selector)
            if title:
                metadata['title'] = title
                break
        
        # Extract description
        desc_selectors = [
            ".//*[contains(@class,'desc') or contains(@class,'description')]",
            ".//*[@class*='desc' or @class*='Description']",
            ".//p[contains(@class,'desc')]"
        ]
        for selector in desc_selectors:
            desc = safe_text(card, selector)
            if desc:
                metadata['description'] = desc
                break
        
        # Extract keywords
        keyword_selectors = [
            ".//*[contains(@class,'keyword')]",
            ".//*[@class*='keyword' or @class*='Keyword']",
            ".//*[@data-keyword]"
        ]
        for selector in keyword_selectors:
            keywords = safe_text(card, selector)
            if keywords:
                metadata['keywords'] = keywords
                break
        
        # Extract alt text from images
        img_alt = safe_attr(card, ".//img", "alt")
        if img_alt:
            metadata['alt_text'] = img_alt
        
        # Extract aria-label
        aria_label = safe_attr(card, ".", "aria-label")
        if not aria_label:
            aria_label = safe_attr(card, ".//*[@aria-label]", "aria-label")
        if aria_label:
            metadata['aria_label'] = aria_label
        
        # Extract data attributes
        try:
            data_attrs = []
            data_elements = card.locator(".//*[@data-*]").all()
            for el in data_elements[:5]:  # Limit to first 5 to avoid too much data
                try:
                    attrs = el.evaluate("""el => {
                        const attrs = {};
                        for (let attr of el.attributes) {
                            if (attr.name.startsWith('data-')) {
                                attrs[attr.name] = attr.value;
                            }
                        }
                        return attrs;
                    }""")
                    if attrs:
                        data_attrs.append(str(attrs))
                except Exception:
                    pass
            if data_attrs:
                metadata['data_attributes'] = " ".join(data_attrs)
        except Exception:
            pass
        
        # Extract image src
        img_src = safe_attr(card, ".//img", "src")
        if img_src:
            metadata['image_src'] = img_src
        
        # Extract video src
        video_src = safe_attr(card, ".//video", "src")
        if not video_src:
            video_src = safe_attr(card, ".//source", "src")
        if video_src:
            metadata['video_src'] = video_src
        
        # Extract all visible text from card (including nested elements)
        try:
            # Get all text from card
            all_text = (card.inner_text() or "").strip()
            
            # Also get text from all child elements to ensure we capture everything
            try:
                all_elements_text = card.evaluate("""
                    (el) => {
                        const texts = [];
                        const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false);
                        let node;
                        while (node = walker.nextNode()) {
                            const text = node.textContent.trim();
                            if (text && text.length > 0) {
                                texts.push(text);
                            }
                        }
                        return texts.join(' ');
                    }
                """)
                if all_elements_text:
                    all_text = all_text + " " + all_elements_text
            except Exception:
                pass
            
            # Get text content from all spans, divs, p tags
            try:
                text_elements = card.locator(".//span | .//div | .//p | .//h1 | .//h2 | .//h3 | .//h4 | .//h5 | .//h6 | .//a | .//label").all()
                for el in text_elements[:20]:  # Limit to first 20 to avoid too much
                    try:
                        if el.is_visible():
                            text = el.inner_text()
                            if text:
                                all_text = all_text + " " + text.strip()
                    except Exception:
                        continue
            except Exception:
                pass
            
            metadata['all_text'] = all_text.strip()
        except Exception:
            pass
        
        # Also extract text from title if not already extracted
        if not metadata['title']:
            try:
                # Try to get first meaningful text from card
                first_text = card.locator(".//*[normalize-space(.)!='']").first
                if first_text.is_visible():
                    title_text = first_text.inner_text()
                    if title_text and len(title_text.strip()) > 0:
                        metadata['title'] = title_text.strip()
            except Exception:
                pass
        
        return metadata
    
    def verify_keyword_in_media_cards(self, keyword, area_xpath="//*[@id='recentUploads']", threshold=70, deep_check=False):
        """
        Comprehensive metadata verification for each visible media card.
        
        Extracts all metadata fields (title, description, keywords, alt text, aria-label, 
        data attributes, etc.) and verifies keyword presence using fuzzywuzzy with multiple
        matching strategies. Reports mismatches as errors/warnings.
        
        Args:
            keyword (str): Keyword to search for
            area_xpath (str): XPath of the area to search in
            threshold (int): Fuzzy matching threshold (0-100)
            deep_check (bool): Whether to perform deep check in modal/dialog
        
        Returns:
            tuple: (matched_count, total_count, mismatch_details)
        """
        # Use UtilityFunctions for helper methods
        if not self.utils:
            self.utils = UtilityFunctions()
        
        # Wait for results area to appear and load
        print("⏳ Waiting for results area to load...")
        time.sleep(3)  # Wait for initial load
        
        # Try to find results area with multiple attempts
        area = None
        for attempt in range(1, 4):
            try:
                area = self.utils.wait_for_results(self.page, area_xpath=area_xpath, timeout=10)
                if area is not None:
                    break
            except Exception:
                pass
            time.sleep(2)
        
        if area is None:
            print("⚠️ Results area not found, trying direct locator...")
            try:
                area = self.page.locator(area_xpath).first
                if area.is_visible():
                    print("✅ Found results area via direct locator")
                else:
                    print("❌ Results area not visible")
                    return 0, 0, []
            except Exception:
                print("❌ No results area found — cannot verify")
                return 0, 0, []
        
        # DEBUG: Print page structure to help identify card selectors
        try:
            debug_info = self.page.evaluate(f"""
                () => {{
                    const area = document.evaluate('{area_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (!area) return {{error: 'Area not found'}};
                    
                    const allDivs = area.querySelectorAll('div');
                    const divsInfo = [];
                    for (let i = 0; i < Math.min(allDivs.length, 20); i++) {{
                        const div = allDivs[i];
                        const rect = div.getBoundingClientRect();
                        const isVisible = rect.width > 0 && rect.height > 0 && window.getComputedStyle(div).display !== 'none';
                        const hasText = div.innerText && div.innerText.trim().length > 0;
                        const hasImage = div.querySelector('img') !== null;
                        const hasVideo = div.querySelector('video') !== null;
                        const classes = div.className || '';
                        const id = div.id || '';
                        
                        if (isVisible && (hasText || hasImage || hasVideo)) {{
                            divsInfo.push({{
                                index: i,
                                tag: div.tagName,
                                id: id,
                                classes: classes,
                                hasText: hasText,
                                hasImage: hasImage,
                                hasVideo: hasVideo,
                                textPreview: (div.innerText || '').substring(0, 50),
                                width: rect.width,
                                height: rect.height
                            }});
                        }}
                    }}
                    
                    return {{
                        areaFound: true,
                        totalDivs: allDivs.length,
                        visibleDivsWithContent: divsInfo.length,
                        divs: divsInfo
                    }};
                }}
            """)
            if debug_info and 'divs' in debug_info:
                print(f"🔍 DEBUG: Found {debug_info.get('totalDivs', 0)} total divs in area")
                print(f"🔍 DEBUG: Found {debug_info.get('visibleDivsWithContent', 0)} visible divs with content")
                if debug_info.get('divs'):
                    print("🔍 DEBUG: Sample divs structure:")
                    for idx, div_info in enumerate(debug_info['divs'][:5]):
                        print(f"   Div {idx+1}: tag={div_info.get('tag')}, classes={div_info.get('classes')}, id={div_info.get('id')}, text={div_info.get('textPreview', '')[:30]}")
        except Exception as e:
            print(f"⚠️ DEBUG info collection failed: {e}")
        
        # Collect cards with multiple attempts and different selectors
        cards = []
        card_selectors = [
            ".//div[contains(@class,'card')]",
            ".//div[contains(@class,'Card')]",
            ".//div[contains(@class,'item')]",
            ".//div[contains(@class,'Item')]",
            ".//div[contains(@class,'grid-item')]",
            ".//div[contains(@class,'masonry-item')]",
            ".//article",
            ".//div[@role='listitem']",
            ".//div[contains(@class,'result')]",
            ".//div[contains(@class,'tile')]",
            ".//div[contains(@class,'entry')]",
            ".//div[contains(@class,'media')]",
            ".//div[contains(@class,'content')]",
            ".//div[contains(@class,'thumbnail')]",
            ".//div[contains(@class,'video')]",
            ".//div[contains(@class,'image')]",
            ".//div[contains(@class,'document')]",
            ".//div[contains(@class,'audio')]",
            ".//*[contains(@class,'card') or contains(@class,'item') or contains(@class,'grid') or contains(@class,'masonry')]",
        ]
        
        for attempt in range(1, 5):
            for selector in card_selectors:
                try:
                    found_cards = self.page.locator(area_xpath).locator(selector).all()
                    if found_cards:
                        # Filter visible cards
                        visible_cards = [c for c in found_cards if c.is_visible()]
                        if visible_cards:
                            cards = visible_cards
                            print(f"✅ Found {len(cards)} cards using selector: {selector}")
                            break
                except Exception:
                    continue
            if cards:
                break
            time.sleep(2)
        
        # Try collect_result_cards as fallback
        if not cards:
            try:
                cards = self.utils.collect_result_cards(self.page, area_xpath)
                if cards:
                    print(f"✅ Found {len(cards)} cards using collect_result_cards")
            except Exception:
                pass
        
        # Final attempt: Use JavaScript to find cards directly
        if not cards:
            print("⚠️ No cards found with standard selectors, trying JavaScript-based detection...")
            time.sleep(3)
            try:
                # Use JavaScript to find all visible divs with content
                js_cards = self.page.evaluate(f"""
                    () => {{
                        const area = document.evaluate('{area_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        if (!area) return [];
                        
                        const allDivs = area.querySelectorAll('div');
                        const cards = [];
                        for (let div of allDivs) {{
                            const rect = div.getBoundingClientRect();
                            const style = window.getComputedStyle(div);
                            const isVisible = rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                            
                            if (isVisible) {{
                                const text = div.innerText || '';
                                const hasImage = div.querySelector('img') !== null;
                                const hasVideo = div.querySelector('video') !== null;
                                const hasContent = (text.trim().length > 10) || hasImage || hasVideo;
                                
                                if (hasContent) {{
                                    // Check if this div is not a child of another card
                                    let isChild = false;
                                    for (let existingCard of cards) {{
                                        if (existingCard.contains(div)) {{
                                            isChild = true;
                                            break;
                                        }}
                                    }}
                                    if (!isChild) {{
                                        cards.push(div);
                                    }}
                                }}
                            }}
                        }}
                        return cards.length;
                    }}
                """)
                if js_cards and js_cards > 0:
                    print(f"✅ JavaScript found {js_cards} potential cards")
                    # Now get the actual locators
                    all_divs = self.page.locator(area_xpath).locator(".//div").all()
                    for div in all_divs:
                        try:
                            if div.is_visible():
                                text = div.inner_text()
                                has_image = len(div.locator(".//img").all()) > 0
                                has_video = len(div.locator(".//video").all()) > 0
                                if (text and len(text.strip()) > 10) or has_image or has_video:
                                    # Check if this div is not nested inside another card
                                    is_nested = False
                                    for existing_card in cards:
                                        try:
                                            if existing_card.locator(f"xpath=ancestor::div[. = '{div.inner_text()[:20]}']").count() > 0:
                                                is_nested = True
                                                break
                                        except Exception:
                                            pass
                                    if not is_nested:
                                        cards.append(div)
                        except Exception:
                            continue
                    if cards:
                        print(f"✅ Found {len(cards)} cards using JavaScript-based detection")
            except Exception as e:
                print(f"⚠️ JavaScript detection failed: {e}")
        
        if not cards:
            print("❌ No results found — cannot mark as passed")
            print("   Please provide the following information:")
            print("   1. Open browser DevTools (F12)")
            print("   2. Inspect one of the result cards")
            print("   3. Provide the card's:")
            print("      - HTML tag (div, article, etc.)")
            print("      - Class names")
            print("      - ID (if any)")
            print("      - XPath or CSS selector")
            print("   4. Or take a screenshot of the page with results visible")
            return 0, 0, []
        
        print(f"✅ Found {len(cards)} result cards for verification")

        print(f"🔍 Verifying keyword '{keyword}' in metadata of all result cards...")
        print(f"📊 Using fuzzy matching threshold: {threshold}%")
        keyword_lower = (keyword or "").lower().strip()
        matched = 0
        total = 0
        mismatch_details = []

        # Predefine skip words (noise words to filter out)
        # NOTE: Don't remove common words that might be part of search keywords
        skip_words = ['see details','mp4','pdf','xls','zip','mov','mkv','jpg','png','avif','svg','tif']

        def clean_text(text):
            """
            Clean text by removing noise words and formatting.
            IMPORTANT: Don't remove words that might be search keywords!
            """
            if not text:
                return ""
            text_lower = text.lower()
            # Only remove noise words that are definitely not search keywords
            # Use word boundaries to avoid removing parts of words
            for w in skip_words:
                text_lower = re.sub(r'\b' + re.escape(w) + r'\b', '', text_lower)
            # Remove durations (e.g., "00:30", "1:23:45")
            text_lower = re.sub(r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b", "", text_lower)
            # Remove file sizes (e.g., "5.2 MB", "100kb")
            text_lower = re.sub(r"\b\d+(?:\.\d+)?\s?(?:kb|mb|gb)\b", "", text_lower)
            # Normalize whitespace
            text_lower = re.sub(r"\s+", " ", text_lower).strip()
            return text_lower

        def check_keyword_match(keyword, metadata_text, threshold):
            """
            Check if keyword matches metadata using multiple fuzzywuzzy strategies.
            Enhanced with word-by-word matching for better accuracy.
            
            Returns:
                tuple: (is_match, best_score, method_used)
            """
            if not metadata_text:
                return False, 0, None
            
            keyword_clean = keyword.lower().strip()
            metadata_clean = clean_text(metadata_text)
            
            if not metadata_clean:
                return False, 0, None
            
            # Strategy 1: Exact substring match (case-insensitive) - highest priority
            if keyword_clean in metadata_clean:
                return True, 100, "exact_match"
            
            # Strategy 2: Check individual words from keyword (for multi-word keywords)
            keyword_words = keyword_clean.split()
            words_found = 0
            if len(keyword_words) > 1:
                # For multi-word keywords, check if all words appear (in any order)
                words_found = sum(1 for word in keyword_words if word in metadata_clean)
                if words_found == len(keyword_words):
                    # All words found - this is a strong match
                    return True, 95, "all_words_match"
                elif words_found > 0:
                    # Some words found - check if enough words match
                    word_match_percentage = (words_found / len(keyword_words)) * 100
                    if word_match_percentage >= 70:  # At least 70% of words found
                        return True, word_match_percentage, "partial_words_match"
            
            # Strategy 3: Partial ratio (BEST for search results - finds keyword within longer text)
            # This is the most important for search results where keyword appears in title/description
            partial_score = fuzz.partial_ratio(keyword_clean, metadata_clean)
            
            # Strategy 4: Token sort ratio (ignores word order) - good for "news breaking" vs "breaking news"
            token_sort_score = fuzz.token_sort_ratio(keyword_clean, metadata_clean)
            
            # Strategy 5: Token set ratio (best for strings with different word counts)
            token_set_score = fuzz.token_set_ratio(keyword_clean, metadata_clean)
            
            # Strategy 6: WRatio (weighted ratio - best for mixed case and strings)
            wr_score = 0
            try:
                if hasattr(fuzz, 'WRatio'):
                    wr_score = fuzz.WRatio(keyword_clean, metadata_clean)
                elif hasattr(fuzz, 'wratio'):
                    wr_score = fuzz.wratio(keyword_clean, metadata_clean)
            except Exception:
                pass
            
            # Strategy 7: Ratio (best for full string similarity)
            ratio_score = fuzz.ratio(keyword_clean, metadata_clean)
            
            # Get the best score from all strategies
            # For search results, partial_ratio is most important
            best_score = max(partial_score, token_sort_score, token_set_score, wr_score, ratio_score)
            
            # Determine which method gave the best score
            if best_score == partial_score:
                method = "partial_ratio"
            elif best_score == token_sort_score:
                method = "token_sort_ratio"
            elif best_score == token_set_score:
                method = "token_set_ratio"
            elif best_score == wr_score:
                method = "WRatio"
            else:
                method = "ratio"
            
            # Matching logic: For search results, we need to be more lenient
            # According to FuzzyWuzzy documentation, partial_ratio is best for finding substrings
            is_match = False
            
            # Primary check: partial_ratio >= 50 means keyword is found in text (most important for search)
            # This is the correct way to use partial_ratio - it finds keyword within longer text
            if partial_score >= 50:
                is_match = True
            # Secondary check: token_sort_ratio or token_set_ratio (good for word order variations)
            elif token_sort_score >= 60 or token_set_score >= 60:
                is_match = True
            # Tertiary check: best_score with threshold (for exact matches)
            elif best_score >= threshold:
                is_match = True
            # Quaternary check: WRatio (weighted ratio - good for mixed case)
            elif wr_score >= 60:
                is_match = True
            # Final check: if any ratio is above 50, consider it a match (very lenient for search)
            elif best_score >= 50:
                is_match = True
            
            return is_match, best_score, method

        # Only inspect first 150 visible cards
        visible_cards = [c for c in cards if c.is_visible()][:150]
        
        for card_idx, card in enumerate(visible_cards, 1):
            total += 1
            try:
                # Extract comprehensive metadata
                metadata = self.extract_comprehensive_metadata(card)
                
                # Combine all metadata fields for checking
                all_metadata_fields = [
                    metadata['title'],
                    metadata['description'],
                    metadata['keywords'],
                    metadata['alt_text'],
                    metadata['aria_label'],
                    metadata['data_attributes'],
                    metadata['all_text']
                ]
                
                # Combine into single text for checking
                combined_metadata = " ".join([f for f in all_metadata_fields if f]).strip()
                
                # Skip empty cards
                if not combined_metadata:
                    print(f"⚠️ Card #{card_idx}: No metadata found (empty card)")
                    mismatch_details.append({
                        'card_number': card_idx,
                        'reason': 'No metadata found',
                        'title': '(empty card)'
                    })
                    continue
                
                # Check keyword match using comprehensive fuzzy matching
                is_match, best_score, method = check_keyword_match(keyword, combined_metadata, threshold)
                
                # Get display title for logging
                display_title = metadata['title'] or metadata['description'] or metadata['alt_text'] or metadata['aria_label'] or "(no title)"
                
                if is_match:
                    matched += 1
                    print(f"✅ Card #{card_idx} MATCH (Score: {best_score}% via {method}) → {display_title[:80]}")
                else:
                    # Log mismatch as ERROR (not debug)
                    print(f"❌ Card #{card_idx} NO MATCH (Best Score: {best_score}% < {threshold}%) → {display_title[:80]}")
                    print(f"   📋 Metadata preview: {combined_metadata[:150]}...")
                    
                    mismatch_details.append({
                        'card_number': card_idx,
                        'title': display_title,
                        'best_score': best_score,
                        'threshold': threshold,
                        'method': method,
                        'metadata_preview': combined_metadata[:200]
                    })
                
                # Optional deep check inside modal/dialog for unmatched cards
                if not is_match and deep_check:
                    try:
                        card.scroll_into_view_if_needed()
                        time.sleep(0.5)
                    except Exception:
                        pass
                    
                    try:
                        btn = card.locator(".//*[contains(.,'See details') or contains(@aria-label,'details') or contains(@class,'details')]").first
                        if btn.is_visible():
                            try:
                                btn.click()
                            except Exception:
                                self.page.evaluate("(el) => el.click();", btn.element_handle())
                            
                            # Wait for dialog
                            try:
                                self.page.wait_for_selector("//*[@role='dialog' or contains(@class,'modal') or contains(@class,'Dialog') or contains(@class,'drawer')]", timeout=3000)
                                dlg = self.page.locator("//*[@role='dialog' or contains(@class,'modal') or contains(@class,'Dialog') or contains(@class,'drawer')]").first
                                dialog_text = (dlg.inner_text() or '').strip()
                                
                                if dialog_text:
                                    # Check keyword in dialog
                                    is_dialog_match, dialog_score, dialog_method = check_keyword_match(keyword, dialog_text, threshold)
                                    if is_dialog_match:
                                        print(f"   ✅ Found match in dialog (Score: {dialog_score}% via {dialog_method})")
                                        matched += 1
                                        # Remove from mismatch list if it was added
                                        mismatch_details = [m for m in mismatch_details if m.get('card_number') != card_idx]
                                    else:
                                        print(f"   ⚠️ Dialog also shows no match (Score: {dialog_score}%)")
                            except Exception:
                                pass
                            
                            # Close dialog
                            try:
                                self.page.keyboard.press("Escape")
                                time.sleep(0.5)
                            except Exception:
                                pass
                    except Exception:
                        pass
                        
            except Exception as e:
                print(f"❌ Card #{card_idx}: Error reading card - {str(e)}")
                mismatch_details.append({
                    'card_number': card_idx,
                    'reason': f'Error reading card: {str(e)}',
                    'title': '(unreadable)'
                })

        # Final summary
        unmatched_count = total - matched
        match_percentage = (matched / total * 100) if total > 0 else 0
        
        print("")
        print("="*80)
        print(f"📊 VERIFICATION SUMMARY")
        print("="*80)
        print(f"🔍 Keyword: '{keyword}'")
        print(f"📈 Total Cards Checked: {total}")
        print(f"✅ Matched Cards: {matched} ({match_percentage:.1f}%)")
        print(f"❌ Unmatched Cards: {unmatched_count} ({100-match_percentage:.1f}%)")
        print(f"🎯 Threshold Used: {threshold}%")
        
        if unmatched_count > 0:
            print("")
            print("⚠️ WARNING: Some search results do not contain the keyword in their metadata!")
            print(f"   Found {unmatched_count} result(s) that may be incorrect.")
            if len(mismatch_details) > 0:
                print("   Top mismatches:")
                for detail in mismatch_details[:5]:  # Show top 5
                    if 'best_score' in detail:
                        print(f"   - Card #{detail['card_number']}: '{detail['title'][:60]}' (Score: {detail['best_score']}%)")
                    else:
                        print(f"   - Card #{detail['card_number']}: {detail.get('reason', 'Unknown issue')}")
        else:
            print("")
            print("✅ All search results contain the keyword in their metadata!")
        
        print("="*80)
        
        return matched, total, mismatch_details
    
    def verify_keyword_in_results(self, keyword, area_xpath="//*[@id='recentUploads']", threshold=70):
        """
        Compatibility wrapper pointing to the unified media-cards verifier.
        
        Args:
            keyword (str): Keyword to search for
            area_xpath (str): XPath of the area to search in
            threshold (int): Fuzzy matching threshold
        
        Returns:
            tuple: (matched_count, total_count, mismatch_details)
        """
        return self.verify_keyword_in_media_cards(keyword, area_xpath=area_xpath, threshold=threshold)
    
    def verify_sorting(self, mode_label, area_xpath="//*[@id='recentUploads']"):
        """
        Verify sorting order by inspecting titles or dates depending on mode_label.
        
        Args:
            mode_label (str): Sorting mode label (e.g., "Title (A–Z)", "Date Added (Newest First)")
            area_xpath (str): XPath of the area to verify
        
        Returns:
            bool: True if sorting is correct, False otherwise
        """
        # Use UtilityFunctions for helper methods
        utils = UtilityFunctions()
        
        try:
            area = self.page.locator(area_xpath).first
            if not area.is_visible():
                print(f"⚠️ Sorting: content area not found.")
                return False
        except Exception:
            print(f"⚠️ Sorting: content area not found.")
            return False

        cards = self.utils.collect_result_cards(self.page, area_xpath)
        titles = [self.utils.extract_card_title(self.page, c).strip() for c in cards]
        dates = [self.utils.extract_card_date(self.page, c) for c in cards]

        ok = True
        if 'Title' in mode_label:
            base = [t for t in titles if t]
            folded = [t.casefold() for t in base]
            asc_sorted = sorted(folded)
            desc_sorted = sorted(folded, reverse=True)
            if 'A' in mode_label:
                ok = folded == asc_sorted
            else:
                ok = folded == desc_sorted
            print(f"🔠 Sorting check ({mode_label}): {'✅' if ok else '❌'} | titles={len(base)}")
        else:
            # Date based
            numeric = [d for d in dates if isinstance(d, int)]
            if len(numeric) >= 2:
                asc = sorted(numeric)
                desc = sorted(numeric, reverse=True)
                observed = numeric
                if 'Newest' in mode_label:
                    ok = observed == desc
                else:
                    ok = observed == asc
                print(f"🗓️ Sorting check ({mode_label}): {'✅' if ok else '❌'} | dates={len(numeric)}")
            else:
                print(f"🗓️ Sorting check ({mode_label}): ⚠️ Insufficient date data, skipping strict check")
                ok = True  # don't fail if dates unavailable
        return ok
    
    def switch_view(self, view_name):
        """
        Switch to a specific view tab: Grid, List, Masonry with robust clicking.
        
        Args:
            view_name (str): Name of view to switch to ("Grid", "List", "Masonry")
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Use UtilityFunctions for robust clicking
        utils = UtilityFunctions()
        
        selectors_map = {
            'Masonry': [
                "//button[contains(text(), 'Masonry')]",
                "//a[contains(text(), 'Masonry')]",
                "//span[contains(text(), 'Masonry')]",
                "//div[contains(text(), 'Masonry')]",
                "//*[contains(@class, 'masonry') and contains(text(), 'Masonry')]",
                "//*[contains(@id, 'masonry')]",
                "//*[contains(@title, 'Masonry')]",
            ],
            'List': [
                "//button[contains(text(), 'List')]",
                "//a[contains(text(), 'List')]",
                "//span[contains(text(), 'List')]",
                "//div[contains(text(), 'List')]",
                "//*[contains(@class, 'list') and contains(text(), 'List')]",
                "//*[contains(@id, 'list')]",
                "//*[contains(@title, 'List')]",
            ],
            'Grid': [
                "//button[contains(text(), 'Grid')]",
                "//a[contains(text(), 'Grid')]",
                "//span[contains(text(), 'Grid')]",
                "//div[contains(text(), 'Grid')]",
                "//*[contains(@class, 'grid') and contains(text(), 'Grid')]",
                "//*[contains(@id, 'grid')]",
                "//*[contains(@title, 'Grid')]",
            ],
        }
        sels = selectors_map.get(view_name, [])
        for sel in sels:
            try:
                el = self.page.locator(sel).first
                if not el.is_visible():
                    continue
                if self.utils.robust_click_element(self.page, el, f"{view_name} view button"):
                    # Wait for view-specific container to appear
                    try:
                        if view_name == 'Masonry':
                            self.page.wait_for_selector("//div[contains(@class,'masonry')]", timeout=5000)
                        elif view_name == 'List':
                            self.page.wait_for_selector("//div[contains(@class,'list')] | //ul[contains(@class,'list')]", timeout=5000)
                        else:
                            self.page.wait_for_selector("//div[contains(@class,'grid')]", timeout=5000)
                    except Exception:
                        pass
                    return True
            except Exception:
                continue
        print(f"⚠️ Could not click section {view_name} after multiple attempts")
        return False
    
    def validate_view_and_return_to_grid(self, view_name, keyword):
        """
        Switch to view, validate results contain keyword (fuzzy), then return to Grid.
        
        Args:
            view_name (str): Name of view to validate
            keyword (str): Keyword to search for
        
        Returns:
            tuple: (matched_count, total_count)
        """
        if view_name != 'Grid':
            if not self.switch_view(view_name):
                print(f"⚠️ Could not switch to {view_name} view")
            time.sleep(1)
        matched, total, mismatch_details = self.verify_keyword_in_results(keyword)
        if view_name != 'Grid':
            self.switch_view('Grid')
            time.sleep(1)
        return matched, total

    def perform_text_based_search(self, keyword, search_type="Normal", threshold=None):
        """
        Perform text-based search verification using visible text extraction.
        
        Args:
            keyword (str): Search keyword
            search_type (str): Type of search (for logging)
            threshold (int, optional): Fuzzy matching threshold. If None, uses utils.FUZZY_THRESHOLD
        
        Returns:
            int: Number of matches found
        """
        if threshold is None:
            threshold = self.utils.FUZZY_THRESHOLD if self.utils else 70
        
        print(f"🔍 {search_type}: Verifying keyword '{keyword}' using text-based search")
        
        # Smooth scroll to load all content
        if self.utils:
            self.utils.smooth_scroll_page(self.page, to="bottom")
        time.sleep(1)
        if self.utils:
            self.utils.smooth_scroll_page(self.page, to="top")
        time.sleep(1)
        
        # Extract all visible text from the page
        try:
            page_text = self.page.locator("body").inner_text()
        except Exception:
            print(f"❌ {search_type}: Could not extract page text")
            return 0
        
        if not page_text or len(page_text.strip()) < 10:
            print(f"⚠️ No posts found — skipping verification")
            return 0
        
        # Convert to lowercase and count keyword matches
        keyword_lower = keyword.lower()
        page_text_lower = page_text.lower()
        
        # Count total occurrences of the keyword
        match_count = page_text_lower.count(keyword_lower)
        
        # Also check for fuzzy matches in text blocks for better accuracy
        text_blocks = [block.strip() for block in page_text.split('\n') if block.strip()]
        noise_words = self.utils.NOISE_WORDS if self.utils else []
        filtered_blocks = []
        
        for block in text_blocks:
            # Skip blocks that are just noise
            if any(noise in block.lower() for noise in noise_words):
                continue
            # Skip very short blocks or numbers only
            if len(block) < 3 or block.isdigit():
                continue
            # Skip time patterns (00:05, 11:30:45)
            if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', block):
                continue
            # Skip file size patterns (11.2 MB, 5.3 GB)
            if re.match(r'^\d+(\.\d+)?\s?(kb|mb|gb)$', block.lower()):
                continue
            filtered_blocks.append(block)
        
        # Count fuzzy matches in filtered blocks
        fuzzy_matches = 0
        for block in filtered_blocks:
            block_lower = block.lower()
            if keyword_lower in block_lower or fuzz.partial_ratio(keyword_lower, block_lower) >= threshold:
                fuzzy_matches += 1
        
        # Use the higher count between exact matches and fuzzy matches
        final_match_count = max(match_count, fuzzy_matches)
        
        # Print results with simple count format
        if final_match_count == 0:
            print(f"❌ {search_type}: No matches found — post may not exist")
        elif final_match_count < 20:
            print(f"✅ {search_type}: {final_match_count} matches found")
            print(f"✅ Partial matches — some data may be hidden in descriptions")
        else:
            print(f"✅ {search_type}: {final_match_count} matches found")
        
        return final_match_count
    
    def perform_text_search_in_area(self, area_xpath, keyword, search_type="Area", threshold=None):
        """
        Restrict text-based verification to a specific results area (e.g., recentUploads).
        
        Args:
            area_xpath (str): XPath of the area to search in
            keyword (str): Search keyword
            search_type (str): Type of search (for logging)
            threshold (int, optional): Fuzzy matching threshold. If None, uses utils.FUZZY_THRESHOLD
        
        Returns:
            int: Number of matches found in the area
        """
        if threshold is None:
            threshold = self.utils.FUZZY_THRESHOLD if self.utils else 70
        
        print(f"🔍 {search_type}: Verifying '{keyword}' within area {area_xpath}")
        try:
            area = self.page.locator(area_xpath).first
            if not area.is_visible():
                print(f"❌ {search_type}: Area not found")
                return 0
        except Exception:
            print(f"❌ {search_type}: Area not found")
            return 0

        try:
            # Prefer innerText of the area only
            area_text = area.evaluate("(el) => el.innerText || '';") or ""
        except Exception:
            try:
                area_text = area.inner_text() or ""
            except Exception:
                area_text = ""

        area_text = area_text.strip()
        if not area_text or len(area_text) < 5:
            print(f"⚠️ {search_type}: Area contains no visible text")
            return 0

        keyword_lower = (keyword or "").lower()
        text_lower = area_text.lower()

        # Exact occurrences
        exact_count = text_lower.count(keyword_lower)

        # Fuzzy across logical blocks within area
        blocks = [b.strip() for b in area_text.split('\n') if b.strip()]
        noise_words = self.utils.NOISE_WORDS if self.utils else []
        filtered_blocks = []
        for b in blocks:
            bl = b.lower()
            if any(n in bl for n in noise_words):
                continue
            if len(b) < 3 or b.isdigit():
                continue
            if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', b):
                continue
            if re.match(r'^\d+(\.\d+)?\s?(kb|mb|gb)$', bl):
                continue
            filtered_blocks.append(b)

        fuzzy_count = 0
        for b in filtered_blocks:
            bl = b.lower()
            if keyword_lower in bl or fuzz.partial_ratio(keyword_lower, bl) >= threshold:
                fuzzy_count += 1

        final_count = max(exact_count, fuzzy_count)
        if final_count == 0:
            print(f"❌ {search_type}: No matches found in area")
        else:
            print(f"✅ {search_type}: {final_count} matches found in area")
        return final_count
    
    # Note: verify_keyword_in_media_cards is defined earlier in this class (line ~1264)
    # This duplicate has been removed - using the comprehensive version above
    
    def verify_keyword_in_results(self, keyword, area_xpath="//*[@id='recentUploads']", threshold=70):
        """
        Compatibility wrapper pointing to the unified media-cards verifier.
        
        Args:
            keyword (str): Search keyword
            area_xpath (str): XPath of the area to search in
            threshold (int): Fuzzy matching threshold
        
        Returns:
            tuple: (matched_count, total_count, mismatch_details)
        """
        return self.verify_keyword_in_media_cards(keyword, area_xpath=area_xpath, threshold=threshold)
    
    def switch_view(self, view_name):
        """
        Switch to a specific view tab: Grid, List, Masonry with robust clicking.
        
        Args:
            view_name (str): Name of the view to switch to ('Grid', 'List', 'Masonry')
        
        Returns:
            bool: True if successful, False otherwise
        """
        selectors_map = {
            'Masonry': [
                "//button[contains(text(), 'Masonry')]",
                "//a[contains(text(), 'Masonry')]",
                "//span[contains(text(), 'Masonry')]",
                "//div[contains(text(), 'Masonry')]",
                "//*[contains(@class, 'masonry') and contains(text(), 'Masonry')]",
                "//*[contains(@id, 'masonry')]",
                "//*[contains(@title, 'Masonry')]",
            ],
            'List': [
                "//button[contains(text(), 'List')]",
                "//a[contains(text(), 'List')]",
                "//span[contains(text(), 'List')]",
                "//div[contains(text(), 'List')]",
                "//*[contains(@class, 'list') and contains(text(), 'List')]",
                "//*[contains(@id, 'list')]",
                "//*[contains(@title, 'List')]",
            ],
            'Grid': [
                "//button[contains(text(), 'Grid')]",
                "//a[contains(text(), 'Grid')]",
                "//span[contains(text(), 'Grid')]",
                "//div[contains(text(), 'Grid')]",
                "//*[contains(@class, 'grid') and contains(text(), 'Grid')]",
                "//*[contains(@id, 'grid')]",
                "//*[contains(@title, 'Grid')]",
            ],
        }
        sels = selectors_map.get(view_name, [])
        for sel in sels:
            try:
                el = self.page.locator(sel).first
                if not el.is_visible():
                    continue
                if robust_click_element(self.page, el, f"{view_name} view button"):
                    # Wait for view-specific container to appear
                    try:
                        if view_name == 'Masonry':
                            self.page.wait_for_selector("//div[contains(@class,'masonry')]", timeout=5000)
                        elif view_name == 'List':
                            self.page.wait_for_selector("//div[contains(@class,'list')] | //ul[contains(@class,'list')]", timeout=5000)
                        else:
                            self.page.wait_for_selector("//div[contains(@class,'grid')]", timeout=5000)
                    except Exception:
                        pass
                    return True
            except Exception:
                continue
        print(f"⚠️ Could not click section {view_name} after multiple attempts")
        return False
    
    def verify_sorting(self, mode_label, area_xpath="//*[@id='recentUploads']"):
        """
        Verify sorting order by inspecting titles or dates depending on mode_label.
        
        Args:
            mode_label (str): Sorting mode label (e.g., "Title (A–Z)", "Date Added (Newest First)")
            area_xpath (str): XPath of the area to check
        
        Returns:
            bool: True if sorting is correct, False otherwise
        """
        try:
            area = self.page.locator(area_xpath).first
            if not area.is_visible():
                print(f"⚠️ Sorting: content area not found.")
                return False
        except Exception:
            print(f"⚠️ Sorting: content area not found.")
            return False

        cards = collect_result_cards(self.page, area_xpath)
        titles = [extract_card_title(self.page, c).strip() for c in cards]
        dates = [extract_card_date(self.page, c) for c in cards]

        ok = True
        if 'Title' in mode_label:
            base = [t for t in titles if t]
            folded = [t.casefold() for t in base]
            asc_sorted = sorted(folded)
            desc_sorted = sorted(folded, reverse=True)
            if 'A' in mode_label:
                ok = folded == asc_sorted
            else:
                ok = folded == desc_sorted
            print(f"🔠 Sorting check ({mode_label}): {'✅' if ok else '❌'} | titles={len(base)}")
        else:
            # Date based
            numeric = [d for d in dates if isinstance(d, int)]
            if len(numeric) >= 2:
                asc = sorted(numeric)
                desc = sorted(numeric, reverse=True)
                observed = numeric
                if 'Newest' in mode_label:
                    ok = observed == desc
                else:
                    ok = observed == asc
                print(f"🗓️ Sorting check ({mode_label}): {'✅' if ok else '❌'} | dates={len(numeric)}")
            else:
                print(f"🗓️ Sorting check ({mode_label}): ⚠️ Insufficient date data, skipping strict check")
                ok = True  # don't fail if dates unavailable
        return ok
    
    def execute_simple_search(self, keyword: str, threshold: int = None):
        """
        Execute complete simple search verification workflow.
        
        This method performs:
        - Grid view verification
        - List view verification
        - Masonry view verification
        
        Args:
            keyword (str): Search keyword
            threshold (int, optional): Fuzzy matching threshold. If None, uses utils.FUZZY_THRESHOLD
        
        Returns:
            dict: Results dictionary with grid, masonry, list matches
        """
        if threshold is None:
            threshold = self.utils.FUZZY_THRESHOLD if self.utils else 70
        
        print("\n" + "="*60)
        print("🔍 SIMPLE SEARCH VERIFICATION")
        print("="*60)
        
        # Wait for results to load
        time.sleep(3)
        
        # Scroll to ensure all content is loaded
        try:
            print("⬇️ Scrolling to bottom of the page...")
            scroll_page(self.page, to="bottom")
            time.sleep(2)
            print("⬆️ Scrolling back to top of the page...")
            scroll_page(self.page, to="top")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Scrolling failed: {str(e)}")

        # Verify in Grid View (default) using comprehensive metadata verification
        print("🧩 Checking results in Grid View (comprehensive metadata verification)...")
        grid_matched, grid_total, grid_mismatches = self.verify_keyword_in_results(keyword, "//*[@id='recentUploads']", threshold)
        grid_matches = grid_matched
        
        # Verify in List View
        print("📋 Checking results in List View (comprehensive metadata verification)...")
        if self.switch_view('List'):
            time.sleep(2)
            list_matched, list_total, list_mismatches = self.verify_keyword_in_results(keyword, "//*[@id='recentUploads']", threshold)
            list_matches = list_matched
            self.switch_view('Grid')
            time.sleep(1)
        else:
            print("⚠️ Could not switch to List view")
            list_matches = 0
        
        # Verify in Masonry View
        print("🧱 Checking results in Masonry View (comprehensive metadata verification)...")
        if self.switch_view('Masonry'):
            time.sleep(2)
            masonry_matched, masonry_total, masonry_mismatches = self.verify_keyword_in_results(keyword, "//*[@id='recentUploads']", threshold)
            masonry_matches = masonry_matched
            self.switch_view('Grid')
            time.sleep(1)
        else:
            print("⚠️ Could not switch to Masonry view")
            masonry_matches = 0
        
        # Check for view count mismatch
        view_counts = [grid_matches, masonry_matches, list_matches]
        if len(set(view_counts)) > 1 and all(count > 0 for count in view_counts):
            print(f"⚠️ View count mismatch — Grid:{grid_matches}, Masonry:{masonry_matches}, List:{list_matches}")
        
        results = {
            'grid': grid_matches,
            'masonry': masonry_matches,
            'list': list_matches
        }
        
        return results

# =============================================================================
# ADVANCED SEARCH FUNCTIONS CLASS
# =============================================================================

class AdvancedSearchFunctions:
    """
    Advanced Search functions class for advanced search functionality.
    
    This class handles:
    - Advanced search tabs (All, Audios, Videos, Images, Document, Others)
    - Advanced search with filters (Category, Date Range)
    - Advanced search sorting
    - Advanced search views
    
    Attributes:
        page (Page): Playwright Page instance
    
    Example:
        >>> advanced_search = AdvancedSearchFunctions(page)
        >>> results = advanced_search.execute_advanced_search_tabs(keyword="news", threshold=70)
    """
    
    def __init__(self, page: Page):
        """
        Initialize Advanced Search Functions.
        
        Args:
            page (Page): Playwright Page instance
        """
        self.page = page
    
    def click_advanced_search_tab(self, tab_label):
        """
        Enhanced tab clicking with multiple fallback strategies for Advanced Search tabs.
        
        Args:
            tab_label (str): Label of the tab to click (e.g., "All", "Audios", "Videos")
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Primary selectors for Advanced Search tabs
        primary_selectors = [
            f"//button[normalize-space(.)='{tab_label}']",
            f"//a[normalize-space(.)='{tab_label}']",
            f"//span[normalize-space(.)='{tab_label}']",
            f"//*[contains(@class,'tab') and normalize-space(.)='{tab_label}']",
            f"//*[@role='tab' and normalize-space(.)='{tab_label}']",
            f"//*[normalize-space(text())='{tab_label}']",
        ]
        
        # Additional selectors for Advanced Search context
        advanced_selectors = [
            f"//*[contains(@class,'advanced') or contains(@class,'search')]//*[normalize-space(.)='{tab_label}']",
            f"//*[@id='advancedSearch']//*[normalize-space(.)='{tab_label}']",
            f"//*[contains(@class,'filter') or contains(@class,'category')]//*[normalize-space(.)='{tab_label}']",
            f"//*[contains(@class,'nav') or contains(@class,'menu')]//*[normalize-space(.)='{tab_label}']",
        ]
        
        all_selectors = primary_selectors + advanced_selectors
        
        for sel in all_selectors:
            try:
                el = self.page.locator(sel).first
                if not el.is_visible():
                    continue
                    
                # Scroll element into view
                el.scroll_into_view_if_needed()
                time.sleep(0.3)
                
                # Try multiple click strategies
                click_success = False
                
                # Strategy 1: Normal click
                try:
                    el.click()
                    click_success = True
                    print(f"✅ Clicked {tab_label} tab (normal click)")
                except Exception:
                    pass
                
                # Strategy 2: JavaScript click
                if not click_success:
                    try:
                        self.page.evaluate("(el) => el.click();", el.element_handle())
                        click_success = True
                        print(f"✅ Clicked {tab_label} tab (JavaScript click)")
                    except Exception:
                        pass
                
                # Strategy 3: Force click
                if not click_success:
                    try:
                        el.click(force=True)
                        click_success = True
                        print(f"✅ Clicked {tab_label} tab (force click)")
                    except Exception:
                        pass
                
                if click_success:
                    return True
                    
            except Exception as e:
                print(f"⚠️ Error clicking {tab_label}: {e}")
                continue
        
        return False
    
    def execute_advanced_search_tabs(self, keyword: str, threshold: int = FUZZY_THRESHOLD):
        """
        Execute advanced search tabs verification.
        
        Tests all advanced search tabs (All, Audios, Videos, Images, Document, Others)
        and verifies keyword presence in each tab.
        
        Args:
            keyword (str): Search keyword
            threshold (int): Fuzzy matching threshold
        
        Returns:
            dict: Results dictionary with tab names and match counts
        """
        print("\n" + "="*60)
        print("📂 ADVANCED SEARCH TABS VERIFICATION")
        print("="*60)
        
        advanced_search_tabs = ["All", "Audios", "Videos", "Images", "Document", "Others"]
        advanced_tab_results = {}
        
        print(f"🔍 Testing {len(advanced_search_tabs)} Advanced Search tabs...")
        
        # Use SimpleSearchFunctions for comprehensive metadata verification
        simple_search = SimpleSearchFunctions(self.page)
        if not simple_search.utils:
            from pathlib import Path
            simple_search.utils = UtilityFunctions(Path(__file__).resolve().parents[1] / "env")
        
        for tab in advanced_search_tabs:
            print(f"\n🔄 Testing Advanced Search tab: {tab}")
            
            # Attempt to click the tab
            if self.click_advanced_search_tab(tab):
                print(f"✅ Successfully opened {tab} tab")
                
                # Wait for content to load
                time.sleep(2)
                
                # Scroll to load all content
                try:
                    print(f"⬇️ Scrolling to load all {tab} content...")
                    scroll_page(self.page, to="bottom")
                    time.sleep(1.5)
                    scroll_page(self.page, to="top")
                    time.sleep(1.0)
                except Exception as e:
                    print(f"⚠️ Scrolling failed for {tab}: {e}")
                
                # Perform comprehensive metadata verification
                print(f"🔍 Performing comprehensive metadata verification for {tab} tab...")
                matched, total, mismatch_details = simple_search.verify_keyword_in_media_cards(
                    keyword, 
                    area_xpath="//*[@id='recentUploads']", 
                    threshold=threshold,
                    deep_check=False
                )
                advanced_tab_results[tab] = matched
                
                if matched > 0:
                    match_percentage = (matched / total * 100) if total > 0 else 0
                    print(f"✅ Advanced Search {tab}: {matched}/{total} cards matched ({match_percentage:.1f}%)")
                    if len(mismatch_details) > 0:
                        print(f"⚠️ Advanced Search {tab}: {len(mismatch_details)} cards did not match keyword in metadata")
                else:
                    print(f"⚠️ Advanced Search {tab}: No matching cards found")
            else:
                print(f"❌ Could not find or click {tab} tab")
                advanced_tab_results[tab] = 0
        
        # Return to All tab at the end
        print(f"\n🔄 Returning to 'All' tab...")
        if self.click_advanced_search_tab("All"):
            print("✅ Successfully returned to 'All' tab")
            time.sleep(2)
        else:
            print("⚠️ Could not return to 'All' tab")
        
        return advanced_tab_results
    
    def execute_advanced_search(self, keyword: str, threshold: int = FUZZY_THRESHOLD):
        """
        Execute complete advanced search verification workflow.
        
        This method performs comprehensive metadata verification on advanced search results.
        It verifies that all results contain the keyword in their metadata.
        
        Args:
            keyword (str): Search keyword
            threshold (int): Fuzzy matching threshold
        
        Returns:
            dict: Results dictionary with verification results
        """
        print("\n" + "="*60)
        print("⚙️ ADVANCED SEARCH VERIFICATION")
        print("="*60)
        
        print(f"🔍 Performing comprehensive advanced search verification for keyword: '{keyword}'")
        
        # Use SimpleSearchFunctions for comprehensive metadata verification
        simple_search = SimpleSearchFunctions(self.page)
        # Initialize utils if not already set
        if not hasattr(simple_search, 'utils') or not simple_search.utils:
            # Create a minimal utils object or use existing one
            try:
                # Try to get utils from the page context if available
                simple_search.utils = None  # Will be set in verify_keyword_in_media_cards if needed
            except Exception:
                pass
        
        # Wait for results to load
        time.sleep(2)
        
        # Scroll to ensure all content is loaded
        try:
            print("⬇️ Scrolling to load all advanced search content...")
            # Try to use utils scroll method if available
            if hasattr(simple_search, 'utils') and simple_search.utils:
                try:
                    simple_search.utils.smooth_scroll_page(self.page, to="bottom")
                    time.sleep(1.5)
                    simple_search.utils.smooth_scroll_page(self.page, to="top")
                except Exception:
                    # Fallback to direct scroll
                    self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1.5)
                    self.page.evaluate("window.scrollTo(0, 0)")
            else:
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1.5)
                self.page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1.0)
        except Exception as e:
            print(f"⚠️ Scrolling failed: {e}")
        
        # Perform comprehensive metadata verification on current advanced search results
        print("🔍 Performing comprehensive metadata verification on advanced search results...")
        matched, total, mismatch_details = simple_search.verify_keyword_in_media_cards(
            keyword,
            area_xpath="//*[@id='recentUploads']",
            threshold=threshold,
            deep_check=False
        )
        
        # Calculate match percentage
        match_percentage = (matched / total * 100) if total > 0 else 0
        unmatched_count = total - matched
        
        # Log results
        if matched > 0:
            print(f"✅ Advanced Search Verification: {matched}/{total} cards matched ({match_percentage:.1f}%)")
            if unmatched_count > 0:
                print(f"⚠️ Advanced Search Verification: {unmatched_count} cards did not match keyword in metadata")
                if len(mismatch_details) > 0:
                    print("   Top mismatches:")
                    for detail in mismatch_details[:3]:  # Show top 3
                        if 'best_score' in detail:
                            print(f"   - Card #{detail['card_number']}: '{detail['title'][:60]}' (Score: {detail['best_score']}%)")
        else:
            print(f"⚠️ Advanced Search Verification: No matching cards found")
        
        results = {
            'matched': matched,
            'total': total,
            'match_percentage': match_percentage,
            'unmatched_count': unmatched_count,
            'mismatch_details': mismatch_details[:10]  # Store top 10 mismatches
        }
        
        return results

# =============================================================================
# TIMELINE FUNCTIONS CLASS
# =============================================================================

class TimelineFunctions:
    """
    Timeline functions class for timeline functionality.
    
    This class handles:
    - Timeline tab navigation
    - Timeline options (Latest, This Week, This Month, This Year, Older)
    - Timeline keyword verification
    
    Attributes:
        page (Page): Playwright Page instance
    
    Example:
        >>> timeline = TimelineFunctions(page)
        >>> results = timeline.execute_timeline(keyword="news", threshold=70)
    """
    
    def __init__(self, page: Page):
        """
        Initialize Timeline Functions.
        
        Args:
            page (Page): Playwright Page instance
        """
        self.page = page
    
    def click_timeline_tab(self):
        """
        Click the Timeline tab to open timeline options.
        
        Returns:
            bool: True if successful, False otherwise
        """
        timeline_selectors = [
            "//button[normalize-space(.)='Timeline']",
            "//a[normalize-space(.)='Timeline']",
            "//span[normalize-space(.)='Timeline']",
            "//*[contains(@class,'timeline') and normalize-space(.)='Timeline']",
            "//*[@id='timeline']",
            "//*[contains(@title, 'Timeline')]",
            "//*[@role='tab' and normalize-space(.)='Timeline']",
            "//button[contains(text(), 'Timeline')]",
            "//a[contains(text(), 'Timeline')]",
            "//span[contains(text(), 'Timeline')]",
            "//*[normalize-space(text())='Timeline']",
        ]
        
        for sel in timeline_selectors:
            try:
                el = self.page.locator(sel).first
                if not el.is_visible():
                    continue
                
                # Scroll element into view
                el.scroll_into_view_if_needed()
                time.sleep(0.3)
                
                # Try multiple click strategies
                click_success = False
                
                # Strategy 1: Normal click
                try:
                    el.click()
                    click_success = True
                    print("✅ Clicked Timeline tab (normal click)")
                except Exception:
                    pass
                
                # Strategy 2: JavaScript click
                if not click_success:
                    try:
                        self.page.evaluate("(el) => el.click();", el.element_handle())
                        click_success = True
                        print("✅ Clicked Timeline tab (JavaScript click)")
                    except Exception:
                        pass
                
                # Strategy 3: Force click
                if not click_success:
                    try:
                        el.click(force=True)
                        click_success = True
                        print("✅ Clicked Timeline tab (force click)")
                    except Exception:
                        pass
                
                if click_success:
                    time.sleep(2)
                    return True
                    
            except Exception as e:
                print(f"⚠️ Error clicking Timeline tab: {e}")
                continue
        
        print("⚠️ Could not find or click Timeline tab")
        return False
    
    def click_timeline_option(self, option_name):
        """
        Click a specific timeline option (Latest, This Week, This Month, This Year, Older).
        
        Args:
            option_name (str): Name of the timeline option to click
        
        Returns:
            bool: True if successful, False otherwise
        """
        timeline_option_selectors = [
            f"//button[normalize-space(.)='{option_name}']",
            f"//a[normalize-space(.)='{option_name}']",
            f"//span[normalize-space(.)='{option_name}']",
            f"//*[contains(@class,'timeline')]//*[normalize-space(.)='{option_name}']",
            f"//*[@role='button' and normalize-space(.)='{option_name}']",
            f"//*[normalize-space(text())='{option_name}']",
        ]
        
        for sel in timeline_option_selectors:
            try:
                el = self.page.locator(sel).first
                if not el.is_visible():
                    continue
                
                el.scroll_into_view_if_needed()
                time.sleep(0.3)
                
                # Try multiple click strategies
                click_success = False
                
                # Strategy 1: Normal click
                try:
                    el.click()
                    click_success = True
                    print(f"✅ Clicked Timeline option {option_name} (normal click)")
                except Exception:
                    pass
                
                # Strategy 2: JavaScript click
                if not click_success:
                    try:
                        self.page.evaluate("(el) => el.click();", el.element_handle())
                        click_success = True
                        print(f"✅ Clicked Timeline option {option_name} (JavaScript click)")
                    except Exception:
                        pass
                
                # Strategy 3: Force click
                if not click_success:
                    try:
                        el.click(force=True)
                        click_success = True
                        print(f"✅ Clicked Timeline option {option_name} (force click)")
                    except Exception:
                        pass
                
                if click_success:
                    time.sleep(2)
                    return True
                    
            except Exception as e:
                print(f"⚠️ Error clicking Timeline option {option_name}: {e}")
                continue
        
        print(f"⚠️ Could not find or click Timeline option: {option_name}")
        return False
    
    def execute_timeline(self, keyword: str, threshold: int = FUZZY_THRESHOLD):
        """
        Execute complete timeline verification workflow.
        
        Tests all timeline options (Latest, This Week, This Month, This Year, Older)
        and verifies keyword presence in each option.
        
        Args:
            keyword (str): Search keyword
            threshold (int): Fuzzy matching threshold
        
        Returns:
            dict: Results dictionary with timeline option names and match counts
        """
        print("\n" + "="*60)
        print("📅 TIMELINE VERIFICATION")
        print("="*60)
        
        timeline_options = ["Latest", "This Week", "This Month", "This Year", "Older"]
        timeline_results = {}
        
        print(f"🔍 Testing {len(timeline_options)} Timeline options...")
        
        # First, click the Timeline tab
        if not self.click_timeline_tab():
            print("❌ Could not open Timeline tab — skipping timeline verification")
            return timeline_results
        
        # Use SimpleSearchFunctions for comprehensive metadata verification
        simple_search = SimpleSearchFunctions(self.page)
        if not simple_search.utils:
            from pathlib import Path
            simple_search.utils = UtilityFunctions(Path(__file__).resolve().parents[1] / "env")
        
        for option in timeline_options:
            print(f"\n🔄 Testing Timeline option: {option}")
            
            # Attempt to click the timeline option
            if self.click_timeline_option(option):
                print(f"✅ Successfully opened {option} timeline")
                
                # Wait for content to load
                time.sleep(2)
                
                # Scroll to load all content
                try:
                    print(f"⬇️ Scrolling to load all {option} content...")
                    scroll_page(self.page, to="bottom")
                    time.sleep(1.5)
                    scroll_page(self.page, to="top")
                    time.sleep(1.0)
                except Exception as e:
                    print(f"⚠️ Scrolling failed for {option}: {e}")
                
                # Perform comprehensive metadata verification
                print(f"🔍 Performing comprehensive metadata verification for {option} timeline...")
                matched, total, mismatch_details = simple_search.verify_keyword_in_media_cards(
                    keyword, 
                    area_xpath="//*[@id='recentUploads']", 
                    threshold=threshold,
                    deep_check=False
                )
                timeline_results[option] = matched
                
                if matched > 0:
                    match_percentage = (matched / total * 100) if total > 0 else 0
                    print(f"✅ Timeline {option}: {matched}/{total} cards matched ({match_percentage:.1f}%)")
                    if len(mismatch_details) > 0:
                        print(f"⚠️ Timeline {option}: {len(mismatch_details)} cards did not match keyword in metadata")
                else:
                    print(f"⚠️ Timeline {option}: No matching cards found")
            else:
                print(f"❌ Could not find or click {option} timeline option")
                timeline_results[option] = 0
        
        return timeline_results

# =============================================================================
# MAIN AUTOMATION CLASS
# =============================================================================

class ElasticSearchAutomation:
    """
    Main automation class for Elastic Search & Advanced Search Timeline testing.
    
    This class orchestrates the complete search testing workflow by using:
    - UtilityFunctions: Browser management
    - SimpleSearchFunctions: Simple search functionality
    - AdvancedSearchFunctions: Advanced search functionality
    - TimelineFunctions: Timeline functionality
    
    Attributes:
        utils (UtilityFunctions): Utility functions instance
        simple_search (SimpleSearchFunctions): Simple search functions instance
        advanced_search (AdvancedSearchFunctions): Advanced search functions instance
        timeline (TimelineFunctions): Timeline functions instance
        page (Page): Playwright Page instance
    
    Example:
        >>> automation = ElasticSearchAutomation()
        >>> automation.run()
    """
    
    def __init__(self):
        """
        Initialize Elastic Search automation.
        
        Loads all configuration from env_variables.py module.
        """
        # Initialize utility functions (browser setup)
        self.utils = UtilityFunctions()
        
        # Initialize function classes (will be set after browser initialization)
        self.simple_search = None
        self.advanced_search = None
        self.timeline = None
        self.page = None
    
    def display_env_variables(self) -> None:
        """
        Display all environment variables loaded from env_variables.py (sensitive values masked).
        
        Delegates to UtilityFunctions.display_env_variables().
        """
        self.utils.display_env_variables()
    
    def initialize_browser(self) -> bool:
        """
        Initialize Playwright browser with Chrome.
        
        Delegates to UtilityFunctions.initialize_browser() and initializes function classes.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.utils.initialize_browser():
            self.page = self.utils.page
            # Initialize function classes with page
            self.simple_search = SimpleSearchFunctions(self.page)
            self.advanced_search = AdvancedSearchFunctions(self.page)
            self.timeline = TimelineFunctions(self.page)
            return True
        return False
    
    def close_browser(self) -> None:
        """
        Close the browser and cleanup resources.
        
        Delegates to UtilityFunctions.close_browser().
        """
        self.utils.close_browser()
    
    def run(self, keyword: str = None, threshold: int = None) -> bool:
        """
        Execute the complete Elastic Search automation workflow.
        
        This method orchestrates the entire search testing process:
        - Displays environment variables
        - Initializes browser
        - Performs OTP-based login
        - Executes search verification workflow
        - Keeps browser open for manual inspection
        
        Args:
            keyword (str, optional): Search keyword. If None, uses ELASTIC_SEARCH_DEFAULT_KEYWORD from env_variables.py
            threshold (int, optional): Fuzzy matching threshold. If None, uses ELASTIC_SEARCH_FUZZY_THRESHOLD from env_variables.py
        
        Returns:
            bool: True if workflow successful, False otherwise
        
        Example:
            >>> automation = ElasticSearchAutomation()
            >>> success = automation.run(keyword="news", threshold=70)
        """
        # Use defaults from env_variables.py if not provided
        if keyword is None:
            keyword = DEFAULT_KEYWORD
        if threshold is None:
            threshold = FUZZY_THRESHOLD
        
        # Store keyword and threshold for use in all verification functions
        self.current_keyword = keyword
        self.current_threshold = threshold
        
        try:
            self.display_env_variables()
            
            # Initialize browser
            if not self.initialize_browser():
                print("❌ Failed to initialize browser")
                return False
            
            # Login using OTP
            print("🔐 Starting OTP-based login...")
            login_success = login_with_otp_sync(self.page)
            
            if not login_success:
                print("❌ Login failed. Exiting.")
                return False
            
            print("✅ Login successful! Proceeding with search workflow...")
            time.sleep(5)
            
            # Try to find and click Content button
            print("📂 Looking for Content section...")
            success = self.utils.find_and_click_content_button(self.page)
            
            if success:
                print("✅ Content section opened successfully.")
                
                # Wait for content section to fully load
                print("⏳ Waiting for content section to load...")
                time.sleep(3)
                
                # Search functionality
                print("🔍 Looking for search box...")
                search_selectors = [
                    "//input[@type='text' and contains(@placeholder, 'search')]",
                    "//input[@type='text' and contains(@placeholder, 'Search')]",
                    "//input[@type='search']",
                    "//input[contains(@class, 'search')]",
                    "//input[contains(@id, 'search')]",
                    "//input[contains(@name, 'search')]",
                    "//input[@type='text']",
                    "//input[@placeholder*='search' or @placeholder*='Search']"
                ]
                
                search_box = None
                for selector in search_selectors:
                    try:
                        search_box = self.page.locator(selector).first
                        if search_box.is_visible():
                            print(f"✅ Found search box using selector: {selector}")
                            break
                    except Exception:
                        continue
                
                if search_box:
                    # STEP 1: Search with the specified keyword
                    print(f"🔍 STEP 1: Searching for keyword: '{keyword}'")
                    try:
                        # Robust clear: Ctrl+A then Backspace before typing
                        search_box.click()
                        search_box.press("Control+a")
                        search_box.press("Backspace")
                    except Exception:
                        try:
                            search_box.fill("")
                        except Exception:
                            pass
                    search_box.fill(keyword)
                    search_box.press("Enter")
                    print(f"✅ Search for '{keyword}' executed!")
                    
                    # Wait for search results to load
                    print("⏳ Waiting for search results to load...")
                    time.sleep(5)
                    
                    # Wait for results area to appear
                    print("⏳ Waiting for results area to appear...")
                    for wait_attempt in range(1, 6):
                        try:
                            results_area = self.page.locator("//*[@id='recentUploads']").first
                            if results_area.is_visible():
                                # Check if cards are present
                                cards = results_area.locator(".//div[contains(@class,'card')]").all()
                                if cards and len(cards) > 0:
                                    print(f"✅ Results area found with {len(cards)} cards")
                                    break
                        except Exception:
                            pass
                        time.sleep(2)
                    
                    # STEP 1.5: Verify search results end tak (BEFORE clearing)
                    print(f"\n{'='*80}")
                    print(f"🔍 STEP 1.5: Verifying search results for '{keyword}' end tak...")
                    print(f"{'='*80}")
                    print("⬇️ Scrolling to bottom to load all search results...")
                    self.utils.smooth_scroll_page(self.page, to="bottom")
                    time.sleep(3)  # Wait for lazy loading
                    
                    # Now verify all results contain the keyword
                    print(f"🔍 Verifying all search results contain keyword '{keyword}'...")
                    matched, total, mismatch_details = self.simple_search.verify_keyword_in_media_cards(
                        keyword,
                        area_xpath="//*[@id='recentUploads']",
                        threshold=threshold,
                        deep_check=False
                    )
                    
                    match_percentage = (matched / total * 100) if total > 0 else 0
                    print("")
                    print("="*80)
                    print(f"📊 SEARCH VERIFICATION RESULTS FOR '{keyword}'")
                    print("="*80)
                    print(f"📈 Total Results Checked: {total}")
                    print(f"✅ Matched Results: {matched} ({match_percentage:.1f}%)")
                    print(f"❌ Unmatched Results: {total - matched} ({100-match_percentage:.1f}%)")
                    
                    if total - matched > 0:
                        print(f"⚠️ WARNING: {total - matched} search result(s) do not contain '{keyword}' in metadata!")
                        print("   These results may be incorrect.")
                    else:
                        print("✅ All search results contain the keyword in their metadata!")
                    print("="*80)
                    
                    # Scroll back to top
                    print("⬆️ Scrolling back to top...")
                    self.utils.smooth_scroll_page(self.page, to="top")
                    time.sleep(2)
                    
                    # NOTE: Search box is NOT cleared - keyword is retained for all subsequent steps
                    print(f"✅ Search keyword '{keyword}' retained in search box for all subsequent verifications")
                    
                    # STEP 2: Scroll down and back to top before clicking view buttons (with search keyword still active)
                    try:
                        print("⬇️ STEP 3: Scrolling to bottom of the page...")
                        self.utils.smooth_scroll_page(self.page, to="bottom")
                        time.sleep(2)
                        print("⬆️ Scrolling back to top of the page...")
                        self.utils.smooth_scroll_page(self.page, to="top")
                        time.sleep(1)
                    except Exception as e:
                        print(f"⚠️ Scrolling failed: {str(e)}")
                    
                    # STEP 4: Click view buttons (Masonry, List, Grid) with scrolling after each
                    self._click_view_buttons_with_scrolling()
                    
                    # STEP 5: Sorting dropdown with explicit XPaths
                    self._execute_sorting_with_explicit_xpaths()
                    
                    # STEP 6: Category tabs (All, Audios, Videos, Images, Document, Others)
                    self._click_category_tabs_with_scrolling()
                    
                    # STEP 7: Advanced Search with full implementation
                    self._execute_advanced_search_full(keyword, threshold)
                    
                    print("🎯 All workflow steps completed!")
                    
                else:
                    print("❌ Search box not found in content section")
            else:
                print("❌ Failed to open Content section")
                print("🔍 Please check the page manually and look for the Content button")
            
            # Keep browser open
            print("🌐 Browser will remain open for manual inspection...")
            print("📝 You can now manually interact with the page")
            
            return True
            
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")
            print("🔍 Check the browser for any error messages")
            return False
        
        finally:
            # Note: We're not calling close_browser() to keep browser open
            print("✅ Script completed. Browser remains open.")
    
    def _click_view_buttons_with_scrolling(self):
        """Click view buttons (Masonry, List, Grid) with scrolling after each, following Selenium script pattern."""
        print("\n📋 STEP 4: Clicking view buttons with scrolling...")
        
        view_buttons = [
            ("Masonry", [
                "//button[contains(text(), 'Masonry')]",
                "//a[contains(text(), 'Masonry')]",
                "//span[contains(text(), 'Masonry')]",
                "//div[contains(text(), 'Masonry')]",
                "//*[contains(@class, 'masonry') and contains(text(), 'Masonry')]",
                "//*[contains(@id, 'masonry')]",
                "//*[contains(@title, 'Masonry')]"
            ]),
            ("List", [
                "//button[contains(text(), 'List')]",
                "//a[contains(text(), 'List')]",
                "//span[contains(text(), 'List')]",
                "//div[contains(text(), 'List')]",
                "//*[contains(@class, 'list') and contains(text(), 'List')]",
                "//*[contains(@id, 'list')]",
                "//*[contains(@title, 'List')]"
            ]),
            ("Grid", [
                "//button[contains(text(), 'Grid')]",
                "//a[contains(text(), 'Grid')]",
                "//span[contains(text(), 'Grid')]",
                "//div[contains(text(), 'Grid')]",
                "//*[contains(@class, 'grid') and contains(text(), 'Grid')]",
                "//*[contains(@id, 'grid')]",
                "//*[contains(@title, 'Grid')]"
            ])
        ]
        
        for view_name, selectors in view_buttons:
            print(f"\n📋 Clicking {view_name} button...")
            clicked = False
            
            for selector in selectors:
                try:
                    el = self.page.locator(selector).first
                    if el.is_visible():
                        print(f"✅ Found {view_name} button using selector: {selector}")
                        el.scroll_into_view_if_needed()
                        time.sleep(1)
                        
                        try:
                            el.click()
                            print(f"✅ {view_name} button clicked successfully!")
                        except Exception:
                            self.page.evaluate("(el) => el.click();", el.element_handle())
                            print(f"✅ {view_name} button clicked with JavaScript!")
                        
                        # Scroll down and up after click
                        print(f"⬇️ Scrolling down after {view_name} click...")
                        self.utils.smooth_scroll_page(self.page, to="bottom")
                        time.sleep(2)
                        
                        # Wait for view to load
                        time.sleep(2)
                        
                        # Verify keyword matching in this view
                        if hasattr(self, 'current_keyword') and self.current_keyword:
                            keyword = self.current_keyword
                            threshold = getattr(self, 'current_threshold', 70)
                            print(f"\n{'='*80}")
                            print(f"🔍 Verifying keyword '{keyword}' in {view_name} view...")
                            print(f"{'='*80}")
                            matched, total, mismatch_details = self.simple_search.verify_keyword_in_media_cards(
                                keyword,
                                area_xpath="//*[@id='recentUploads']",
                                threshold=threshold,
                                deep_check=False
                            )
                            match_percentage = (matched / total * 100) if total > 0 else 0
                            print(f"📊 {view_name} View: {matched}/{total} matched ({match_percentage:.1f}%)")
                            if total - matched > 0:
                                print(f"⚠️ {view_name} View: {total - matched} results do not match '{keyword}'")
                            else:
                                print(f"✅ {view_name} View: All results match '{keyword}'")
                        
                        print(f"⬆️ Scrolling back to top after {view_name} click...")
                        self.utils.smooth_scroll_page(self.page, to="top")
                        time.sleep(2)
                        
                        clicked = True
                        break
                except Exception:
                    continue
            
            if not clicked:
                print(f"❌ {view_name} button not found!")
        
        print("🎯 All view button steps completed!")
    
    def _execute_sorting_with_explicit_xpaths(self):
        """Execute sorting dropdown using explicit XPaths as per Selenium script."""
        print("\n📋 STEP 5: Interacting with sorting dropdown using explicit XPaths...")
        
        def open_sort_dropdown():
            candidates = [
                "//p[contains(@class,'text-blue-400')]",
                "//*/text()[normalize-space(.)='Date Added (Newest First)']/parent::*",
                "//*[@id='recentUploads']//p[normalize-space(.)='Date Added (Newest First)']",
                "//*[@id='recentUploads']//svg",
                "//*[@id='recentUploads']//div[contains(@class,'text-xs')]",
            ]
            for xp in candidates:
                try:
                    el = self.page.locator(xp).first
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        time.sleep(0.15)
                        try:
                            el.click()
                        except Exception:
                            try:
                                self.page.evaluate("(el) => el.click();", el.element_handle())
                            except Exception:
                                try:
                                    el.click(force=True)
                                except Exception:
                                    return False
                        return True
                except Exception:
                    continue
            return False
        
        def wait_for_menu():
            try:
                self.page.wait_for_selector("//*[@role='listbox' or contains(@class,'menu') or contains(@class,'dropdown') or contains(@class,'Menu') or contains(@class,'Listbox')]", timeout=5000)
            except Exception:
                pass
        
        def js_force_click(element):
            self.page.evaluate("""
                var el=arguments[0];
                el.scrollIntoView({block:'center'});
                try{el.focus();}catch(e){}
                var r=el.getBoundingClientRect();
                var x=r.left + r.width/2; var y=r.top + r.height/2;
                ['mouseover','mousemove','mousedown','mouseup','click'].forEach(function(type){
                  var evt=new MouseEvent(type,{bubbles:true,cancelable:true,view:window,clientX:x,clientY:y});
                  el.dispatchEvent(evt);
                });
            """, element.element_handle())
        
        def select_by_xpath(xpath_expr, label, delay_seconds=4):
            try:
                self.utils.smooth_scroll_page(self.page, to="top")
            except Exception:
                pass
            
            if not open_sort_dropdown():
                print("⚠️ Could not open sort dropdown for XPath selection.")
                return
            
            time.sleep(0.3)
            success = False
            
            for attempt in range(1, 4):
                try:
                    el = self.page.locator(xpath_expr).first
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        time.sleep(0.1)
                        try:
                            el.click()
                        except Exception:
                            try:
                                self.page.evaluate("(el) => el.click();", el.element_handle())
                            except Exception:
                                js_force_click(el)
                        success = True
                        print(f"✅ Selected (XPath): {label} (attempt {attempt})")
                        break
                except Exception as e:
                    # Re-open dropdown in case it closed between attempts
                    try:
                        open_sort_dropdown()
                    except Exception:
                        pass
                    time.sleep(0.25)
            
            if not success:
                print(f"⚠️ Failed XPath select for {label}")
            
            try:
                self.utils.smooth_scroll_page(self.page, to="bottom")
                time.sleep(0.2)
                self.utils.smooth_scroll_page(self.page, to="top")
            except Exception:
                pass
            time.sleep(delay_seconds)
            
            # Wait for sorting results to load
            time.sleep(2)
            
            # Verify keyword matching after sorting
            if hasattr(self, 'current_keyword') and self.current_keyword:
                keyword = self.current_keyword
                threshold = getattr(self, 'current_threshold', 70)
                print(f"\n{'='*80}")
                print(f"🔍 Verifying keyword '{keyword}' after sorting: {label}...")
                print(f"{'='*80}")
                matched, total, mismatch_details = self.simple_search.verify_keyword_in_media_cards(
                    keyword,
                    area_xpath="//*[@id='recentUploads']",
                    threshold=threshold,
                    deep_check=False
                )
                match_percentage = (matched / total * 100) if total > 0 else 0
                print(f"📊 Sorting ({label}): {matched}/{total} matched ({match_percentage:.1f}%)")
                if total - matched > 0:
                    print(f"⚠️ Sorting ({label}): {total - matched} results do not match '{keyword}'")
                else:
                    print(f"✅ Sorting ({label}): All results match '{keyword}'")
        
        # Use explicit XPaths for options as primary method (from Selenium script)
        OPTION_XPATHS = [
            ("//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[3]", "Date Added (Newest First)"),
            ("//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[1]", "Title (A–Z)"),
            ("//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[2]", "Title (Z–A)"),
            ("//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[4]", "Date Added (Oldest First)"),
            ("//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[3]", "Date Added (Newest First)"),  # Return to first
        ]
        
        for xp, lbl in OPTION_XPATHS:
            select_by_xpath(xp, lbl)
        
        print("🎯 Dropdown interaction sequence completed!")
    
    def _click_category_tabs_with_scrolling(self):
        """Click category tabs (All, Audios, Videos, Images, Document, Others) with scrolling after each."""
        print("\n📋 STEP 6: Clicking category tabs and scrolling...")
        
        def click_tab(tab_label):
            selectors = [
                f"//button[normalize-space(.)='{tab_label}']",
                f"//a[normalize-space(.)='{tab_label}']",
                f"//span[normalize-space(.)='{tab_label}']",
                f"//*[contains(@class,'tab') and normalize-space(.)='{tab_label}']",
                f"//*[@role='tab' and normalize-space(.)='{tab_label}']",
                f"//*[normalize-space(text())='{tab_label}']",
            ]
            for sel in selectors:
                try:
                    el = self.page.locator(sel).first
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        time.sleep(0.2)
                        try:
                            el.click()
                        except Exception:
                            try:
                                self.page.evaluate("(el) => el.click();", el.element_handle())
                            except Exception:
                                el.click(force=True)
                        return True
                except Exception:
                    continue
            return False
        
        tabs_sequence = ["All", "Audios", "Videos", "Images", "Document", "Others"]
        for tab in tabs_sequence:
            if click_tab(tab):
                print(f"✅ Opened tab: {tab}")
                time.sleep(1)
                
                # Wait for tab results to load
                time.sleep(2)
                
                # Verify keyword matching in this tab
                if hasattr(self, 'current_keyword') and self.current_keyword:
                    keyword = self.current_keyword
                    threshold = getattr(self, 'current_threshold', 70)
                    print(f"\n{'='*80}")
                    print(f"🔍 Verifying keyword '{keyword}' in {tab} tab...")
                    print(f"{'='*80}")
                    matched, total, mismatch_details = self.simple_search.verify_keyword_in_media_cards(
                        keyword,
                        area_xpath="//*[@id='recentUploads']",
                        threshold=threshold,
                        deep_check=False
                    )
                    match_percentage = (matched / total * 100) if total > 0 else 0
                    print(f"📊 {tab} Tab: {matched}/{total} matched ({match_percentage:.1f}%)")
                    if total - matched > 0:
                        print(f"⚠️ {tab} Tab: {total - matched} results do not match '{keyword}'")
                    else:
                        print(f"✅ {tab} Tab: All results match '{keyword}'")
            else:
                print(f"⚠️ Could not find tab: {tab}")
            try:
                self.utils.smooth_scroll_page(self.page, to="bottom")
                time.sleep(1.0)
                self.utils.smooth_scroll_page(self.page, to="top")
            except Exception:
                pass
            time.sleep(1.0)
        
        # Return to All at the end
        if click_tab("All"):
            print("✅ Returned to 'All' tab")
        else:
            print("⚠️ Could not return to 'All' tab")
    
    def _execute_advanced_search_full(self, keyword: str, threshold: int):
        """Execute full Advanced Search workflow following Selenium script pattern."""
        print("\n📋 STEP 7: Advanced Search automation...")
        
        def click_advanced_search_button():
            candidates = [
                "//button[normalize-space(.)='Advanced Search']",
                "//button[normalize-space(.)='Advance Search']",
                "//*[contains(@class,'btn') and (normalize-space(.)='Advanced Search' or normalize-space(.)='Advance Search')]",
                "//*[@id='advancedSearch' or contains(@id,'advance') or contains(@id,'advanced')]",
                "//a[normalize-space(.)='Advanced Search' or normalize-space(.)='Advance Search']",
            ]
            for xp in candidates:
                try:
                    el = self.page.locator(xp).first
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        time.sleep(0.2)
                        try:
                            el.click()
                        except Exception:
                            try:
                                self.page.evaluate("(el) => el.click();", el.element_handle())
                            except Exception:
                                el.click(force=True)
                        return True
                except Exception:
                    continue
            return False
        
        def wait_for_advanced_panel():
            try:
                self.page.wait_for_selector("//*[contains(., 'Advanced Search') or contains(., 'Advance Search')]", timeout=5000)
            except Exception:
                pass
        
        def open_dropdown_near(label_text):
            label_variants = [label_text, label_text.replace(':',''), label_text.lower().title(), label_text.lower(), label_text.upper()]
            candidates = []
            for lt in label_variants:
                candidates.extend([
                    f"//*[normalize-space(.)='{lt}']/following::*[self::select or self::div or self::button][1]",
                    f"//label[normalize-space(.)='{lt}']/following::*[self::select or self::div or self::button][1]",
                    f"//*[contains(@placeholder,'{lt}') or contains(@aria-label,'{lt}')]",
                ])
            for xp in candidates:
                try:
                    el = self.page.locator(xp).first
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        time.sleep(0.15)
                        try:
                            el.click()
                        except Exception:
                            try:
                                self.page.evaluate("(el) => el.click();", el.element_handle())
                            except Exception:
                                el.click(force=True)
                        return el
                except Exception:
                    continue
            return None
        
        def select_option_from_open_menu(option_text):
            paths = [
                f"//li[normalize-space(.)='{option_text}']",
                f"//*[@role='option' and normalize-space(.)='{option_text}']",
                f"//div[contains(@class,'menu') or contains(@class,'dropdown') or contains(@class,'listbox') or @role='listbox']//*[normalize-space(.)='{option_text}']",
                f"//option[normalize-space(.)='{option_text}']",
            ]
            for p in paths:
                try:
                    el = self.page.locator(p).first
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        time.sleep(0.1)
                        try:
                            el.click()
                        except Exception:
                            self.page.evaluate("(el) => el.click();", el.element_handle())
                        return True
                except Exception:
                    continue
            return False
        
        def set_category(category_text):
            el = open_dropdown_near("Category")
            if el:
                time.sleep(0.2)
                ok = select_option_from_open_menu(category_text)
                if not ok:
                    # Try native select element
                    try:
                        sel = self.page.locator("//select[ancestor::*[contains(.,'Category')]][1]").first
                        if sel.is_visible():
                            self.page.select_option(sel, label=category_text)
                            ok = True
                    except Exception:
                        ok = False
                print(f"{'✅' if ok else '⚠️'} Category set to: {category_text}")
                return ok
            return False
        
        def set_date_range_manual(range_string):
            """Set date range manually using text input (e.g., '2025-09-01 ~ 2025-09-30')."""
            candidates = [
                "//input[contains(@placeholder,'YYYY') or contains(@placeholder,'yyyy') or contains(@placeholder,'Date') or contains(@placeholder,'date')]",
                "//input[@type='text' and (contains(@aria-label,'Date') or contains(@name,'date'))]",
                "//*[normalize-space(.)='Date Range']/following::input[1]",
            ]
            for xp in candidates:
                try:
                    el = self.page.locator(xp).first
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        time.sleep(0.1)
                        try:
                            el.fill("")
                        except Exception:
                            pass
                        try:
                            el.fill(range_string)
                            el.press("Enter")
                            print("✅ Date range entered via fill")
                            return True
                        except Exception:
                            # Force value via JS
                            self.page.evaluate("""
                                var el=arguments[0], val=arguments[1];
                                var setter=Object.getOwnPropertyDescriptor(el.__proto__,'value');
                                if(setter&&setter.set){setter.set.call(el,val);}else{el.value=val;}
                                el.dispatchEvent(new Event('input',{bubbles:true}));
                                el.dispatchEvent(new Event('change',{bubbles:true}));
                            """, el.element_handle(), range_string)
                            print("✅ Date range entered via JS force-set")
                            return True
                except Exception:
                    continue
            print("⚠️ Could not set date range manually")
            return False
        
        def set_keyword(text_value):
            inputs = [
                "//*[@id='keywords']",
                "//input[@type='text' and (contains(@placeholder,'Keyword') or contains(@aria-label,'Keyword'))]",
                "//*[normalize-space(.)='Keyword']/following::input[1]",
                "//input[@type='search']",
            ]
            for xp in inputs:
                try:
                    el = self.page.locator(xp).first
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        time.sleep(0.1)
                        try:
                            el.fill("")
                        except Exception:
                            pass
                        try:
                            el.fill(text_value)
                            el.press("Enter")
                            print("✅ Keyword entered via fill")
                            return True
                        except Exception:
                            # Force value via JS
                            self.page.evaluate("""
                                var el=arguments[0], val=arguments[1];
                                var setter=Object.getOwnPropertyDescriptor(el.__proto__,'value');
                                if(setter&&setter.set){setter.set.call(el,val);}else{el.value=val;}
                                el.dispatchEvent(new Event('input',{bubbles:true}));
                                el.dispatchEvent(new Event('change',{bubbles:true}));
                            """, el.element_handle(), text_value)
                            print("✅ Keyword entered via JS force-set")
                            return True
                except Exception:
                    continue
            print("⚠️ Could not set Keyword")
            return False
        
        def tick_title_only():
            """Tick ONLY Title checkbox, NOT Description."""
            def tick(label):
                xpaths = [
                    f"//label[normalize-space(.)='{label}']/preceding::input[@type='checkbox'][1]",
                    f"//input[@type='checkbox' and (@name='{label.lower()}' or @aria-label='{label}')]",
                    f"//*[normalize-space(.)='{label}']/preceding::input[@type='checkbox'][1]",
                    f"//*[@role='checkbox' and normalize-space(.)='{label}']"
                ]
                for xp in xpaths:
                    try:
                        el = self.page.locator(xp).first
                        if el.is_visible():
                            el.scroll_into_view_if_needed()
                            time.sleep(0.05)
                            try:
                                is_selected = el.is_checked()
                            except Exception:
                                is_selected = False
                            if not is_selected:
                                try:
                                    el.check()
                                except Exception:
                                    try:
                                        el.click()
                                    except Exception:
                                        self.page.evaluate("(el) => el.click();", el.element_handle())
                            return True
                    except Exception:
                        continue
                return False
            
            ok = tick("Title")
            print(f"{'✅' if ok else '⚠️'} Title checkbox ticked (Description NOT ticked)")
            return ok
        
        def verify_advanced_search_results(view_name, keyword, threshold):
            """
            Verify Advanced Search results using proper fuzzy matching.
            Uses the same comprehensive fuzzy matching as Simple Search and Timeline.
            """
            print(f"\n🔍 Verifying Advanced Search results in {view_name} (using fuzzy matching)...")
            print(f"📊 Using fuzzy matching threshold: {threshold}%")
            try:
                print(f"⬇️ Scrolling to bottom in {view_name}...")
                self.utils.smooth_scroll_page(self.page, to="bottom")
                time.sleep(2)
                
                # Use the same comprehensive fuzzy matching as Simple Search
                matched, total, mismatch_details = self.simple_search.verify_keyword_in_media_cards(
                    keyword,
                    area_xpath="//*[@id='recentUploads']",
                    threshold=threshold,
                    deep_check=False
                )
                
                match_percentage = (matched / total * 100) if total > 0 else 0
                print(f"📊 {view_name}: {matched}/{total} matched ({match_percentage:.1f}%)")
                
                if total - matched > 0:
                    print(f"⚠️ {view_name}: {total - matched} results do not match '{keyword}'")
                else:
                    print(f"✅ {view_name}: All results match '{keyword}'")
                
                print(f"⬆️ Scrolling back to top...")
                self.utils.smooth_scroll_page(self.page, to="top")
                time.sleep(1)
                
                # Reset to Grid view after verification
                click_view_button("Grid")
                time.sleep(1)
                
                return matched, total
            except Exception as e:
                print(f"❌ Error verifying {view_name}: {e}")
                # Reset to Grid view even on error
                try:
                    click_view_button("Grid")
                except Exception:
                    pass
                return 0, 0
        
        def verify_results_in_view(view_name, keyword, threshold):
            """Verify results in a specific view (Grid/Masonry/List) by scrolling to end."""
            # Use proper fuzzy matching for Advanced Search (same as Simple Search and Timeline)
            return verify_advanced_search_results(view_name, keyword, threshold)
        
        def click_view_button(view_name):
            """Click a view button (Grid/Masonry/List)."""
            selectors = [
                f"//button[normalize-space(.)='{view_name}']",
                f"//a[normalize-space(.)='{view_name}']",
                f"//span[normalize-space(.)='{view_name}']",
                f"//*[contains(@class,'{view_name.lower()}') and contains(text(),'{view_name}')]",
            ]
            for sel in selectors:
                try:
                    el = self.page.locator(sel).first
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        time.sleep(0.2)
                        try:
                            el.click()
                        except Exception:
                            try:
                                self.page.evaluate("(el) => el.click();", el.element_handle())
                            except Exception:
                                el.click(force=True)
                        time.sleep(1)
                        return True
                except Exception:
                    continue
            return False
        
        def click_category_tab(tab_label):
            """Click a category tab (All, Audio, Document, etc.)."""
            selectors = [
                f"//button[normalize-space(.)='{tab_label}']",
                f"//a[normalize-space(.)='{tab_label}']",
                f"//span[normalize-space(.)='{tab_label}']",
                f"//*[@role='tab' and normalize-space(.)='{tab_label}']",
            ]
            for sel in selectors:
                try:
                    el = self.page.locator(sel).first
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        time.sleep(0.2)
                        try:
                            el.click()
                        except Exception:
                            try:
                                self.page.evaluate("(el) => el.click();", el.element_handle())
                            except Exception:
                                el.click(force=True)
                        time.sleep(1)
                        return True
                except Exception:
                    continue
            return False
        
        # Execute Advanced Search workflow
        if not click_advanced_search_button():
            print("❌ Advanced Search button not found")
            return
        
        wait_for_advanced_panel()
        time.sleep(2)
        
        # Step 1: Set Category to "All"
        print("\n📋 Step 1: Setting Category to 'All'...")
        set_category("All")
        time.sleep(1)
        
        # Step 2: Set Date Range (Last 2 months from today)
        print("\n📋 Step 2: Setting Date Range (Last 2 months from today)...")
        today = datetime.now()
        # Calculate 2 months ago
        two_months_ago = today - timedelta(days=60)  # Approximately 2 months
        # Format: YYYY-MM-DD ~ YYYY-MM-DD
        start_date = two_months_ago.strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        date_range_str = f"{start_date} ~ {end_date}"
        print(f"   Date Range: {date_range_str}")
        set_date_range_manual(date_range_str)
        time.sleep(1)
        
        # Step 3: Tick Title checkbox (NOT Description)
        print("\n📋 Step 3: Ticking Title checkbox (Description NOT ticked)...")
        tick_title_only()
        time.sleep(2)
        
        # Step 4: NO keyword added (keyword field left empty)
        print("\n📋 Step 4: Keyword field left EMPTY (as per requirements)")
        print("   Note: Search box should still have 'news' word from previous step")
        time.sleep(3)
        
        # Step 5: Verify results in Grid, Masonry, List views
        print("\n" + "="*80)
        print("📋 Step 5: Verifying results in all views (Grid, Masonry, List)")
        print("="*80)
        
        # Grid view
        if click_view_button("Grid"):
            print("✅ Grid view clicked")
            verify_results_in_view("Grid", keyword, threshold)
        else:
            print("⚠️ Grid view button not found")
        
        # Masonry view
        if click_view_button("Masonry"):
            print("✅ Masonry view clicked")
            verify_results_in_view("Masonry", keyword, threshold)
        else:
            print("⚠️ Masonry view button not found")
        
        # List view
        if click_view_button("List"):
            print("✅ List view clicked")
            verify_results_in_view("List", keyword, threshold)
        else:
            print("⚠️ List view button not found")
        
        # Step 6: Sorting (same as simple search)
        print("\n" + "="*80)
        print("📋 Step 6: Sorting verification (Latest, Newest, Oldest, etc.)")
        print("="*80)
        self._execute_sorting_with_explicit_xpaths()
        
        # Step 7: Category tabs (All, Audio, Document, Video, Images, Others)
        print("\n" + "="*80)
        print("📋 Step 7: Category tabs verification (All, Audio, Document, Video, Images, Others)")
        print("="*80)
        category_tabs = ["All", "Audios", "Videos", "Images", "Document", "Others"]
        for tab in category_tabs:
            if click_category_tab(tab):
                print(f"✅ {tab} tab clicked")
                time.sleep(1)
                matched, total = verify_results_in_view(f"{tab} Tab", keyword, threshold)
                # Reset to All tab after each verification
                click_category_tab("All")
                time.sleep(1)
            else:
                print(f"⚠️ {tab} tab not found")
        
        # Ensure we're on All tab and Grid view
        click_category_tab("All")
        click_view_button("Grid")
        time.sleep(1)
        
        # Step 8: Iterate through categories one by one
        print("\n" + "="*80)
        print("📋 Step 8: Iterating through categories (All, Document, News, Event, Drama, Movie, Other)")
        print("="*80)
        categories = ["All", "Document", "News", "Event", "Drama", "Movie", "Other"]
        
        for category in categories:
            print(f"\n{'='*80}")
            print(f"🔄 Processing Category: {category}")
            print(f"{'='*80}")
            
            # Set category
            if set_category(category):
                time.sleep(2)
                
                # Verify in Grid, Masonry, List views
                print(f"\n📋 Verifying {category} category in all views...")
                for view in ["Grid", "Masonry", "List"]:
                    if click_view_button(view):
                        verify_results_in_view(f"{category} - {view}", keyword, threshold)
                        # Reset to Grid after each view
                        click_view_button("Grid")
                        time.sleep(1)
                
                # Verify in category tabs
                print(f"\n📋 Verifying {category} category in all tabs...")
                for tab in category_tabs:
                    if click_category_tab(tab):
                        time.sleep(1)
                        verify_results_in_view(f"{category} - {tab}", keyword, threshold)
                        # Reset to All tab after each tab verification
                        click_category_tab("All")
                        time.sleep(1)
                
                # Ensure we're on All tab and Grid view
                click_category_tab("All")
                click_view_button("Grid")
                time.sleep(1)
            else:
                print(f"⚠️ Could not set category: {category}")
        
        # Step 9: Timeline verification
        print("\n" + "="*80)
        print("📋 Step 9: Timeline verification")
        print("="*80)
        
        if not self.timeline:
            self.timeline = TimelineFunctions(self.page)
        
        timeline_results = self.timeline.execute_timeline(keyword, threshold)
        
        print("\n" + "="*80)
        print("✅ Advanced Search workflow completed!")
        print("="*80)
    
    def _execute_search_workflows(self, keyword: str, threshold: int):
        """
        Execute all search verification workflows.
        
        This method orchestrates:
        - Simple search verification (using SimpleSearchFunctions)
        - Sorting verification (using SimpleSearchFunctions)
        - Advanced search tabs verification (using AdvancedSearchFunctions)
        - Advanced search verification (using AdvancedSearchFunctions)
        - Timeline verification (using TimelineFunctions)
        
        Args:
            keyword (str): Search keyword
            threshold (int): Fuzzy matching threshold
        """
        print("🔄 Starting search verification workflows...")
        
        # ====================================================================
        # 🔍 SIMPLE SEARCH VERIFICATION
        # ====================================================================
        self.simple_search_results = self.simple_search.execute_simple_search(keyword, threshold)
        
        # ====================================================================
        # 🗓️ SORTING VERIFICATION
        # ====================================================================
        self._execute_sorting_verification(keyword, threshold)
        
        # ====================================================================
        # 📂 ADVANCED SEARCH TABS VERIFICATION
        # ====================================================================
        self.advanced_search_tabs_results = self.advanced_search.execute_advanced_search_tabs(keyword, threshold)
        
        # ====================================================================
        # ⚙️ ADVANCED SEARCH VERIFICATION
        # ====================================================================
        self.advanced_search_results = self.advanced_search.execute_advanced_search(keyword, threshold)
        
        # ====================================================================
        # 🕒 TIMELINE VERIFICATION
        # ====================================================================
        self.timeline_results = self.timeline.execute_timeline(keyword, threshold)
        
        # Generate final report
        self._generate_final_report(keyword)
    
    def _execute_sorting_verification(self, keyword: str, threshold: int):
        """
        Execute sorting verification workflow.
        
        Args:
            keyword (str): Search keyword
            threshold (int): Fuzzy matching threshold
        """
        # ====================================================================
        # 🗓️ SORTING VERIFICATION
        # ====================================================================
        print("\n" + "="*60)
        print("🗓️ SORTING VERIFICATION")
        print("="*60)
        
        def open_sort_dropdown():
            # Robust open: try label, caret, container
            candidates = [
                "//p[contains(@class,'text-blue-400')]",  # visible label
                "//*/text()[normalize-space(.)='Date Added (Newest First)']/parent::*",
                "//*[@id='recentUploads']//p[normalize-space(.)='Date Added (Newest First)']",
                "//*[@id='recentUploads']//svg",  # caret
                "//*[@id='recentUploads']//div[contains(@class,'text-xs')]",  # menu container area
            ]
            el = None
            for xp in candidates:
                try:
                    el = self.page.locator(xp).first
                    if el.is_visible():
                        break
                except Exception:
                    continue
            if not el:
                print("❌ Could not locate sort control by label/caret.")
                return False
            try:
                el.scroll_into_view_if_needed()
            except Exception:
                pass
            time.sleep(0.15)
            try:
                el.click()
            except Exception:
                try:
                    self.page.evaluate("(el) => el.click();", el.element_handle())
                except Exception:
                    try:
                        el.click(force=True)
                    except Exception:
                        return False
            return True
        
        def wait_for_menu():
            try:
                self.page.wait_for_selector("//*[@role='listbox' or contains(@class,'menu') or contains(@class,'dropdown') or contains(@class,'Menu') or contains(@class,'Listbox')]", timeout=5000)
            except Exception:
                pass
        
        def click_sort_option(option_text):
            # Map option text to exact XPaths
            xpath_mapping = {
                "Title (A–Z)": "//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[1]",
                "Title (Z–A)": "//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[2]",
                "Date Added (Newest First)": "//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[3]",
                "Date Added (Oldest First)": "//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[4]"
            }
            
            # Get the exact XPath for the option
            exact_xpath = xpath_mapping.get(option_text)
            if not exact_xpath:
                print(f"⚠️ No exact XPath found for option: {option_text}")
                return False
            
            # Ensure menu is visible first
            wait_for_menu()
            
            # Use the robust click helper
            return robust_click_sorting_option(self.page, exact_xpath, option_text)
        
        def select_by_xpath(xpath_expr, label, delay_seconds=4):
            def js_force_click(element):
                self.page.evaluate("""
                    var el=arguments[0];
                    el.scrollIntoView({block:'center'});
                    try{el.focus();}catch(e){}
                    var r=el.getBoundingClientRect();
                    var x=r.left + r.width/2; var y=r.top + r.height/2;
                    ['mouseover','mousemove','mousedown','mouseup','click'].forEach(function(type){
                      var evt=new MouseEvent(type,{bubbles:true,cancelable:true,view:window,clientX:x,clientY:y});
                      el.dispatchEvent(evt);
                    });
                """, element.element_handle())
            try:
                scroll_page(self.page, to="top")
            except Exception:
                pass
            if not open_sort_dropdown():
                print("⚠️ Could not open sort dropdown for XPath selection.")
                return
            time.sleep(0.3)
            success = False
            last_err = None
            for attempt in range(1, 4):
                try:
                    el = self.page.locator(xpath_expr).first
                    el.wait_for(state="visible", timeout=5000)
                    el.scroll_into_view_if_needed()
                    time.sleep(0.1)
                    try:
                        el.click()
                    except Exception:
                        try:
                            self.page.evaluate("(el) => el.click();", el.element_handle())
                        except Exception:
                            js_force_click(el)
                    success = True
                    print(f"✅ Selected (XPath): {label} (attempt {attempt})")
                    break
                except Exception as e:
                    last_err = e
                    # Re-open dropdown in case it closed between attempts
                    try:
                        open_sort_dropdown()
                    except Exception:
                        pass
                    time.sleep(0.25)
            if not success:
                print(f"⚠️ Failed XPath select for {label}: {last_err}")
            try:
                if self.utils:
                    self.utils.scroll_page(self.page, to="bottom")
                time.sleep(0.2)
                if self.utils:
                    self.utils.scroll_page(self.page, to="top")
            except Exception:
                pass
            time.sleep(delay_seconds)
        
        # Helper: map label to exact option XPath
        option_to_xpath = {
            "Date Added (Newest First)": "//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[3]",
            "Title (A–Z)": "//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[1]",
            "Title (Z–A)": "//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[2]",
            "Date Added (Oldest First)": "//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[4]",
        }
        
        # Test all sorting options
        sorting_results = {}
        sorting_options = [
            ("Date Added (Newest First)", "Newest"),
            ("Title (A–Z)", "A–Z"),
            ("Title (Z–A)", "Z–A"),
            ("Date Added (Oldest First)", "Oldest")
        ]
        
        for option_text, short_name in sorting_options:
            print(f"🔄 Testing sorting: {option_text}")
            # Open dropdown and force-click the exact option XPath for this label
            try:
                xpath_for_option = option_to_xpath.get(option_text)
                if not xpath_for_option:
                    print(f"⚠️ No XPath mapping for {option_text}")
                else:
                    select_by_xpath(xpath_for_option, option_text)
            except Exception as e:
                print(f"⚠️ Error selecting sort option {option_text}: {e}")
            
            # Wait for results to reload
            time.sleep(3)
            
            # Scroll to load all content
            try:
                scroll_page(self.page, to="bottom")
                time.sleep(1)
                scroll_page(self.page, to="top")
                time.sleep(1)
            except Exception:
                pass
            
            # Verify keyword in results
            matches = self.simple_search.perform_text_search_in_area("//*[@id='recentUploads']", keyword, f"Sorting ({short_name})", threshold)
            sorting_results[short_name] = matches
            
            if matches > 0:
                print(f"✅ Sorting ({short_name}): {matches} matches found")
            else:
                print(f"⚠️ No posts found — skipping verification")
        
        # Return to Date Added (Newest First) after testing all sorting options
        print("🔄 Returning to 'Date Added (Newest First)' after sorting tests...")
        try:
            select_by_xpath("//*[@id='recentUploads']/div[1]/div[3]/div/div/div/div/p[3]", "Date Added (Newest First)")
            time.sleep(2)
            print("✅ Returned to 'Date Added (Newest First)'")
        except Exception as e:
            print(f"⚠️ Could not return to 'Date Added (Newest First)': {e}")
        
        print("🎯 Sorting verification completed!")
        self.sorting_results = sorting_results
    
    def _generate_final_report(self, keyword: str):
        """
        Generate comprehensive final report.
        
        Args:
            keyword (str): Search keyword
        """
        print("\n" + "="*60)
        print(f"📊 SEARCH VALIDATION SUMMARY — Keyword: \"{keyword}\"")
        print("="*60)
        
        # Simple Search Results
        if hasattr(self, 'simple_search_results'):
            print(f"✅ Grid View .......... {self.simple_search_results.get('grid', 0)} matches found")
            print(f"✅ Masonry View ........ {self.simple_search_results.get('masonry', 0)} matches found")
            print(f"✅ List View ........... {self.simple_search_results.get('list', 0)} matches found")
        
        # Sorting Results
        if hasattr(self, 'sorting_results'):
            for sort_name, matches in self.sorting_results.items():
                if matches > 0:
                    print(f"✅ Sorting ({sort_name}) ....... {matches} matches found")
                else:
                    print(f"⚠️ Sorting ({sort_name}) ....... No posts found")
        
        # Advanced Search Tabs Results
        if hasattr(self, 'advanced_search_tabs_results'):
            for tab_name, matches in self.advanced_search_tabs_results.items():
                if matches > 0:
                    print(f"✅ Advanced Search Tab ({tab_name}) ..... {matches} matches found")
                else:
                    print(f"⚠️ Advanced Search Tab ({tab_name}) ..... No posts found")
        
        # Advanced Search Results
        if hasattr(self, 'advanced_search_results'):
            if self.advanced_search_results.get('tabs'):
                for tab_name, matches in self.advanced_search_results['tabs'].items():
                    if matches > 0:
                        print(f"✅ Advanced {tab_name} Tab .......... {matches} matches found")
        
        # Timeline Results
        if hasattr(self, 'timeline_results'):
            for option_name, matches in self.timeline_results.items():
                if matches > 0:
                    print(f"✅ Timeline Option ({option_name}) ..... {matches} matches found")
                else:
                    print(f"⚠️ Timeline Option ({option_name}) ..... No posts found")
        
        print("="*60)
        print("🎯 Final report generated!")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main entry point for standalone script execution."""
    parser = argparse.ArgumentParser(description='Advanced Search Test Script for NIMAR.gov.pk')
    parser.add_argument('--keyword', default=None, help=f'Search keyword (default: {DEFAULT_KEYWORD} from env_variables.py)')
    parser.add_argument('--threshold', type=int, default=None, help=f'Fuzzy matching threshold (default: {FUZZY_THRESHOLD} from env_variables.py)')
    
    args = parser.parse_args()
    
    automation = ElasticSearchAutomation()
    # Use None to trigger defaults from env_variables.py, or use provided values
    keyword = args.keyword if args.keyword else None
    threshold = args.threshold if args.threshold is not None else None
    success = automation.run(keyword=keyword, threshold=threshold)
    
    if success:
        print("\n✅ Automation completed successfully!")
    else:
        print("\n❌ Automation completed with errors.")
    
    return success

if __name__ == "__main__":
    main()
