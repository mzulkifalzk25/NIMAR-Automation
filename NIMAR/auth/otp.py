"""
=======================================================================
📄 NIMAR OTP Automation Script — otp.py
=======================================================================

🔧 Purpose:
    Automates the OTP-based login process for the NIMAR web portal.
    This script uses Playwright for browser automation and IMAP to
    securely fetch OTP codes from Gmail inbox messages.

    This module follows a single main class architecture (similar to
    test_configurator.py) where all functionality is encapsulated
    within the NimarOTPAutomation class.

⚙️ Features:
    • Single main class architecture (NimarOTPAutomation)
    • All helper methods are class methods
    • Loads credentials and settings from env_variables.py
    • Marks old emails as read before requesting a new OTP
    • Waits for and extracts a 6-digit OTP from Gmail
    • Logs in to the NIMAR portal automatically using Playwright
    • Handles missing environment variables, network delays, and errors gracefully

📁 Project Structure:
    Automation/
    ├── auth/
    │   └── otp.py              ← This module
    ├── uploads/
    │   └── single-zipfile-upload.py  ← Uses login_with_otp_sync from this module
    ├── env_variables.py         ← Environment variables module
    └── requirements.txt        ← Python dependencies

🔐 Environment Variables (imported from env_variables.py):
    EMAIL_USER=your_email@gmail.com
    EMAIL_PASS=your_gmail_app_password
    PORTAL_URL=https://portal.nimar.com
    USERNAME=your_portal_username
    PASSWORD=your_portal_password
    EMAIL_SERVER=imap.gmail.com
    LOG_LEVEL=INFO
    (See env_variables.py for complete list)

🚀 How to Run:
    1. Install all required packages:
           pip install -r requirements.txt
           playwright install

    2. Run the script standalone:
           python auth/otp.py

    3. Or import and use in your own script:
           from auth.otp import login_with_otp_sync
           success = login_with_otp_sync(page)

📦 Main Class:

    NimarOTPAutomation
       → Main automation class for NIMAR OTP-based login workflow
       → All functionality is encapsulated within this single class
       → Methods:
           - run()                    → Execute complete OTP login workflow
           - mark_all_as_read()       → Mark all emails as read
           - _extract_email_body()    → Extract email body content
           - get_latest_otp_after_request() → Get OTP from Gmail
           - login_async()            → Async login workflow
           - login_sync()             → Sync login workflow

    Module-level Functions (for backward compatibility):
       - login_with_otp_async(page)   → Async OTP login wrapper
       - login_with_otp_sync(page)   → Sync OTP login wrapper

🧩 Dependencies:
    - playwright         → Automate web login flow
    - imaplib, email     → Handle Gmail IMAP for OTP retrieval
    - asyncio            → Async flow

🧠 Author:
    Rabbia Gillani SQA
    Version: 3.0.0
    Date: 2025-11-10
=======================================================================
"""
import re
import time
import imaplib
import email
from email import message
import asyncio
import datetime
import logging
from typing import Optional
from playwright.async_api import async_playwright, Page
from playwright.sync_api import sync_playwright

# Get logger for this module
logger = logging.getLogger(__name__)

from NIMAR.env_variables import (
    EMAIL_USER,
    EMAIL_PASS,
    PORTAL_URL,
    USERNAME,
    PASSWORD,
    EMAIL_SERVER,
    OTP_RETRIES,
    OTP_DELAY,
    OTP_CREDENTIAL_ENTRY_WAIT,
    OTP_BUTTON_TIMEOUT,
    OTP_EMAIL_WAIT_TIME,
    OTP_INPUT_DELAY,
    OTP_VERIFY_BUTTON_TIMEOUT,
    OTP_LOGIN_COMPLETE_WAIT,
    BROWSER_HEADLESS,
    BROWSER_IGNORE_HTTPS_ERRORS,
    BROWSER_NO_VIEWPORT,
    MANUAL_OTP
)

if not EMAIL_USER:
    raise ValueError("EMAIL_USER environment variable is required.")
if not EMAIL_PASS:
    raise ValueError("EMAIL_PASS environment variable is required.")
if not PORTAL_URL:
    raise ValueError("PORTAL_URL environment variable is required.")
if not USERNAME:
    raise ValueError("USERNAME environment variable is required.")
if not PASSWORD:
    raise ValueError("PASSWORD environment variable is required.")
if not EMAIL_SERVER:
    raise ValueError("EMAIL_SERVER environment variable is required.")
if not OTP_RETRIES:
    raise ValueError("OTP_RETRIES environment variable is required.")
if not OTP_DELAY:
    raise ValueError("OTP_DELAY environment variable is required.")
if not OTP_CREDENTIAL_ENTRY_WAIT:
    raise ValueError("OTP_CREDENTIAL_ENTRY_WAIT environment variable is required.")
if not OTP_BUTTON_TIMEOUT:
    raise ValueError("OTP_BUTTON_TIMEOUT environment variable is required.")
if not OTP_EMAIL_WAIT_TIME:
    raise ValueError("OTP_EMAIL_WAIT_TIME environment variable is required.")
if not OTP_INPUT_DELAY:
    raise ValueError("OTP_INPUT_DELAY environment variable is required.")
if not OTP_VERIFY_BUTTON_TIMEOUT:
    raise ValueError("OTP_VERIFY_BUTTON_TIMEOUT environment variable is required.")
if not OTP_LOGIN_COMPLETE_WAIT:
    raise ValueError("OTP_LOGIN_COMPLETE_WAIT environment variable is required.")
# Note: BROWSER_HEADLESS, BROWSER_IGNORE_HTTPS_ERRORS, and BROWSER_NO_VIEWPORT have defaults
# and can legitimately be False, so we don't validate them here


class NimarOTPAutomation:
    """
    Main automation class for NIMAR OTP-based login workflow.
    
    This class orchestrates the complete OTP login process, similar to
    ConfiguratorTestSuite structure. All functionality is within this single class.
    
    Attributes:
        email_user (str): Gmail email address
        email_pass (str): Gmail app password
        portal_url (str): Portal URL
        username (str): Portal username
        password (str): Portal password
        mail_server (str): IMAP server address
        retries (int): Maximum retry attempts for OTP
        delay (int): Delay between retries in seconds
    
    Example:
        >>> automation = NimarOTPAutomation()
        >>> await automation.run()
    """
    
    def __init__(self):
        """
        Initialize NIMAR OTP automation.
        
        Loads all configuration from env_variables.py module.
        """
        self.email_user = EMAIL_USER
        self.email_pass = EMAIL_PASS
        self.portal_url = PORTAL_URL
        self.username = USERNAME
        self.password = PASSWORD
        
        if not all([self.email_user, self.email_pass, self.portal_url, self.username, self.password]):
            logger.critical("Missing one or more required environment variables.")
            raise ValueError("Missing required environment variables. Check env_variables.py.")
        
        mail_server = EMAIL_SERVER
        if not mail_server:
            raise ValueError("EMAIL_SERVER environment variable is required. Set it in env_variables.py.")
        self.mail_server = mail_server
        
        retries_str = OTP_RETRIES
        if not retries_str:
            raise ValueError("OTP_RETRIES environment variable is required. Set it in env_variables.py.")
        self.retries = int(retries_str)
        
        delay_str = OTP_DELAY
        if not delay_str:
            raise ValueError("OTP_DELAY environment variable is required. Set it in env_variables.py.")
        self.delay = int(delay_str)
    
    def mark_all_as_read(self) -> bool:
        """
        Marks all Gmail messages as read before requesting new OTP.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            mail = imaplib.IMAP4_SSL(self.mail_server)
            mail.login(self.email_user, self.email_pass)
            mail.select("inbox")
            mail.store("1:*", "+FLAGS", "\\Seen")
            mail.logout()
            logger.info("All previous emails marked as read.")
            return True
        except Exception as e:
            logger.error(f"Unable to mark emails as read: {e}")
            return False
    
    def _extract_email_body(self, msg: message.Message) -> str:
        """
        Extract text body from email message.
        
        Args:
            msg (message.Message): Email message object
        
        Returns:
            str: Email body text
        """
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() in ["text/plain", "text/html"]:
                    try:
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
                    except Exception:
                        continue
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")
        return body
    
    def get_latest_otp_after_request(self, request_time: datetime.datetime) -> Optional[str]:
        """
        Waits for a new Gmail message with a 6-digit OTP after request_time.
        
        Args:
            request_time (datetime): Timestamp when OTP was requested (only emails after this time are checked)
        
        Returns:
            str or None: 6-digit OTP code if found, None otherwise
        """
        try:
            mail = imaplib.IMAP4_SSL(self.mail_server)
            mail.login(self.email_user, self.email_pass)
            mail.select("inbox")

            for attempt in range(self.retries):
                result, data = mail.search(None, "ALL")
                if not data or not data[0]:
                    logger.info(f"No new emails yet (attempt {attempt + 1}/{self.retries})...")
                    time.sleep(self.delay)
                    continue

                latest_email_id = data[0].split()[-1]
                result, msg_data = mail.fetch(latest_email_id, "(RFC822 INTERNALDATE)")
                msg = email.message_from_bytes(msg_data[0][1])
                internal_date = msg_data[0][0].decode(errors="ignore")

                match = re.search(r'\d{1,2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', internal_date)
                if match:
                    email_time = datetime.datetime.strptime(match.group(), "%d-%b-%Y %H:%M:%S")
                    if email_time <= request_time:
                        time.sleep(self.delay)
                        continue

                body = self._extract_email_body(msg)
                otp_match = re.search(r"\b\d{6}\b", body)
                if otp_match:
                    otp = otp_match.group()
                    logger.info("New OTP received.")
                    mail.logout()
                    return otp

                logger.info(f"Waiting for OTP email... (attempt {attempt + 1}/{self.retries})")
                time.sleep(self.delay)

            logger.error("OTP not received within expected time.")
            mail.logout()
            return None

        except Exception as e:
            logger.error(f"Error while fetching OTP: {e}")
            return None

    async def login_async(self, page) -> bool:
        """
        Perform complete login workflow (asynchronous version).
    
    Args:
        page: Playwright async Page object (from async_playwright)
    
    Returns:
        bool: True if login successful, False otherwise
        """
        try:
            # Log credentials being used
            logger.info("=" * 60)
            logger.info("🔐 LOGIN CREDENTIALS BEING USED:")
            logger.info(f"   Portal URL: {self.portal_url}")
            logger.info(f"   Username: {self.username}")
            logger.info(f"   Password: {'*' * len(self.password) if self.password else 'NOT SET'}")
            logger.info(f"   Email User: {self.email_user}")
            logger.info(f"   Email Server: {self.mail_server}")
            logger.info("=" * 60)
            
            self.mark_all_as_read()
            
            current_url = page.url
            if self.portal_url not in current_url:
                logger.info("Opening NIMAR user portal...")
                await page.goto(self.portal_url)
            await page.wait_for_load_state("networkidle")
            
            credential_entry_wait_str = OTP_CREDENTIAL_ENTRY_WAIT
            if not credential_entry_wait_str:
                raise ValueError("OTP_CREDENTIAL_ENTRY_WAIT environment variable is required. Set it in env_variables.py.")
            credential_entry_wait = int(credential_entry_wait_str)
            
            # Wait for login form to be ready
            logger.info("Waiting for login form...")
            await page.wait_for_selector("#name", timeout=10000)
            await page.wait_for_selector("#password", timeout=10000)
            
            await page.fill("#name", self.username)
            await page.fill("#password", self.password)
            logger.info("Login credentials entered.")
            
            # Wait a moment for form validation
            await page.wait_for_timeout(500)
            
            # Click the Login button explicitly - wait for it to be enabled
            logger.info("Clicking Login button...")
            login_button_selectors = [
                'button[type="submit"]',  # Try submit button first
                '//button[@type="submit"]',
                'button:has-text("Login")',
                '//button[normalize-space()="Login"]',
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    login_btn = page.locator(selector).first
                    # Wait for button to be visible and enabled
                    await login_btn.wait_for(state="visible", timeout=5000)
                    # Check if button is enabled (not disabled)
                    is_disabled = await login_btn.get_attribute("disabled")
                    if is_disabled is None or is_disabled == "false":
                        # Wait for any animations/transitions
                        await page.wait_for_timeout(300)
                        await login_btn.click()
                        login_clicked = True
                        logger.info(f"Login button clicked using selector: {selector[:50]}")
                        break
                    else:
                        logger.warning(f"Login button found but is disabled with selector: {selector[:50]}")
                except Exception as e:
                    logger.warning(f"Error with selector {selector[:50]}: {str(e)[:100]}")
                    continue
            
            if not login_clicked:
                # Try submitting the form directly
                try:
                    logger.info("Trying to submit form directly...")
                    form = page.locator("form").first
                    if await form.is_visible():
                        await form.evaluate("form => form.submit()")
                        login_clicked = True
                        logger.info("Form submitted directly.")
                except Exception as e:
                    logger.warning(f"Form submission failed: {e}")
                
                if not login_clicked:
                    # Fallback to Enter key
                    logger.info("Using Enter key as fallback...")
                    await page.keyboard.press("Enter")
            
            # Wait for navigation or page change after login
            logger.info("Waiting for login to process...")
            initial_url = page.url
            
            # Wait for either URL change OR OTP section to appear
            # The page might stay on the same URL but show OTP section
            logger.info("Waiting for page to load after login...")
            try:
                # First, wait for network to be idle (form submission completed)
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            
            # Check if we're still on login page or if OTP section appeared
            max_wait = 10
            otp_section_found = False
            for i in range(max_wait):
                current_url = page.url
                # Check if URL changed
                if "/login" not in current_url or current_url != initial_url:
                    logger.info("Navigation detected (URL changed).")
                    break
                
                # Check if OTP section appeared (even if URL didn't change)
                try:
                    # Try to find OTP-related elements
                    otp_inputs = await page.locator("input[aria-label^='Please enter OTP character']").count()
                    if otp_inputs > 0:
                        logger.info("OTP section detected on page.")
                        otp_section_found = True
                        break
                except Exception:
                    pass
                
                # Check for OTP button
                try:
                    otp_btn_check = page.locator('button:has-text("OTP"), button[type="button"]:has-text("OTP")').first
                    if await otp_btn_check.is_visible(timeout=1000):
                        logger.info("OTP button detected on page.")
                        otp_section_found = True
                        break
                except Exception:
                    pass
                
                await page.wait_for_timeout(1000)
            
            # Additional wait to ensure page is ready
            await page.wait_for_timeout(credential_entry_wait)
    
            otp_button_timeout_str = OTP_BUTTON_TIMEOUT
            if not otp_button_timeout_str:
                raise ValueError("OTP_BUTTON_TIMEOUT environment variable is required. Set it in env_variables.py.")
            otp_button_timeout = int(otp_button_timeout_str)
            
            # Try multiple selectors for OTP button
            otp_btn = None
            otp_selectors = [
                '//*[@id="portal"]/div/div/div/div[2]/div/button[3]',
                'button:has-text("OTP")',
                'button:has-text("Send OTP")',
                'button:has-text("Request OTP")',
                '//button[contains(text(), "OTP")]',
                '//button[contains(@class, "otp")]',
            ]
            
            logger.info(f"Looking for OTP button (timeout: {otp_button_timeout}ms)...")
            # Use minimum 5 seconds per selector, or divide timeout evenly
            timeout_per_selector = max(5000, otp_button_timeout // len(otp_selectors))
            for selector in otp_selectors:
                try:
                    logger.info(f"Trying selector: {selector[:50]}...")
                    otp_btn = await page.wait_for_selector(selector, timeout=timeout_per_selector, state="visible")
                    if otp_btn:
                        logger.info(f"Found OTP button using selector: {selector[:50]}")
                        break
                except Exception as e:
                    logger.debug(f"Selector '{selector[:50]}' not found: {str(e)[:100]}")
                    continue
            
            if not otp_btn:
                # Debug: Take screenshot and show page content
                logger.error("OTP button not found with any selector.")
                logger.error(f"Current URL: {page.url}")
                logger.info("Taking screenshot for debugging...")
                try:
                    await page.screenshot(path="otp_button_not_found.png")
                    logger.info("Screenshot saved as 'otp_button_not_found.png'")
                except Exception as screenshot_error:
                    logger.warning(f"Could not take screenshot: {screenshot_error}")
                
                # Show available buttons for debugging
                try:
                    buttons = await page.locator("button").all()
                    logger.debug(f"Found {len(buttons)} buttons on the page:")
                    for i, btn in enumerate(buttons[:10]):  # Show first 10 buttons
                        try:
                            text = (await btn.text_content())[:50] if await btn.is_visible() else "[hidden]"
                            logger.debug(f"  Button {i+1}: {text}")
                        except:
                            pass
                except Exception:
                    pass
                
                raise Exception("OTP button not found. Check screenshot for page state.")
            
            await otp_btn.click()
            logger.info("OTP request initiated.")
    
            otp_request_time = datetime.datetime.now(datetime.UTC)
            logger.info("OTP requested. Waiting for email delivery...")
    
            otp_email_wait_time_str = OTP_EMAIL_WAIT_TIME
            if not otp_email_wait_time_str:
                raise ValueError("OTP_EMAIL_WAIT_TIME environment variable is required. Set it in env_variables.py.")
            otp_email_wait_time = int(otp_email_wait_time_str)
            await page.wait_for_timeout(otp_email_wait_time)
    
            # Check if manual OTP is provided, otherwise retrieve from email
            if MANUAL_OTP:
                otp = MANUAL_OTP.strip()
                logger.info(f"✅ Using manual OTP: {otp}")
            else:
                otp = self.get_latest_otp_after_request(otp_request_time)
                if not otp:
                    logger.error("❌ OTP retrieval failed. Exiting login sequence.")
                    return False
    
            otp_inputs = await page.query_selector_all("input[aria-label^='Please enter OTP character']")
            if len(otp_inputs) == 6:
                otp_input_delay_str = OTP_INPUT_DELAY
                if not otp_input_delay_str:
                    raise ValueError("OTP_INPUT_DELAY environment variable is required. Set it in env_variables.py.")
                otp_input_delay = int(otp_input_delay_str)
                
                for i, digit in enumerate(otp):
                    await otp_inputs[i].fill(digit)
                    await page.wait_for_timeout(otp_input_delay)
                
                try:
                    otp_verify_button_timeout_str = OTP_VERIFY_BUTTON_TIMEOUT
                    if not otp_verify_button_timeout_str:
                        raise ValueError("OTP_VERIFY_BUTTON_TIMEOUT environment variable is required. Set it in env_variables.py.")
                    otp_verify_button_timeout = int(otp_verify_button_timeout_str)
                    verify_btn = await page.wait_for_selector(
                        "//button[normalize-space()='Verify OTP']", timeout=otp_verify_button_timeout
                    )
                    await verify_btn.click()
                    logger.info("OTP verified.")
                except Exception:
                    verify_btn = await page.query_selector("//button[normalize-space()='Verify OTP']")
                    await page.evaluate("(el) => el.click()", verify_btn)
                    logger.warning("Used JavaScript fallback click for Verify OTP.")
            else:
                logger.error("OTP input fields missing or incorrect.")
                return False
    
            otp_login_complete_wait_str = OTP_LOGIN_COMPLETE_WAIT
            if not otp_login_complete_wait_str:
                raise ValueError("OTP_LOGIN_COMPLETE_WAIT environment variable is required. Set it in env_variables.py.")
            otp_login_complete_wait = int(otp_login_complete_wait_str)
            await page.wait_for_timeout(otp_login_complete_wait)
            logger.info("Login flow complete.")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def login_sync(self, page) -> bool:
        """
        Perform complete login workflow (synchronous version).
        
        Args:
            page: Playwright sync Page object (from sync_playwright)
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # Log credentials being used
            logger.info("=" * 60)
            logger.info("🔐 LOGIN CREDENTIALS BEING USED:")
            logger.info(f"   Portal URL: {self.portal_url}")
            logger.info(f"   Username: {self.username}")
            logger.info(f"   Password: {'*' * len(self.password) if self.password else 'NOT SET'}")
            logger.info(f"   Email User: {self.email_user}")
            logger.info(f"   Email Server: {self.mail_server}")
            logger.info("=" * 60)
            
            self.mark_all_as_read()
            
            current_url = page.url
            if self.portal_url not in current_url:
                logger.info("Opening NIMAR user portal...")
                page.goto(self.portal_url)
                page.wait_for_load_state("networkidle")
            
            credential_entry_wait_str = OTP_CREDENTIAL_ENTRY_WAIT
            if not credential_entry_wait_str:
                raise ValueError("OTP_CREDENTIAL_ENTRY_WAIT environment variable is required. Set it in env_variables.py.")
            credential_entry_wait = int(credential_entry_wait_str) / 1000
            
            # Wait for login form to be ready
            logger.info("Waiting for login form...")
            page.wait_for_selector("#name", timeout=10000)
            page.wait_for_selector("#password", timeout=10000)
            
            page.fill("#name", self.username)
            page.fill("#password", self.password)
            logger.info("Login credentials entered.")
            
            # Wait a moment for form validation
            time.sleep(0.5)
            
            # Click the Login button explicitly - wait for it to be enabled
            logger.info("Clicking Login button...")
            login_button_selectors = [
                'button[type="submit"]',  # Try submit button first
                '//button[@type="submit"]',
                'button:has-text("Login")',
                '//button[normalize-space()="Login"]',
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    login_btn = page.locator(selector).first
                    # Wait for button to be visible and enabled
                    login_btn.wait_for(state="visible", timeout=5000)
                    # Check if button is enabled (not disabled)
                    is_disabled = login_btn.get_attribute("disabled")
                    if is_disabled is None or is_disabled == "false":
                        # Wait for any animations/transitions
                        time.sleep(0.3)
                        login_btn.click()
                        login_clicked = True
                        logger.info(f"Login button clicked using selector: {selector[:50]}")
                        break
                    else:
                        logger.warning(f"Login button found but is disabled with selector: {selector[:50]}")
                except Exception as e:
                    logger.warning(f"Error with selector {selector[:50]}: {str(e)[:100]}")
                    continue
            
            if not login_clicked:
                # Try submitting the form directly
                try:
                    logger.info("Trying to submit form directly...")
                    form = page.locator("form").first
                    if form.is_visible():
                        form.evaluate("form => form.submit()")
                        login_clicked = True
                        logger.info("Form submitted directly.")
                except Exception as e:
                    logger.warning(f"Form submission failed: {e}")
                
                if not login_clicked:
                    # Fallback to Enter key
                    logger.info("Using Enter key as fallback...")
                    page.keyboard.press("Enter")
            
            # Wait for navigation or page change after login
            logger.info("Waiting for login to process...")
            initial_url = page.url
            
            # Wait for either URL change OR OTP section to appear
            # The page might stay on the same URL but show OTP section
            logger.info("Waiting for page to load after login...")
            try:
                # First, wait for network to be idle (form submission completed)
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            
            # Check if we're still on login page or if OTP section appeared
            max_wait = 10
            otp_section_found = False
            for i in range(max_wait):
                current_url = page.url
                # Check if URL changed
                if "/login" not in current_url or current_url != initial_url:
                    logger.info("Navigation detected (URL changed).")
                    break
                
                # Check if OTP section appeared (even if URL didn't change)
                try:
                    # Try to find OTP-related elements
                    otp_inputs = page.locator("input[aria-label^='Please enter OTP character']").count()
                    if otp_inputs > 0:
                        logger.info("OTP section detected on page.")
                        otp_section_found = True
                        break
                except Exception:
                    pass
                
                # Check for OTP button
                try:
                    otp_btn_check = page.locator('button:has-text("OTP"), button[type="button"]:has-text("OTP")').first
                    if otp_btn_check.is_visible(timeout=1000):
                        logger.info("OTP button detected on page.")
                        otp_section_found = True
                        break
                except Exception:
                    pass
                
                time.sleep(1)
            
            # Additional wait to ensure page is ready
            time.sleep(credential_entry_wait)
            
            otp_button_timeout_str = OTP_BUTTON_TIMEOUT
            if not otp_button_timeout_str:
                raise ValueError("OTP_BUTTON_TIMEOUT environment variable is required. Set it in env_variables.py.")
            otp_button_timeout = int(otp_button_timeout_str)
            
            # Try multiple selectors for OTP button
            otp_btn = None
            otp_selectors = [
                '//*[@id="portal"]/div/div/div/div[2]/div/button[3]',
                'button:has-text("OTP")',
                'button:has-text("Send OTP")',
                'button:has-text("Request OTP")',
                '//button[contains(text(), "OTP")]',
                '//button[contains(@class, "otp")]',
            ]
            
            logger.info(f"Looking for OTP button (timeout: {otp_button_timeout}ms)...")
            # Use minimum 5 seconds per selector, or divide timeout evenly
            timeout_per_selector = max(5000, otp_button_timeout // len(otp_selectors))
            for selector in otp_selectors:
                try:
                    logger.info(f"Trying selector: {selector[:50]}...")
                    otp_btn = page.wait_for_selector(selector, timeout=timeout_per_selector, state="visible")
                    if otp_btn:
                        logger.info(f"Found OTP button using selector: {selector[:50]}")
                        break
                except Exception as e:
                    logger.debug(f"Selector '{selector[:50]}' not found: {str(e)[:100]}")
                    continue
            
            if not otp_btn:
                # Debug: Take screenshot and show page content
                logger.error("OTP button not found with any selector.")
                logger.error(f"Current URL: {page.url}")
                logger.info("Taking screenshot for debugging...")
                try:
                    page.screenshot(path="otp_button_not_found.png")
                    logger.info("Screenshot saved as 'otp_button_not_found.png'")
                except Exception as screenshot_error:
                    logger.warning(f"Could not take screenshot: {screenshot_error}")
                
                # Show available buttons for debugging
                try:
                    buttons = page.locator("button").all()
                    logger.debug(f"Found {len(buttons)} buttons on the page:")
                    for i, btn in enumerate(buttons[:10]):  # Show first 10 buttons
                        try:
                            text = btn.text_content()[:50] if btn.is_visible() else "[hidden]"
                            logger.debug(f"  Button {i+1}: {text}")
                        except:
                            pass
                except Exception:
                    pass
                
                raise Exception("OTP button not found. Check screenshot for page state.")
            
            otp_btn.click()
            logger.info("OTP request initiated.")
            
            otp_request_time = datetime.datetime.now(datetime.UTC)
            logger.info("OTP requested. Waiting for email delivery...")
            
            otp_email_wait_time_str = OTP_EMAIL_WAIT_TIME
            if not otp_email_wait_time_str:
                raise ValueError("OTP_EMAIL_WAIT_TIME environment variable is required. Set it in env_variables.py.")
            otp_email_wait_time = int(otp_email_wait_time_str) / 1000
            time.sleep(otp_email_wait_time)
            
            # Check if manual OTP is provided, otherwise retrieve from email
            if MANUAL_OTP:
                otp = MANUAL_OTP.strip()
                logger.info(f"✅ Using manual OTP: {otp}")
            else:
                otp = self.get_latest_otp_after_request(otp_request_time)
                if not otp:
                    logger.error("❌ OTP retrieval failed. Exiting login sequence.")
                    return False
            
            otp_inputs = page.locator("input[aria-label^='Please enter OTP character']").all()
            if len(otp_inputs) == 6:
                otp_input_delay_str = OTP_INPUT_DELAY
                if not otp_input_delay_str:
                    raise ValueError("OTP_INPUT_DELAY environment variable is required. Set it in env_variables.py.")
                otp_input_delay = int(otp_input_delay_str) / 1000
                for i, digit in enumerate(otp):
                    otp_inputs[i].fill(digit)
                    time.sleep(otp_input_delay)
                
                try:
                    verify_btn = page.locator("//button[normalize-space()='Verify OTP']")
                    otp_verify_button_timeout_str = OTP_VERIFY_BUTTON_TIMEOUT
                    if not otp_verify_button_timeout_str:
                        raise ValueError("OTP_VERIFY_BUTTON_TIMEOUT environment variable is required. Set it in env_variables.py.")
                    otp_verify_button_timeout = int(otp_verify_button_timeout_str)
                    verify_btn.wait_for(state="visible", timeout=otp_verify_button_timeout)
                    verify_btn.click()
                    logger.info("OTP verified.")
                except Exception:
                    verify_btn = page.locator("//button[normalize-space()='Verify OTP']")
                    verify_btn.click(force=True)
                    logger.warning("Used JavaScript fallback click for Verify OTP.")
            else:
                logger.error("OTP input fields missing or incorrect.")
                return False
            
            otp_login_complete_wait_str = OTP_LOGIN_COMPLETE_WAIT
            if not otp_login_complete_wait_str:
                raise ValueError("OTP_LOGIN_COMPLETE_WAIT environment variable is required. Set it in env_variables.py.")
            otp_login_complete_wait = int(otp_login_complete_wait_str) / 1000
            time.sleep(otp_login_complete_wait)
            logger.info("Login flow complete.")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def login_with_otp_async(self, page, email_user=None, email_pass=None, 
                                   portal_url=None, username=None, password=None):
        """
        Performs OTP-based login on an existing Playwright page (async version).
        
        This method can be called with an existing page object, or uses
        instance variables if parameters are not provided.
        
        Args:
            page: Playwright async Page object (from async_playwright)
            email_user (str, optional): Gmail email address. If None, uses instance variable
            email_pass (str, optional): Gmail app password. If None, uses instance variable
            portal_url (str, optional): Portal URL. If None, uses instance variable
            username (str, optional): Portal username. If None, uses instance variable
            password (str, optional): Portal password. If None, uses instance variable
        
        Returns:
            bool: True if login successful, False otherwise
        """
        email_user = email_user or self.email_user
        email_pass = email_pass or self.email_pass
        portal_url = portal_url or self.portal_url
        username = username or self.username
        password = password or self.password
        
        if not all([email_user, email_pass, portal_url, username, password]):
            logger.critical("Missing one or more required environment variables.")
            return False
        
        return await self.login_async(page)
    
    async def run(self):
        """
        Execute the complete OTP login automation workflow.
        
        This method orchestrates the entire login process:
        - Initializes browser
        - Performs login
        - Closes browser
        
        Returns:
            bool: True if login successful, False otherwise
        
        Example:
            >>> automation = NimarOTPAutomation()
            >>> await automation.run()
        """
        try:
            async with async_playwright() as p:
                launch_args = [
                    "--ignore-certificate-errors",
                    "--ignore-ssl-errors",
                    "--disable-web-security",
                    "--no-proxy-server",
                    "--start-maximized"
                ]
                
                # BROWSER_HEADLESS, BROWSER_IGNORE_HTTPS_ERRORS, and BROWSER_NO_VIEWPORT are booleans
                # from env_variables.py (they have defaults and can be False)
                browser_headless = BROWSER_HEADLESS
                browser_ignore_https = BROWSER_IGNORE_HTTPS_ERRORS
                browser_no_viewport = BROWSER_NO_VIEWPORT
                
                browser = await p.chromium.launch(headless=browser_headless, args=launch_args)
                context = await browser.new_context(
                    ignore_https_errors=browser_ignore_https,
                    no_viewport=browser_no_viewport,
                    viewport=None
                )
                page = await context.new_page()
                
                success = await self.login_async(page)
                
                if success:
                    logger.info("Login flow complete. Closing browser...")
                else:
                    logger.error("Login failed. Closing browser...")
                
                try:
                    if not page.is_closed():
                        otp_login_complete_wait_str = OTP_LOGIN_COMPLETE_WAIT
                        if otp_login_complete_wait_str:
                            otp_login_complete_wait = int(otp_login_complete_wait_str)
                            await page.wait_for_timeout(otp_login_complete_wait)
                    await browser.close()
                except Exception as e:
                    logger.warning(f"Browser close exception: {e}")
                
                return success
        except Exception as e:
            logger.error(f"Error during automation: {e}")
            return False


async def login_with_otp_async(page, email_user=None, email_pass=None, portal_url=None, username=None, password=None):
    """
    Performs OTP-based login on an existing Playwright page (async version).
    
    This is a module-level wrapper function for backward compatibility.
    It creates a NimarOTPAutomation instance and calls its method.
    
    Args:
        page: Playwright async Page object (from async_playwright)
        email_user (str, optional): Gmail email address. If None, loaded from env_variables.py
        email_pass (str, optional): Gmail app password. If None, loaded from env_variables.py
        portal_url (str, optional): Portal URL. If None, loaded from env_variables.py
        username (str, optional): Portal username. If None, loaded from env_variables.py
        password (str, optional): Portal password. If None, loaded from env_variables.py
    
    Returns:
        bool: True if login successful, False otherwise
    """
    automation = NimarOTPAutomation()
    return await automation.login_with_otp_async(page, email_user, email_pass, portal_url, username, password)


def login_with_otp_sync(page, email_user=None, email_pass=None,
                        portal_url=None, username=None, password=None):
    """
    Performs OTP-based login on an existing Playwright page (sync version).
    
    This is a module-level wrapper function for backward compatibility.
    Other scripts can import this function.
    
    Args:
        page: Playwright sync Page object (from sync_playwright)
        email_user (str, optional): Gmail email address. If None, loaded from env_variables.py
        email_pass (str, optional): Gmail app password. If None, loaded from env_variables.py
        portal_url (str, optional): Portal URL. If None, loaded from env_variables.py
        username (str, optional): Portal username. If None, loaded from env_variables.py
        password (str, optional): Portal password. If None, loaded from env_variables.py
    
    Returns:
        bool: True if login successful, False otherwise
    
    Example:
        >>> from playwright.sync_api import sync_playwright
        >>> with sync_playwright() as p:
        ...     browser = p.chromium.launch()
        ...     page = browser.new_page()
        ...     success = login_with_otp_sync(page)
    """
    automation = NimarOTPAutomation()
    return automation.login_sync(page)


if __name__ == "__main__":
    async def run_automation():
        """Main entry point for standalone script execution."""
        automation = NimarOTPAutomation()
        await automation.run()
    
    asyncio.run(run_automation())
