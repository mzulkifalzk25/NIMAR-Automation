"""
=======================================================================
📄 Upload Sequence Validation Automation Script
=======================================================================

🔧 Purpose:
    Validates the upload sequence of multiple files to ensure they maintain
    their order after upload. This script uploads files, fills metadata,
    and validates the sequence by checking the modal navigation.

    This module follows a single main class architecture (similar to
    test_configurator.py) where all functionality is encapsulated
    within the SequenceValidationAutomation class.

⚙️ Features:
    • Single main class architecture (SequenceValidationAutomation)
    • All helper methods are class methods
    • Uploads multiple files in sequence
    • Validates file order via modal navigation
    • Fills metadata automatically
    • Uses Playwright for browser automation
    • Dynamically extracts S3 bucket URL from modal HTML

📁 Project Structure:
    Automation/
    ├── auth/
    │   └── otp.py              ← OTP login function (login_with_otp_sync)
    ├── uploads/
    │   ├── upload-sequence-validation.py  ← This script
    │   └── single-zipfile-upload.py  ← CircleHandler (imported)
    └── requirements.txt        ← Python dependencies

🚀 How to Run:
    1. Install all required packages:
           pip install -r requirements.txt
           playwright install

    2. Run the script standalone:
           python uploads/upload-sequence-validation.py

    3. Or import and use in your own script:
           from uploads.upload_sequence_validation import SequenceValidationAutomation
           automation = SequenceValidationAutomation()
           success = automation.run()

📦 Main Class:

    SequenceValidationAutomation
       → Main automation suite class for upload sequence validation workflow
       → All functionality is encapsulated within this single class
       → Methods:
           - run()                    → Execute complete validation workflow
           - _initialize_browser()     → Initialize Playwright browser
           - _upload_files()          → Upload files to portal
           - _fill_and_submit_metadata() → Fill and submit metadata form
           - _validate_sequence()    → Validate file sequence via modal
           - _extract_s3_url()       → Extract S3 bucket URL from modal HTML

    External Dependencies:
       - login_with_otp_sync() from auth.otp → OTP-based login
       - CircleHandler from single-zipfile-upload.py → Circle navigation

🔐 Environment Variables Required:
    - Portal credentials (PORTAL_URL, USERNAME, PASSWORD)
    - Email settings (EMAIL_USER, EMAIL_PASS, EMAIL_SERVER)
    - File paths (FILE_URL_1, FILE_URL_2, FILE_URL_3, etc.)
    - Metadata fields (POST_TITLE, CONTENT_TITLE, DESCRIPTION, KEYWORDS)
    - Timing variables (various wait times)
    (All variables are imported from NIMAR.env_variables)

🧩 Dependencies:
    - playwright       → Browser automation
    - auth.otp         → OTP login functionality (login_with_otp_sync)
    - NIMAR.env_variables → Environment variables module
    - single-zipfile-upload.py → CircleHandler class (for circle navigation)

🧠 Author:
    Rabbia Gillani SQA
    Version: 3.0.0
    Date: 2025-11-10
=======================================================================
"""
import os
import re
import time

from typing import Optional, List, Tuple
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from NIMAR.auth.otp import login_with_otp_sync
from NIMAR.env_variables import (
    WAIT_TIMEOUT,
    CIRCLES_CLICK_WAIT,
    CIRCLE_NAME,
    QA_CIRCLE_OPEN_WAIT,
    PORTAL_URL,
    S3_BUCKET_URL,
    FILE_URL_1,
    FILE_URL_2,
    FILE_URL_3,
    DESKTOP_PATH,
    DESKTOP_FOLDER,
    POST_TITLE,
    CONTENT_TITLE,
    DESCRIPTION,
    KEYWORDS,
    BROWSER_HEADLESS,
    BROWSER_IGNORE_HTTPS_ERRORS,
    BROWSER_NO_VIEWPORT,
    OTP_LOGIN_COMPLETE_WAIT,
)


class CircleHandler:
    """
    Handles circle navigation in the portal.
    
    This class manages opening the specified circle (e.g., QA Testing)
    in the portal after login.
    
    Attributes:
        page: Playwright sync Page object
        wait_timeout (int): Timeout in milliseconds
    
    Example:
        >>> circle_handler = CircleHandler(page)
        >>> success = circle_handler.open_circle()
    """
    
    def __init__(self, page, wait_timeout: Optional[int] = None):
        """
        Initialize circle handler.
        
        Args:
            page: Playwright sync Page object
            wait_timeout (int, optional): Timeout in milliseconds. If None, uses WAIT_TIMEOUT from env_variables
        """
        self.page = page
        
        if wait_timeout is None:
            wait_timeout_str = WAIT_TIMEOUT
            if not wait_timeout_str:
                raise ValueError("WAIT_TIMEOUT environment variable is required.")
            wait_timeout = int(wait_timeout_str) * 1000
        self.wait_timeout = wait_timeout
    
    def open_circle(self) -> bool:
        """
        Opens the QA Testing circle (or specified circle) in the portal.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            wait_timeout_str = WAIT_TIMEOUT
            if not wait_timeout_str:
                raise ValueError("WAIT_TIMEOUT environment variable is required.")
            wait_timeout = int(wait_timeout_str) * 1000
            
            self.page.locator("//a[contains(.,'Circles')]").wait_for(state="visible", timeout=wait_timeout)
            self.page.locator("//a[contains(.,'Circles')]").click()
            print("📂 Circles clicked")
            
            circles_click_wait_str = CIRCLES_CLICK_WAIT
            if not circles_click_wait_str:
                raise ValueError("CIRCLES_CLICK_WAIT environment variable is required.")
            circles_click_wait = float(circles_click_wait_str)
            time.sleep(circles_click_wait)

            circle_name = CIRCLE_NAME
            if not circle_name:
                raise ValueError("CIRCLE_NAME environment variable is required.")
            
            qa_circle = self.page.locator(f"//*[contains(text(),'{circle_name}')]")
            qa_circle.wait_for(state="visible", timeout=wait_timeout)
            qa_circle.scroll_into_view_if_needed()
            qa_circle.click()
            print(f"🟢 {circle_name} circle opened")
            
            qa_circle_open_wait_str = QA_CIRCLE_OPEN_WAIT
            if not qa_circle_open_wait_str:
                raise ValueError("QA_CIRCLE_OPEN_WAIT environment variable is required.")
            qa_circle_open_wait = float(qa_circle_open_wait_str)
            time.sleep(qa_circle_open_wait)

            return True
        except Exception as e:
            print(f"❌ Failed to open QA Testing circle: {e}")
            return False


class BrowserManager:
    """
    Handles Playwright browser setup and initialization.
    
    This class manages browser creation, configuration, and cleanup.
    Similar to browser setup in single-zipfile-upload.py but kept here
    for this specific automation workflow.
    
    Attributes:
        playwright: Playwright instance
        browser (Browser): Playwright Browser instance
        context (BrowserContext): Browser context instance
        page (Page): Playwright Page instance
    
    Example:
        >>> browser_mgr = BrowserManager()
        >>> browser_mgr.initialize()
        >>> browser_mgr.page.goto("https://example.com")
    """
    
    def __init__(self):
        """
        Initialize browser manager.
        """
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    def initialize(self) -> bool:
        """
        Initialize Playwright browser with Chrome.
        
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
            
            browser_headless_str = BROWSER_HEADLESS
            browser_ignore_https_str = BROWSER_IGNORE_HTTPS_ERRORS
            
            if not browser_headless_str:
                raise ValueError("BROWSER_HEADLESS environment variable is required.")
            if not browser_ignore_https_str:
                raise ValueError("BROWSER_IGNORE_HTTPS_ERRORS environment variable is required.")
            
            browser_headless = browser_headless_str.lower() == "true"
            browser_ignore_https = browser_ignore_https_str.lower() == "true"
            
            self.browser = self.playwright.chromium.launch(headless=browser_headless, args=launch_args)
            self.context = self.browser.new_context(ignore_https_errors=browser_ignore_https)
            self.page = self.context.new_page()
            
            portal_url = PORTAL_URL
            if not portal_url:
                raise ValueError("PORTAL_URL environment variable is required.")
            
            self.page.goto(portal_url)
            self.page.wait_for_load_state("networkidle")
            time.sleep(5)
            
            print("✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize browser: {e}")
            return False
    
    def close(self) -> None:
        """Close the browser."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("✅ Browser closed")
        except Exception as e:
            print(f"⚠️ Error closing browser: {e}")


class UploadHandler:
    """
    Handles file upload workflow including button clicks and file selection.
    
    This class manages the complete upload process:
    - Clicking Upload button
    - Selecting multiple files
    - Starting upload process
    - Waiting for upload completion (1 minute wait after Start Upload)
    - Clicking Add Metadata button
    
    Attributes:
        page (Page): Playwright Page instance
    
    Example:
        >>> upload_handler = UploadHandler(page)
        >>> filenames = upload_handler.upload_files(file_list)
    """
    
    def __init__(self, page: Page):
        """
        Initialize upload handler.
        
        Args:
            page: Playwright Page instance
        """
        self.page = page
    
    def upload_files(self, file_list: List[str]) -> List[str]:
        """
        Upload multiple files in sequence.
        
        Args:
            file_list (List[str]): List of file paths to upload
        
        Returns:
            List[str]: List of uploaded file basenames
        """
        original_names = [os.path.basename(f) for f in file_list]

        print("\n" + "="*100)
        print("📂 EXPECTED FILE UPLOAD SEQUENCE (Before Upload):")
        print("   → " + "  |  ".join(original_names))
        print("="*100 + "\n")

        wait_timeout_str = WAIT_TIMEOUT
        wait_timeout = int(wait_timeout_str) * 1000
        
        buttons = self.page.query_selector_all("button")
        for btn in buttons:
            text = btn.text_content()
            if text and text.strip().lower() == "upload":
                btn.evaluate("el => el.click()")
                break
        print("📤 Upload button clicked")
        
        time.sleep(2)

        file_input = self.page.wait_for_selector("input[type='file']", timeout=wait_timeout, state="attached")
        absolute_file_list = [os.path.abspath(f) for f in file_list]
        self.page.set_input_files("input[type='file']", absolute_file_list)
        print(f"📂 Selected {len(file_list)} files together")

        start_upload_btn = self.page.wait_for_selector(
            "//button[normalize-space()='Start Upload']", timeout=wait_timeout
        )
        start_upload_btn.evaluate("el => el.click()")
        print("⬆️ Start Upload clicked")
        
        time.sleep(60)

        add_metadata_btn = self.page.wait_for_selector(
            "//button[contains(text(),'Add Metadata')]", timeout=wait_timeout
        )
        add_metadata_btn.evaluate("el => el.click()")
        print("🟢 'Add Metadata for these files' clicked")
        
        time.sleep(2)

        return original_names


class MetadataHandler:
    """
    Handles metadata form filling and submission.
    
    This class manages the complete metadata workflow:
    - Filling metadata fields (Post Title, Title, Description, Keywords)
    - Clicking lock icons to apply metadata to all files
    - Submitting the form
    
    Attributes:
        page (Page): Playwright Page instance
    
    Example:
        >>> metadata_handler = MetadataHandler(page)
        >>> success = metadata_handler.fill_and_submit(files_meta)
    """
    
    def __init__(self, page: Page):
        """
        Initialize metadata handler.
        
        Args:
            page: Playwright Page instance
        """
        self.page = page
    
    def fill_and_submit(self, files_meta: List[Tuple[str, str, str, str]]) -> bool:
        """
        Fill metadata form and submit.
        
        Args:
            files_meta (List[Tuple[str, str, str, str]]): List of metadata tuples (post_title, content_title, description, keyword)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            post_title, content_title, description, keyword = files_meta[0]

            wait_timeout_str = WAIT_TIMEOUT
            wait_timeout = int(wait_timeout_str) * 1000

            post_field = self.page.wait_for_selector("//input[@placeholder='Post Title']", timeout=wait_timeout, state="visible")
            post_field.evaluate("el => el.value = ''")
            post_field.fill(post_title)
            print(f"📝 Post Title filled: {post_title}")

            title_field = self.page.wait_for_selector("//input[@placeholder='Title']", timeout=wait_timeout, state="visible")
            title_field.fill(content_title)
            print(f"📝 Title filled: {content_title}")
            
            desc_field = self.page.wait_for_selector("//textarea[@placeholder='Description']", timeout=wait_timeout, state="visible")
            desc_field.fill(description)
            print(f"📝 Description filled")
            
            keyword_field = self.page.wait_for_selector("//input[@placeholder='Keywords']", timeout=wait_timeout, state="visible")
            keyword_field.fill(keyword)
            print(f"📝 Keywords filled: {keyword}")
            
            print(f"📝 Metadata filled once: {post_title}")
            
            time.sleep(1)

            container = self.page.wait_for_selector("//form", timeout=wait_timeout)
            lock_icons = container.query_selector_all("svg")
            print(f"Found {len(lock_icons)} lock icons")

            start_time = time.time()
            clicked_count = 0
            for i, lock in enumerate(lock_icons, start=1):
                if time.time() - start_time > 3:
                    break
                try:
                    lock.evaluate("el => el.scrollIntoView({block: 'center', behavior: 'instant'})")
                    self.page.wait_for_timeout(100)
                    try:
                        lock.click(force=True, timeout=1000)
                    except:
                        lock.evaluate("el => el.click()")
                    self.page.wait_for_timeout(200)
                    clicked_count += 1
                    print(f"🔒 Clicked lock {i}")
                except Exception as e:
                    print(f"⚠️ Failed to click lock {i}: {e}")
                    continue
            
            print(f"✅ Successfully clicked {clicked_count} lock icons out of {len(lock_icons)}")

            submit_btn = self.page.wait_for_selector("//button[normalize-space()='Submit']", timeout=wait_timeout)
            submit_btn.evaluate("el => el.scrollIntoView(true)")
            submit_btn.evaluate("el => el.click()")
            print("📤 Submit clicked")
            
            print("⏳ Waiting 30 seconds after submit before next step...")
            time.sleep(30)
            
            return True
        except Exception as e:
            print(f"❌ Failed to fill and submit metadata: {e}")
            return False


class ValidationHandler:
    """
    Handles sequence validation via modal navigation.
    
    This class manages the complete validation workflow:
    - Opening first thumbnail (opens modal)
    - Validating each file's extension in sequence
    - Navigating through files using Next button
    - Extracting file URLs from modal (object, video, or image elements)
    - Generating detailed validation report with match status
    
    Attributes:
        page (Page): Playwright Page instance
    
    Example:
        >>> validation_handler = ValidationHandler(page)
        >>> success = validation_handler.validate_sequence(expected_files)
    """
    
    def __init__(self, page: Page):
        """
        Initialize validation handler.
        
        Args:
            page: Playwright Page instance
        """
        self.page = page
    
    def validate_sequence(self, expected_files: List[str]) -> bool:
        """
        Validate uploaded files sequence via modal navigation.
        
        Args:
            expected_files (List[str]): List of file paths that were uploaded in order.
                                       Only the extensions (.mp4, .pdf, .png, etc.) are used for validation.
        
        Returns:
            bool: True if all files matched sequence correctly, False otherwise
        """
        expected_exts = [os.path.splitext(f)[1].lower() for f in expected_files]
        results = []

        print("\n" + "="*100)
        print("🏠 [VALIDATION] Checking ALL uploaded files in sequence via modal navigation")
        print("🎯 Expected Extensions Order: " + "  |  ".join(expected_exts))
        print("="*100)

        try:
            wait_timeout_str = WAIT_TIMEOUT
            wait_timeout = int(wait_timeout_str) * 1000
            
            thumb = self.page.wait_for_selector(
                "(//div[contains(@class,'cursor-pointer')]//img)[1]", 
                timeout=wait_timeout,
                state="visible"
            )
            thumb.evaluate("el => el.scrollIntoView({block:'center'})")
            thumb.evaluate("el => el.click()")
            print("🖱️ First thumbnail clicked → modal opened")
            
            self.page.wait_for_selector("#portal", timeout=wait_timeout, state="attached")
            print("✅ Modal detected")
            modal_element = self.page.locator("#portal")

            time.sleep(4)

            modal_element = self.page.locator("#portal")
            modal_html = modal_element.evaluate("el => el.outerHTML")
            
            s3_bucket_url = None
            try:
                # Match both http and https URLs
                url_pattern = r'(https?://[^\s"\'<>]*minioapi[^\s"\'<>]*/)'
                url_match = re.search(url_pattern, modal_html, re.I)
                if url_match:
                    # Extract base URL (everything up to the first slash after domain)
                    full_url = url_match.group(1)
                    # Extract base URL (e.g., https://minioapi.forbmax.ai/ or http://minioapi.forbmax.ai/)
                    base_url_match = re.search(r'((?:https?://)[^/]+/)', full_url)
                    if base_url_match:
                        s3_bucket_url = base_url_match.group(1)
                        print(f"🔍 S3 Bucket URL dynamically detected: {s3_bucket_url}")
                    else:
                        # Fallback: extract domain part (preserve http/https)
                        domain_match = re.search(r'((?:https?://)[^/\s"\'<>]+)', full_url)
                        if domain_match:
                            s3_bucket_url = domain_match.group(1) + "/"
                            print(f"🔍 S3 Bucket URL dynamically detected (fallback): {s3_bucket_url}")
            except Exception as e:
                print(f"⚠️ Could not extract S3 bucket URL dynamically: {e}")
            
            if not s3_bucket_url:
                # Fallback to env variable if dynamic extraction fails
                s3_bucket_url = S3_BUCKET_URL
                if not s3_bucket_url:
                    print("❌ S3 bucket URL not found in environment variables and dynamic extraction failed")
                    return False
                print(f"⚠️ Using S3 bucket URL from environment: {s3_bucket_url}")

            # 2️⃣ Loop through each expected extension
            for idx, expected_ext in enumerate(expected_exts, start=1):
                print("\n" + "-"*80)
                print(f"📂 Step {idx}/{len(expected_exts)} → Expecting type '{expected_ext}'")

                modal_element = self.page.locator("#portal")
                modal_html = modal_element.evaluate("el => el.outerHTML")
                file_url = None

                try:
                    obj_locator = modal_element.locator("object")
                    if obj_locator.count() > 0:
                        obj_el = obj_locator.first
                        file_url = obj_el.get_attribute("data")
                except:
                    pass

                if not file_url:
                    try:
                        vid_locator = modal_element.locator("video")
                        if vid_locator.count() > 0:
                            vid_el = vid_locator.first
                            file_url = vid_el.get_attribute("src")
                    except:
                        pass

                if not file_url:
                    imgs = modal_element.locator("img").all()
                    for img in imgs:
                        try:
                            src = img.get_attribute("src")
                            if src and ("profile_pics" in src or "department_logos" in src):
                                continue
                            if src:
                                file_url = src
                                break
                        except:
                            continue

                # --- Regex fallback - Dynamically use detected S3 bucket URL
                # Instead of hardcoded URL, use dynamically extracted S3 bucket URL
                # Handles both http and https protocols
                if not file_url:
                    escaped_s3_url = re.escape(s3_bucket_url.rstrip('/'))
                    # Match both http and https (in case the URL pattern contains protocol)
                    dynamic_regex_pattern = rf'(?:https?://)?{escaped_s3_url}[^\s"\'<>]+\.(pdf|mp4|mov|png|jpg|jpeg|gif)(?:\?[^\s"\'<>]*)?'
                    
                    print(f"🔍 Using dynamically detected S3 bucket URL for regex: {s3_bucket_url}")
                    match = re.search(
                        dynamic_regex_pattern,
                        modal_html, re.I
                    )
                    if match:
                        file_url = match.group(0)
                        # If the matched URL doesn't start with http/https, prepend the protocol from s3_bucket_url
                        if not file_url.startswith(('http://', 'https://')):
                            protocol = s3_bucket_url.split('://')[0] if '://' in s3_bucket_url else 'https'
                            file_url = f"{protocol}://{file_url}"
                        print(f"✅ File URL found using dynamic S3 bucket URL pattern")

                # Normalize + verify
                if file_url:
                    clean_url = file_url.split("?")[0]
                    detected_ext = os.path.splitext(clean_url)[1].lower()

                    status = "✅ MATCH" if detected_ext == expected_ext else "❌ FAIL"
                    print(f"🔗 File URL: {clean_url}")
                    print(f"📄 Detected Ext: {detected_ext} | 🎯 Expected Ext: {expected_ext} → {status}")

                    results.append((expected_ext, clean_url, status))
                else:
                    print("❌ Could not detect media URL in modal")
                    results.append((expected_ext, None, "❌ FAIL"))

                if idx < len(expected_exts):
                    time.sleep(5)
                    try:
                        next_btn = self.page.wait_for_selector(
                            "//*[@id='portal']/div/div/div/button[2]", 
                            timeout=wait_timeout,
                            state="visible"
                        )
                        next_btn.evaluate("el => el.click()")
                        print("➡️ Clicked Next Arrow → moving to next file")
                        time.sleep(4)
                    except Exception as e:
                        print(f"⚠️ Could not click Next arrow: {e}")
                        break

            time.sleep(5)

            # 4️⃣ Print Final Proof Report
            print("\n" + "="*100)
            print("📊 FINAL VALIDATION REPORT")
            print("="*100)

            # Expected sequence (before upload)
            print("📂 EXPECTED ORDER (Before Upload):")
            print("   → " + "  |  ".join(expected_exts))
            print("-"*100)

            # Detected sequence (from modal)
            detected_exts = [os.path.splitext(url)[1].lower() if url else "None" for _, url, _ in results]
            print("📂 DETECTED ORDER (From Modal):")
            print("   → " + "  |  ".join(detected_exts))
            print("-"*100)

            # Proof table
            print("📑 DETAILED PROOF")
            for i, (exp_ext, url, status) in enumerate(results, start=1):
                detected = os.path.splitext(url)[1].lower() if url else 'None'
                print(f" {i}. Expected: {exp_ext:<5} | Detected: {detected:<5} | {status} | URL: {url if url else 'No URL'}")

            # Final verdict
            all_matched = all(s == "✅ MATCH" for _, _, s in results)
            if all_matched:
                print("\n🎯 RESULT: ✅ ALL FILES MATCHED SEQUENCE CORRECTLY")
            else:
                print("\n🎯 RESULT: ❌ SEQUENCE MISMATCH FOUND")

            print("="*100 + "\n")
            
            return all_matched
        except Exception as e:
            print(f"💥 ERROR in validation workflow: {e}")
            return False


class SequenceValidationAutomation:
    """
    Main automation suite class for upload sequence validation workflow.
    
    This class orchestrates the complete validation process, similar to
    ConfiguratorTestSuite structure. All helper methods are class methods.
    
    This class coordinates all the handlers to execute the complete validation process:
    - Browser initialization
    - Login using OTP (calls login_with_otp_sync from auth.otp)
    - Opening QA Testing circle (uses CircleHandler from single-zipfile-upload.py)
    - Uploading files (UploadHandler)
    - Filling and submitting metadata (MetadataHandler)
    - Validating sequence (ValidationHandler)
    
    Note: This class reuses login functionality from auth.otp and CircleHandler
    from single-zipfile-upload.py to maintain consistency across automation scripts.
    
    Attributes:
        files (List[str]): List of file paths to upload
        files_meta (List[Tuple[str, str, str, str]]): List of metadata tuples
        playwright: Playwright instance
        browser_mgr: Browser manager instance
        circle_handler (CircleHandler): Circle handler instance
        upload_handler (UploadHandler): Upload handler instance
        metadata_handler (MetadataHandler): Metadata handler instance
        validation_handler (ValidationHandler): Validation handler instance
    
    Example:
        >>> suite = SequenceValidationAutomation()
        >>> success = suite.run()
    """
    
    def __init__(self, 
                 files: Optional[List[str]] = None,
                 files_meta: Optional[List[Tuple[str, str, str, str]]] = None):
        """
        Initialize sequence validation automation.
        
        Args:
            files (List[str], optional): List of file paths to upload. If None, loaded from env_variables.
            files_meta (List[Tuple[str, str, str, str]], optional): List of metadata tuples. If None, loaded from env_variables.
        """
        # Load files and metadata from env if not provided
        if files is None or files_meta is None:
            # Get file names from environment variables
            file1 = FILE_URL_1
            file2 = FILE_URL_2
            file3 = FILE_URL_3
            
            if files is None:
                # Construct full paths dynamically from Desktop\New folder
                desktop_path = DESKTOP_PATH
                desktop_folder_name = DESKTOP_FOLDER
                desktop_folder = os.path.join(os.environ["USERPROFILE"], desktop_path, desktop_folder_name)
                
                files = []
                if file1:
                    full_path1 = os.path.join(desktop_folder, file1)
                    if os.path.exists(full_path1):
                        files.append(full_path1)
                if file2:
                    full_path2 = os.path.join(desktop_folder, file2)
                    if os.path.exists(full_path2):
                        files.append(full_path2)
                if file3:
                    full_path3 = os.path.join(desktop_folder, file3)
                    if os.path.exists(full_path3):
                        files.append(full_path3)
            
            if files_meta is None:
                # Get metadata from environment variables
                post_title = POST_TITLE
                content_title = CONTENT_TITLE
                description = DESCRIPTION
                keywords = KEYWORDS
                files_meta = [(post_title, content_title, description, keywords)]
        
        self.files = [f for f in files if os.path.exists(f)]
        self.files_meta = files_meta
        
        # Initialize components (will be set in run())
        self.playwright = None
        self.browser_mgr = None
        self.circle_handler: Optional[CircleHandler] = None
        self.upload_handler: Optional[UploadHandler] = None
        self.metadata_handler: Optional[MetadataHandler] = None
        self.validation_handler: Optional[ValidationHandler] = None
    
    def run(self) -> bool:
        """
        Execute the complete validation automation workflow.
        
        This method orchestrates the entire validation process:
        - Initializes browser
        - Performs login
        - Executes validation workflow
        - Closes browser
        
        Returns:
            bool: True if all steps completed successfully, False otherwise
        
        Example:
            >>> suite = SequenceValidationAutomation()
            >>> success = suite.run()
        """
        try:
            if not self.files:
                print("❌ No files found")
                return False
            
            # Initialize browser with dynamic screen adjustment
            print("🌐 Initializing browser...")
            self.playwright = sync_playwright().start()
            
            browser_headless_str = BROWSER_HEADLESS
            if not browser_headless_str:
                raise ValueError("BROWSER_HEADLESS environment variable is required.")
            browser_headless = browser_headless_str.lower() == "true"
            browser_ignore_https_str = BROWSER_IGNORE_HTTPS_ERRORS
            if not browser_ignore_https_str:
                raise ValueError("BROWSER_IGNORE_HTTPS_ERRORS environment variable is required.")
            browser_ignore_https = browser_ignore_https_str.lower() == "true"
            
            self.browser_mgr = type('BrowserManager', (), {})()
            
            launch_args = [
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--disable-web-security",
                "--no-proxy-server",
                "--start-maximized"
            ]
            
            self.browser_mgr.browser = self.playwright.chromium.launch(
                headless=browser_headless,
                args=launch_args
            )
            
            browser_no_viewport_str = BROWSER_NO_VIEWPORT
            if not browser_no_viewport_str:
                raise ValueError("BROWSER_NO_VIEWPORT environment variable is required.")
            browser_no_viewport = browser_no_viewport_str.lower() == "true"
            
            self.browser_mgr.context = self.browser_mgr.browser.new_context(
                ignore_https_errors=browser_ignore_https,
                no_viewport=browser_no_viewport,
                viewport=None
            )
            
            self.browser_mgr.page = self.browser_mgr.context.new_page()
            
            page = self.browser_mgr.page
            print("✅ Browser initialized (dynamically adjusts to screen size)")
            
            print("🔐 Starting login...")
            login_success = login_with_otp_sync(page)
            if not login_success:
                print("❌ Login failed. Exiting.")
                if self.browser_mgr.browser:
                    self.browser_mgr.browser.close()
                return False
            print("✅ Login successful")
            
            print("📂 Opening QA Testing circle...")
            self.circle_handler = CircleHandler(page)
            if not self.circle_handler.open_circle():
                print("❌ Failed to open circle. Exiting.")
                return False
            
            print("📤 Uploading files...")
            self.upload_handler = UploadHandler(page)
            expected_sequence = self.upload_handler.upload_files(self.files)
            
            print("📝 Filling and submitting metadata...")
            self.metadata_handler = MetadataHandler(page)
            if not self.metadata_handler.fill_and_submit(self.files_meta):
                print("❌ Failed to fill and submit metadata. Exiting.")
                return False
            
            print("🔍 Validating upload sequence...")
            self.validation_handler = ValidationHandler(page)
            validation_success = self.validation_handler.validate_sequence(expected_sequence)
            
            if validation_success:
                print("✅ Validation completed successfully!")
            else:
                print("⚠️ Validation found sequence mismatch")

            return validation_success

        except Exception as e:
            print(f"💥 ERROR during validation automation: {e}")
            return False
        finally:
            # Close browser same as otp.py: await browser.close()
            if hasattr(self, 'browser_mgr') and self.browser_mgr and hasattr(self.browser_mgr, 'browser'):
                try:
                    if not self.browser_mgr.page.is_closed():
                        otp_login_complete_wait_str = OTP_LOGIN_COMPLETE_WAIT
                        if otp_login_complete_wait_str:
                            otp_login_complete_wait = int(otp_login_complete_wait_str) / 1000
                            time.sleep(otp_login_complete_wait)
                    self.browser_mgr.browser.close()
                    print("✅ Browser closed successfully")
                except Exception as e:
                    print(f"Browser close exception: {e}")
            if hasattr(self, 'playwright') and self.playwright:
                try:
                    self.playwright.stop()
                except:
                    pass

