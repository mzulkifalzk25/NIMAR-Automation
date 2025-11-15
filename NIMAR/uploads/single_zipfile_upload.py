"""
=======================================================================
📄 Single ZIP File Upload Automation Script
=======================================================================

🔧 Purpose:
    Automates the upload of a single ZIP file to the NIMAR portal.
    This script uses OTP-based login from auth.otp module and handles
    the complete upload workflow including metadata entry.

    This module follows a single main class architecture (similar to
    test_configurator.py) where all functionality is encapsulated
    within the UploadAutomationSuite class.

⚙️ Features:
    • Single main class architecture (UploadAutomationSuite)
    • All helper methods are class methods
    • Reuses OTP login functionality from auth.otp module
    • Uploads ZIP file to QA Testing circle
    • Fills metadata form automatically
    • Verifies download functionality

📁 Project Structure:
    Automation/
    ├── auth/
    │   └── otp.py              ← OTP login function (imported here)
    ├── uploads/
    │   └── single-zipfile-upload.py  ← This script
    └── requirements.txt        ← Python dependencies

🚀 How to Run:
    1. Install all required packages:
           pip install -r requirements.txt
           playwright install

    2. Run the script standalone:
           python uploads/single-zipfile-upload.py

    3. Or import and use in your own script:
           from uploads.single_zipfile_upload import UploadAutomationSuite
           suite = UploadAutomationSuite()
           success = suite.run()

📦 Main Class:

    UploadAutomationSuite
       → Main automation suite class for single ZIP file upload workflow
       → All functionality is encapsulated within this single class
       → Methods:
           - run()                    → Execute complete upload workflow
           - open_circle()            → Open QA Testing circle
           - click_upload_button()    → Click upload button and select file
           - start_upload()           → Start upload process
           - fill_metadata_form()     → Fill metadata form
           - submit_metadata_form()   → Submit metadata form
           - open_and_verify_download() → Open modal and verify download

🔐 Environment Variables Required:
    - Portal credentials (PORTAL_URL, USERNAME, PASSWORD)
    - Email settings (EMAIL_USER, EMAIL_PASS, EMAIL_SERVER)
    - File paths (DESKTOP_PATH, DESKTOP_FOLDER, ZIP_FILE)
    - Circle name (CIRCLE_NAME)
    - Metadata fields (POST_TITLE, CONTENT_TITLE, DESCRIPTION, KEYWORDS)
    - Timing variables (WAIT_TIMEOUT, UPLOAD_WAIT_TIME, etc.)

🧩 Dependencies:
    - playwright         → Browser automation
    - auth.otp           → OTP login function (login_with_otp_sync)

🧠 Author:
    Rabbia Gillani SQA
    Version: 3.0.0
    Date: 2025-11-10
=======================================================================
"""

import os
import time
import shutil
import logging

from pathlib import Path
from typing import Optional, Tuple
from playwright.sync_api import sync_playwright

from NIMAR.auth.otp import login_with_otp_sync

# Get logger for this module
logger = logging.getLogger(__name__)
from NIMAR.env_variables import (
    DESKTOP_FOLDER, DESKTOP_PATH, ZIP_FILE, BROWSER_HEADLESS, BROWSER_IGNORE_HTTPS_ERRORS, BROWSER_NO_VIEWPORT,
    WAIT_TIMEOUT, STEP_GAP_SECONDS, UPLOAD_WAIT_TIME, UPLOAD_BUTTON_SCROLL_WAIT, UPLOAD_BUTTON_SCROLL_WAIT, UPLOAD_CANCELED_DETECTION_TIMEOUT, BROWSER_DIALOG_TIMEOUT, PORTAL_CONFIRM_WAIT, CLICK_PORTAL_START_UPLOAD_MAX_RETRIES, START_UPLOAD_ENABLED_CHECK_MAX_ATTEMPTS, START_UPLOAD_ENABLED_CHECK_INTERVAL, START_UPLOAD_SCROLL_WAIT, WAIT_AND_CLICK_START_MAX_RETRIES, START_UPLOAD_SCROLL_WAIT, START_UPLOAD_CLICK_WAIT, START_UPLOAD_CLICK_WAIT, WAIT_TIMEOUT, ADD_METADATA_SCROLL_WAIT, ADD_METADATA_CLICK_WAIT, POST_TITLE, CONTENT_TITLE, DESCRIPTION, KEYWORDS, SUBMIT_FORM_WAIT, WAIT_TIMEOUT, MODAL_THUMBNAIL_SCROLL_WAIT, DOWNLOAD_BUTTON_SCROLL_WAIT, DOWNLOADS_FOLDER, WAIT_TIMEOUT, CIRCLES_CLICK_WAIT, CIRCLE_NAME, QA_CIRCLE_OPEN_WAIT, WAIT_TIMEOUT, STEP_GAP_SECONDS, UPLOAD_BUTTON_SCROLL_WAIT, UPLOAD_BUTTON_SCROLL_WAIT, UPLOAD_CANCELED_DETECTION_TIMEOUT, BROWSER_DIALOG_TIMEOUT, PORTAL_CONFIRM_WAIT, CLICK_PORTAL_START_UPLOAD_MAX_RETRIES, START_UPLOAD_ENABLED_CHECK_MAX_ATTEMPTS, START_UPLOAD_ENABLED_CHECK_INTERVAL, START_UPLOAD_SCROLL_WAIT, WAIT_TIMEOUT, WAIT_AND_CLICK_START_MAX_RETRIES, WAIT_TIMEOUT, WAIT_TIMEOUT, UPLOAD_WAIT_TIME, START_UPLOAD_SCROLL_WAIT, START_UPLOAD_CLICK_WAIT, START_UPLOAD_CLICK_WAIT, WAIT_TIMEOUT, ADD_METADATA_SCROLL_WAIT, ADD_METADATA_CLICK_WAIT, POST_TITLE, CONTENT_TITLE, DESCRIPTION, KEYWORDS, WAIT_TIMEOUT, SUBMIT_FORM_WAIT, WAIT_TIMEOUT, MODAL_THUMBNAIL_SCROLL_WAIT, MODAL_OPEN_WAIT, DOWNLOAD_BUTTON_SCROLL_WAIT, DOWNLOADS_FOLDER, LOGIN_SUCCESS_WAIT, SUBMIT_AFTER_WAIT
)


# Note: BROWSER_HEADLESS, BROWSER_IGNORE_HTTPS_ERRORS, and BROWSER_NO_VIEWPORT have defaults
# in env_variables.py and can legitimately be False, so we don't validate them here


class UploadHandler:
    """
    Handles file upload workflow including button clicks and file selection.
    
    This class manages the complete upload process:
    - Clicking Upload button
    - Selecting ZIP file
    - Starting upload process
    - Handling upload retries and cancellations
    
    Attributes:
        page: Playwright sync Page object
        wait_timeout (int): Timeout in milliseconds
        step_gap_seconds (float): Delay between steps
        upload_wait_seconds (int): Wait time after upload
    
    Example:
        >>> upload_handler = UploadHandler(page)
        >>> success, filename = upload_handler.click_upload_button("/path/to/file.zip")
        >>> if success:
        ...     upload_handler.start_upload("/path/to/file.zip", filename)
    """
    
    def __init__(self, page, wait_timeout: Optional[int] = None,
                 step_gap_seconds: Optional[float] = None,
                 upload_wait_seconds: Optional[int] = None):
        """
        Initialize upload handler.
        
        Args:
            page: Playwright sync Page object
            wait_timeout (int, optional): Timeout in milliseconds. If None, uses WAIT_TIMEOUT from env_variables
            step_gap_seconds (float, optional): Delay between steps. If None, uses STEP_GAP_SECONDS from env_variables
            upload_wait_seconds (int, optional): Wait time after upload. If None, uses UPLOAD_WAIT_TIME from env_variables
        """
        self.page = page
        
        if wait_timeout is None:
            if not WAIT_TIMEOUT:
                raise ValueError("WAIT_TIMEOUT environment variable is required.")
            wait_timeout = int(WAIT_TIMEOUT) * 1000
        self.wait_timeout = wait_timeout
        
        if step_gap_seconds is None:
            if not STEP_GAP_SECONDS:
                raise ValueError("STEP_GAP_SECONDS environment variable is required.")
            step_gap_seconds = float(STEP_GAP_SECONDS)
        self.step_gap_seconds = step_gap_seconds
        
        if upload_wait_seconds is None:
            if not UPLOAD_WAIT_TIME:
                raise ValueError("UPLOAD_WAIT_TIME environment variable is required.")
            upload_wait_seconds = int(UPLOAD_WAIT_TIME)
        self.upload_wait_seconds = upload_wait_seconds
    
    def click_upload_button(self, zip_file: str) -> Tuple[bool, Optional[str]]:
        """
        Clicks the Upload button and selects the ZIP file.
        
        Args:
            zip_file (str): Path to the ZIP file to upload
        
        Returns:
            tuple: (success: bool, uploaded_filename: str or None)
        
        Example:
            >>> upload_handler = UploadHandler(page)
            >>> success, filename = upload_handler.click_upload_button("/path/to/file.zip")
            >>> if success:
            ...     print(f"File selected: {filename}")
        """
        uploaded_filename = os.path.basename(zip_file)

        try:
            # Click Upload button
            upload_btn = self.page.locator("//*[@id='scrollingDiv']/div[2]/div[2]/div[1]/div/div[2]/div[2]/button")
            upload_btn.wait_for(state="visible", timeout=self.wait_timeout)
            upload_btn.scroll_into_view_if_needed()
            if not UPLOAD_BUTTON_SCROLL_WAIT:
                raise ValueError("UPLOAD_BUTTON_SCROLL_WAIT environment variable is required.")
            upload_button_scroll_wait = float(UPLOAD_BUTTON_SCROLL_WAIT)
            time.sleep(upload_button_scroll_wait)
            upload_btn.click()
            logger.info("📤 Upload button clicked")
        except Exception as e:
            logger.warning(f"Could not click Upload button with XPath, trying fallback method: {e}")
            # Fallback: Try to find button by text
            upload_btns = self.page.locator("button").all()
            for btn in upload_btns:
                if btn.text_content().strip().lower() == "upload":
                    btn.scroll_into_view_if_needed()
                    if not UPLOAD_BUTTON_SCROLL_WAIT:
                        raise ValueError("UPLOAD_BUTTON_SCROLL_WAIT environment variable is required.")
                    upload_button_scroll_wait = float(UPLOAD_BUTTON_SCROLL_WAIT)
                    time.sleep(upload_button_scroll_wait)
                    btn.click(force=True)
                    logger.info("📤 Upload button clicked (fallback method)")
                    break
        
        time.sleep(self.step_gap_seconds)
        
        try:
            files_input = self.page.locator("#files")
            files_input.wait_for(state="attached", timeout=self.wait_timeout)
            self.page.set_input_files("#files", zip_file)
            time.sleep(self.step_gap_seconds)
            self.page.evaluate("(sel)=>{const el=document.querySelector(sel); if(el){el.dispatchEvent(new Event('change',{bubbles:true}));}}", "#files")
            logger.info("📦 ZIP file selected via #files")
        except Exception as e:
            logger.warning(f"#files not usable, falling back to generic input[type='file']: {e}")
            file_input = self.page.locator("input[type='file']")
            file_input.wait_for(state="attached", timeout=self.wait_timeout)
            file_input.set_input_files(zip_file)
            self.page.evaluate("(sel)=>{const el=document.querySelector(sel); if(el){el.dispatchEvent(new Event('change',{bubbles:true}));}}", "input[type='file']")
            logger.info("📦 ZIP file selected")
            time.sleep(self.step_gap_seconds)
        
        try:
            file_tile = self.page.locator(f"//*[@id='portal']//*[contains(text(), '{uploaded_filename}')]")
            file_tile.wait_for(state="visible", timeout=self.wait_timeout)
            logger.info("🧱 File tile visible in modal")
            time.sleep(self.step_gap_seconds)
        except Exception as e:
            logger.warning(f"File tile not confirmed: {e}")
        
        return True, uploaded_filename
    
    def _upload_canceled_detected(self, short_timeout_ms: Optional[int] = None) -> bool:
        """
        Detect if 'Upload canceled' message appears in portal.
        
        Args:
            short_timeout_ms (int, optional): Timeout in milliseconds. If None, loaded from env
        
        Returns:
            bool: True if canceled message detected, False otherwise
        """
        if short_timeout_ms is None:
            if not UPLOAD_CANCELED_DETECTION_TIMEOUT:
                raise ValueError("UPLOAD_CANCELED_DETECTION_TIMEOUT environment variable is required.")
            short_timeout_ms = int(UPLOAD_CANCELED_DETECTION_TIMEOUT)
        try:
            cancel_label = self.page.locator("//*[@id='portal']//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'upload cancel') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'upload cancelled') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'upload canceled')]")
            cancel_label.wait_for(state="visible", timeout=short_timeout_ms)
            logger.warning("Detected 'Upload canceled' message")
            return True
        except Exception:
            return False

    def _accept_browser_dialog_once(self, timeout_seconds: Optional[float] = None) -> None:
        """
        Accepts the next browser dialog (alert/confirm) if it appears within timeout.
        
        Args:
            timeout_seconds (float, optional): Timeout in seconds. If None, loaded from env
        """
        if timeout_seconds is None:
            if not BROWSER_DIALOG_TIMEOUT:
                raise ValueError("BROWSER_DIALOG_TIMEOUT environment variable is required.")
            timeout_seconds = float(BROWSER_DIALOG_TIMEOUT)
        accepted = {"done": False}
        def handler(dialog):
            try:
                dialog.accept()
                accepted["done"] = True
                logger.info("✅ Browser dialog accepted")
            except Exception:
                pass
        self.page.once("dialog", handler)
        t0 = time.time()
        while time.time() - t0 < timeout_seconds and not accepted["done"]:
            time.sleep(0.1)

    def _click_portal_confirm_if_present(self, wait_ms: Optional[int] = None) -> bool:
        """
        Clicks a confirm/ok/proceed button inside the portal if it appears.
        
        Args:
            wait_ms (int, optional): Wait time in milliseconds. If None, loaded from env
        
        Returns:
            bool: True if button clicked, False otherwise
        """
        if wait_ms is None:
            if not PORTAL_CONFIRM_WAIT:
                raise ValueError("PORTAL_CONFIRM_WAIT environment variable is required.")
            wait_ms = int(PORTAL_CONFIRM_WAIT)
        candidates = [
            "//*[@id='portal']//button[normalize-space()='OK']",
            "//*[@id='portal']//button[normalize-space()='Ok']",
            "//*[@id='portal']//button[normalize-space()='Yes']",
            "//*[@id='portal']//button[contains(.,'Proceed')]",
            "//*[@id='portal']//button[contains(.,'Confirm')]",
            "//*[@id='portal']//button[contains(.,'Start Upload')]",
        ]
        deadline = time.time() + (wait_ms / 1000.0)
        while time.time() < deadline:
            for sel in candidates:
                try:
                    btn = self.page.locator(sel)
                    btn.wait_for(state="visible", timeout=250)
                    btn.scroll_into_view_if_needed()
                    time.sleep(0.1)
                    btn.click()
                    logger.info(f"✅ Portal confirm clicked: {sel}")
                    return True
                except Exception:
                    continue
            time.sleep(0.1)
        return False

    def _click_portal_start_upload(self, max_retries: Optional[int] = None) -> bool:
        """
        Click Start Upload button inside portal using provided XPath.
        
        Args:
            max_retries (int, optional): Maximum retry attempts. If None, loaded from env
        
        Returns:
            bool: True if clicked successfully, False otherwise
        """
        if max_retries is None:
            if not CLICK_PORTAL_START_UPLOAD_MAX_RETRIES:
                raise ValueError("CLICK_PORTAL_START_UPLOAD_MAX_RETRIES environment variable is required.")
            max_retries = int(CLICK_PORTAL_START_UPLOAD_MAX_RETRIES)
        
        if not START_UPLOAD_ENABLED_CHECK_MAX_ATTEMPTS:
            raise ValueError("START_UPLOAD_ENABLED_CHECK_MAX_ATTEMPTS environment variable is required.")
        if not START_UPLOAD_ENABLED_CHECK_INTERVAL:
            raise ValueError("START_UPLOAD_ENABLED_CHECK_INTERVAL environment variable is required.")
        if not START_UPLOAD_SCROLL_WAIT:
            raise ValueError("START_UPLOAD_SCROLL_WAIT environment variable is required.")
        
        enabled_check_max_attempts = int(START_UPLOAD_ENABLED_CHECK_MAX_ATTEMPTS)
        enabled_check_interval = float(START_UPLOAD_ENABLED_CHECK_INTERVAL)
        start_upload_scroll_wait = float(START_UPLOAD_SCROLL_WAIT)
        
        for attempt in range(max_retries):
            try:
                su_inner = self.page.locator("//*[@id='portal']/div/div/div/div[2]/div/div/div[2]/div/div[2]/button/div")
                su_inner.wait_for(state="visible", timeout=self.wait_timeout)
                su_btn = su_inner.locator("xpath=ancestor::button[1]")
                for _ in range(enabled_check_max_attempts):
                    if su_btn.is_enabled():
                        break
                    time.sleep(enabled_check_interval)
                su_btn.scroll_into_view_if_needed()
                time.sleep(start_upload_scroll_wait)
                try:
                    su_btn.click()
                except Exception:
                    self.page.evaluate("el=>el.click()", su_btn)
                logger.info("⬆️ Start Upload clicked (portal)")
                return True
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{max_retries} to click portal Start Upload failed: {e}")
                time.sleep(1)
        return False

    def _wait_and_click_start(self, zip_file: str, uploaded_filename: str, max_retries: Optional[int] = None) -> bool:
        """
        Wait until header shows selected file count and start button is enabled, then click.
        
        Args:
            zip_file (str): Path to ZIP file (for retry if needed)
            uploaded_filename (str): Name of uploaded file
            max_retries (int, optional): Maximum retry attempts. If None, loaded from env
        
        Returns:
            bool: True if successful, False otherwise
        """
        if max_retries is None:
            if not WAIT_AND_CLICK_START_MAX_RETRIES:
                raise ValueError("WAIT_AND_CLICK_START_MAX_RETRIES environment variable is required.")
            max_retries = int(WAIT_AND_CLICK_START_MAX_RETRIES)
        for attempt in range(max_retries):
            try:
                header = self.page.locator("//*[@id='portal']//*[contains(., 'file selected') or contains(., 'File selected')]")
                header.wait_for(state="visible", timeout=self.wait_timeout)
            except Exception:
                logger.info("ℹ️ Header with 'file selected' not found; proceeding anyway")
            
            try:
                self.page.locator(f"//*[@id='portal']//*[contains(text(), '{uploaded_filename}')]").wait_for(state="visible", timeout=self.wait_timeout)
            except Exception as e:
                logger.warning(f"File tile missing before start upload: {e}")
            
            if self._click_portal_start_upload():
                self._accept_browser_dialog_once()
                self._click_portal_confirm_if_present()
                if self._upload_canceled_detected():
                    logger.info("↻ Retrying: re-selecting file due to cancellation...")
                    try:
                        self.page.set_input_files("#files", zip_file)
                        self.page.evaluate("(sel)=>{const el=document.querySelector(sel); if(el){el.dispatchEvent(new Event('change',{bubbles:true}));}}", "#files")
                    except Exception as e2:
                        logger.error(f"Failed to re-select file: {e2}")
                        return False
                    continue
                return True
            time.sleep(1)
        return False
    
    def start_upload(self, zip_file: str, uploaded_filename: str) -> bool:
        """
        Clicks the Start Upload button and waits for upload to complete.
        
        Args:
            zip_file (str): Path to the ZIP file (for retry if needed)
            uploaded_filename (str): Name of the uploaded file
        
        Returns:
            bool: True if successful, False otherwise
        
        Example:
            >>> upload_handler = UploadHandler(page)
            >>> success = upload_handler.start_upload("/path/to/file.zip", "file.zip")
            >>> if success:
            ...     print("Upload started successfully")
        """
        try:
            start_upload_inner = self.page.locator("//*[@id='portal']/div/div/div/div[2]/div/div/div[2]/div/div[2]/button/div")
            start_upload_inner.wait_for(state="visible", timeout=self.wait_timeout)
            start_upload_btn = start_upload_inner.locator("xpath=ancestor::button[1]")
            start_upload_btn.scroll_into_view_if_needed()
            if not START_UPLOAD_SCROLL_WAIT:
                raise ValueError("START_UPLOAD_SCROLL_WAIT environment variable is required.")
            start_upload_scroll_wait = float(START_UPLOAD_SCROLL_WAIT)
            time.sleep(start_upload_scroll_wait)
            start_upload_btn.click()
            logger.info("⬆️ Start Upload clicked")
            if not START_UPLOAD_CLICK_WAIT:
                raise ValueError("START_UPLOAD_CLICK_WAIT environment variable is required.")
            start_upload_click_wait = float(START_UPLOAD_CLICK_WAIT)
            time.sleep(start_upload_click_wait)
            
            if not self._wait_and_click_start(zip_file, uploaded_filename):
                logger.error("Could not start upload after readiness checks")
                return False
            else:
                logger.info("⬆️ Start Upload initiated")
            
            logger.info(f"⏳ Waiting {self.upload_wait_seconds}s for upload processing...")
            time.sleep(self.upload_wait_seconds)
            
            try:
                self.page.locator("//*[@id='portal']//button[contains(.,'Add Metadata')]").wait_for(state="visible", timeout=self.wait_timeout)
                logger.info("✅ Upload stage confirmed — Add Metadata visible")
            except Exception:
                logger.info("ℹ️ Add Metadata not visible yet; proceeding with retries later")
            
            return True
        except Exception as e:
            logger.warning(f"Could not click Start Upload (primary XPath): {e}")
            try:
                alt = self.page.locator("//button[normalize-space()='Start Upload']")
                alt.wait_for(state="visible", timeout=self.wait_timeout)
                alt.scroll_into_view_if_needed()
                alt.click(force=True)
                logger.info("⬆️ Start Upload clicked (fallback)")
                if not START_UPLOAD_CLICK_WAIT:
                    raise ValueError("START_UPLOAD_CLICK_WAIT environment variable is required.")
                start_upload_click_wait = float(START_UPLOAD_CLICK_WAIT)
                time.sleep(start_upload_click_wait)
                
                if not self._wait_and_click_start(zip_file, uploaded_filename):
                    logger.error("Could not start upload after readiness checks (fallback)")
                    return False
                else:
                    logger.info("⬆️ Start Upload initiated (fallback)")
                
                logger.info(f"⏳ Waiting {self.upload_wait_seconds}s for upload processing (fallback)...")
                time.sleep(self.upload_wait_seconds)
                
                try:
                    self.page.locator("//*[@id='portal']//button[contains(.,'Add Metadata')]").wait_for(state="visible", timeout=self.wait_timeout)
                    logger.info("✅ Upload stage confirmed — Add Metadata visible (fallback path)")
                except Exception:
                    logger.info("ℹ️ Add Metadata not visible yet (fallback path)")
                
                return True
            except Exception as e2:
                logger.error(f"Start Upload click failed: {e2}")
                return False


class MetadataHandler:
    """
    Handles metadata form filling and submission.
    
    This class manages the complete metadata workflow:
    - Clicking Add Metadata button
    - Filling metadata fields (Post Title, Title, Description, Keywords)
    - Submitting the form
    
    Attributes:
        page: Playwright sync Page object
        wait_timeout (int): Timeout in milliseconds
    
    Example:
        >>> metadata_handler = MetadataHandler(page)
        >>> success = metadata_handler.fill_form()
        >>> if success:
        ...     metadata_handler.submit_form()
    """
    
    def __init__(self, page, wait_timeout: Optional[int] = None):
        """
        Initialize metadata handler.
        
        Args:
            page: Playwright sync Page object
            wait_timeout (int, optional): Timeout in milliseconds. If None, uses WAIT_TIMEOUT from env_variables
        """
        self.page = page
        
        if wait_timeout is None:
            if not WAIT_TIMEOUT:
                raise ValueError("WAIT_TIMEOUT environment variable is required.")
            wait_timeout = int(WAIT_TIMEOUT) * 1000
        self.wait_timeout = wait_timeout
    
    def fill_form(self) -> bool:
        """
        Fills the metadata form with values from environment variables.
        
        Returns:
            bool: True if successful, False otherwise
        
        Example:
            >>> metadata_handler = MetadataHandler(page)
            >>> success = metadata_handler.fill_form()
            >>> if success:
            ...     print("Metadata form filled successfully")
        """
        try:
            # Click Add Metadata button
            add_metadata_btn = self.page.locator("//*[@id='portal']//button[contains(.,'Add Metadata')]")
            add_metadata_btn.wait_for(state="attached", timeout=self.wait_timeout)
            add_metadata_btn.wait_for(state="visible", timeout=self.wait_timeout)
            add_metadata_btn.scroll_into_view_if_needed()
            if not ADD_METADATA_SCROLL_WAIT:
                raise ValueError("ADD_METADATA_SCROLL_WAIT environment variable is required.")
            add_metadata_scroll_wait = float(ADD_METADATA_SCROLL_WAIT)
            time.sleep(add_metadata_scroll_wait)
            add_metadata_btn.click()
            logger.info("🟢 Add Metadata clicked")
        except Exception as e:
            logger.warning(f"Primary Add Metadata click failed: {e}")
            try:
                add_metadata_btn.scroll_into_view_if_needed()
                add_metadata_btn.click(force=True)
                logger.info("🟢 Add Metadata clicked (force)")
            except Exception as e2:
                logger.error(f"Add Metadata click failed: {e2}")
                return False
        
        if not ADD_METADATA_CLICK_WAIT:
            raise ValueError("ADD_METADATA_CLICK_WAIT environment variable is required.")
        add_metadata_click_wait = float(ADD_METADATA_CLICK_WAIT)
        time.sleep(add_metadata_click_wait)

        # Fill metadata fields
        try:
            if not POST_TITLE:
                raise ValueError("POST_TITLE environment variable is required.")
            if not CONTENT_TITLE:
                raise ValueError("CONTENT_TITLE environment variable is required.")
            if not DESCRIPTION:
                raise ValueError("DESCRIPTION environment variable is required.")
            if not KEYWORDS:
                raise ValueError("KEYWORDS environment variable is required.")
            
            post_title = POST_TITLE
            content_title = CONTENT_TITLE
            description = DESCRIPTION
            keyword = KEYWORDS

            if not post_title:
                raise ValueError("POST_TITLE environment variable is required.")
            if not content_title:
                raise ValueError("CONTENT_TITLE environment variable is required.")
            if not description:
                raise ValueError("DESCRIPTION environment variable is required.")
            if not keyword:
                raise ValueError("KEYWORDS environment variable is required.")

            post_field = self.page.locator("//input[@placeholder='Post Title']")
            post_field.wait_for(state="visible", timeout=self.wait_timeout)
            post_field.clear()
            post_field.fill(post_title)

            self.page.locator("//input[@placeholder='Title']").fill(content_title)
            self.page.locator("//textarea[@placeholder='Description']").fill(description)
            self.page.locator("//input[@placeholder='Keywords']").fill(keyword)
            logger.info(f"📝 Metadata filled successfully: {post_title}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to fill metadata form: {e}")
            return False
    
    def submit_form(self) -> bool:
        """
        Submits the metadata form.
        
        Returns:
            bool: True if successful, False otherwise
        
        Example:
            >>> metadata_handler = MetadataHandler(page)
            >>> success = metadata_handler.submit_form()
            >>> if success:
            ...     print("Metadata form submitted successfully")
        """
        try:
            submit_btn = self.page.locator("//button[normalize-space()='Submit']")
            submit_btn.wait_for(state="visible", timeout=self.wait_timeout)
            submit_btn.scroll_into_view_if_needed()
            submit_btn.click()
            logger.info("📤 Submit clicked")

            if not SUBMIT_FORM_WAIT:
                raise ValueError("SUBMIT_FORM_WAIT environment variable is required.")
            submit_form_wait = float(SUBMIT_FORM_WAIT)
            time.sleep(submit_form_wait)
            
            logger.info("✅ Upload and metadata submission complete.")
            return True
        except Exception as e:
            logger.error(f"Failed to submit metadata form: {e}")
            return False


class ModalHandler:
    """
    Handles modal opening and download verification.
    
    This class manages the complete modal workflow:
    - Clicking uploaded ZIP thumbnail to open modal
    - Clicking Download button
    - Saving downloaded file
    - Verifying file names match
    
    Attributes:
        page: Playwright sync Page object
        wait_timeout (int): Timeout in milliseconds
    
    Example:
        >>> modal_handler = ModalHandler(page)
        >>> success = modal_handler.open_and_verify_download("file.zip")
        >>> if success:
        ...     print("Download verified successfully")
    """
    
    def __init__(self, page, wait_timeout: Optional[int] = None):
        """
        Initialize modal handler.
        
        Args:
            page: Playwright sync Page object
            wait_timeout (int, optional): Timeout in milliseconds. If None, uses WAIT_TIMEOUT from env_variables
        """
        self.page = page
        
        if wait_timeout is None:
            if not WAIT_TIMEOUT:
                raise ValueError("WAIT_TIMEOUT environment variable is required.")
            wait_timeout = int(WAIT_TIMEOUT) * 1000
        self.wait_timeout = wait_timeout
    
    def open_and_verify_download(self, uploaded_filename: str) -> bool:
        """
        Opens the modal by clicking uploaded ZIP thumbnail and verifies download.
        
        Args:
            uploaded_filename (str): Name of the uploaded file
        
        Returns:
            bool: True if successful, False otherwise
        
        Example:
            >>> modal_handler = ModalHandler(page)
            >>> success = modal_handler.open_and_verify_download("file.zip")
            >>> if success:
            ...     print("Modal opened and download verified")
        """
        try:
            # Click the uploaded ZIP thumbnail to open the modal
            zip_thumb = self.page.locator("//*[@id='scrollingDiv']/div[4]/div[2]/div[1]/div[2]/div/div[1]/div[4]/div/div")
            zip_thumb.wait_for(state="visible", timeout=self.wait_timeout)
            zip_thumb.scroll_into_view_if_needed()
            if not MODAL_THUMBNAIL_SCROLL_WAIT:
                raise ValueError("MODAL_THUMBNAIL_SCROLL_WAIT environment variable is required.")
            modal_thumbnail_scroll_wait = float(MODAL_THUMBNAIL_SCROLL_WAIT)
            time.sleep(modal_thumbnail_scroll_wait)
            zip_thumb.click()
            logger.info("🖱️ Uploaded ZIP thumbnail clicked → modal opening...")
            
            # Wait for Download button and click
            dl_span = self.page.locator("//*[@id='portal']/div/div/div/div/div/div[2]/div/div/button/span")
            dl_span.wait_for(state="visible", timeout=self.wait_timeout)
            dl_btn = dl_span.locator("xpath=ancestor::button[1]")
            dl_btn.scroll_into_view_if_needed()
            if not DOWNLOAD_BUTTON_SCROLL_WAIT:
                raise ValueError("DOWNLOAD_BUTTON_SCROLL_WAIT environment variable is required.")
            download_button_scroll_wait = float(DOWNLOAD_BUTTON_SCROLL_WAIT)
            time.sleep(download_button_scroll_wait)

            if not DOWNLOADS_FOLDER:
                raise ValueError("DOWNLOADS_FOLDER environment variable is required.")
            downloads_folder = DOWNLOADS_FOLDER
            downloads_path = os.path.join(os.environ["USERPROFILE"], downloads_folder)
            os.makedirs(downloads_path, exist_ok=True)

            # Use Playwright download API
            with self.page.expect_download() as d_info:
                dl_btn.click()
            download = d_info.value
            suggested = download.suggested_filename
            target_path = os.path.join(downloads_path, suggested)
            try:
                download.save_as(target_path)
            except Exception:
                temp_path = download.path()
                if temp_path and os.path.exists(temp_path):
                    try:
                        shutil.copyfile(temp_path, target_path)
                    except Exception:
                        pass

            logger.info(f"⬇️ Download saved as: {os.path.basename(target_path)}")

            # Verify file names
            downloaded_file = os.path.basename(target_path)
            uploaded_name_root = uploaded_filename.lower().split(".zip")[0]
            downloaded_name_root = downloaded_file.lower().split(".zip")[0]

            logger.info(f"\n🔍 Uploaded File Name : {uploaded_filename}")
            logger.info(f"🔍 Downloaded File Name: {downloaded_file}")

            if uploaded_name_root == downloaded_name_root:
                logger.info("🎯 Verification Passed — File names match perfectly.")
            elif downloaded_name_root.startswith(uploaded_name_root):
                logger.warning("Verification Partial — Browser likely appended a suffix (e.g., '(1)').")
            else:
                logger.error("Verification Failed — Downloaded name doesn't match uploaded name!")

            return True
        except Exception as e:
            logger.error(f"ERROR during modal open or download verification: {e}")
            return False


class UploadAutomationSuite:
    """
    Main automation suite class for single ZIP file upload workflow.
    
    This class orchestrates the complete upload process, similar to
    ConfiguratorTestSuite structure. All helper methods are class methods.
    
    Attributes:
        playwright: Playwright instance
        browser: Browser instance
        context: Browser context instance
        page: Page instance
        zip_file (str): Path to ZIP file to upload
    
    Example:
        >>> suite = UploadAutomationSuite()
        >>> suite.run()
    """

    def __init__(self):
        """
        Initialize upload automation suite.
        """
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.zip_file = None
    
    def open_circle(self) -> bool:
        """
        Opens the QA Testing circle (or specified circle) in the portal.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not WAIT_TIMEOUT:
                raise ValueError("WAIT_TIMEOUT environment variable is required.")
            wait_timeout = int(WAIT_TIMEOUT) * 1000
            
            self.page.locator("//a[contains(.,'Circles')]").wait_for(state="visible", timeout=wait_timeout)
            self.page.locator("//a[contains(.,'Circles')]").click()
            logger.info("📂 Circles clicked")
            
            if not CIRCLES_CLICK_WAIT:
                raise ValueError("CIRCLES_CLICK_WAIT environment variable is required.")
            circles_click_wait = float(CIRCLES_CLICK_WAIT)
            time.sleep(circles_click_wait)

            if not CIRCLE_NAME:
                raise ValueError("CIRCLE_NAME environment variable is required.")
            circle_name = CIRCLE_NAME
            
            qa_circle = self.page.locator(f"//*[contains(text(),'{circle_name}')]")
            qa_circle.wait_for(state="visible", timeout=wait_timeout)
            qa_circle.scroll_into_view_if_needed()
            qa_circle.click()
            logger.info(f"🟢 {circle_name} circle opened")
            
            if not QA_CIRCLE_OPEN_WAIT:
                raise ValueError("QA_CIRCLE_OPEN_WAIT environment variable is required.")
            qa_circle_open_wait = float(QA_CIRCLE_OPEN_WAIT)
            time.sleep(qa_circle_open_wait)

            return True
        except Exception as e:
            logger.error(f"Failed to open QA Testing circle: {e}")
            return False
    
    def click_upload_button(self, zip_file: str) -> Tuple[bool, Optional[str]]:
        """
        Clicks the Upload button and selects the ZIP file.
        
        Args:
            zip_file (str): Path to the ZIP file to upload
        
        Returns:
            tuple: (success: bool, uploaded_filename: str or None)
        """
        uploaded_filename = os.path.basename(zip_file)
        
        if not WAIT_TIMEOUT:
            raise ValueError("WAIT_TIMEOUT environment variable is required.")
        wait_timeout = int(WAIT_TIMEOUT) * 1000
        
        if not STEP_GAP_SECONDS:
            raise ValueError("STEP_GAP_SECONDS environment variable is required.")
        step_gap_seconds = float(STEP_GAP_SECONDS)

        try:
            # Click Upload button
            upload_btn = self.page.locator("//*[@id='scrollingDiv']/div[2]/div[2]/div[1]/div/div[2]/div[2]/button")
            upload_btn.wait_for(state="visible", timeout=wait_timeout)
            upload_btn.scroll_into_view_if_needed()
            if not UPLOAD_BUTTON_SCROLL_WAIT:
                raise ValueError("UPLOAD_BUTTON_SCROLL_WAIT environment variable is required.")
            upload_button_scroll_wait = float(UPLOAD_BUTTON_SCROLL_WAIT)
            time.sleep(upload_button_scroll_wait)
            upload_btn.click()
            logger.info("📤 Upload button clicked")
        except Exception as e:
            logger.warning(f"Could not click Upload button with XPath, trying fallback method: {e}")
            # Fallback: Try to find button by text
            upload_btns = self.page.locator("button").all()
            for btn in upload_btns:
                if btn.text_content().strip().lower() == "upload":
                    btn.scroll_into_view_if_needed()
                    if not UPLOAD_BUTTON_SCROLL_WAIT:
                        raise ValueError("UPLOAD_BUTTON_SCROLL_WAIT environment variable is required.")
                    upload_button_scroll_wait = float(UPLOAD_BUTTON_SCROLL_WAIT)
                    time.sleep(upload_button_scroll_wait)
                    btn.click(force=True)
                    logger.info("📤 Upload button clicked (fallback method)")
                    break
        
        time.sleep(step_gap_seconds)

        # Select ZIP file
        try:
            files_input = self.page.locator("#files")
            files_input.wait_for(state="attached", timeout=wait_timeout)
            self.page.set_input_files("#files", zip_file)
            time.sleep(step_gap_seconds)
            self.page.evaluate("(sel)=>{const el=document.querySelector(sel); if(el){el.dispatchEvent(new Event('change',{bubbles:true}));}}", "#files")
            logger.info("📦 ZIP file selected via #files")
        except Exception as e:
            logger.warning(f"#files not usable, falling back to generic input[type='file']: {e}")
            file_input = self.page.locator("input[type='file']")
            file_input.wait_for(state="attached", timeout=wait_timeout)
            file_input.set_input_files(zip_file)
            self.page.evaluate("(sel)=>{const el=document.querySelector(sel); if(el){el.dispatchEvent(new Event('change',{bubbles:true}));}}", "input[type='file']")
            logger.info("📦 ZIP file selected")
            time.sleep(step_gap_seconds)

        # Confirm file tile appears
        try:
            file_tile = self.page.locator(f"//*[@id='portal']//*[contains(text(), '{uploaded_filename}')]")
            file_tile.wait_for(state="visible", timeout=wait_timeout)
            logger.info("🧱 File tile visible in modal")
            time.sleep(step_gap_seconds)
        except Exception as e:
            logger.warning(f"File tile not confirmed: {e}")
        
        return True, uploaded_filename
    
    def _upload_canceled_detected(self, short_timeout_ms: Optional[int] = None) -> bool:
        """Detect if 'Upload canceled' message appears in portal."""
        if short_timeout_ms is None:
            if not UPLOAD_CANCELED_DETECTION_TIMEOUT:
                raise ValueError("UPLOAD_CANCELED_DETECTION_TIMEOUT environment variable is required.")
            short_timeout_ms = int(UPLOAD_CANCELED_DETECTION_TIMEOUT)
        try:
            cancel_label = self.page.locator("//*[@id='portal']//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'upload cancel') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'upload cancelled') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'upload canceled')]")
            cancel_label.wait_for(state="visible", timeout=short_timeout_ms)
            logger.warning("Detected 'Upload canceled' message")
            return True
        except Exception:
            return False

    def _accept_browser_dialog_once(self, timeout_seconds: Optional[float] = None) -> None:
        """Accepts the next browser dialog (alert/confirm) if it appears within timeout."""
        if timeout_seconds is None:
            if not BROWSER_DIALOG_TIMEOUT:
                raise ValueError("BROWSER_DIALOG_TIMEOUT environment variable is required.")
            timeout_seconds = float(BROWSER_DIALOG_TIMEOUT)
        accepted = {"done": False}
        def handler(dialog):
            try:
                dialog.accept()
                accepted["done"] = True
                logger.info("✅ Browser dialog accepted")
            except Exception:
                pass
        self.page.once("dialog", handler)
        t0 = time.time()
        while time.time() - t0 < timeout_seconds and not accepted["done"]:
            time.sleep(0.1)

    def _click_portal_confirm_if_present(self, wait_ms: Optional[int] = None) -> bool:
        """Clicks a confirm/ok/proceed button inside the portal if it appears."""
        if wait_ms is None:
            if not PORTAL_CONFIRM_WAIT:
                raise ValueError("PORTAL_CONFIRM_WAIT environment variable is required.")
            wait_ms = int(PORTAL_CONFIRM_WAIT)
        candidates = [
            "//*[@id='portal']//button[normalize-space()='OK']",
            "//*[@id='portal']//button[normalize-space()='Ok']",
            "//*[@id='portal']//button[normalize-space()='Yes']",
            "//*[@id='portal']//button[contains(.,'Proceed')]",
            "//*[@id='portal']//button[contains(.,'Confirm')]",
            "//*[@id='portal']//button[contains(.,'Start Upload')]",
        ]
        deadline = time.time() + (wait_ms / 1000.0)
        while time.time() < deadline:
            for sel in candidates:
                try:
                    btn = self.page.locator(sel)
                    btn.wait_for(state="visible", timeout=250)
                    btn.scroll_into_view_if_needed()
                    time.sleep(0.1)
                    btn.click()
                    logger.info(f"✅ Portal confirm clicked: {sel}")
                    return True
                except Exception:
                    continue
            time.sleep(0.1)
        return False

    def _click_portal_start_upload(self, max_retries: Optional[int] = None) -> bool:
        """Click Start Upload button inside portal using provided XPath."""
        if max_retries is None:
            if not CLICK_PORTAL_START_UPLOAD_MAX_RETRIES:
                raise ValueError("CLICK_PORTAL_START_UPLOAD_MAX_RETRIES environment variable is required.")
            max_retries = int(CLICK_PORTAL_START_UPLOAD_MAX_RETRIES)
        
        if not START_UPLOAD_ENABLED_CHECK_MAX_ATTEMPTS:
            raise ValueError("START_UPLOAD_ENABLED_CHECK_MAX_ATTEMPTS environment variable is required.")
        if not START_UPLOAD_ENABLED_CHECK_INTERVAL:
            raise ValueError("START_UPLOAD_ENABLED_CHECK_INTERVAL environment variable is required.")
        if not START_UPLOAD_SCROLL_WAIT:
            raise ValueError("START_UPLOAD_SCROLL_WAIT environment variable is required.")
        
        enabled_check_max_attempts = int(START_UPLOAD_ENABLED_CHECK_MAX_ATTEMPTS)
        enabled_check_interval = float(START_UPLOAD_ENABLED_CHECK_INTERVAL)
        start_upload_scroll_wait = float(START_UPLOAD_SCROLL_WAIT)
        
        if not WAIT_TIMEOUT:
            raise ValueError("WAIT_TIMEOUT environment variable is required.")
        wait_timeout = int(WAIT_TIMEOUT) * 1000
        
        for attempt in range(max_retries):
            try:
                su_inner = self.page.locator("//*[@id='portal']/div/div/div/div[2]/div/div/div[2]/div/div[2]/button/div")
                su_inner.wait_for(state="visible", timeout=wait_timeout)
                su_btn = su_inner.locator("xpath=ancestor::button[1]")
                for _ in range(enabled_check_max_attempts):
                    if su_btn.is_enabled():
                        break
                    time.sleep(enabled_check_interval)
                su_btn.scroll_into_view_if_needed()
                time.sleep(start_upload_scroll_wait)
                try:
                    su_btn.click()
                except Exception:
                    self.page.evaluate("el=>el.click()", su_btn)
                logger.info("⬆️ Start Upload clicked (portal)")
                return True
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{max_retries} to click portal Start Upload failed: {e}")
                time.sleep(1)
        return False

    def _wait_and_click_start(self, zip_file: str, uploaded_filename: str, max_retries: Optional[int] = None) -> bool:
        """Wait until header shows selected file count and start button is enabled, then click."""
        if max_retries is None:
            if not WAIT_AND_CLICK_START_MAX_RETRIES:
                raise ValueError("WAIT_AND_CLICK_START_MAX_RETRIES environment variable is required.")
            max_retries = int(WAIT_AND_CLICK_START_MAX_RETRIES)
        
        if not WAIT_TIMEOUT:
            raise ValueError("WAIT_TIMEOUT environment variable is required.")
        wait_timeout = int(WAIT_TIMEOUT) * 1000
        
        for attempt in range(max_retries):
            try:
                header = self.page.locator("//*[@id='portal']//*[contains(., 'file selected') or contains(., 'File selected')]")
                header.wait_for(state="visible", timeout=wait_timeout)
            except Exception:
                logger.info("ℹ️ Header with 'file selected' not found; proceeding anyway")
            
            try:
                self.page.locator(f"//*[@id='portal']//*[contains(text(), '{uploaded_filename}')]").wait_for(state="visible", timeout=wait_timeout)
            except Exception as e:
                logger.warning(f"File tile missing before start upload: {e}")
            
            if self._click_portal_start_upload():
                self._accept_browser_dialog_once()
                self._click_portal_confirm_if_present()
                if self._upload_canceled_detected():
                    logger.info("↻ Retrying: re-selecting file due to cancellation...")
                    try:
                        self.page.set_input_files("#files", zip_file)
                        self.page.evaluate("(sel)=>{const el=document.querySelector(sel); if(el){el.dispatchEvent(new Event('change',{bubbles:true}));}}", "#files")
                    except Exception as e2:
                        logger.error(f"Failed to re-select file: {e2}")
                        return False
                    continue
                return True
            time.sleep(1)
        return False
    
    def start_upload(self, zip_file: str, uploaded_filename: str) -> bool:
        """
        Clicks the Start Upload button and waits for upload to complete.
        
        Args:
            zip_file (str): Path to the ZIP file (for retry if needed)
            uploaded_filename (str): Name of the uploaded file
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not WAIT_TIMEOUT:
            raise ValueError("WAIT_TIMEOUT environment variable is required.")
        wait_timeout = int(WAIT_TIMEOUT) * 1000
        
        if not UPLOAD_WAIT_TIME:
            raise ValueError("UPLOAD_WAIT_TIME environment variable is required.")
        upload_wait_seconds = int(UPLOAD_WAIT_TIME)
        
        try:
            start_upload_inner = self.page.locator("//*[@id='portal']/div/div/div/div[2]/div/div/div[2]/div/div[2]/button/div")
            start_upload_inner.wait_for(state="visible", timeout=wait_timeout)
            start_upload_btn = start_upload_inner.locator("xpath=ancestor::button[1]")
            start_upload_btn.scroll_into_view_if_needed()
            if not START_UPLOAD_SCROLL_WAIT:
                raise ValueError("START_UPLOAD_SCROLL_WAIT environment variable is required.")
            start_upload_scroll_wait = float(START_UPLOAD_SCROLL_WAIT)
            time.sleep(start_upload_scroll_wait)
            start_upload_btn.click()
            logger.info("⬆️ Start Upload clicked")
            if not START_UPLOAD_CLICK_WAIT:
                raise ValueError("START_UPLOAD_CLICK_WAIT environment variable is required.")
            start_upload_click_wait = float(START_UPLOAD_CLICK_WAIT)
            time.sleep(start_upload_click_wait)
            
            if not self._wait_and_click_start(zip_file, uploaded_filename):
                logger.error("Could not start upload after readiness checks")
                return False
            else:
                logger.info("⬆️ Start Upload initiated")
            
            logger.info(f"⏳ Waiting {upload_wait_seconds}s for upload processing...")
            time.sleep(upload_wait_seconds)
            
            try:
                self.page.locator("//*[@id='portal']//button[contains(.,'Add Metadata')]").wait_for(state="visible", timeout=wait_timeout)
                logger.info("✅ Upload stage confirmed — Add Metadata visible")
            except Exception:
                logger.info("ℹ️ Add Metadata not visible yet; proceeding with retries later")
            
            return True
        except Exception as e:
            logger.warning(f"Could not click Start Upload (primary XPath): {e}")
            try:
                alt = self.page.locator("//button[normalize-space()='Start Upload']")
                alt.wait_for(state="visible", timeout=wait_timeout)
                alt.scroll_into_view_if_needed()
                alt.click(force=True)
                logger.info("⬆️ Start Upload clicked (fallback)")
                if not START_UPLOAD_CLICK_WAIT:
                    raise ValueError("START_UPLOAD_CLICK_WAIT environment variable is required.")
                start_upload_click_wait = float(START_UPLOAD_CLICK_WAIT)
                time.sleep(start_upload_click_wait)
                
                if not self._wait_and_click_start(zip_file, uploaded_filename):
                    logger.error("Could not start upload after readiness checks (fallback)")
                    return False
                else:
                    logger.info("⬆️ Start Upload initiated (fallback)")
                
                logger.info(f"⏳ Waiting {upload_wait_seconds}s for upload processing (fallback)...")
                time.sleep(upload_wait_seconds)
                
                try:
                    self.page.locator("//*[@id='portal']//button[contains(.,'Add Metadata')]").wait_for(state="visible", timeout=wait_timeout)
                    logger.info("✅ Upload stage confirmed — Add Metadata visible (fallback path)")
                except Exception:
                    logger.info("ℹ️ Add Metadata not visible yet (fallback path)")
                
                return True
            except Exception as e2:
                logger.error(f"Start Upload click failed: {e2}")
                return False
    
    def fill_metadata_form(self) -> bool:
        """
        Fills the metadata form with values from environment variables.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not WAIT_TIMEOUT:
            raise ValueError("WAIT_TIMEOUT environment variable is required.")
        wait_timeout = int(WAIT_TIMEOUT) * 1000
        
        try:
            # Click Add Metadata button
            add_metadata_btn = self.page.locator("//*[@id='portal']//button[contains(.,'Add Metadata')]")
            add_metadata_btn.wait_for(state="attached", timeout=wait_timeout)
            add_metadata_btn.wait_for(state="visible", timeout=wait_timeout)
            add_metadata_btn.scroll_into_view_if_needed()
            if not ADD_METADATA_SCROLL_WAIT:
                raise ValueError("ADD_METADATA_SCROLL_WAIT environment variable is required.")
            add_metadata_scroll_wait = float(ADD_METADATA_SCROLL_WAIT)
            time.sleep(add_metadata_scroll_wait)
            add_metadata_btn.click()
            logger.info("🟢 Add Metadata clicked")
        except Exception as e:
            logger.warning(f"Primary Add Metadata click failed: {e}")
            try:
                add_metadata_btn.scroll_into_view_if_needed()
                add_metadata_btn.click(force=True)
                logger.info("🟢 Add Metadata clicked (force)")
            except Exception as e2:
                logger.error(f"Add Metadata click failed: {e2}")
                return False
        
        if not ADD_METADATA_CLICK_WAIT:
            raise ValueError("ADD_METADATA_CLICK_WAIT environment variable is required.")
        add_metadata_click_wait = float(ADD_METADATA_CLICK_WAIT)
        time.sleep(add_metadata_click_wait)

        # Fill metadata fields
        try:
            if not POST_TITLE:
                raise ValueError("POST_TITLE environment variable is required.")
            if not CONTENT_TITLE:
                raise ValueError("CONTENT_TITLE environment variable is required.")
            if not DESCRIPTION:
                raise ValueError("DESCRIPTION environment variable is required.")
            if not KEYWORDS:
                raise ValueError("KEYWORDS environment variable is required.")
            
            post_title = POST_TITLE
            content_title = CONTENT_TITLE
            description = DESCRIPTION
            keyword = KEYWORDS

            if not post_title:
                raise ValueError("POST_TITLE environment variable is required.")
            if not content_title:
                raise ValueError("CONTENT_TITLE environment variable is required.")
            if not description:
                raise ValueError("DESCRIPTION environment variable is required.")
            if not keyword:
                raise ValueError("KEYWORDS environment variable is required.")

            post_field = self.page.locator("//input[@placeholder='Post Title']")
            post_field.wait_for(state="visible", timeout=wait_timeout)
            post_field.evaluate("el => el.value = ''")
            post_field.fill(post_title)

            self.page.locator("//input[@placeholder='Title']").fill(content_title)
            self.page.locator("//textarea[@placeholder='Description']").fill(description)
            self.page.locator("//input[@placeholder='Keywords']").fill(keyword)
            logger.info(f"📝 Metadata filled successfully: {post_title}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to fill metadata form: {e}")
            return False
    
    def submit_metadata_form(self) -> bool:
        """
        Submits the metadata form.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not WAIT_TIMEOUT:
            raise ValueError("WAIT_TIMEOUT environment variable is required.")
        wait_timeout = int(WAIT_TIMEOUT) * 1000
        
        try:
            submit_btn = self.page.locator("//button[normalize-space()='Submit']")
            submit_btn.wait_for(state="visible", timeout=wait_timeout)
            submit_btn.scroll_into_view_if_needed()
            submit_btn.click()
            logger.info("📤 Submit clicked")

            if not SUBMIT_FORM_WAIT:
                raise ValueError("SUBMIT_FORM_WAIT environment variable is required.")
            submit_form_wait = float(SUBMIT_FORM_WAIT)
            time.sleep(submit_form_wait)
            
            logger.info("✅ Upload and metadata submission complete.")
            return True
        except Exception as e:
            logger.error(f"Failed to submit metadata form: {e}")
            return False
    
    def open_and_verify_download(self, uploaded_filename: str) -> bool:
        """
        Opens the modal by clicking uploaded ZIP thumbnail and verifies download.
        
        Args:
            uploaded_filename (str): Name of the uploaded file
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not WAIT_TIMEOUT:
            raise ValueError("WAIT_TIMEOUT environment variable is required.")
        wait_timeout = int(WAIT_TIMEOUT) * 1000
        
        try:
            # Click the uploaded ZIP thumbnail to open the modal
            zip_thumb = self.page.locator("//*[@id='scrollingDiv']/div[4]/div[2]/div[1]/div[2]/div/div[1]/div[4]/div/div")
            zip_thumb.wait_for(state="visible", timeout=wait_timeout)
            zip_thumb.scroll_into_view_if_needed()
            if not MODAL_THUMBNAIL_SCROLL_WAIT:
                raise ValueError("MODAL_THUMBNAIL_SCROLL_WAIT environment variable is required.")
            modal_thumbnail_scroll_wait = float(MODAL_THUMBNAIL_SCROLL_WAIT)
            time.sleep(modal_thumbnail_scroll_wait)
            zip_thumb.click()
            logger.info("🖱️ Uploaded ZIP thumbnail clicked → modal opening...")
            
            modal_open_wait = float(MODAL_OPEN_WAIT) if MODAL_OPEN_WAIT else 5.0
            logger.info(f"⏳ Waiting {modal_open_wait} seconds after modal opens...")
            time.sleep(modal_open_wait)
            
            dl_span = self.page.locator("//*[@id='portal']/div/div/div/div/div/div[2]/div/div/button/span")
            dl_span.wait_for(state="visible", timeout=wait_timeout)
            dl_btn = dl_span.locator("xpath=ancestor::button[1]")
            dl_btn.scroll_into_view_if_needed()
            if not DOWNLOAD_BUTTON_SCROLL_WAIT:
                raise ValueError("DOWNLOAD_BUTTON_SCROLL_WAIT environment variable is required.")
            download_button_scroll_wait = float(DOWNLOAD_BUTTON_SCROLL_WAIT)
            time.sleep(download_button_scroll_wait)

            if not DOWNLOADS_FOLDER:
                raise ValueError("DOWNLOADS_FOLDER environment variable is required.")
            downloads_folder = DOWNLOADS_FOLDER
            downloads_path = os.path.join(os.environ["USERPROFILE"], downloads_folder)
            os.makedirs(downloads_path, exist_ok=True)

            # Use Playwright download API
            with self.page.expect_download() as d_info:
                dl_btn.click()
            download = d_info.value
            suggested = download.suggested_filename
            target_path = os.path.join(downloads_path, suggested)
            try:
                download.save_as(target_path)
            except Exception:
                temp_path = download.path()
                if temp_path and os.path.exists(temp_path):
                    try:
                        shutil.copyfile(temp_path, target_path)
                    except Exception:
                        pass

            logger.info(f"⬇️ Download saved as: {os.path.basename(target_path)}")

            # Verify file names
            downloaded_file = os.path.basename(target_path)
            uploaded_name_root = uploaded_filename.lower().split(".zip")[0]
            downloaded_name_root = downloaded_file.lower().split(".zip")[0]

            logger.info(f"\n🔍 Uploaded File Name : {uploaded_filename}")
            logger.info(f"🔍 Downloaded File Name: {downloaded_file}")

            if uploaded_name_root == downloaded_name_root:
                logger.info("🎯 Verification Passed — File names match perfectly.")
            elif downloaded_name_root.startswith(uploaded_name_root):
                logger.warning("Verification Partial — Browser likely appended a suffix (e.g., '(1)').")
            else:
                logger.error("Verification Failed — Downloaded name doesn't match uploaded name!")

            return True
        except Exception as e:
            logger.error(f"ERROR during modal open or download verification: {e}")
            return False
    
    def run(self) -> bool:
        """
        Execute the complete upload automation workflow.
        
        This method orchestrates the entire upload process:
        - Initializes browser
        - Performs login
        - Executes upload workflow
        - Closes browser
        
        Returns:
            bool: True if upload successful, False otherwise
        
        Example:
            >>> suite = UploadAutomationSuite()
            >>> success = suite.run()
        """
        try:
            # Get project root (parent of NIMAR folder)
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_file_dir)  # Go up from NIMAR/uploads to NIMAR
            project_root = os.path.dirname(project_root)  # Go up from NIMAR to project root
            media_folder = os.path.join(project_root, "media")
            
            # Check if ZIP_FILE is set
            if not ZIP_FILE:
                raise ValueError("ZIP_FILE environment variable is required. Set it in .env file (e.g., ZIP_FILE=crusader.zip)")
            
            # Construct full path: media_folder/ZIP_FILE
            zip_file_path = os.path.join(media_folder, ZIP_FILE)
            logger.info(f"📂 ZIP file path: {zip_file_path}")

            if os.path.exists(zip_file_path):
                self.zip_file = zip_file_path
                logger.info(f"✅ Using ZIP file from media folder: {self.zip_file}")

            if not os.path.exists(self.zip_file):
                logger.error(f"ZIP file not found at {self.zip_file}")
                return False
            
            # Playwright Setup
            self.playwright = sync_playwright().start()
            launch_args = [
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--disable-web-security",
                "--no-proxy-server",
                "--start-maximized"
            ]
                        
            browser_headless = BROWSER_HEADLESS.lower() == "true"
            browser_ignore_https = BROWSER_IGNORE_HTTPS_ERRORS.lower() == "true"
            browser_no_viewport = BROWSER_NO_VIEWPORT.lower() == "true"
            
            self.browser = self.playwright.chromium.launch(headless=browser_headless, args=launch_args)
            self.context = self.browser.new_context(
                ignore_https_errors=browser_ignore_https,
                no_viewport=browser_no_viewport,
                viewport=None
            )
            self.page = self.context.new_page()
            
            # Login using OTP
            logger.info("🔐 Starting OTP-based login...")
            login_success = login_with_otp_sync(self.page)
            
            if not login_success:
                logger.error("Login failed. Exiting.")
                return False
            
            logger.info("✅Login successful! Proceeding with upload workflow...")
            if not LOGIN_SUCCESS_WAIT:
                raise ValueError("LOGIN_SUCCESS_WAIT environment variable is required.")

            login_success_wait = float(LOGIN_SUCCESS_WAIT)
            time.sleep(login_success_wait)
            
            # Verify ZIP file exists
            if not os.path.exists(self.zip_file):
                logger.error(f"ZIP file not found at {self.zip_file}")
                return False
            
            # Open QA Testing circle
            if not self.open_circle():
                logger.error("Failed to open QA Testing circle. Exiting.")
                return False
            
            # Click upload button and select file
            success, uploaded_filename = self.click_upload_button(self.zip_file)
            if not success:
                logger.error("Failed to click upload button. Exiting.")
                return False
            
            # Start upload
            if not self.start_upload(self.zip_file, uploaded_filename):
                logger.error("Failed to start upload. Exiting.")
                return False
            
            logger.info("✅ Upload completed, proceeding to metadata form...")
            
            # Fill metadata form
            if not self.fill_metadata_form():
                logger.error("Failed to fill metadata form. Exiting.")
                return False
            
            # Submit metadata form
            if not self.submit_metadata_form():
                logger.error("Failed to submit metadata form. Exiting.")
                return False
            
            logger.info("✅ Upload and metadata submission complete.")
            
            submit_after_wait = float(SUBMIT_AFTER_WAIT) if SUBMIT_AFTER_WAIT else 5.0
            logger.info(f"⏳ Waiting {submit_after_wait} seconds after submit before opening modal...")
            time.sleep(submit_after_wait)
            
            logger.info("Opening modal for verification...")
            
            # Open modal and verify download
            if not self.open_and_verify_download(uploaded_filename):
                logger.warning("Modal open or download verification had issues.")
            
            logger.info("\n🎯 FINAL RESULT: ZIP file uploaded successfully, modal opened, and download verified!")
            return True
            
        except Exception as e:
            logger.error(f"Error during automation: {e}")
            return False
        finally:
            # Note: Browser closing is handled by caller when using _run_upload_workflow
            if not hasattr(self, '_skip_browser_close') or not self._skip_browser_close:
                try:
                    if self.browser:
                        self.browser.close()
                    if self.playwright:
                        self.playwright.stop()
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
    
    def _run_upload_workflow(self) -> bool:
        """
        Execute the upload workflow without login (assumes already logged in).
        This method is used when login is handled separately.
        
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            # Set flag to skip browser close (caller will handle it)
            self._skip_browser_close = True
            
            # Get project root (parent of NIMAR folder)
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_file_dir)  # Go up from NIMAR/uploads to NIMAR
            project_root = os.path.dirname(project_root)  # Go up from NIMAR to project root
            media_folder = os.path.join(project_root, "media")
            
            # Check if ZIP_FILE is set
            if not ZIP_FILE:
                raise ValueError("ZIP_FILE environment variable is required. Set it in .env file (e.g., ZIP_FILE=crusader.zip)")
            
            # Construct full path: media_folder/ZIP_FILE
            zip_file_path = os.path.join(media_folder, ZIP_FILE)
            logger.info(f"📂 ZIP file path: {zip_file_path}")
            
            if os.path.exists(zip_file_path):
                self.zip_file = zip_file_path
                logger.info(f"✅ Using ZIP file from media folder: {self.zip_file}")
            
            if not os.path.exists(self.zip_file):
                logger.error(f"ZIP file not found at {self.zip_file}")
                return False
            
            # Open QA Testing circle
            if not self.open_circle():
                logger.error("Failed to open QA Testing circle. Exiting.")
                return False
            
            # Click upload button and select file
            success, uploaded_filename = self.click_upload_button(self.zip_file)
            if not success:
                logger.error("Failed to click upload button. Exiting.")
                return False
            
            # Start upload
            if not self.start_upload(self.zip_file, uploaded_filename):
                logger.error("Failed to start upload. Exiting.")
                return False
            
            logger.info("✅ Upload completed, proceeding to metadata form...")
            
            # Fill metadata form
            if not self.fill_metadata_form():
                logger.error("Failed to fill metadata form. Exiting.")
                return False
            
            # Submit metadata form
            if not self.submit_metadata_form():
                logger.error("Failed to submit metadata form. Exiting.")
                return False
            
            logger.info("✅ Upload and metadata submission complete.")
            
            submit_after_wait = float(SUBMIT_AFTER_WAIT) if SUBMIT_AFTER_WAIT else 5.0
            logger.info(f"⏳ Waiting {submit_after_wait} seconds after submit before opening modal...")
            time.sleep(submit_after_wait)
            
            logger.info("Opening modal for verification...")
            
            # Open modal and verify download
            if not self.open_and_verify_download(uploaded_filename):
                logger.warning("Modal open or download verification had issues.")
            
            logger.info("\n🎯 FINAL RESULT: ZIP file uploaded successfully, modal opened, and download verified!")
            return True
            
        except Exception as e:
            logger.error(f"Error during upload workflow: {e}")
            return False
