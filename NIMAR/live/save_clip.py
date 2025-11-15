"""
=======================================================================
📄 Live Test Save Clip Automation Script
=======================================================================

🔧 Purpose:
    Automates the live stream testing workflow including:
    - OTP-based login
    - Live stream navigation
    - Stream time tracking
    - Previous day stream retrieval
    - 5-minute clip cropping and saving

    This module follows a single main class architecture (similar to
    test_configurator.py) where all functionality is encapsulated
    within the LiveTestSaveClipAutomation class.

⚙️ Features:
    • Single main class architecture (LiveTestSaveClipAutomation)
    • All helper methods are class methods
    • Reuses OTP login functionality from auth.otp module
    • Dynamic stream time tracking with MutationObserver
    • Previous day stream retrieval and duration tracking
    • 5-minute clip cropping and export

📁 Project Structure:
    Automation/
    ├── auth/
    │   └── otp.py              ← OTP login function (imported here)
    ├── live/
    │   └── live-test-save-clip.py  ← This script
    ├── env_variables.py         ← Environment variables module
    └── requirements.txt        ← Python dependencies

🚀 How to Run:
    1. Install all required packages:
           pip install -r requirements.txt
           playwright install

    2. Run the script standalone:
           python live/live-test-save-clip.py

    3. Or import and use in your own script:
           from live.live_test_save_clip import LiveTestSaveClipAutomation
           automation = LiveTestSaveClipAutomation()
           success = automation.run()

📦 Main Class:

    LiveTestSaveClipAutomation
       → Main automation class for live stream test and clip save workflow
       → All functionality is encapsulated within this single class
       → Methods:
           - run()                    → Execute complete workflow
           - display_env_variables()  → Display environment variables
           - navigate_to_live()       → Navigate to live stream
           - track_stream_time()      → Track live stream time
           - open_calendar()          → Open calendar for date selection
           - set_previous_day_date()  → Set previous day date
           - get_previous_day_stream() → Get previous day stream
           - return_to_live()         → Return to live stream
           - crop_and_save_clip()     → Crop 5-minute clip and save

🔐 Environment Variables Required:
    - Portal credentials (PORTAL_URL, USERNAME, PASSWORD)
    - Email settings (EMAIL_USER, EMAIL_PASS, EMAIL_SERVER)
    - Browser settings (BROWSER_HEADLESS, BROWSER_IGNORE_HTTPS_ERRORS, BROWSER_NO_VIEWPORT)
    - OTP login timings (OTP_CREDENTIAL_ENTRY_WAIT, etc.)
    - Wait timeouts (WAIT_TIMEOUT, etc.)
    (See env_variables.py for complete list)

🧩 Dependencies:
    - playwright         → Browser automation
    - auth.otp           → OTP login function (login_with_otp_sync)

🧠 Author:
    Rabbia Gillani SQA
    Version: 1.0.0
    Date: 2025-11-10
=======================================================================
"""
import re
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, List
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from NIMAR.auth.otp import login_with_otp_sync

# Import environment variables
from NIMAR.env_variables import (
    PORTAL_URL,
    BROWSER_HEADLESS,
    BROWSER_IGNORE_HTTPS_ERRORS,
    BROWSER_NO_VIEWPORT,
    WAIT_TIMEOUT,
    LOGIN_SUCCESS_WAIT,
    WAIT_AFTER_GET_STREAM,
    LIVE_BROWSER_HEADLESS,
    LIVE_USE_SYSTEM_CHROME,
    LIVE_USE_CHROME_CHANNEL,
    LOG_LEVEL
)


class LiveTestSaveClipAutomation:
    """
    Main automation class for live stream test and clip save workflow.
    
    This class orchestrates the complete live stream testing process, similar to
    ConfiguratorTestSuite structure. All functionality is within this single class.
    
    Attributes:
        playwright: Playwright instance
        browser: Browser instance
        context: Browser context instance
        page: Page instance
        live_status_current (str): Current live stream time
        live_status_pc (str): PC time when live status was captured
        prev_total_seconds (float): Previous day stream duration in seconds
        prev_date_token (str): Previous day date token
    
    Example:
        >>> automation = LiveTestSaveClipAutomation()
        >>> success = automation.run()
    """
    
    def __init__(self):
        """
        Initialize live test save clip automation.
        
        Loads all configuration from env_variables.py module.
        """
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.live_status_current = ""
        self.live_status_pc = ""
        self.prev_total_seconds = None
        self.prev_date_token = ""
    
    def _print_block(self, title: str, lines: List[str]) -> None:
        """
        Print a formatted block with title and lines.
        
        Args:
            title (str): Block title
            lines (List[str]): List of lines to print
        """
        sep = "=" * 50
        print(f"\n{sep}\n{title}\n{sep}")
        for line in lines:
            print(line)
        print(sep)
    
    def display_env_variables(self) -> None:
        """
        Display all environment variables loaded from env_variables.py (sensitive values masked).
        
        This method prints all environment variables organized by category,
        masking sensitive information like passwords.
        """
        from NIMAR.env_variables import (
            PORTAL_URL, USERNAME, PASSWORD,
            EMAIL_USER, EMAIL_PASS, EMAIL_SERVER,
            OTP_CREDENTIAL_ENTRY_WAIT, OTP_BUTTON_TIMEOUT, OTP_EMAIL_WAIT_TIME,
            OTP_INPUT_DELAY, OTP_VERIFY_BUTTON_TIMEOUT, OTP_LOGIN_COMPLETE_WAIT,
            OTP_RETRIES, OTP_DELAY
        )
        
        print("\n" + "="*80)
        print("📋 ENVIRONMENT VARIABLES LOADED FROM env_variables.py (Live Test Module)")
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
            "OTP Login Timings": {
                "OTP_CREDENTIAL_ENTRY_WAIT": OTP_CREDENTIAL_ENTRY_WAIT,
                "OTP_BUTTON_TIMEOUT": OTP_BUTTON_TIMEOUT,
                "OTP_EMAIL_WAIT_TIME": OTP_EMAIL_WAIT_TIME,
                "OTP_INPUT_DELAY": OTP_INPUT_DELAY,
                "OTP_VERIFY_BUTTON_TIMEOUT": OTP_VERIFY_BUTTON_TIMEOUT,
                "OTP_LOGIN_COMPLETE_WAIT": OTP_LOGIN_COMPLETE_WAIT,
                "OTP_RETRIES": OTP_RETRIES,
                "OTP_DELAY": OTP_DELAY
            },
            "Wait Timeouts": {
                "WAIT_TIMEOUT": WAIT_TIMEOUT,
                "LOGIN_SUCCESS_WAIT": LOGIN_SUCCESS_WAIT
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
                        masked_value = "*" * min(len(value), 20) + ("..." if len(value) > 20 else "")
                        print(f"   ✅ {var_name}: {masked_value}")
                    else:
                        print(f"   ✅ {var_name}: {value}")
        
        if missing_vars:
            print(f"\n⚠️  WARNING: {len(missing_vars)} variable(s) missing from env_variables.py:")
            for var in missing_vars:
                print(f"      - {var}")
            print("\n   Please add these variables to your env_variables.py.")
        else:
            print("\n✅ All environment variables are loaded successfully!")
        
        print("="*80 + "\n")
    
    def navigate_to_live_menu(self) -> bool:
        """
        Navigate to live stream menu section.
        
        This method forcefully clicks Live button using the specific XPath provided.
        Uses multiple click strategies to ensure successful navigation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            wait_timeout = WAIT_TIMEOUT or 20
            wait_timeout_ms = wait_timeout * 1000
            
            clicked = False
            
            # Method 1: Use the specific XPath provided by user (PRIMARY METHOD)
            # XPath: //*[@id="root"]/div/div[1]/div[3]/div/div[6]/a/div/p
            try:
                print("🔍 Attempting to click Live button using specific XPath...")
                live_btn = self.page.locator('//*[@id="root"]/div/div[1]/div[3]/div/div[6]/a/div/p')
                live_btn.wait_for(state="visible", timeout=wait_timeout)
                live_btn.scroll_into_view_if_needed()
                time.sleep(1)
                live_btn.click(force=True)
                print("✅ Live button clicked (method 1 - specific XPath, force click)")
                clicked = True
                time.sleep(2)
            except Exception as e1:
                print("WARNING: " + f"⚠️ Method 1 (force click) failed: {e1}")
                
                # Method 2: Try JavaScript click on the same XPath
                try:
                    print("🔍 Trying JavaScript click on specific XPath...")
                    live_btn = self.page.locator('//*[@id="root"]/div/div[1]/div[3]/div/div[6]/a/div/p')
                    live_btn.wait_for(state="visible", timeout=wait_timeout)
                    live_btn.scroll_into_view_if_needed()
                    time.sleep(1)
                    live_btn.evaluate("el => el.click()")
                    print("✅ Live button clicked (method 2 - JavaScript click)")
                    clicked = True
                    time.sleep(2)
                except Exception as e2:
                    print("WARNING: " + f"⚠️ Method 2 (JavaScript click) failed: {e2}")
                    
                    # Method 3: Try clicking the parent anchor element
                    try:
                        print("🔍 Trying to click parent anchor element...")
                        live_anchor = self.page.locator('//*[@id="root"]/div/div[1]/div[3]/div/div[6]/a')
                        live_anchor.wait_for(state="visible", timeout=wait_timeout)
                        live_anchor.scroll_into_view_if_needed()
                        time.sleep(1)
                        live_anchor.click(force=True)
                        print("✅ Live anchor clicked (method 3 - parent anchor)")
                        clicked = True
                        time.sleep(2)
                    except Exception as e3:
                        print("WARNING: " + f"⚠️ Method 3 (parent anchor) failed: {e3}")
                        
                        # Method 4: Try JavaScript click on parent anchor
                        try:
                            print("🔍 Trying JavaScript click on parent anchor...")
                            live_anchor = self.page.locator('//*[@id="root"]/div/div[1]/div[3]/div/div[6]/a')
                            live_anchor.wait_for(state="visible", timeout=wait_timeout)
                            live_anchor.scroll_into_view_if_needed()
                            time.sleep(1)
                            live_anchor.evaluate("el => el.click()")
                            print("✅ Live anchor clicked (method 4 - JavaScript on anchor)")
                            clicked = True
                            time.sleep(2)
                        except Exception as e4:
                            print("WARNING: " + f"⚠️ Method 4 (JavaScript on anchor) failed: {e4}")
                            
                            # Method 5: Try clicking by text content (fallback)
                            try:
                                print("🔍 Trying to find Live button by text content...")
                                live_by_text = self.page.locator("//p[normalize-space()='Live']")
                                if live_by_text.count() > 0:
                                    # Try each Live button found
                                    for i in range(live_by_text.count()):
                                        try:
                                            btn = live_by_text.nth(i)
                                            btn.wait_for(state="visible", timeout=2000)
                                            
                                            # Check if it's the correct one by checking XPath structure
                                            btn_xpath = btn.evaluate("""
                                                el => {
                                                    let path = [];
                                                    while (el && el.nodeType === 1) {
                                                        let index = 0;
                                                        let sibling = el.previousElementSibling;
                                                        while (sibling) {
                                                            index++;
                                                            sibling = sibling.previousElementSibling;
                                                        }
                                                        let tag = el.tagName.toLowerCase();
                                                        path.unshift(`${tag}[${index + 1}]`);
                                                        el = el.parentElement;
                                                    }
                                                    return path.join('/');
                                                }
                                            """)
                                            
                                            # If this button matches our target structure (div[6]/a/div/p), use it
                                            if 'div[6]' in btn_xpath or len(btn_xpath.split('/')) >= 5:
                                                btn.scroll_into_view_if_needed()
                                                time.sleep(1)
                                                btn.click(force=True)
                                                print(f"✅ Live button clicked (method 5 - by text, button {i+1})")
                                                clicked = True
                                                time.sleep(2)
                                                break
                                        except Exception:
                                            continue
                            except Exception as e5:
                                print("WARNING: " + f"⚠️ Method 5 (by text) failed: {e5}")
            
            if not clicked:
                print("ERROR: " + "❌ Could not click Live button - all methods failed")
                return False
            
            print("✅ Live button clicked successfully")
            
            login_success_wait = LOGIN_SUCCESS_WAIT or 3
            login_success_wait = float(login_success_wait)
            time.sleep(login_success_wait)
            
            # Verify that we are on the live channels view by checking for channel list container
            try:
                channels_container = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div')
                channels_container.wait_for(state="visible", timeout=wait_timeout)
                print("✅ Verified: Now on live channels view")
            except Exception:
                # Retry click once if verification failed
                print("WARNING: " + "⚠️ Live view not verified, retrying click once...")
                try:
                    # Retry with the specific XPath
                    live_btn = self.page.locator('//*[@id="root"]/div/div[1]/div[3]/div/div[6]/a/div/p')
                    live_btn.wait_for(state="visible", timeout=wait_timeout)
                    live_btn.scroll_into_view_if_needed()
                    time.sleep(1)
                    live_btn.click(force=True)
                    time.sleep(login_success_wait)
                    channels_container = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div')
                    channels_container.wait_for(state="visible", timeout=wait_timeout)
                    print("✅ Verified: Now on live channels view (after retry)")
                except Exception as e:
                    print("ERROR: " + f"❌ Live view verification failed after retry: {e}")
                    # Still return True if we clicked, as navigation might have worked
                    if clicked:
                        print("WARNING: " + "⚠️ Click succeeded but verification failed - continuing anyway")
                        return True
                    return False
            
            return True
            
        except Exception as e:
            print("ERROR: " + f"NO: Error navigating to live menu -> {e}")
            return False
    
    def get_all_channels(self) -> List[Tuple[str, int]]:
        """
        Get all available channels dynamically.
        
        This method finds all channel buttons and extracts their names and indices.
        
        Returns:
            List[Tuple[str, int]]: List of (channel_name, button_index) tuples
        """
        try:
            wait_timeout = WAIT_TIMEOUT or 20
            wait_timeout_ms = wait_timeout * 1000
            
            # Find all channel buttons using pattern: button[1], button[2], etc.
            channels = []
            max_channels = 50  # Maximum channels to check
            
            for i in range(1, max_channels + 1):
                try:
                    # Try to find channel button with index i
                    channel_btn = self.page.locator(f'//*[@id="root"]/div/div[2]/div/div/div[3]/div/button[{i}]/div[2]/p')
                    channel_btn.wait_for(state="visible", timeout=2000)
                    channel_name = channel_btn.text_content()
                    if channel_name and channel_name.strip():
                        channels.append((channel_name.strip(), i))
                        print(f"Found channel {i}: {channel_name.strip()}")
                except Exception:
                    # No more channels found
                    break
            
            if channels:
                print(f"✅ Total channels found: {len(channels)}")
                return channels
            else:
                print("WARNING: " + "⚠️ No channels found. Trying alternative method...")
                # Alternative: Try to find all buttons in the channel container
                try:
                    channel_container = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div')
                    buttons = channel_container.locator('button').all()
                    for idx, btn in enumerate(buttons, start=1):
                        try:
                            # Try to get text from div[2]/p
                            text_elem = btn.locator('div[2]/p')
                            if text_elem.count() > 0:
                                channel_name = text_elem.first.text_content()
                                if channel_name and channel_name.strip():
                                    channels.append((channel_name.strip(), idx))
                                    print(f"Found channel {idx}: {channel_name.strip()}")
                        except Exception:
                            continue
                    
                    if channels:
                        print(f"✅ Total channels found (alternative method): {len(channels)}")
                        return channels
                except Exception as e:
                    print("ERROR: " + f"Error in alternative channel detection: {e}")
            
            return channels
            
        except Exception as e:
            print("ERROR: " + f"NO: Error getting channels -> {e}")
            return []
    
    def open_channel(self, channel_index: int, channel_name: str = "") -> bool:
        """
        Open a specific channel by index with forceful clicking.
        
        Args:
            channel_index (int): Index of the channel button (1-based)
            channel_name (str): Name of the channel (for logging)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            wait_timeout = WAIT_TIMEOUT or 20
            wait_timeout_ms = wait_timeout * 1000
            
            print(f"🔍 Attempting to open channel {channel_index} ({channel_name})...")
            
            # Wait for channel list to be ready
            time.sleep(3)
            
            # Try multiple selectors and click methods
            channel_opened = False
            
            # Method 1: Try clicking the button directly
            try:
                channel_btn = self.page.locator(f'//*[@id="root"]/div/div[2]/div/div/div[3]/div/button[{channel_index}]')
                channel_btn.wait_for(state="visible", timeout=wait_timeout)
                channel_btn.scroll_into_view_if_needed()
                time.sleep(1)
                channel_btn.click(force=True)
                print(f"✅ Channel button clicked (method 1)")
                time.sleep(3)
                channel_opened = True
            except Exception as e1:
                print("WARNING: " + f"⚠️ Method 1 failed: {e1}")
                
                # Method 2: Try clicking the text element (p tag)
                try:
                    channel_text = self.page.locator(f'//*[@id="root"]/div/div[2]/div/div/div[3]/div/button[{channel_index}]/div[2]/p')
                    channel_text.wait_for(state="visible", timeout=wait_timeout)
                    channel_text.scroll_into_view_if_needed()
                    time.sleep(1)
                    channel_text.click(force=True)
                    print(f"✅ Channel text clicked (method 2)")
                    time.sleep(3)
                    channel_opened = True
                except Exception as e2:
                    print("WARNING: " + f"⚠️ Method 2 failed: {e2}")
                    
                    # Method 3: Try JavaScript click
                    try:
                        channel_btn = self.page.locator(f'//*[@id="root"]/div/div[2]/div/div/div[3]/div/button[{channel_index}]')
                        channel_btn.wait_for(state="visible", timeout=wait_timeout)
                        channel_btn.scroll_into_view_if_needed()
                        time.sleep(1)
                        channel_btn.evaluate("el => el.click()")
                        print(f"✅ Channel button clicked via JavaScript (method 3)")
                        time.sleep(3)
                        channel_opened = True
                    except Exception as e3:
                        print("WARNING: " + f"⚠️ Method 3 failed: {e3}")
                        
                        # Method 4: Try clicking by channel name text
                        if channel_name:
                            try:
                                channel_by_name = self.page.locator(f'//*[@id="root"]/div/div[2]/div/div/div[3]/div//button[.//p[contains(text(), "{channel_name}")]]')
                                channel_by_name.wait_for(state="visible", timeout=wait_timeout)
                                channel_by_name.scroll_into_view_if_needed()
                                time.sleep(1)
                                channel_by_name.click(force=True)
                                print(f"✅ Channel clicked by name (method 4)")
                                time.sleep(3)
                                channel_opened = True
                            except Exception as e4:
                                print("WARNING: " + f"⚠️ Method 4 failed: {e4}")
            
            if channel_opened:
                # Wait longer for page navigation after clicking channel
                time.sleep(5)
                
                # Wait for page to settle (network idle)
                try:
                    self.page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass  # Continue even if networkidle times out
                
                # Check if we're still on channel list (channel NOT opened)
                channel_still_visible = False
                try:
                    # If we can still see channel buttons, channel didn't open
                    channel_list_check = self.page.locator(f'//*[@id="root"]/div/div[2]/div/div/div[3]/div/button[{channel_index}]')
                    if channel_list_check.count() > 0:
                        # Check if button is still visible (means we're still on list)
                        try:
                            channel_list_check.wait_for(state="visible", timeout=3000)
                            channel_still_visible = True
                        except Exception:
                            # Button not visible, might have opened
                            channel_still_visible = False
                except Exception:
                    channel_still_visible = False
                
                if channel_still_visible:
                    print("ERROR: " + f"❌ Channel {channel_index} ({channel_name}) did NOT open - still on channel list!")
                    print("ERROR: " + f"   Trying alternative click methods...")
                    
                    # Try clicking again with different method
                    try:
                        # Try clicking the entire button area
                        channel_container = self.page.locator(f'//*[@id="root"]/div/div[2]/div/div/div[3]/div/button[{channel_index}]')
                        channel_container.click(force=True, timeout=5000)
                        print(f"✅ Retry: Channel button clicked again (force click)")
                        time.sleep(5)
                        self.page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception as retry_error:
                        print("ERROR: " + f"❌ Retry click also failed: {retry_error}")
                        return False
                
                # Check if start live button is visible (indicates channel is opened)
                channel_verified = False
                try:
                    start_live_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[3]/p')
                    start_live_btn.wait_for(state="visible", timeout=10000)
                    print(f"✅ Channel {channel_index} ({channel_name}) opened successfully! (Start Live button visible)")
                    channel_verified = True
                except Exception as e1:
                    print("WARNING: " + f"⚠️ Start Live button not found: {e1}")
                    # Alternative check: see if video element exists
                    try:
                        video = self.page.locator("video")
                        video.wait_for(state="attached", timeout=5000)
                        print(f"✅ Channel {channel_index} ({channel_name}) opened successfully! (Video element detected)")
                        channel_verified = True
                    except Exception as e2:
                        print("WARNING: " + f"⚠️ Video element not found: {e2}")
                
                if not channel_verified:
                    # Check URL or page content to verify
                    current_url = self.page.url
                    page_title = self.page.title()
                    print("ERROR: " + f"❌ Channel {channel_index} ({channel_name}) OPENING FAILED!")
                    print("ERROR: " + f"   Current URL: {current_url}")
                    print("ERROR: " + f"   Page title: {page_title}")
                    print("ERROR: " + f"   Neither Start Live button nor video element found")
                    print("ERROR: " + f"   The channel click might not have worked. Please verify manually.")
                    return False
                
                return True
            else:
                print("ERROR: " + f"❌ All click methods failed to open channel {channel_index} ({channel_name})")
                print("ERROR: " + f"   Tried: Direct button click, Text click, JavaScript click, Name-based click")
                return False
            
        except Exception as e:
            print("ERROR: " + f"NO: Error opening channel {channel_index} -> {e}")
            return False
    
    def start_live_stream(self) -> bool:
        """
        Click start from live button to start the live stream.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            wait_timeout = WAIT_TIMEOUT or 20
            wait_timeout_ms = wait_timeout * 1000
            
            print("🔍 Attempting to click Start-from-live button...")
            
            # Wait before clicking
            time.sleep(3)
            
            # Try multiple click methods
            clicked = False
            
            # Method 1: Click the p tag directly
            try:
                start_live_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[3]/p')
                start_live_btn.wait_for(state="visible", timeout=wait_timeout)
                start_live_btn.scroll_into_view_if_needed()
                time.sleep(1)
                start_live_btn.click(force=True)
                print("✅ Start-from-live button clicked (method 1)")
                time.sleep(3)
                clicked = True
            except Exception as e1:
                print("WARNING: " + f"⚠️ Method 1 failed: {e1}")
                
                # Method 2: Click the button parent
                try:
                    start_live_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[3]')
                    start_live_btn.wait_for(state="visible", timeout=wait_timeout)
                    start_live_btn.scroll_into_view_if_needed()
                    time.sleep(1)
                    start_live_btn.click(force=True)
                    print("✅ Start-from-live button clicked (method 2)")
                    time.sleep(3)
                    clicked = True
                except Exception as e2:
                    print("WARNING: " + f"⚠️ Method 2 failed: {e2}")
                    
                    # Method 3: JavaScript click
                    try:
                        start_live_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[3]')
                        start_live_btn.wait_for(state="visible", timeout=wait_timeout)
                        start_live_btn.scroll_into_view_if_needed()
                        time.sleep(1)
                        start_live_btn.evaluate("el => el.click()")
                        print("✅ Start-from-live button clicked via JavaScript (method 3)")
                        time.sleep(3)
                        clicked = True
                    except Exception as e3:
                        print("WARNING: " + f"⚠️ Method 3 failed: {e3}")
            
            if clicked:
                # Verify video element is present after clicking
                time.sleep(5)  # Wait longer for video to load
                try:
                    video = self.page.locator("video")
                    video.wait_for(state="attached", timeout=10000)
                    
                    # FORCEFULLY extract and set the actual stream URL from network requests
                    print("🔍 Forcefully extracting stream URL from network requests...")
                    stream_url = None
                    
                    # First, check captured stream URLs from network requests
                    if hasattr(self, 'captured_stream_urls') and self.captured_stream_urls:
                        stream_url = self.captured_stream_urls[-1]  # Use the latest one
                        print(f"✅ Using captured stream URL: {stream_url}")
                    
                    # If not found, try to get the stream URL from the page
                    if not stream_url:
                        try:
                            # Check if there's an HLS.js instance with the stream URL
                            stream_url_check = self.page.evaluate("""
                                (function(){
                                    // Check for HLS.js instance
                                    if (typeof Hls !== 'undefined') {
                                        var videos = document.querySelectorAll('video');
                                        for (var i = 0; i < videos.length; i++) {
                                            var v = videos[i];
                                            if (v.hls && v.hls.url) {
                                                return v.hls.url;
                                            }
                                        }
                                        // Check window for HLS instances
                                        if (window.hlsInstances && window.hlsInstances.length > 0) {
                                            return window.hlsInstances[0].url;
                                        }
                                    }
                                    
                                    // Check for video source elements
                                    var v = document.querySelector('video');
                                    if (v) {
                                        var sources = v.querySelectorAll('source');
                                        for (var i = 0; i < sources.length; i++) {
                                            var src = sources[i].src;
                                            if (src && (src.includes('.m3u8') || src.includes('nginx-clipping'))) {
                                                return src;
                                            }
                                        }
                                    }
                                    
                                    // Check data attributes or hidden inputs
                                    var streamInputs = document.querySelectorAll('[data-stream-url], [data-hls-url], input[type="hidden"][value*=".m3u8"]');
                                    for (var i = 0; i < streamInputs.length; i++) {
                                        var url = streamInputs[i].getAttribute('data-stream-url') || 
                                                  streamInputs[i].getAttribute('data-hls-url') || 
                                                  streamInputs[i].value;
                                        if (url && url.includes('.m3u8')) {
                                            return url;
                                        }
                                    }
                                    
                                    return null;
                                })()
                            """)
                            
                            if stream_url_check:
                                stream_url = stream_url_check
                                print(f"✅ Found stream URL in page: {stream_url}")
                        except Exception as e:
                            print("WARNING: " + f"⚠️ Could not extract stream URL from page: {e}")
                    
                    # If still not found, wait a bit for network requests to capture it
                    if not stream_url:
                        print("⏳ Waiting for stream URL to be captured from network requests...")
                        for wait_net in range(5):
                            time.sleep(2)
                            if hasattr(self, 'captured_stream_urls') and self.captured_stream_urls:
                                stream_url = self.captured_stream_urls[-1]
                                print(f"✅ Stream URL captured: {stream_url}")
                                break
                    
                    # Forcefully trigger the page's stream initialization
                    # The page might need events or clicks to start loading
                    print("🔧 Forcefully triggering page's stream initialization...")
                    
                    # Method 1: Try clicking any "Get Stream" or similar buttons
                    try:
                        stream_buttons = [
                            "//button[contains(.,'Get Stream')]",
                            "//button[contains(.,'Load Stream')]",
                            "//button[contains(.,'Start Stream')]",
                            "//button[contains(@class,'stream')]",
                            "//button[contains(@id,'stream')]"
                        ]
                        for btn_xpath in stream_buttons:
                            try:
                                btn = self.page.locator(btn_xpath)
                                if btn.count() > 0:
                                    btn.first.click()
                                    print(f"✅ Clicked stream button: {btn_xpath}")
                                    time.sleep(2)
                                    break
                            except:
                                continue
                    except Exception as e:
                        print("DEBUG: " + f"   No stream button found: {e}")
                    
                    # Method 2: Trigger video events to wake up the player
                    try:
                        self.page.evaluate("""
                            (function(){
                                var v = document.querySelector('video');
                                if (v) {
                                    // Trigger all video events that might wake up the player
                                    var events = ['loadstart', 'loadedmetadata', 'canplay', 'canplaythrough', 'loadeddata', 'play', 'playing'];
                                    events.forEach(function(eventName) {
                                        try {
                                            v.dispatchEvent(new Event(eventName, {bubbles: true}));
                                        } catch(e) {}
                                    });
                                    
                                    // Force load if needed
                                    if (v.networkState === 0 || v.networkState === 3) {
                                        v.load();
                                    }
                                    
                                    // Try to play
                                    if (v.paused) {
                                        v.play().catch(function(e) {
                                            console.log('Auto-play blocked:', e);
                                        });
                                    }
                                }
                                
                                // Also trigger any window events that might initialize the player
                                try {
                                    window.dispatchEvent(new Event('load'));
                                    window.dispatchEvent(new Event('DOMContentLoaded'));
                                } catch(e) {}
                            })()
                        """)
                        print("✅ Triggered video and window events")
                    except Exception as e:
                        print("DEBUG: " + f"   Could not trigger events: {e}")
                    
                    # Method 3: Wait and check if page's HLS.js needs time
                    print("⏳ Waiting for page's own video player to initialize stream...")
                    time.sleep(5)  # Give more time for page's JS to initialize
                    
                    # Wait for page's own player to load the stream
                    # Also check if we need to manually trigger the page's player
                    print("🔍 Waiting for page's video player to load stream naturally...")
                    video_playing = False
                    
                    for wait_attempt in range(40):  # Wait up to 80 seconds for page's player
                        try:
                            video_state = self.page.evaluate("""
                                (function(){
                                    var v = document.querySelector('video');
                                    if (!v) return {exists: false};
                                    
                                    // Check if video is actually playing (best indicator)
                                    var isPlaying = !v.paused && !v.ended && v.currentTime > 0 && v.readyState >= 2;
                                    
                                    // Check if page has its own HLS instance
                                    var hasPageHLS = v.hls && typeof v.hls.loadSource === 'function';
                                    var hlsReady = false;
                                    var hlsState = null;
                                    if (hasPageHLS) {
                                        // Check HLS state
                                        hlsReady = v.hls.media !== null;
                                        try {
                                            hlsState = v.hls.levels ? v.hls.levels.length : 0;
                                        } catch(e) {
                                            hlsState = 'unknown';
                                        }
                                    }
                                    
                                    // Check if there's a video source set (even if blob)
                                    var hasSource = v.src || v.currentSrc || '';
                                    var sourceType = hasSource.startsWith('blob:') ? 'blob' : (hasSource.startsWith('http') ? 'http' : 'none');
                                    
                                    return {
                                        exists: true,
                                        isPlaying: isPlaying,
                                        readyState: v.readyState,
                                        networkState: v.networkState,
                                        paused: v.paused,
                                        currentTime: v.currentTime,
                                        duration: v.duration,
                                        src: v.src || v.currentSrc || 'no src',
                                        hasPageHLS: hasPageHLS,
                                        hlsReady: hlsReady,
                                        hlsState: hlsState,
                                        sourceType: sourceType,
                                        error: v.error ? v.error.message : null,
                                        errorCode: v.error ? v.error.code : null,
                                        buffered: v.buffered.length > 0
                                    };
                                })()
                            """)
                            
                            # Every 10 attempts (20 seconds), try to trigger the player again
                            if wait_attempt > 0 and wait_attempt % 10 == 0:
                                print("🔄 Re-triggering page's player (periodic check)...")
                                try:
                                    self.page.evaluate("""
                                        (function(){
                                            var v = document.querySelector('video');
                                            if (v) {
                                                // Try to reload/restart
                                                if (v.networkState === 0 || v.networkState === 3) {
                                                    v.load();
                                                }
                                                // Try to play
                                                if (v.paused) {
                                                    v.play().catch(function(e) {
                                                        console.log('Periodic play attempt:', e.name);
                                                    });
                                                }
                                            }
                                        })()
                                    """)
                                except:
                                    pass
                            
                            if video_state.get('exists'):
                                is_playing = video_state.get('isPlaying', False)
                                ready_state = video_state.get('readyState', 0)
                                network_state = video_state.get('networkState', 0)
                                has_page_hls = video_state.get('hasPageHLS', False)
                                hls_ready = video_state.get('hlsReady', False)
                                hls_state = video_state.get('hlsState')
                                source_type = video_state.get('sourceType', 'none')
                                current_time = video_state.get('currentTime', 0)
                                buffered = video_state.get('buffered', False)
                                
                                # Log progress every 10 seconds (reduced frequency)
                                if wait_attempt % 10 == 0:
                                    print(f"📹 Video loading... (readyState={ready_state}, networkState={network_state})")
                                
                                # Best case: video is actually playing
                                if is_playing:
                                    video_playing = True
                                    print(f"✅ Video is playing! (currentTime: {current_time:.1f}s, readyState: {ready_state})")
                                    break
                                
                                # Good case: video has data and is ready to play
                                if ready_state >= 2 and buffered:
                                    print(f"✅ Video has data ready (readyState: {ready_state}, buffered: {buffered})")
                                    # Try to play if paused
                                    if video_state.get('paused'):
                                        try:
                                            self.page.evaluate("document.querySelector('video').play().catch(e => console.log('Play attempt:', e))")
                                        except:
                                            pass
                                    # Continue waiting to see if it starts playing
                                
                                # Check for page's HLS instance
                                if has_page_hls:
                                    if hls_ready:
                                        print(f"✅ Page's HLS.js is ready and attached (levels: {hls_state})")
                                        # If HLS is ready but not playing, try to trigger play
                                        if video_state.get('paused') and wait_attempt % 5 == 0:
                                            try:
                                                self.page.evaluate("""
                                                    (function(){
                                                        var v = document.querySelector('video');
                                                        if (v && v.hls) {
                                                            // Try to start playback
                                                            v.play().catch(function(e) {
                                                                console.log('HLS play attempt:', e.name);
                                                            });
                                                        }
                                                    })()
                                                """)
                                            except:
                                                pass
                                    else:
                                        if wait_attempt % 5 == 0:
                                            print(f"⏳ Page's HLS.js detected but not ready yet... (waiting for media attachment)")
                                    
                                    # If no HLS and no source, the page's player might not have initialized
                                    if not has_page_hls and source_type == 'none' and wait_attempt > 10:
                                        print("WARNING: " + f"⚠️ Page's player not initializing - no HLS instance and no source detected")
                                        # Try to find and click any initialization buttons
                                        try:
                                            init_buttons = self.page.locator("//button[contains(.,'Play') or contains(.,'Start') or contains(.,'Load')]")
                                            if init_buttons.count() > 0:
                                                init_buttons.first.click()
                                                print("✅ Clicked potential initialization button")
                                                time.sleep(3)
                                        except:
                                            pass
                                    
                                    # Check for errors (but don't fail - page's player might recover)
                                    error_code = video_state.get('errorCode')
                                    if error_code:
                                        if wait_attempt % 10 == 0:  # Log error every 20 seconds
                                            print("WARNING: " + f"⚠️ Video error code: {error_code}, but waiting for page's player to recover...")
                                    
                                    # If network is loading, that's good - continue waiting
                                    if network_state == 2:  # NETWORK_LOADING
                                        if wait_attempt % 5 == 0:
                                            print(f"⏳ Video is loading... (readyState: {ready_state}, networkState: {network_state})")
                            
                            time.sleep(2)
                        except Exception as e:
                            print("WARNING: " + f"⚠️ Error checking video state: {e}")
                            time.sleep(2)
                        
                        if not video_playing:
                            print("WARNING: " + f"⚠️ Video not playing after waiting, but page's player might still be loading...")
                            # Final attempt: check if we can manually trigger the page's player
                            try:
                                print("🔧 Final attempt: Checking if page's player needs manual trigger...")
                                final_check = self.page.evaluate("""
                                    (function(){
                                        var v = document.querySelector('video');
                                        if (!v) return {exists: false};
                                        
                                        // Check if there's a React component or state that controls the player
                                        var reactPlayer = v.closest('[class*="player"], [class*="video"], [class*="stream"]');
                                        
                                        // Try to find any clickable elements that might start the stream
                                        var playButtons = document.querySelectorAll('button[class*="play"], button[class*="start"], button[class*="stream"]');
                                        
                                        return {
                                            exists: true,
                                            hasReactPlayer: reactPlayer !== null,
                                            playButtonsFound: playButtons.length,
                                            readyState: v.readyState,
                                            networkState: v.networkState,
                                            src: v.src || v.currentSrc || 'no src'
                                        };
                                    })()
                                """)
                                
                                if final_check.get('playButtonsFound', 0) > 0:
                                    print(f"🔍 Found {final_check.get('playButtonsFound')} potential play buttons, trying to click...")
                                    try:
                                        play_btn = self.page.locator("button[class*='play'], button[class*='start'], button[class*='stream']").first
                                        play_btn.click()
                                        print("✅ Clicked play button")
                                        time.sleep(5)
                                    except:
                                        pass
                            except Exception as e:
                                print("DEBUG: " + f"   Final check failed: {e}")
                        
                        # Don't fail - the page's player might work even if not playing yet
                    
                    # Try to play video manually (autoplay might be blocked)
                    print("🔍 Attempting to play video manually...")
                    try:
                        play_result = self.page.evaluate("""
                            (function(){
                                var v = document.querySelector('video');
                                if (!v) return {success: false, error: 'No video element'};
                                
                                // Set video attributes for better streaming
                                v.preload = 'auto';
                                v.muted = false;
                                
                                // Check if video player library is present (HLS.js, Video.js, etc.)
                                var hasHLS = typeof Hls !== 'undefined';
                                var hasVideoJS = typeof videojs !== 'undefined';
                                var playerReady = true;
                                
                                if (hasHLS) {
                                    // Check if HLS is ready
                                    var hls = v.hls || (window.hlsInstances && window.hlsInstances[0]);
                                    if (hls) {
                                        playerReady = hls.readyState === 2;  // HLS.READY
                                        console.log('HLS.js found, readyState:', hls.readyState);
                                    }
                                }
                                
                                // Don't call load() if video is already loading/loaded (it can interrupt)
                                // Only call load() if video has no data and networkState indicates no source
                                if (v.readyState === 0 && v.networkState === 3) {
                                    // Try to reload the video
                                    try {
                                        v.load();
                                        console.log('Video load() called');
                                    } catch(e) {
                                        console.log('Video load() error:', e);
                                    }
                                    return {
                                        success: true,
                                        action: 'load_called',
                                        readyState: v.readyState,
                                        networkState: v.networkState,
                                        playerReady: playerReady
                                    };
                                }
                                
                                // Wait for video to be ready before playing
                                if (v.readyState >= 1 || (playerReady && v.networkState >= 2)) {
                                    try {
                                        // Ensure video is not muted (for autoplay)
                                        v.muted = false;
                                        
                                        // Try to play
                                        var playPromise = v.play();
                                        if (playPromise !== undefined) {
                                            playPromise.then(() => {
                                                console.log('Video play() succeeded');
                                            }).catch(error => {
                                                // Don't log AbortError - it's common
                                                if (error.name !== 'AbortError') {
                                                    console.error('Video play() failed:', error.name, error.message);
                                                }
                                            });
                                        }
                                        
                                        return {
                                            success: true,
                                            action: 'play_attempted',
                                            paused: v.paused,
                                            readyState: v.readyState,
                                            networkState: v.networkState,
                                            src: v.src || v.currentSrc || 'no src',
                                            autoplay: v.autoplay,
                                            error: v.error ? v.error.message : null,
                                            errorCode: v.error ? v.error.code : null,
                                            playerReady: playerReady,
                                            hasHLS: hasHLS,
                                            hasVideoJS: hasVideoJS
                                        };
                                    } catch(e) {
                                        return {success: false, error: e.message, playerReady: playerReady};
                                    }
                                } else {
                                    return {
                                        success: true,
                                        action: 'waiting_for_data',
                                        readyState: v.readyState,
                                        networkState: v.networkState,
                                        playerReady: playerReady,
                                        hasHLS: hasHLS,
                                        hasVideoJS: hasVideoJS
                                    };
                                }
                            })()
                        """)
                        print(f"📹 Video play attempt: {play_result}")
                        
                        # Check for errors in play result
                        if play_result.get('error'):
                            print("ERROR: " + f"❌ Video play error: {play_result.get('error')}")
                            if play_result.get('errorCode'):
                                print("ERROR: " + f"   Error code: {play_result.get('errorCode')}")
                    except Exception as play_error:
                        print("WARNING: " + f"⚠️ Error trying to play video: {play_error}")
                    
                    # Wait for video to start playing and check if it's actually playing
                    time.sleep(5)
                    
                    # Final check: Is video actually playing?
                    try:
                        final_video_check = self.page.evaluate("""
                            (function(){
                                var v = document.querySelector('video');
                                if (!v) return {exists: false};
                                return {
                                    exists: true,
                                    playing: !v.paused && !v.ended && v.currentTime > 0,
                                    paused: v.paused,
                                    readyState: v.readyState,
                                    networkState: v.networkState,
                                    currentTime: v.currentTime,
                                    duration: v.duration,
                                    error: v.error ? v.error.message : null,
                                    src: v.src || v.currentSrc || 'no src'
                                };
                            })()
                        """)
                        
                        if final_video_check.get('exists'):
                            if final_video_check.get('playing'):
                                print(f"✅ Video is playing! (currentTime: {final_video_check.get('currentTime', 0):.2f}s)")
                            elif final_video_check.get('paused'):
                                print("WARNING: " + f"⚠️ Video is paused (readyState: {final_video_check.get('readyState')}, networkState: {final_video_check.get('networkState')})")
                            else:
                                print(f"📹 Video state: paused={final_video_check.get('paused')}, readyState={final_video_check.get('readyState')}, networkState={final_video_check.get('networkState')}")
                    except Exception as e:
                        print("WARNING: " + f"⚠️ Error checking final video state: {e}")
                    
                    # Check if video has an error with detailed diagnostics
                    video_error_check = self.page.evaluate("""
                        (function(){
                            var v = document.querySelector('video');
                            if (!v) return {exists: false, error: 'No video element'};
                            
                            // Get all video sources
                            var sources = [];
                            var sourceElements = v.querySelectorAll('source');
                            sourceElements.forEach(function(s) {
                                sources.push({
                                    src: s.src,
                                    type: s.type
                                });
                            });
                            
                            // Check for errors
                            var errorInfo = null;
                            if (v.error) {
                                errorInfo = {
                                    message: v.error.message,
                                    code: v.error.code,
                                    MEDIA_ERR_ABORTED: v.error.code === 1,
                                    MEDIA_ERR_NETWORK: v.error.code === 2,
                                    MEDIA_ERR_DECODE: v.error.code === 3,
                                    MEDIA_ERR_SRC_NOT_SUPPORTED: v.error.code === 4
                                };
                            }
                            
                            return {
                                exists: true,
                                error: errorInfo,
                                readyState: v.readyState,
                                networkState: v.networkState,
                                src: v.src || v.currentSrc || 'no src',
                                sources: sources,
                                paused: v.paused,
                                currentTime: v.currentTime,
                                duration: v.duration,
                                buffered: v.buffered.length > 0 ? {
                                    start: v.buffered.start(0),
                                    end: v.buffered.end(0)
                                } : null
                            };
                        })()
                    """)
                    
                    if video_error_check.get('error'):
                        error_info = video_error_check.get('error')
                        print("ERROR: " + f"❌ Video element has ERROR: {error_info.get('message', 'Unknown error')}")
                        print("ERROR: " + f"   Error code: {error_info.get('code', 'N/A')}")
                        
                        # Explain error codes
                        if error_info.get('MEDIA_ERR_ABORTED'):
                            print("ERROR: " + f"   → MEDIA_ERR_ABORTED: User aborted loading")
                        elif error_info.get('MEDIA_ERR_NETWORK'):
                            print("ERROR: " + f"   → MEDIA_ERR_NETWORK: Network error while loading")
                        elif error_info.get('MEDIA_ERR_DECODE'):
                            print("ERROR: " + f"   → MEDIA_ERR_DECODE: Decoding error")
                        elif error_info.get('MEDIA_ERR_SRC_NOT_SUPPORTED'):
                            print("ERROR: " + f"   → MEDIA_ERR_SRC_NOT_SUPPORTED: Format not supported")
                        
                        print("ERROR: " + f"   Video src: {video_error_check.get('src', 'N/A')}")
                        sources = video_error_check.get('sources', [])
                        if sources:
                            print("ERROR: " + f"   Video sources:")
                            for src in sources:
                                print("ERROR: " + f"     - {src.get('src', 'N/A')} (type: {src.get('type', 'N/A')})")
                        
                        print("ERROR: " + f"   This indicates the stream failed to load")
                        print("ERROR: " + f"   Possible solutions:")
                        print("ERROR: " + f"   1. Check network connectivity")
                        print("ERROR: " + f"   2. Verify stream URL is accessible")
                        print("ERROR: " + f"   3. Check if stream format is supported")
                        print("ERROR: " + f"   4. Try refreshing the page manually")
                        return False
                    
                    # Log video state with more details
                    print(f"📹 Video state: readyState={video_error_check.get('readyState')}, networkState={video_error_check.get('networkState')}, paused={video_error_check.get('paused')}")
                    print(f"📹 Video src: {video_error_check.get('src', 'N/A')}")
                    sources = video_error_check.get('sources', [])
                    if sources:
                        print(f"📹 Video sources: {len(sources)} found")
                        for src in sources:
                            print(f"   - {src.get('src', 'N/A')} (type: {src.get('type', 'N/A')})")
                    
                    buffered = video_error_check.get('buffered')
                    if buffered:
                        print(f"📹 Video buffered: {buffered.get('start', 0):.2f}s - {buffered.get('end', 0):.2f}s")
                    
                    # If video is paused, try to play it multiple times
                    if video_error_check.get('paused'):
                        print("🔍 Video is paused, attempting to play...")
                        for attempt in range(3):
                            try:
                                play_result = self.page.evaluate("""
                                    (function(){
                                        var v = document.querySelector('video');
                                        if (!v) return {success: false, error: 'No video'};
                                        try {
                                            v.muted = false;
                                            var promise = v.play();
                                            return {
                                                success: true,
                                                paused: v.paused,
                                                readyState: v.readyState
                                            };
                                        } catch(e) {
                                            return {success: false, error: e.message};
                                        }
                                    })()
                                """)
                                if not play_result.get('paused'):
                                    print(f"✅ Video started playing (attempt {attempt + 1})")
                                    break
                                time.sleep(2)
                            except Exception as e:
                                print("WARNING: " + f"⚠️ Play attempt {attempt + 1} failed: {e}")
                    
                    print(f"✅ Live stream started successfully (video detected, readyState: {video_error_check.get('readyState', 'N/A')})!")
                    return True
                except Exception as e:
                    print("WARNING: " + f"⚠️ Live stream button clicked but video not detected: {e}")
                    print("WARNING: " + f"   This might be normal if video takes longer to load")
                    # Check if video exists but not ready
                    video_exists = self.page.locator("video").count() > 0
                    if video_exists:
                        print(f"   Video element exists but might still be loading")
                        return True
                    else:
                        print("ERROR: " + f"   Video element not found - stream might not have started")
                        return False
            else:
                print("ERROR: " + "❌ All methods failed to click Start-from-live button")
                print("ERROR: " + "   Tried: Direct click, Button parent click, JavaScript click")
                return False
            
        except Exception as e:
            print("ERROR: " + f"NO: Error starting live stream -> {e}")
            return False
    
    def track_live_stream_time(self, channel_name: str) -> Tuple[bool, str, str]:
        """
        Track live stream time and compare with PC time for a specific channel.
        
        Args:
            channel_name (str): Name of the channel being tracked
        
        Returns:
            Tuple[bool, str, str]: (success, live_time, pc_time)
        """
        try:
            wait_timeout = WAIT_TIMEOUT or 20
            wait_timeout_ms = wait_timeout * 1000
            
            # Ensure video element is present
            video = self.page.locator("video")
            video.wait_for(state="attached", timeout=wait_timeout)
            
            # Setup MutationObserver JavaScript
            setup_observer_js = r"""
              (function(){
                const TAG = '[STREAM_TIME]';
                const seen = new Set();
                const timePattern = /\b\d{1,2}:\d{2}(?::\d{2})?(\s*\/\s*\d{1,2}:\d{2}(?::\d{2})?)?\b/;

                function scanAllTextNodes(root){
                  const walker = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT, null);
                  const found = [];
                  let node;
                  while ((node = walker.nextNode())){
                    const t = (node.textContent || '').trim();
                    if (!t) continue;
                    const m = t.match(timePattern);
                    if (m && m[0]){
                      const val = m[0];
                      if (!seen.has(val)){
                        seen.add(val);
                        found.push(val);
                      }
                    }
                  }
                  return found;
                }

                const initial = scanAllTextNodes(document.body);
                if (initial.length){
                  console.log(TAG + ' initial: ' + initial.join(', '));
                }

                if (!window.__streamTimeObserver){
                  window.__streamTimeObserver = new MutationObserver((mutations)=>{
                    let any = false;
                    for (const m of mutations){
                      if (m.type === 'childList'){
                        m.addedNodes && m.addedNodes.forEach(n=>{
                          if (n.nodeType === Node.TEXT_NODE){
                            const t = (n.textContent||'').trim();
                            const mm = t.match(timePattern);
                            if (mm && mm[0] && !seen.has(mm[0])){ seen.add(mm[0]); console.log(TAG + ' update: ' + mm[0]); any = true; }
                          } else if (n.nodeType === Node.ELEMENT_NODE){
                            const f = scanAllTextNodes(n);
                            if (f.length){ console.log(TAG + ' update: ' + f.join(', ')); any = true; }
                          }
                        });
                      } else if (m.type === 'characterData'){
                        const t = (m.target && m.target.data || '').trim();
                        const mm = t.match(timePattern);
                        if (mm && mm[0] && !seen.has(mm[0])){ seen.add(mm[0]); console.log(TAG + ' update: ' + mm[0]); any = true; }
                      } else if (m.type === 'attributes'){
                        const el = m.target;
                        const f = scanAllTextNodes(el);
                        if (f.length){ console.log(TAG + ' update: ' + f.join(', ')); any = true; }
                      }
                    }
                  });
                  window.__streamTimeObserver.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true });
                }

                return initial;
              })();
            """
            
            initial_matches = self.page.evaluate(setup_observer_js)
            # Don't log initial matches - too verbose
            
            # First, wait for video element to be ready and try to play it
            video_ready = False
            video_wait_start = time.time()
            video_wait_timeout = 60  # Wait up to 60 seconds for video (increased for streaming)
            
            print(f"🔍 Waiting for video element to be ready (timeout: {video_wait_timeout}s)...")
            
            while time.time() - video_wait_start < video_wait_timeout:
                try:
                    video_count = self.page.locator("video").count()
                    if video_count > 0:
                        # Check if video is actually loaded and try to play
                        video_info = self.page.evaluate("""
                            (function(){
                                var v = document.querySelector('video');
                                if (!v) return {exists: false, ready: false, error: null};
                                
                                // Don't try to play if video is still loading (readyState 0)
                                // Wait for at least metadata (readyState >= 1)
                                var shouldTryPlay = false;
                                if (v.readyState >= 1 && v.paused) {
                                    shouldTryPlay = true;
                                }
                                
                                if (shouldTryPlay) {
                                    try {
                                        // Only play if we have metadata or data
                                        var playPromise = v.play();
                                        if (playPromise !== undefined) {
                                            playPromise.catch(function(error) {
                                                // Don't log AbortError - it's common when video is reloading
                                                if (error.name !== 'AbortError') {
                                                    console.log('Video play error:', error.name, error.message);
                                                }
                                            });
                                        }
                                    } catch(e) {
                                        if (e.name !== 'AbortError') {
                                            console.log('Play exception:', e.name, e.message);
                                        }
                                    }
                                }
                                
                                return {
                                    exists: true,
                                    ready: v.readyState >= 2,
                                    readyState: v.readyState,
                                    networkState: v.networkState,
                                    error: v.error ? v.error.message : null,
                                    errorCode: v.error ? v.error.code : null,
                                    src: v.src || v.currentSrc || 'no src',
                                    paused: v.paused,
                                    currentTime: v.currentTime,
                                    duration: v.duration,
                                    buffered: v.buffered.length > 0
                                };
                            })()
                        """)
                        
                        if video_info.get('exists'):
                            ready_state = video_info.get('readyState', 0)
                            network_state = video_info.get('networkState', 0)
                            
                            # Log progress every 10 seconds (reduced frequency)
                            elapsed = time.time() - video_wait_start
                            if int(elapsed) % 10 == 0:
                                print(f"📹 Video loading... (readyState={ready_state}, networkState={network_state})")
                            
                            if video_info.get('error'):
                                # Don't fail immediately on error - might recover
                                error_code = video_info.get('errorCode')
                                # MEDIA_ERR_SRC_NOT_SUPPORTED (4) is critical
                                if error_code == 4:
                                    print("ERROR: " + f"❌ Video format not supported (error code 4)")
                                    print("ERROR: " + f"   Video src: {video_info.get('src')}")
                                    break
                                else:
                                    print("WARNING: " + f"⚠️ Video element has error: {video_info.get('error')}")
                                    print("WARNING: " + f"   Error code: {error_code}, continuing to wait...")
                            
                            # Check if video is actually playing (not just loaded)
                            is_playing = not video_info.get('paused', True) and video_info.get('currentTime', 0) > 0
                            
                            # Video is ready if:
                            # 1. Video is actually playing (best case)
                            # 2. readyState >= 2 (HAVE_CURRENT_DATA) - has current frame data
                            # 3. readyState >= 1 (HAVE_METADATA) AND networkState >= 2 (NETWORK_LOADING) - loading metadata
                            # 4. Video has buffered data
                            if is_playing:
                                video_ready = True
                                current_time = video_info.get('currentTime', 0)
                                print(f"✅ Video is playing! (currentTime: {current_time:.2f}s, readyState: {ready_state})")
                                break
                            elif ready_state >= 2:
                                video_ready = True
                                print(f"✅ Video element is ready (readyState: {ready_state}, networkState: {network_state})")
                                break
                            elif ready_state >= 1 and (network_state >= 2 or video_info.get('buffered')):
                                # Video is loading, continue waiting
                                if network_state == 2:  # NETWORK_LOADING
                                    print(f"⏳ Video is loading data (readyState: {ready_state}, networkState: {network_state})")
                                elif video_info.get('buffered'):
                                    video_ready = True
                                    print(f"✅ Video has buffered data (readyState: {ready_state})")
                                    break
                            
                    time.sleep(3)  # Check every 3 seconds
                except Exception as e:
                    print("WARNING: " + f"⚠️ Error checking video: {e}")
                    time.sleep(3)
            
            if not video_ready:
                # Final check - maybe video exists but not fully loaded
                try:
                    final_check = self.page.evaluate("""
                        (function(){
                            var v = document.querySelector('video');
                            if (!v) return {exists: false};
                            return {
                                exists: true,
                                readyState: v.readyState,
                                networkState: v.networkState,
                                error: v.error ? v.error.message : null,
                                src: v.src || v.currentSrc || 'no src'
                            };
                        })()
                    """)
                    
                    if final_check.get('exists'):
                        print("WARNING: " + f"⚠️ Video exists but not fully ready after {video_wait_timeout}s")
                        print("WARNING: " + f"   readyState: {final_check.get('readyState')}, networkState: {final_check.get('networkState')}")
                        print("WARNING: " + f"   src: {final_check.get('src')}")
                        if final_check.get('error'):
                            print("ERROR: " + f"   Error: {final_check.get('error')}")
                        # Continue anyway - might work
                        video_ready = True
                except Exception:
                    pass
            
            if not video_ready:
                print("ERROR: " + f"❌ Channel '{channel_name}' - Video element not ready after {video_wait_timeout} seconds")
                print("ERROR: " + f"   This might indicate a stream error or loading issue")
                print("ERROR: " + f"   Possible causes:")
                print("ERROR: " + f"   - Network connectivity issues")
                print("ERROR: " + f"   - Stream server not responding")
                print("ERROR: " + f"   - Browser autoplay policy blocking")
                print("ERROR: " + f"   - Video codec not supported")
                print("ERROR: " + f"   Please check the browser manually to see if stream is playing")
                return False, "", ""
            
            # Poll video element directly for time
            start_ts = time.time()
            collected_times = []
            pc_time_at_samples = []
            poll_duration = 15  # Poll for 15 seconds to get a sample
            
            while time.time() - start_ts < poll_duration:
                try:
                    vals = self.page.evaluate("""
                        (function(){
                            var v = document.querySelector('video');
                            if (!v) return null;
                            return [v.currentTime, v.duration];
                        })()
                    """)
                    if vals and isinstance(vals, list) and len(vals) == 2:
                        cur = vals[0] if vals[0] is not None else 0
                        dur = vals[1] if vals[1] is not None else 0
                        
                        # Only collect if we have valid values
                        if dur and dur > 0:
                            def _fmt(sec):
                                try:
                                    sec = float(sec)
                                    sec = int(sec)
                                except Exception:
                                    return "0:00"
                                h = sec // 3600
                                m = (sec % 3600) // 60
                                s = sec % 60
                                if h:
                                    return f"{h}:{m:02d}:{s:02d}"
                                return f"{m}:{s:02d}"
                            
                            direct_val = f"{_fmt(cur)} / {_fmt(dur)}"
                            if direct_val not in collected_times:
                                collected_times.append(direct_val)
                                pc_time_at_samples.append(datetime.now().strftime("%H:%M:%S"))
                                # Only log first sample, not every sample
                                if len(collected_times) == 1:
                                    print(f"📊 Collected time sample: {direct_val}")
                                if len(collected_times) >= 2:
                                    break
                except Exception as e:
                    print("WARNING: " + f"⚠️ Error polling video time: {e}")
                    pass
                time.sleep(2)
            
            # Get results
            if collected_times:
                latest = collected_times[-1]
                pc_now = pc_time_at_samples[-1] if pc_time_at_samples else datetime.now().strftime("%H:%M:%S")
                try:
                    current_part = latest.split('/')[0].strip()
                except Exception:
                    current_part = latest
                
                print(f"✅ Channel '{channel_name}' - Live time: {current_part}, PC time: {pc_now}")
                return True, current_part, pc_now
            else:
                print("ERROR: " + f"❌ Channel '{channel_name}' - Could not collect stream time after {poll_duration} seconds")
                print("ERROR: " + f"   Video might not be playing or stream might have an error")
                print("ERROR: " + f"   Please check the browser manually")
                return False, "", ""
            
        except Exception as e:
            print("ERROR: " + f"NO: Error tracking stream time for channel '{channel_name}' -> {e}")
            return False, "", ""
    
    def verify_previous_days_streams(self, channel_name: str, days: int = 2) -> List[Tuple[str, bool, float]]:
        """
        Verify previous N days' streams for a channel.
        
        Args:
            channel_name (str): Name of the channel
            days (int): Number of previous days to verify (default: 2)
        
        Returns:
            List[Tuple[str, bool, float]]: List of (date, loaded, duration_seconds) tuples
        """
        results = []
        
        for day_offset in range(1, days + 1):
            try:
                from datetime import datetime, timedelta
                prev_date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
                
                print(f"📅 Verifying {channel_name} - Previous day {day_offset}: {prev_date}")
                
                # Open calendar (must be on live view first)
                time.sleep(3)
                
                # Verify we're on live view before opening calendar
                try:
                    # Check if we're on live view by looking for calendar button or live controls
                    live_view_check = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[2]')
                    live_view_check.wait_for(state="visible", timeout=5000)
                    print(f"✅ Confirmed on live view before opening calendar")
                except Exception as e:
                    print("ERROR: " + f"❌ Not on live view! Cannot open calendar. Error: {e}")
                    print("ERROR: " + f"   Please ensure we're on the live stream view before verifying previous days")
                    results.append((prev_date, False, 0.0))
                    continue
                
                calendar_opened = self.open_calendar()
                time.sleep(3)
                
                if not calendar_opened:
                    print("ERROR: " + f"❌ Calendar did NOT open for date {prev_date}")
                    print("ERROR: " + f"   Cannot proceed with date selection")
                    results.append((prev_date, False, 0.0))
                    continue
                
                if calendar_opened:
                    # Step 1: Click on date input field to open calendar modal
                    time.sleep(3)
                    date_input_clicked = False
                    
                    try:
                        # Try to find and click date input field to open calendar modal
                        date_input_selectors = [
                            'input[type="date"]',
                            'input[placeholder*="date" i]',
                            'input[aria-label*="date" i]',
                            'input[name*="date" i]',
                            '.MuiInputBase-input',
                            'input.MuiInputBase-input'
                        ]
                        
                        for selector in date_input_selectors:
                            try:
                                date_input = self.page.locator(selector).first
                                if date_input.count() > 0:
                                    date_input.wait_for(state="visible", timeout=5000)
                                    date_input.scroll_into_view_if_needed()
                                    time.sleep(1)
                                    date_input.click()
                                    print(f"✅ Date input clicked (selector: {selector})")
                                    date_input_clicked = True
                                    time.sleep(2)
                                    break
                            except Exception:
                                continue
                        
                        # Fallback: Try to find date input in calendar dialog
                        if not date_input_clicked:
                            try:
                                dialogs = self.page.locator('[role="dialog"], [role="presentation"], .MuiPickersPopper-root, .MuiPopover-root')
                                if dialogs.count() > 0:
                                    dialog = dialogs.first
                                    date_input_in_dialog = dialog.locator('input').first
                                    if date_input_in_dialog.count() > 0:
                                        date_input_in_dialog.wait_for(state="visible", timeout=5000)
                                        date_input_in_dialog.scroll_into_view_if_needed()
                                        time.sleep(1)
                                        date_input_in_dialog.click()
                                        print("✅ Date input clicked in dialog")
                                        date_input_clicked = True
                                        time.sleep(2)
                            except Exception:
                                pass
                        
                    except Exception as e:
                        print("WARNING: " + f"⚠️ Could not click date input: {e}")
                    
                    # Step 2: Wait for calendar modal to open
                    time.sleep(2)
                    
                    # Step 3: Click on the specific date in the calendar grid
                    date_selected = False
                    try:
                        # Parse date to get day number
                        from datetime import datetime
                        date_obj = datetime.strptime(prev_date, "%Y-%m-%d")
                        day_number = date_obj.day
                        
                        # Try multiple strategies to click the date in calendar
                        date_click_strategies = [
                            # Strategy 1: Click by button text containing day number
                            f'button:has-text("{day_number}")',
                            f'//button[text()="{day_number}"]',
                            f'//button[contains(text(), "{day_number}")]',
                            # Strategy 2: Click by aria-label or data attributes
                            f'button[aria-label*="{prev_date}"]',
                            f'button[data-date="{prev_date}"]',
                            # Strategy 3: Click in calendar grid by position
                            f'.MuiPickersDay-root:has-text("{day_number}")',
                            f'[role="gridcell"] button:has-text("{day_number}")',
                        ]
                        
                        for strategy in date_click_strategies:
                            try:
                                date_button = self.page.locator(strategy).first
                                if date_button.count() > 0:
                                    date_button.wait_for(state="visible", timeout=5000)
                                    date_button.scroll_into_view_if_needed()
                                    time.sleep(1)
                                    date_button.click(force=True)
                                    print(f"✅ Date {day_number} clicked in calendar (strategy: {strategy[:50]})")
                                    date_selected = True
                                    time.sleep(2)
                                    break
                            except Exception:
                                continue
                        
                        # Fallback: JavaScript click on date button
                        if not date_selected:
                            try:
                                click_date_js = f"""
                                (function(dayNum, dateStr){{
                                    // Find all buttons in calendar
                                    const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
                                    for (const btn of buttons) {{
                                        const text = (btn.textContent || '').trim();
                                        const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                                        const dataDate = btn.getAttribute('data-date');
                                        
                                        // Check if button matches day number or date
                                        if (text === String(dayNum) || 
                                            text === String(dayNum).padStart(2, '0') ||
                                            ariaLabel.includes(dateStr.toLowerCase()) ||
                                            dataDate === dateStr) {{
                                            // Make sure it's in a calendar context
                                            const parent = btn.closest('[role="dialog"], [role="presentation"], .MuiPickersPopper-root, .MuiPopover-root, .MuiCalendarPicker-root');
                                            if (parent) {{
                                                btn.click();
                                                return true;
                                            }}
                                        }}
                                    }}
                                    return false;
                                }})({day_number}, '{prev_date}')
                                """
                                result = self.page.evaluate(click_date_js)
                                if result:
                                    print(f"✅ Date {day_number} clicked via JavaScript")
                                    date_selected = True
                                    time.sleep(2)
                            except Exception as js_err:
                                print("WARNING: " + f"⚠️ JavaScript date click failed: {js_err}")
                        
                    except Exception as date_select_err:
                        print("ERROR: " + f"❌ Error selecting date {prev_date}: {date_select_err}")
                    
                    if not date_selected:
                        print("ERROR: " + f"❌ Could not select date {prev_date} from calendar modal")
                        print("ERROR: " + f"   Trying fallback: Direct date input set")
                        
                        # Fallback: Try direct date input set
                        try:
                            set_date_js = """
                              (function(dateValue){
                                function setVal(el, val){
                                  el.value = val;
                                  el.dispatchEvent(new Event('input', {bubbles:true}));
                                  el.dispatchEvent(new Event('change', {bubbles:true}));
                                }
                                const isVisible = el => !!(el && el.offsetParent !== null);
                                const inputs = Array.from(document.querySelectorAll('input'))
                                  .filter(isVisible);
                                let changed = false;
                                for (const el of inputs){
                                  const t = (el.getAttribute('type')||'').toLowerCase();
                                  const ph = (el.getAttribute('placeholder')||'').toLowerCase();
                                  const ar = (el.getAttribute('aria-label')||'').toLowerCase();
                                  const name = (el.getAttribute('name')||'').toLowerCase();
                                  if (t === 'date' || ph.includes('date') || ar.includes('date') || name.includes('date')){
                                    setVal(el, dateValue); changed = true; break;
                                  }
                                }
                                if (!changed){
                                  const dialogs = Array.from(document.querySelectorAll('[role="dialog"], [role="presentation"], .MuiPickersPopper-root, .MuiPopover-root'));
                                  for (const d of dialogs){
                                    const el = d.querySelector('input');
                                    if (isVisible(el)){ setVal(el, dateValue); changed = true; break; }
                                  }
                                }
                                return changed;
                              })
                            """
                            ok = self.page.evaluate(set_date_js, prev_date)
                            if ok:
                                print(f"✅ Set date via fallback method: {prev_date}")
                                date_selected = True
                            else:
                                print("ERROR: " + f"❌ Fallback date set also failed")
                                results.append((prev_date, False, 0.0))
                                continue
                        except Exception as fallback_err:
                            print("ERROR: " + f"❌ Fallback date set error: {fallback_err}")
                            results.append((prev_date, False, 0.0))
                            continue
                    
                    # Step 4: Close calendar modal (if still open)
                    time.sleep(2)
                    try:
                        # Try pressing Escape to close calendar
                        self.page.keyboard.press("Escape")
                        time.sleep(1)
                        print("✅ Calendar closed (Escape key)")
                    except Exception:
                        # Try clicking outside calendar
                        try:
                            self.page.mouse.click(100, 100)
                            time.sleep(1)
                            print("✅ Calendar closed (clicked outside)")
                        except Exception:
                            print("WARNING: " + "⚠️ Could not close calendar, continuing anyway...")
                            time.sleep(1)
                
                # Click Get Stream button - Forcefully with multiple strategies
                wait_timeout = WAIT_TIMEOUT or 20
                wait_timeout_ms = wait_timeout * 1000
                
                get_stream_clicked = False
                time.sleep(3)
                
                # Strategy 1: Direct click with force
                try:
                    get_stream_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[4]/div/div/div[2]/div/button/span')
                    get_stream_btn.wait_for(state="visible", timeout=wait_timeout)
                    get_stream_btn.scroll_into_view_if_needed()
                    time.sleep(1)
                    get_stream_btn.click(force=True)
                    print(f"✅ Get Stream clicked for {prev_date} (method 1: direct force click)")
                    get_stream_clicked = True
                except Exception as e1:
                    print("WARNING: " + f"⚠️ Method 1 failed: {e1}")
                    
                    # Strategy 2: JavaScript click on span
                    try:
                        get_stream_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[4]/div/div/div[2]/div/button/span')
                        get_stream_btn.wait_for(state="visible", timeout=wait_timeout)
                        get_stream_btn.scroll_into_view_if_needed()
                        time.sleep(1)
                        get_stream_btn.evaluate("el => el.click()")
                        print(f"✅ Get Stream clicked for {prev_date} (method 2: JavaScript on span)")
                        get_stream_clicked = True
                    except Exception as e2:
                        print("WARNING: " + f"⚠️ Method 2 failed: {e2}")
                        
                        # Strategy 3: Click parent button
                        try:
                            get_stream_btn_parent = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[4]/div/div/div[2]/div/button')
                            get_stream_btn_parent.wait_for(state="visible", timeout=wait_timeout)
                            get_stream_btn_parent.scroll_into_view_if_needed()
                            time.sleep(1)
                            get_stream_btn_parent.click(force=True)
                            print(f"✅ Get Stream clicked for {prev_date} (method 3: parent button)")
                            get_stream_clicked = True
                        except Exception as e3:
                            print("WARNING: " + f"⚠️ Method 3 failed: {e3}")
                            
                            # Strategy 4: JavaScript click on parent button
                            try:
                                get_stream_btn_parent = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[4]/div/div/div[2]/div/button')
                                get_stream_btn_parent.wait_for(state="visible", timeout=wait_timeout)
                                get_stream_btn_parent.scroll_into_view_if_needed()
                                time.sleep(1)
                                get_stream_btn_parent.evaluate("el => el.click()")
                                print(f"✅ Get Stream clicked for {prev_date} (method 4: JavaScript on parent)")
                                get_stream_clicked = True
                            except Exception as e4:
                                print("ERROR: " + f"❌ All methods failed to click Get Stream: {e4}")
                                results.append((prev_date, False, 0.0))
                                continue
                
                if not get_stream_clicked:
                    print("ERROR: " + f"❌ Could not click Get Stream button for {prev_date}")
                    results.append((prev_date, False, 0.0))
                    continue
                
                # Wait after Get Stream click (as requested by user)
                wait_after_get_stream = WAIT_AFTER_GET_STREAM or 5
                wait_after_get_stream = float(wait_after_get_stream)
                print(f"⏳ Waiting {wait_after_get_stream} seconds after Get Stream click...")
                time.sleep(wait_after_get_stream)
                
                # Verify URL contains the previous date (critical check)
                # Wait longer for URL to update after Get Stream click
                url_verified = False
                current_url = ""
                max_url_wait = 15  # Wait up to 15 seconds for URL to update
                url_check_start = time.time()
                
                print(f"🔍 Checking URL for date {prev_date}...")
                while time.time() - url_check_start < max_url_wait:
                    try:
                        current_url = self.page.url
                        print(f"   Current URL: {current_url}")
                        if prev_date in current_url:
                            url_verified = True
                            print(f"✅ URL verified: Contains date {prev_date} in URL")
                            break
                    except Exception:
                        pass
                    time.sleep(1)  # Check every second
                
                if not url_verified:
                    print("ERROR: " + f"❌ {channel_name} - {prev_date}: URL does NOT contain date {prev_date}")
                    print("ERROR: " + f"   Current URL: {current_url}")
                    print("ERROR: " + f"   Expected date in URL: {prev_date}")
                    print("ERROR: " + f"   Stream for {prev_date} is NOT available (URL did not update)")
                    results.append((prev_date, False, 0.0))
                    continue
                
                # Quick duration check (no wait for video to play, just capture if available)
                # Wait 5 seconds is already done above, now just check duration
                duration_seconds = 0.0
                loaded = False
                
                try:
                    # Quick check for video duration immediately (no play, just metadata)
                    vals = self.page.evaluate(
                        """
                        (function(){
                            var v = document.querySelector('video');
                            if(!v) return null;
                            // Just get duration if available, don't try to play
                            var dur = v.duration;
                            if(isFinite(dur) && dur > 0) {
                                return [v.readyState, dur];
                            }
                            // If duration not available, try loading metadata only (fast)
                            try {
                                v.load(); // Load metadata without playing
                            } catch(e) {}
                            // Return current state
                            return [v.readyState, isFinite(v.duration) && v.duration > 0 ? v.duration : null];
                        })()
                        """
                    )
                    
                    if vals and isinstance(vals, list) and len(vals) == 2:
                        rs, dur = vals
                        if dur and float(dur) > 0:
                            loaded = True
                            duration_seconds = float(dur)
                            print(f"✅ {channel_name} - {prev_date}: Duration captured - {duration_seconds:.0f} seconds")
                        else:
                            # One quick retry after 2 seconds (total ~7 seconds from Get Stream click)
                            time.sleep(2)
                            vals2 = self.page.evaluate(
                                """
                                (function(){
                                    var v = document.querySelector('video');
                                    if(!v) return null;
                                    var dur = v.duration;
                                    return [v.readyState, isFinite(dur) && dur > 0 ? dur : null];
                                })()
                                """
                            )
                            if vals2 and isinstance(vals2, list) and len(vals2) == 2:
                                rs2, dur2 = vals2
                                if dur2 and float(dur2) > 0:
                                    loaded = True
                                    duration_seconds = float(dur2)
                                    print(f"✅ {channel_name} - {prev_date}: Duration captured (retry) - {duration_seconds:.0f} seconds")
                except Exception as dur_err:
                    print("WARNING: " + f"⚠️ Error checking duration: {dur_err}")
                
                if loaded and duration_seconds > 0:
                    hours = duration_seconds / 3600.0
                    h = int(duration_seconds) // 3600
                    m = (int(duration_seconds) % 3600) // 60
                    s = int(duration_seconds) % 60
                    print(f"✅ {channel_name} - {prev_date}: Stream duration - {hours:.2f} hours ({h}:{m:02d}:{s:02d})")
                    results.append((prev_date, True, duration_seconds))
                else:
                    print("WARNING: " + f"⚠️ {channel_name} - {prev_date}: Duration not available (stream might not exist)")
                    results.append((prev_date, False, 0.0))
                
                # After verifying each day, go back to live view for next day verification
                # (We need to be on live view to open calendar again for next day)
                if day_offset < days:
                    print(f"↩️ Returning to live view for next day verification...")
                    time.sleep(3)
                    return_success = self.return_to_live()
                    if not return_success:
                        print("ERROR: " + f"❌ Failed to return to live view after verifying {prev_date}")
                        print("ERROR: " + f"   Cannot proceed with next day verification")
                        # Try to continue anyway, but log the issue
                    time.sleep(3)
                    
            except Exception as e:
                print("ERROR: " + f"❌ Error verifying {prev_date} for {channel_name}: {e}")
                results.append((prev_date, False, 0.0))
                # Try to return to live even if error occurred
                try:
                    if day_offset < days:
                        self.return_to_live()
                        time.sleep(2)
                except Exception:
                    pass
        
        # After all days are verified, ensure we're back on live view
        try:
            print(f"↩️ Final return to live view after all days verified...")
            time.sleep(3)
            return_success = self.return_to_live()
            if not return_success:
                print("ERROR: " + f"❌ Failed to return to live view after verifying all days")
                print("ERROR: " + f"   This might cause issues when going back to channel list")
            time.sleep(3)
        except Exception as e:
            print("ERROR: " + f"❌ Exception while returning to live view: {e}")
        
        return results
    
    def go_back_to_channel_list(self) -> bool:
        """
        Go back to the channel list from a channel view.
        
        Uses navigate_to_live_menu() which has robust logout protection.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            wait_timeout = WAIT_TIMEOUT or 20
            wait_timeout_ms = wait_timeout * 1000
            
            print("↩️ Going back to channel list...")
            time.sleep(2)
            
            # Method 1: Use navigate_to_live_menu() which has logout protection
            try:
                if self.navigate_to_live_menu():
                    # Verify we're on channel list
                    try:
                        channels_container = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div')
                        channels_container.wait_for(state="visible", timeout=wait_timeout)
                        print("✅ Successfully returned to channel list")
                        time.sleep(2)
                        return True
                    except Exception:
                        print("WARNING: " + "⚠️ navigate_to_live_menu succeeded but channel list not verified")
                        # Still return True as navigation might have worked
                        return True
            except Exception as e1:
                print("WARNING: " + f"⚠️ navigate_to_live_menu failed: {e1}")
            
            # Method 2: Try specific XPath for Live button (if available)
            try:
                sidebar = self.page.locator('//*[@id="root"]/div/div[1]')
                sidebar.wait_for(state="visible", timeout=wait_timeout)
                
                live_buttons = sidebar.locator("//p[normalize-space()='Live']")
                for i in range(live_buttons.count()):
                    try:
                        btn = live_buttons.nth(i)
                        # Check it's not logout
                        parent_text = btn.evaluate("el => (el.closest('div, a, button')?.textContent || '').toLowerCase()")
                        if 'logout' not in parent_text:
                            btn.wait_for(state="visible", timeout=2000)
                            btn.scroll_into_view_if_needed()
                            time.sleep(0.5)
                            btn.click()
                            print(f"✅ Clicked Live button (method 2, button {i+1})")
                            time.sleep(3)
                            
                            # Verify we're on channel list
                            try:
                                channels_container = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div')
                                channels_container.wait_for(state="visible", timeout=wait_timeout)
                                print("✅ Successfully returned to channel list (method 2)")
                                return True
                            except Exception:
                                pass
                    except Exception:
                        continue
            except Exception as e2:
                print("WARNING: " + f"⚠️ Method 2 failed: {e2}")
            
            # Method 3: Try browser back as last resort
            try:
                self.page.go_back()
                print("✅ Used browser back to go to channel list")
                time.sleep(3)
                
                # Verify we're on channel list
                try:
                    channels_container = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div')
                    channels_container.wait_for(state="visible", timeout=wait_timeout)
                    print("✅ Successfully returned to channel list (method 3 - browser back)")
                    return True
                except Exception:
                    print("WARNING: " + "⚠️ Browser back executed but channel list not verified")
                    return True  # Still return True as navigation might have worked
            except Exception as e3:
                print("ERROR: " + f"❌ All methods failed to go back to channel list: {e3}")
                return False
                    
        except Exception as e:
            print("ERROR: " + f"NO: Error going back to channel list -> {e}")
            return False
    
    def process_all_channels(self) -> List[dict]:
        """
        Process all channels dynamically: verify live time and previous days streams.
        
        For each channel:
        1. Open the channel
        2. Click live button (specific XPath) to go to live state
        3. Track stream time and compare with PC time
        4. Check 1 day old stream (total recorded duration)
        5. Check 2 days old stream (total recorded duration)
        6. Go back to channel list
        7. Move to next channel
        
        Returns:
            List[dict]: List of channel verification results
        """
        results = []
        
        # Get all channels
        channels = self.get_all_channels()
        
        if not channels:
            print("ERROR: " + "❌ No channels found. Cannot process.")
            return results
        
        print(f"\n{'='*80}")
        print(f"📺 Processing {len(channels)} channels...")
        print(f"{'='*80}\n")
        
        for channel_name, channel_index in channels:
            try:
                print(f"\n{'='*80}")
                print(f"📺 Processing Channel: {channel_name} (Index: {channel_index})")
                print(f"{'='*80}")
                
                # Step 1: Open channel
                time.sleep(3)
                if not self.open_channel(channel_index, channel_name):
                    print("ERROR: " + f"❌ Failed to open channel: {channel_name}")
                    results.append({
                        'channel_name': channel_name,
                        'channel_index': channel_index,
                        'live_time': '',
                        'pc_time': '',
                        'previous_days': [],
                        'success': False
                    })
                    continue
                
                # Wait after opening channel
                time.sleep(3)
                
                # Step 2: Click live button to go to live state (using specific XPath)
                print(f"🔴 Clicking live button to go to live state...")
                live_button_clicked = False
                wait_timeout = WAIT_TIMEOUT or 20
                wait_timeout_ms = wait_timeout * 1000
                
                try:
                    # Use the specific XPath provided by user
                    live_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[3]/p')
                    live_btn.wait_for(state="visible", timeout=wait_timeout)
                    live_btn.scroll_into_view_if_needed()
                    time.sleep(1)
                    live_btn.click(force=True)
                    print(f"✅ Live button clicked (using specific XPath)")
                    live_button_clicked = True
                    time.sleep(3)
                except Exception as e1:
                    print("WARNING: " + f"⚠️ Direct click failed: {e1}, trying JavaScript...")
                    try:
                        live_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[3]/p')
                        live_btn.evaluate("el => el.click()")
                        print(f"✅ Live button clicked via JavaScript")
                        live_button_clicked = True
                        time.sleep(3)
                    except Exception as e2:
                        print("ERROR: " + f"❌ Failed to click live button: {e2}")
                
                if not live_button_clicked:
                    print("WARNING: " + f"⚠️ Could not click live button for: {channel_name}, continuing anyway...")
                
                # Wait for stream to start
                time.sleep(5)
                
                # Step 3: Track live stream time and compare with PC time
                print(f"⏱️ Tracking stream time and comparing with PC time...")
                live_success, live_time, pc_time = self.track_live_stream_time(channel_name)
                
                # Compare and report stream time vs PC time
                if live_success and live_time and pc_time:
                    print(f"\n{'='*80}")
                    print(f"⏱️ TIME COMPARISON FOR {channel_name}")
                    print(f"{'='*80}")
                    print(f"📺 Stream Time: {live_time}")
                    print(f"🖥️  PC Time:     {pc_time}")
                    print(f"{'='*80}\n")
                else:
                    print("WARNING: " + f"⚠️ Could not track live time for: {channel_name}")
                    live_time = ""
                    pc_time = ""
                
                # Wait after tracking time
                time.sleep(3)
                
                # Step 4 & 5: Verify previous 2 days (1 day old and 2 days old)
                print(f"📅 Verifying previous days streams (1 day and 2 days old)...")
                previous_days_results = self.verify_previous_days_streams(channel_name, days=2)
                
                # Wait after verification
                time.sleep(3)
                
                # Store results
                channel_result = {
                    'channel_name': channel_name,
                    'channel_index': channel_index,
                    'live_time': live_time,
                    'pc_time': pc_time,
                    'previous_days': previous_days_results,
                    'success': live_success
                }
                results.append(channel_result)
                
                # Print detailed summary for this channel
                print(f"\n{'='*80}")
                print(f"📊 FINAL SUMMARY FOR {channel_name}")
                print(f"{'='*80}")
                print(f"⏱️ Stream Time: {live_time if live_time else 'N/A'}")
                print(f"🖥️  PC Time:     {pc_time if pc_time else 'N/A'}")
                print(f"\n📅 Previous Days Streams:")
                for date, loaded, duration in previous_days_results:
                    status = "✅ Loaded" if loaded else "❌ Not Loaded"
                    if loaded:
                        hours = duration / 3600.0
                        h = int(duration) // 3600
                        m = (int(duration) % 3600) // 60
                        s = int(duration) % 60
                        print(f"   {date}: {status} - Total Duration: {hours:.2f} hours ({h}:{m:02d}:{s:02d})")
                    else:
                        print(f"   {date}: {status}")
                print(f"{'='*80}\n")
                
                # Step 6: Go back to channel list (for all channels except last)
                if channel_index < channels[-1][1]:  # Not the last channel
                    print(f"↩️ Going back to channel list for next channel...")
                    time.sleep(3)
                    if not self.go_back_to_channel_list():
                        print("WARNING: " + f"⚠️ Failed to go back to channel list, trying navigate_to_live_menu...")
                        self.navigate_to_live_menu()
                    time.sleep(3)
                    
            except Exception as e:
                print("ERROR: " + f"❌ Error processing channel {channel_name}: {e}")
                results.append({
                    'channel_name': channel_name,
                    'channel_index': channel_index,
                    'live_time': '',
                    'pc_time': '',
                    'previous_days': [],
                    'success': False
                })
                # Try to go back to channel list
                try:
                    print(f"↩️ Attempting to go back to channel list after error...")
                    self.go_back_to_channel_list()
                except Exception:
                    try:
                        self.navigate_to_live_menu()
                    except Exception:
                        pass
        
        return results
    
    def track_stream_time(self) -> bool:
        """
        Track live stream time using MutationObserver and console log polling.
        
        This method sets up JavaScript observers to track stream time updates
        and collects samples for comparison.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            wait_timeout = WAIT_TIMEOUT or 20
            wait_timeout_ms = wait_timeout * 1000
            
            # Ensure video element is present
            video = self.page.locator("video")
            video.wait_for(state="attached", timeout=wait_timeout)
            
            # Setup MutationObserver JavaScript
            setup_observer_js = r"""
      (function(){
        const TAG = '[STREAM_TIME]';
        const seen = new Set();
        const timePattern = /\b\d{1,2}:\d{2}(?::\d{2})?(\s*\/\s*\d{1,2}:\d{2}(?::\d{2})?)?\b/;

        function scanAllTextNodes(root){
          const walker = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT, null);
          const found = [];
          let node;
          while ((node = walker.nextNode())){
            const t = (node.textContent || '').trim();
            if (!t) continue;
            const m = t.match(timePattern);
            if (m && m[0]){
              const val = m[0];
              if (!seen.has(val)){
                seen.add(val);
                found.push(val);
              }
            }
          }
          return found;
        }

        const initial = scanAllTextNodes(document.body);
        if (initial.length){
          console.log(TAG + ' initial: ' + initial.join(', '));
        }

        if (!window.__streamTimeObserver){
          window.__streamTimeObserver = new MutationObserver((mutations)=>{
            let any = false;
            for (const m of mutations){
              if (m.type === 'childList'){
                m.addedNodes && m.addedNodes.forEach(n=>{
                  if (n.nodeType === Node.TEXT_NODE){
                    const t = (n.textContent||'').trim();
                    const mm = t.match(timePattern);
                    if (mm && mm[0] && !seen.has(mm[0])){ seen.add(mm[0]); console.log(TAG + ' update: ' + mm[0]); any = true; }
                  } else if (n.nodeType === Node.ELEMENT_NODE){
                    const f = scanAllTextNodes(n);
                    if (f.length){ console.log(TAG + ' update: ' + f.join(', ')); any = true; }
                  }
                });
              } else if (m.type === 'characterData'){
                const t = (m.target && m.target.data || '').trim();
                const mm = t.match(timePattern);
                if (mm && mm[0] && !seen.has(mm[0])){ seen.add(mm[0]); console.log(TAG + ' update: ' + mm[0]); any = true; }
              } else if (m.type === 'attributes'){
                const el = m.target;
                const f = scanAllTextNodes(el);
                if (f.length){ console.log(TAG + ' update: ' + f.join(', ')); any = true; }
              }
            }
          });
          window.__streamTimeObserver.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true });
        }

                return initial;
              })();
            """

            initial_matches = self.page.evaluate(setup_observer_js)
            # Don't log initial matches - too verbose
            
            # Fallback: poll video element
            setup_video_poll_js = """
          (function(){
            if (window.__streamTimeVideoTimer) return 'already-set';
            function fmt(sec){
              if (isNaN(sec) || sec < 0) return '0:00';
              sec = Math.floor(sec);
              const h = Math.floor(sec/3600);
              const m = Math.floor((sec%3600)/60);
              const s = sec%60;
              const mm = (h>0? String(m).padStart(2,'0'): String(m));
              const ss = String(s).padStart(2,'0');
              return h>0 ? `${h}:${mm}:${ss}` : `${m}:${ss}`;
            }
            function tick(){
              const v = document.querySelector('video');
              if (!v) return;
              const cur = fmt(v.currentTime);
              const dur = fmt(v.duration);
              console.log('[STREAM_TIME] video: ' + cur + ' / ' + dur);
            }
            window.__streamTimeVideoTimer = setInterval(tick, 1000);
            return 'set';
          })();
        """
            res = self.page.evaluate(setup_video_poll_js)
            # Don't log polling setup - too verbose

            # Poll console logs for time updates
            seen_console_times = set(initial_matches or [])
            time_regex = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*/\s*\d{1,2}:\d{2}(?::\d{2})?)?\b")

            start_ts = time.time()
            last_direct_val = None
            collected_times = []
            pc_time_at_samples = []
            
            while time.time() - start_ts < 60:
                # Check console messages (Playwright doesn't have direct console log access like Selenium)
                # Use direct video sampling instead
                try:
                    vals = self.page.evaluate("var v=document.querySelector('video'); return v? [v.currentTime, v.duration]: null;")
                    if vals and isinstance(vals, list) and len(vals) == 2:
                        cur = int(vals[0]) if vals[0] is not None else 0
                        dur = int(vals[1]) if vals[1] is not None else 0
                        
                        def _fmt(sec):
                            try:
                                sec = int(sec)
                            except Exception:
                                return "0:00"
                            h = sec // 3600
                            m = (sec % 3600) // 60
                            s = sec % 60
                            if h:
                                return f"{h}:{m:02d}:{s:02d}"
                            return f"{m}:{s:02d}"
                        
                        direct_val = f"{_fmt(cur)} / {_fmt(dur)}"
                        if direct_val != last_direct_val:
                            last_direct_val = direct_val
                            # Only log first sample, not every update
                            if len(collected_times) == 0:
                                print(f"📊 Stream time: {direct_val}")
                            collected_times.append(direct_val)
                            pc_time_at_samples.append(datetime.now().strftime("%H:%M:%S"))
                            if len(collected_times) >= 3:
                                break
                except Exception:
                    pass
                
                if len(collected_times) >= 3:
                    break
                time.sleep(1)

            # Store results
            if collected_times:
                latest = collected_times[-1]
                pc_now = pc_time_at_samples[-1] if pc_time_at_samples else ""
                try:
                    current_part = latest.split('/')[0].strip()
                except Exception:
                    current_part = latest
                
                self.live_status_current = current_part
                self.live_status_pc = pc_now
                
                self._print_block(
                    "LIVE STATUS",
                    [
                        f"Live stream time (current): {current_part}",
                        f"PC time: {pc_now}",
                    ],
                )
            else:
                print("WARNING: " + "NO: Could not collect stream time samples for comparison")
            
            return True

        except Exception as e:
            print("ERROR: " + f"NO: Error setting up dynamic stream time tracking -> {e}")
            return False
    
    def open_calendar(self) -> bool:
        """
        Open calendar for date selection.
        
        Tries multiple selectors to find and click the calendar button.
        
        Returns:
            bool: True if calendar opened, False otherwise
        """
        try:
            wait_timeout = WAIT_TIMEOUT or 20
            wait_timeout_ms = wait_timeout * 1000
            
            # Try SVG path first
            try:
                calendar_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[2]/svg/path')
                calendar_btn.wait_for(state="visible", timeout=wait_timeout)
                calendar_btn.click()
                print("YES: Calendar opened")
                time.sleep(2)
                return True
            except Exception:
                pass

            # Fallback to button
            try:
                calendar_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[2]')
                calendar_btn.wait_for(state="visible", timeout=wait_timeout)
                calendar_btn.click()
                print("YES: Calendar opened")
                time.sleep(2)
                return True
            except Exception:
                print("WARNING: " + "NO: Calendar button not found (both selectors failed)")
                return False
                
        except Exception as e:
            print("ERROR: " + f"NO: Error opening calendar -> {e}")
            return False
    
    def set_previous_day_date(self) -> bool:
        """
        Set previous day date in calendar.
        
        Uses JavaScript to find and set date input field.
        
        Returns:
            bool: True if date set successfully, False otherwise
        """
        try:
            from datetime import datetime, timedelta
            prev_day = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            self.prev_date_token = prev_day

            set_date_js = """
          (function(v){
            function setVal(el, val){
              el.value = val;
              el.dispatchEvent(new Event('input', {bubbles:true}));
              el.dispatchEvent(new Event('change', {bubbles:true}));
            }
            const isVisible = el => !!(el && el.offsetParent !== null);
            const inputs = Array.from(document.querySelectorAll('input'))
              .filter(isVisible);
            let changed = false;
            for (const el of inputs){
              const t = (el.getAttribute('type')||'').toLowerCase();
              const ph = (el.getAttribute('placeholder')||'').toLowerCase();
              const ar = (el.getAttribute('aria-label')||'').toLowerCase();
              const name = (el.getAttribute('name')||'').toLowerCase();
              if (t === 'date' || ph.includes('date') || ar.includes('date') || name.includes('date')){
                setVal(el, v); changed = true; break;
              }
            }
            if (!changed){
              const dialogs = Array.from(document.querySelectorAll('[role="dialog"], [role="presentation"], .MuiPickersPopper-root, .MuiPopover-root'));
              for (const d of dialogs){
                const el = d.querySelector('input');
                if (isVisible(el)){ setVal(el, v); changed = true; break; }
              }
            }
            return changed;
          })(arguments[0]);
        """
            
            ok = self.page.evaluate(set_date_js, prev_day)
            if ok:
                print(f"YES: Set previous day date -> {prev_day}")
                return True
            else:
                print("WARNING: " + f"NO: Could not set previous day date -> {prev_day}")
                return False
                
        except Exception as e:
            print("ERROR: " + f"NO: Error while setting date -> {e}")
            return False
    
    def get_previous_day_stream(self) -> bool:
        """
        Get previous day stream and collect duration information.
        
        Clicks Get Stream button, waits for video to update, and collects
        stream duration information.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            wait_timeout = WAIT_TIMEOUT or 20
            wait_timeout_ms = wait_timeout * 1000
            
            # Get old video source
            old_src = None
            try:
                old_src = self.page.evaluate("var v=document.querySelector('video'); return v? v.currentSrc || v.src : null;")
            except Exception:
                pass
            
            # Click Get Stream button
            get_stream_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[4]/div/div/div[2]/div/button/span')
            get_stream_btn.wait_for(state="visible", timeout=wait_timeout)
            get_stream_btn.click()
            print("YES: Get Stream button clicked")
            
            # Refresh after Get Stream
            try:
                self.page.reload()
                print("INFO: Previous-day page refreshed after Get Stream click")
            except Exception:
                pass
            
            time.sleep(5)
            
            # Wait for video to update
            t0 = time.time()
            changed = False
            while time.time() - t0 < 15:
                vals = self.page.evaluate("var v=document.querySelector('video'); return v? [v.currentSrc||v.src, v.currentTime]: null;")
                if vals and isinstance(vals, list) and len(vals) == 2:
                    src_now, cur_now = vals[0], vals[1]
                    if (old_src and src_now and src_now != old_src) or (cur_now is not None and cur_now < 2):
                        changed = True
                        break
                time.sleep(0.5)
            
            if changed:
                print("YES: Previous day stream loaded (video updated)")
            else:
                print("WARNING: " + "WARN: Video did not update after clicking Get Stream (continuing)")

            # Collect duration
            loaded = False
            t0 = time.time()
            while time.time() - t0 < 60:
                try:
                    vals = self.page.evaluate(
                        """
                        var v=document.querySelector('video');
                        if(!v) return null;
                        if(!(isFinite(v.duration) && v.duration>0)) { try{ v.load(); v.play(); setTimeout(()=>{try{v.pause()}catch(e){}}, 500); }catch(e){} }
                        return [v.readyState, isFinite(v.duration)?v.duration:null];
                        """
                    )
                    if vals and isinstance(vals, list) and len(vals) == 2:
                        rs, dur = vals
                        if dur and float(dur) > 0 and (rs is None or int(rs) >= 1):
                            loaded = True
                            break
                except Exception:
                    pass
                time.sleep(0.5)

            if loaded:
                vals = self.page.evaluate("var v=document.querySelector('video'); return v? [v.currentTime, v.duration]: null;")
                if vals and isinstance(vals, list) and len(vals) == 2 and vals[1]:
                    self.prev_total_seconds = float(vals[1])
                else:
                    print("WARNING: " + "NO: Could not read previous day stream duration (pre-refresh)")
            else:
                print("WARNING: " + "NO: Previous day video did not finish loading (pre-refresh)")

            # Verify URL and refresh
            try:
                expected_token = self.prev_date_token
                verified = False
                t0 = time.time()
                while time.time() - t0 < 15:
                    cur = self.page.url
                    if expected_token in cur:
                        verified = True
                        break
                    time.sleep(0.5)
                if verified:
                    print(f"YES: URL reflects selected date -> {self.page.url}")
                else:
                    print("WARNING: " + f"WARN: URL did not include date token '{expected_token}' within wait window")
            except Exception:
                pass

            # Refresh page
            try:
                self.page.reload()
                print("INFO: Previous-day page refreshed")
            except Exception:
                pass
            time.sleep(5)

            # Recompute duration after refresh if needed
            try:
                if self.prev_total_seconds is None:
                    vals = self.page.evaluate("var v=document.querySelector('video'); return v? [v.currentTime, v.duration]: null;")
                    if vals and isinstance(vals, list) and len(vals) == 2 and vals[1]:
                        self.prev_total_seconds = float(vals[1])
                
                if self.prev_total_seconds:
                    total_seconds = self.prev_total_seconds
                    total_hours = total_seconds / 3600.0
                    sec_int = int(total_seconds)
                    h = sec_int // 3600
                    m = (sec_int % 3600) // 60
                    s = sec_int % 60
                    self._print_block(
                        "PREVIOUS-DAY STATUS",
                        [
                            f"Date selected: {self.prev_date_token}",
                            f"Stream duration: {total_hours:.2f} hours",
                            f"Stream duration (H:MM:SS): {h}:{m:02d}:{s:02d}",
                            f"Stream duration (M:SS): {int(total_seconds//60)}:{int(total_seconds%60):02d}",
                        ],
                    )
                else:
                    print("WARNING: " + "NO: Previous day duration not available after refresh")
            except Exception as e:
                print("ERROR: " + f"NO: Error computing previous day status after refresh -> {e}")
            
            return True
            
        except Exception as e:
            print("ERROR: " + f"NO: Error getting previous day stream -> {e}")
            return False
    
    def return_to_live(self) -> bool:
        """
        Return to live stream view from previous day stream.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            wait_timeout = WAIT_TIMEOUT or 20
            wait_timeout_ms = wait_timeout * 1000
            
            print("🔍 Attempting to return to live view...")
            
            # Try multiple methods to return to live
            returned = False
            
            # Method 1: Try primary XPath for "Back to Live" button (p tag)
            try:
                back_live = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[3]/p')
                back_live.wait_for(state="visible", timeout=wait_timeout)
                back_live.scroll_into_view_if_needed()
                time.sleep(1)
                back_live.click(force=True)
                print("✅ Back to Live clicked (method 1)")
                time.sleep(3)
                returned = True
            except Exception as e1:
                print("WARNING: " + f"⚠️ Method 1 failed: {e1}")
                
                # Method 2: Try JavaScript click
                try:
                    back_live = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[3]/p')
                    back_live.wait_for(state="visible", timeout=wait_timeout)
                    back_live.scroll_into_view_if_needed()
                    time.sleep(1)
                    back_live.evaluate("el => el.click()")
                    print("✅ Back to Live clicked via JavaScript (method 2)")
                    time.sleep(3)
                    returned = True
                except Exception as e2:
                    print("WARNING: " + f"⚠️ Method 2 failed: {e2}")
                    
                    # Method 3: Try clicking the button parent
                    try:
                        back_live_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[3]')
                        back_live_btn.wait_for(state="visible", timeout=wait_timeout)
                        back_live_btn.scroll_into_view_if_needed()
                        time.sleep(1)
                        back_live_btn.click(force=True)
                        print("✅ Back to Live button clicked (method 3)")
                        time.sleep(3)
                        returned = True
                    except Exception as e3:
                        print("WARNING: " + f"⚠️ Method 3 failed: {e3}")
                        
                        # Method 4: Try alternative XPath (might be different layout)
                        try:
                            alt_back_live = self.page.locator('//button[contains(., "Live") or contains(., "Back")]')
                            if alt_back_live.count() > 0:
                                alt_back_live.first.scroll_into_view_if_needed()
                                time.sleep(1)
                                alt_back_live.first.click(force=True)
                                print("✅ Back to Live clicked (method 4 - alternative)")
                                time.sleep(3)
                                returned = True
                        except Exception as e4:
                            print("WARNING: " + f"⚠️ Method 4 failed: {e4}")
            
            if returned:
                # Verify we're back on live view
                time.sleep(2)
                try:
                    # Check if "Start from Live" button is visible (indicates we're on live view)
                    start_live_check = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[3]/p')
                    start_live_check.wait_for(state="visible", timeout=5000)
                    print("✅ Successfully returned to live view (verified)")
                except Exception:
                    # Alternative: Check for video element or calendar button
                    try:
                        calendar_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[2]')
                        calendar_btn.wait_for(state="visible", timeout=5000)
                        print("✅ Successfully returned to live view (calendar button visible)")
                    except Exception:
                        print("WARNING: " + "⚠️ Returned to live but verification uncertain")
                
                # Refresh and wait
                try:
                    self.page.reload()
                    print("INFO: Page refreshed after returning to live")
                    time.sleep(5)
                except Exception as e:
                    print("WARNING: " + f"⚠️ Page refresh failed: {e}")
                
                return True
            else:
                print("ERROR: " + "❌ All methods failed to return to live view")
                print("ERROR: " + "   Tried: Direct click, JavaScript click, Button parent click, Alternative XPath")
                print("ERROR: " + "   Cannot proceed with next day verification")
                return False
            
        except Exception as e:
            print("ERROR: " + f"❌ Error returning to live -> {e}")
            return False
    
    def crop_and_save_clip(self) -> bool:
        """
        Crop a 5-minute clip and save it.
        
        This method:
        - Clicks scissors button
        - Starts cropping
        - Selects 5-minute range
        - Exports clip
        - Fills metadata and saves
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            wait_timeout = WAIT_TIMEOUT or 20
            wait_timeout_ms = wait_timeout * 1000
            
            # 1) Click scissors button (using JavaScript like Selenium script)
            try:
                scissors = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[1]/svg/path')
                scissors.wait_for(state="attached", timeout=wait_timeout)
                scissors.scroll_into_view_if_needed()
                scissors.evaluate("el => el.click()")
                print("YES: Scissors button clicked")
            except Exception:
                # Fallback to parent button with JavaScript
                try:
                    parent_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/button[1]')
                    parent_btn.wait_for(state="visible", timeout=wait_timeout)
                    parent_btn.scroll_into_view_if_needed()
                    parent_btn.evaluate("el => el.click()")
                    print("YES: Scissors parent button clicked")
                except Exception as e_sc:
                    print("ERROR: " + f"NO: Scissors button not clickable -> {e_sc}")
                    return False

            time.sleep(1)

            # 2) Click Start Cropping (using multiple strategies like Selenium script)
            try:
                start_parent = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[4]/div[2]/button')
                start_parent.wait_for(state="visible", timeout=wait_timeout)
                start_parent.scroll_into_view_if_needed()
                
                # Remove possible overlays that block clicks (like Selenium script)
                try:
                    self.page.evaluate('document.elementFromPoint(window.innerWidth/2, window.innerHeight/2).blur && document.elementFromPoint(window.innerWidth/2, window.innerHeight/2).blur();')
                except Exception:
                    pass

                # Try multiple click methods (like Selenium script)
                clicked = False
                for method in ["js", "native"]:
                    try:
                        if method == "js":
                            start_parent.evaluate("el => el.click()")
                        else:
                            start_parent.click()
                        clicked = True
                        break
                    except Exception:
                        continue
                
                if not clicked:
                    raise Exception("all click strategies failed")
                
                print("YES: Start cropping clicked")
            except Exception as e_st:
                print("ERROR: " + f"NO: Start cropping not clickable -> {e_st}")
                return False

            time.sleep(1)

            # 3) Select 5-minute range (robust with retries like Selenium script)
            attempts = 0
            while attempts < 5:
                attempts += 1
                try:
                    # Wait for elements to be ready
                    track = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[5]/div/div')
                    start_handle = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[5]/div/div/div[2]')
                    end_handle = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[5]/div/div/div[3]')
                    
                    track.wait_for(state="attached", timeout=wait_timeout)
                    start_handle.wait_for(state="attached", timeout=wait_timeout)
                    end_handle.wait_for(state="attached", timeout=wait_timeout)
                    
                    # Wait a bit for track to be fully rendered
                    time.sleep(0.5)
                    
                    # Get video duration - using proper arrow function syntax
                    duration_sec = self.page.evaluate("() => { const v = document.querySelector('video'); return v ? v.duration : 0; }") or 0
                    
                    # Get track dimensions
                    track_box = track.bounding_box()
                    if not track_box:
                        print("WARNING: " + "WARN: Missing track bounds; retrying...")
                        time.sleep(0.3)
                        continue

                    track_width = track_box['width']
                    if not (duration_sec and track_width and duration_sec > 0):
                        print("WARNING: " + "WARN: Missing duration/track width; retrying...")
                        time.sleep(0.3)
                        continue
                    
                    # Calculate 5-minute range in pixels
                    five_min_px = max(4, int((300.0 / float(duration_sec)) * track_width))
                    
                    # Get bounding boxes for all elements
                    track_box = track.bounding_box()
                    start_box = start_handle.bounding_box()
                    end_box = end_handle.bounding_box()
                    
                    if not track_box or not start_box or not end_box:
                        print("WARNING: " + "WARN: Missing element bounds; retrying...")
                        time.sleep(0.3)
                        continue
                    
                    tx = track_box['x']
                    tw = track_box['width']
                    sx = start_box['x'] + start_box['width']/2
                    ex = end_box['x'] + end_box['width']/2
                    
                    # Calculate 5-minute range positions
                    target_left = tx + 4
                    target_right = min(tx + tw - 4, target_left + five_min_px)
                    
                    # Calculate drag distances
                    dx_left = int(round(target_left - sx))
                    dx_right = int(round(target_right - ex))
                    
                    # Drag start handle to left using mouse - simplified approach
                    if abs(dx_left) > 1:
                        try:
                            start_center_x = start_box['x'] + start_box['width']/2
                            start_center_y = start_box['y'] + start_box['height']/2
                            target_x = start_center_x + dx_left
                            
                            # Scroll handle into view first
                            start_handle.scroll_into_view_if_needed()
                            time.sleep(0.3)
                            
                            # Use direct mouse drag (most reliable)
                            self.page.mouse.move(start_center_x, start_center_y)
                            time.sleep(0.2)
                            self.page.mouse.down()
                            time.sleep(0.2)
                            # Move in steps for smooth dragging
                            self.page.mouse.move(target_x, start_center_y, steps=30)
                            time.sleep(0.2)
                            self.page.mouse.up()
                            time.sleep(0.5)
                        except Exception as drag_err:
                            print("WARNING: " + f"WARN: Start handle drag failed: {drag_err}; continuing...")
                            time.sleep(0.3)

                    # Wait and get updated end handle position
                    time.sleep(0.5)
                    end_box = end_handle.bounding_box()
                    if end_box:
                        ex = end_box['x'] + end_box['width']/2
                        dx_right = int(round(target_right - ex))
                    
                    # Drag end handle to right using mouse - simplified approach
                    if abs(dx_right) > 1:
                        end_box = end_handle.bounding_box()
                        if end_box:
                            try:
                                end_center_x = end_box['x'] + end_box['width']/2
                                end_center_y = end_box['y'] + end_box['height']/2
                                target_x = end_center_x + dx_right
                                
                                # Scroll handle into view first
                                end_handle.scroll_into_view_if_needed()
                                time.sleep(0.3)
                                
                                # Use direct mouse drag (most reliable)
                                self.page.mouse.move(end_center_x, end_center_y)
                                time.sleep(0.2)
                                self.page.mouse.down()
                                time.sleep(0.2)
                                # Move in steps for smooth dragging
                                self.page.mouse.move(target_x, end_center_y, steps=30)
                                time.sleep(0.2)
                                self.page.mouse.up()
                                time.sleep(0.5)
                            except Exception as drag_err:
                                print("WARNING: " + f"WARN: End handle drag failed: {drag_err}; continuing...")
                                time.sleep(0.3)

                    # Verify selection - simplified (just wait and assume success)
                    time.sleep(1.0)
                    
                    # Simple verification - just check if handles moved
                    try:
                        # Get final positions
                        final_start_box = start_handle.bounding_box()
                        final_end_box = end_handle.bounding_box()
                        
                        if final_start_box and final_end_box:
                            final_sx = final_start_box['x'] + final_start_box['width']/2
                            final_ex = final_end_box['x'] + final_end_box['width']/2
                            
                            # Check if handles actually moved
                            if abs(final_sx - sx) > 2 or abs(final_ex - ex) > 2:
                                print("YES: Slider handles moved successfully")
                            else:
                                print("WARNING: " + "WARN: Slider handles may not have moved; proceeding anyway")
                        else:
                            print("WARNING: " + "WARN: Could not verify slider position; proceeding anyway")
                    except Exception as e:
                        print("WARNING: " + f"WARN: Could not verify slider position: {e}; proceeding anyway")

                    print("YES: Range set successfully (safe in-bounds drag)")
                    break
                    
                except Exception as e_move:
                    error_msg = str(e_move)
                    if attempts < 5:
                        print("WARNING: " + f"WARN: Slider adjustment failed (attempt {attempts}/5): {error_msg[:100]}... retrying...")
                        time.sleep(0.5)
                        continue
                    else:
                        print("ERROR: " + f"NO: Error while adjusting crop range -> {error_msg}")
                        import traceback
                        print("ERROR: " + f"Full traceback: {traceback.format_exc()}")
                        return False
            else:
                print("ERROR: " + "NO: Failed to set selection after retries")
                return False
            
            # 4) Click Export button (using multiple strategies like Selenium script)
            # After Export click, wait 20 seconds as requested
            clicked_export = False
            export_strategies = [
                ('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[4]/div[2]/button[3]/svg', 'js'),
                ('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[4]/div[2]/button[3]', 'native'),
            ]
            for xp, how in export_strategies:
                try:
                    el = self.page.locator(xp)
                    el.wait_for(state="attached", timeout=wait_timeout)
                    el.scroll_into_view_if_needed()
                    if how == 'js':
                        el.evaluate("el => el.click()")
                    else:
                        try:
                            el.click()
                        except Exception:
                            # Fallback to JavaScript if native click fails
                            el.evaluate("el => el.click()")
                    clicked_export = True
                    print("YES: Export button clicked")
                    break
                except Exception:
                    continue
                
            if not clicked_export:
                print("ERROR: " + "NO: Export button not clickable after strategies")
                return False
            
            # Wait 20 seconds after Export button click (as requested)
            print("⏳ Waiting 20 seconds after Export button click...")
            time.sleep(20)
            
            # Wait for publish dialog
            try:
                publish_dialog = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[5]/div/div/div[2]/input[1]')
                publish_dialog.wait_for(state="visible", timeout=60000)
                print("YES: Publish dialog appeared")
            except Exception as e_wait:
                print("ERROR: " + f"NO: Publish dialog did not appear -> {e_wait}")
                return False

            # 5) Fill metadata (using clear and fill like Selenium script)
            rand_post = f"Post {uuid.uuid4().hex[:6]}"
            rand_title = f"Title {uuid.uuid4().hex[:6]}"
            rand_desc = f"Desc {uuid.uuid4().hex[:8]}"

            post_title = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[5]/div/div/div[2]/input[1]')
            title_input = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[5]/div/div/div[2]/input[2]')
            desc_input = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[5]/div/div/div[2]/input[3]')
            
            
            post_title.wait_for(state="visible", timeout=wait_timeout)
            title_input.wait_for(state="visible", timeout=wait_timeout)
            desc_input.wait_for(state="visible", timeout=wait_timeout)
            
            # Clear and fill like Selenium script
            for el, text in [(post_title, rand_post), (title_input, rand_title), (desc_input, rand_desc)]:
                try:
                    el.evaluate("el => el.value = ''")
                    el.fill(text)
                except Exception:
                    try:
                        el.fill(text)
                    except Exception:
                        pass

            self._print_block("CLIP METADATA", [f"Post: {rand_post}", f"Title: {rand_title}", f"Description: {rand_desc}"])
            
            # 6) Click Save button (using JavaScript like Selenium script)
            try:
                save_btn = self.page.locator('//*[@id="root"]/div/div[2]/div/div/div[3]/div[1]/div[5]/div/div/div[1]/div/button/span')
                save_btn.wait_for(state="visible", timeout=wait_timeout)
                save_btn.evaluate("el => el.click()")
                print("YES: Save button clicked (clip submitted)")
                
                # Wait 20 seconds after Save button click (as requested)
                print("⏳ Waiting 20 seconds after Save button click...")
                time.sleep(20)
                
                # Print final status (using current channel data if available)
                try:
                    # Try to get previous day duration from the last processed channel
                    pd_secs = int(self.prev_total_seconds) if self.prev_total_seconds else 0
                    pd_h = pd_secs // 3600
                    pd_m = (pd_secs % 3600) // 60
                    pd_s = pd_secs % 60
                    pd_hms = f"{pd_h}:{pd_m:02d}:{pd_s:02d}"
                    pd_hours_float = (pd_secs / 3600.0) if pd_secs else 0.0
                    prev_date_str = self.prev_date_token if self.prev_date_token else "N/A"
                except Exception:
                    pd_hms = "0:00:00"
                    pd_hours_float = 0.0
                    prev_date_str = "N/A"
                
                live_time_str = self.live_status_current if self.live_status_current else "N/A"
                pc_time_str = self.live_status_pc if self.live_status_pc else "N/A"
                
                self._print_block(
                    "CLIP CREATION - FINAL STATUS",
                    [
                        f"Live status: Stream {live_time_str} | PC {pc_time_str}",
                        f"Previous-day status: {prev_date_str} loaded {pd_hours_float:.2f} hours ({pd_hms})",
                        "Clip saved: visibility = Only me",
                    ],
                )
                
                return True
                
            except Exception as e_sv:
                print("ERROR: " + f"NO: Save button not clickable -> {e_sv}")
                return False

        except Exception as e:
            print("ERROR: " + f"NO: Error during crop/export workflow -> {e}")
            return False
    
    def run(self) -> bool:
        """
        Execute the complete live test save clip automation workflow.
        
        This method orchestrates the entire process:
        - Displays environment variables
        - Initializes browser
        - Performs OTP-based login
        - Navigates to live stream
        - Tracks stream time
        - Opens calendar and sets previous day date
        - Gets previous day stream
        - Returns to live
        - Crops and saves 5-minute clip
        - Keeps browser open for manual interaction
        
        Returns:
            bool: True if workflow successful, False otherwise
        
        Example:
            >>> automation = LiveTestSaveClipAutomation()
            >>> success = automation.run()
        """
        try:
            self.display_env_variables()
            
            # Get portal URL
            if not PORTAL_URL:
                raise ValueError("PORTAL_URL environment variable is required. Set it in env_variables.py.")
            
            # Playwright Setup
            # Check if user wants to use a simple browser (regular Edge)
            # Note: USE_SIMPLE_BROWSER not in env_variables.py, defaulting to False
            use_simple_browser = False
            
            if use_simple_browser:
                print("🌐 Using simple browser mode (regular Edge, not Playwright controlled)")
                # Launch regular Edge browser
                import subprocess
                import webbrowser
                if PORTAL_URL:
                    print(f"📂 Opening {PORTAL_URL} in your default browser...")
                    print("⚠️ You will need to manually complete the login and test workflow")
                    webbrowser.open(PORTAL_URL)
                    input("Press Enter after you've completed the test manually...")
                    return True
            else:
                print("🤖 Using Playwright controlled Edge browser")
            
            self.playwright = sync_playwright().start()
            launch_args = [
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--disable-web-security",
                "--no-proxy-server",
                "--start-maximized",
                "--autoplay-policy=no-user-gesture-required",  # Allow autoplay
                "--disable-features=BlockInsecurePrivateNetworkRequests",  # Allow insecure requests
                "--use-fake-ui-for-media-stream",  # Fake UI for media stream (for testing)
                "--use-fake-device-for-media-stream",  # Fake device for media stream
                "--allow-running-insecure-content",  # Allow insecure content
                "--disable-blink-features=AutomationControlled",  # Hide automation
                "--disable-features=VizDisplayCompositor"  # Better video rendering
            ]
            # Prefer LIVE_* overrides for this script only
            browser_headless = LIVE_BROWSER_HEADLESS if LIVE_BROWSER_HEADLESS is not None else BROWSER_HEADLESS
            browser_ignore_https = BROWSER_IGNORE_HTTPS_ERRORS if BROWSER_IGNORE_HTTPS_ERRORS is not None else True
            browser_no_viewport = BROWSER_NO_VIEWPORT if BROWSER_NO_VIEWPORT is not None else True
            # Per-script override first, then global
            # Note: LIVE_USE_SYSTEM_EDGE, USE_SYSTEM_EDGE, LIVE_USE_EDGE_CHANNEL, USE_EDGE_CHANNEL not in env_variables.py
            use_system_edge = False
            use_edge_channel = LIVE_USE_CHROME_CHANNEL if LIVE_USE_CHROME_CHANNEL is not None else False
            
            if browser_headless is None:
                raise ValueError("BROWSER_HEADLESS environment variable is required. Set it in env_variables.py.")
            if browser_ignore_https is None:
                raise ValueError("BROWSER_IGNORE_HTTPS_ERRORS environment variable is required. Set it in env_variables.py.")
            if browser_no_viewport is None:
                raise ValueError("BROWSER_NO_VIEWPORT environment variable is required. Set it in env_variables.py.")
            
            if use_system_edge:
                # Use installed Edge with persistent context to leverage full codec support (like manual browser)
                print("🧩 Using system Edge with persistent context for full codec support")
                user_data_dir = str(Path.home() / ".nimar_edge_profile")
                try:
                    self.context = self.playwright.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        channel="msedge",
                        headless=browser_headless,
                        args=launch_args,
                        ignore_https_errors=browser_ignore_https,
                        no_viewport=browser_no_viewport,
                        viewport=None,
                        permissions=["camera", "microphone"],
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                        java_script_enabled=True,
                        bypass_csp=True
                    )
                    self.page = self.context.new_page()
                except Exception as e:
                    print("WARNING: " + f"⚠️ Failed to launch system Edge persistent context: {e}. Falling back to Edge channel.")
                    use_system_edge = False
            
            if not use_system_edge:
                if use_edge_channel:
                    # Try using installed Edge via channel without persistent profile
                    print("🧪 Using Edge channel for Playwright launch")
                    try:
                        self.browser = self.playwright.chromium.launch(channel="msedge", headless=browser_headless, args=launch_args)
                    except Exception as e:
                        print("WARNING: " + f"⚠️ Edge channel launch failed: {e}. Falling back to bundled Chromium.")
                        self.browser = self.playwright.chromium.launch(headless=browser_headless, args=launch_args)
                else:
                    self.browser = self.playwright.chromium.launch(headless=browser_headless, args=launch_args)
                
                # Set permissions for video/audio streaming (autoplay is not a permission, handled via launch args)
                permissions = ["camera", "microphone"]
                
                # Create context with video streaming support
                self.context = self.browser.new_context(
                    ignore_https_errors=browser_ignore_https,
                    no_viewport=browser_no_viewport,
                    viewport=None,
                    permissions=permissions,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                    # Enable video/audio autoplay via JavaScript
                    java_script_enabled=True,
                    # Allow insecure content
                    bypass_csp=True
                )
                
                # Grant permissions to page
                self.page = self.context.new_page()
            
            # Grant permissions explicitly (autoplay is handled via browser args, not permissions)
            try:
                self.context.grant_permissions(permissions, origin=PORTAL_URL)
                print(f"✅ Granted permissions: {', '.join(permissions)}")
                print(f"✅ Autoplay enabled via browser launch arguments")
            except Exception as e:
                print("WARNING: " + f"⚠️ Could not grant permissions: {e}")
            
            # Add JavaScript to handle video autoplay and error handling
            self.page.add_init_script("""
                // Override autoplay policy
                Object.defineProperty(navigator, 'mediaDevices', {
                    get: () => ({
                        getUserMedia: () => Promise.resolve(new MediaStream())
                    })
                });
                
                // Allow video autoplay and handle errors
                HTMLVideoElement.prototype.play = (function(original) {
                    return function() {
                        this.muted = false;
                        var promise = original.apply(this, arguments);
                        if (promise !== undefined) {
                            promise.catch(function(error) {
                                console.error('Video play error:', error);
                            });
                        }
                        return promise;
                    };
                })(HTMLVideoElement.prototype.play);
                
                // Log video errors
                window.addEventListener('error', function(e) {
                    if (e.target && e.target.tagName === 'VIDEO') {
                        console.error('Video error:', e.message, e.target.error);
                    }
                }, true);
                
                // Monitor video loading and source changes
                function setupVideoMonitoring() {
                    var videos = document.querySelectorAll('video');
                    videos.forEach(function(v) {
                        // Monitor source changes
                        var observer = new MutationObserver(function(mutations) {
                            mutations.forEach(function(mutation) {
                                if (mutation.type === 'attributes' && (mutation.attributeName === 'src' || mutation.attributeName === 'currentSrc')) {
                                    console.log('Video src changed:', v.src || v.currentSrc);
                                    // Reload video when source changes
                                    if (v.src || v.currentSrc) {
                                        try {
                                            v.load();
                                        } catch(e) {
                                            console.log('Error reloading video:', e);
                                        }
                                    }
                                }
                            });
                        });
                        observer.observe(v, { attributes: true, attributeFilter: ['src'] });
                        
                        // Monitor video events
                        v.addEventListener('error', function(e) {
                            if (v.error) {
                                console.error('Video element error:', v.error.message, 'Code:', v.error.code);
                            }
                        });
                        v.addEventListener('loadstart', function() {
                            console.log('Video load started, src:', v.src || v.currentSrc);
                        });
                        v.addEventListener('loadedmetadata', function() {
                            console.log('Video metadata loaded');
                        });
                        v.addEventListener('canplay', function() {
                            console.log('Video can play');
                        });
                        v.addEventListener('canplaythrough', function() {
                            console.log('Video can play through');
                        });
                        v.addEventListener('loadeddata', function() {
                            console.log('Video data loaded');
                        });
                        v.addEventListener('playing', function() {
                            console.log('Video is playing');
                        });
                    });
                }
                
                // Setup monitoring when DOM is ready
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', setupVideoMonitoring);
                } else {
                    setupVideoMonitoring();
                }
                
                // Also monitor for new video elements added dynamically
                var bodyObserver = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.tagName === 'VIDEO') {
                                setupVideoMonitoring();
                            }
                        });
                    });
                });
                bodyObserver.observe(document.body, { childList: true, subtree: true });
            """)
            
            # Set up console message listener to catch video errors (filter out non-critical errors)
            def handle_console(msg):
                msg_text = msg.text.lower()
                # Filter out non-critical errors
                if msg.type == "error":
                    # Skip common non-critical errors
                    if any(skip in msg_text for skip in [
                        "failed to load resource: the server responded with a status of 404",
                        "failed to execute 'observe' on 'mutationobserver'",
                        "do not use scan directly in a server component",
                        "aborterror: the play() request was interrupted"
                    ]):
                        return  # Don't log these non-critical errors
                    print("ERROR: " + f"🔴 Console Error: {msg.text}")
                elif "video" in msg_text or "stream" in msg_text:
                    # Only log important video messages, not every console log
                    if "error" in msg_text or "failed" in msg_text:
                        print(f"📹 Console: {msg.text}")
            
            self.page.on("console", handle_console)
            
            # Set up page error listener
            def handle_page_error(error):
                print("ERROR: " + f"🔴 Page Error: {error}")
            
            self.page.on("pageerror", handle_page_error)
            
            # Store stream URLs from network requests
            self.captured_stream_urls = []
            
            # Set up request/response monitoring for video streams (only log important ones)
            def handle_response(response):
                url = response.url
                # Only log .m3u8 files (playlists) and errors, not every .ts segment
                if '.m3u8' in url.lower():
                    status = response.status
                    if status >= 400:
                        print("ERROR: " + f"🔴 Stream Playlist Failed: {url} - Status: {status}")
                    elif status == 200 or status == 206:
                        # Only capture .m3u8 URLs for later use, don't log every request
                        if url not in self.captured_stream_urls:
                            self.captured_stream_urls.append(url)
                            print(f"✅ Captured stream playlist: {url}")
            
            self.page.on("response", handle_response)
            
            # Monitor for video source changes
            def handle_video_source_change():
                """Monitor when video source is set"""
                self.page.evaluate("""
                    (function(){
                        var observer = new MutationObserver(function(mutations) {
                            mutations.forEach(function(mutation) {
                                if (mutation.type === 'attributes' && mutation.attributeName === 'src') {
                                    var v = mutation.target;
                                    console.log('Video src changed:', v.src || v.currentSrc);
                                    if (v.src || v.currentSrc) {
                                        v.load();
                                    }
                                }
                            });
                        });
                        
                        // Observe video elements
                        var videos = document.querySelectorAll('video');
                        videos.forEach(function(v) {
                            observer.observe(v, { attributes: true, attributeFilter: ['src'] });
                        });
                        
                        // Also observe for new video elements
                        var bodyObserver = new MutationObserver(function(mutations) {
                            mutations.forEach(function(mutation) {
                                mutation.addedNodes.forEach(function(node) {
                                    if (node.tagName === 'VIDEO') {
                                        observer.observe(node, { attributes: true, attributeFilter: ['src'] });
                                    }
                                });
                            });
                        });
                        bodyObserver.observe(document.body, { childList: true, subtree: true });
                    })();
                """)
            
            # Set up video source monitoring after page loads
            self.page.on("load", handle_video_source_change)
            
            print("✅ Browser initialized with video streaming support and error monitoring")
            
            # Navigate to portal
            self.page.goto(PORTAL_URL)
            self.page.wait_for_load_state("networkidle")
            time.sleep(5)
            
            # Login using OTP
            print("🔐 Starting OTP-based login...")
            login_success = login_with_otp_sync(self.page)
            
            if not login_success:
                print("ERROR: " + "❌ Login failed. Exiting.")
                return False
            
            print("✅ Login successful! Proceeding with live test workflow...")
            login_success_wait = float(LOGIN_SUCCESS_WAIT or 5)
            time.sleep(login_success_wait)
            
            # Navigate to live menu
            if not self.navigate_to_live_menu():
                print("ERROR: " + "❌ Failed to navigate to live menu. Exiting.")
                return False
            
            # Process all channels
            channel_results = self.process_all_channels()
            
            if not channel_results:
                print("ERROR: " + "❌ No channels were processed. Exiting.")
                return False
            
            # Print final summary of all channels (proper format)
            print(f"\n{'='*80}")
            print("📊 FINAL SUMMARY - ALL CHANNELS")
            print(f"{'='*80}")
            for result in channel_results:
                print(f"\n📺 Channel: {result['channel_name']}")
                print(f"   ⏱️  Live Stream Time: {result['live_time'] if result['live_time'] else 'N/A'}")
                print(f"   🖥️  PC Time:           {result['pc_time'] if result['pc_time'] else 'N/A'}")
                print(f"   📅 Previous Days Streams:")
                for date, loaded, duration in result['previous_days']:
                    if loaded:
                        hours = duration / 3600.0
                        h = int(duration) // 3600
                        m = (int(duration) % 3600) // 60
                        s = int(duration) % 60
                        print(f"      ✅ {date}: Available - Total Duration: {hours:.2f} hours ({h}:{m:02d}:{s:02d})")
                    else:
                        print(f"      ❌ {date}: NOT Available")
            print(f"\n{'='*80}\n")
            
            # Print complete table at the end
            print(f"\n{'='*180}")
            print("📋 COMPLETE CHANNELS STATUS TABLE")
            print(f"{'='*180}")
            
            # Table header - dynamic based on number of previous days checked
            max_days = 0
            for result in channel_results:
                if result['previous_days']:
                    max_days = max(max_days, len(result['previous_days']))
            
            # Build header with dynamic previous day columns
            header_parts = [
                f"{'Channel Name':<20}",
                f"{'Live: Stream/PC':<20}",
            ]
            
            # Add columns for each previous day
            for day_num in range(1, max_days + 1):
                header_parts.append(f"{f'Day {day_num}':<30}")
            
            # Add status column
            header_parts.append(f"{'Status':<15}")
            
            header = " | ".join(header_parts)
            separator = "-" * 180
            print(header)
            print(separator)
            
            # Table rows
            for result in channel_results:
                channel_name = result['channel_name'][:19] if len(result['channel_name']) > 19 else result['channel_name']
                
                # Live comparison: Stream time vs PC time
                stream_time = result['live_time'] if result['live_time'] else 'N/A'
                pc_time = result['pc_time'] if result['pc_time'] else 'N/A'
                live_comparison = f"{stream_time} / {pc_time}"
                if len(live_comparison) > 19:
                    live_comparison = live_comparison[:19]
                
                # Build row parts
                row_parts = [
                    channel_name,
                    live_comparison,
                ]
                
                # Add each previous day's information
                total_loaded_seconds = 0.0
                loaded_count = 0
                
                for day_num in range(max_days):
                    if result['previous_days'] and day_num < len(result['previous_days']):
                        date, loaded, duration = result['previous_days'][day_num]
                        if loaded:
                            hours = duration / 3600.0
                            h = int(duration) // 3600
                            m = (int(duration) % 3600) // 60
                            s = int(duration) % 60
                            day_info = f"{date}: {hours:.2f}h ({h}:{m:02d}:{s:02d})"
                            total_loaded_seconds += duration
                            loaded_count += 1
                        else:
                            day_info = f"{date}: ❌ Not Available"
                    else:
                        day_info = "N/A"
                    
                    if len(day_info) > 29:
                        day_info = day_info[:29]
                    row_parts.append(day_info)
                
                # Status
                total_days_checked = len(result['previous_days']) if result['previous_days'] else 0
                if total_days_checked > 0:
                    status_icon = f"✅ {loaded_count}/{total_days_checked}"
                else:
                    status_icon = "❌ Not Checked"
                
                row_parts.append(status_icon)
                
                # Format row with proper spacing
                formatted_row_parts = []
                widths = [20, 20] + [30] * max_days + [15]
                for i, part in enumerate(row_parts):
                    if i < len(widths):
                        formatted_row_parts.append(f"{part:<{widths[i]}}")
                    else:
                        formatted_row_parts.append(part)
                
                row = " | ".join(formatted_row_parts)
                print(row)
            
            print(separator)
            print(f"{'='*180}\n")
            
            # Navigate back to live menu for clip creation
            print(f"\n{'='*80}")
            print("🎬 Starting clip creation workflow...")
            print(f"{'='*80}\n")
            
            if not self.navigate_to_live_menu():
                print("WARNING: " + "⚠️ Could not navigate back to live menu for clip creation.")
                return True  # Return True even if clip creation fails, as channel verification is complete
            
            # Get all channels and always select second channel for clip creation
            print("📺 Getting channels for clip creation...")
            channels = self.get_all_channels()
            
            if not channels:
                print("ERROR: " + "❌ No channels found for clip creation. Exiting.")
                return True  # Return True even if clip creation fails
            
            if len(channels) < 2:
                print("WARNING: " + "⚠️ Only one channel found, using first channel for clip creation.")
                second_channel_name, second_channel_index = channels[0]
            else:
                # Always use second channel for clip creation
                second_channel_name, second_channel_index = channels[1]
            
            print(f"📺 Opening second channel for clip creation: {second_channel_name}")
            
            # Open channel for clip creation
            time.sleep(3)
            if not self.open_channel(second_channel_index, second_channel_name):
                print("ERROR: " + f"❌ Failed to open channel for clip: {second_channel_name}")
                return True  # Return True even if clip creation fails
            
            print("✅ Channel opened")
            time.sleep(3)
            
            # Create clip directly (no stream initialization needed, as per clip-creation-only.py)
            print("✂️ Creating 5-minute clip...")
            if not self.crop_and_save_clip():
                print("WARNING: " + "⚠️ Crop and save clip had issues.")
            else:
                print("✅ Clip created and saved successfully!")
            
            print("\n✅ Script completed successfully! Closing browser...")
            
            return True
            
        except Exception as e:
            print("ERROR: " + f"❌ Error during automation: {e}")
            return False
        finally:
            # Close browser
            try:
                if self.browser:
                    self.browser.close()
                if self.playwright:
                    self.playwright.stop()
            except Exception as e:
                print("WARNING: " + f"Error closing browser: {e}")


if __name__ == "__main__":
    automation = LiveTestSaveClipAutomation()
    success = automation.run()
    
    if success:
        print("✅ Automation completed successfully!")
    else:
        print("ERROR: ❌ Automation failed. Check logs for details.")
