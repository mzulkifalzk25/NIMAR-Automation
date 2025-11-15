import asyncio
import logging
import time

from playwright.sync_api import sync_playwright

from NIMAR.auth.otp import login_with_otp_sync
from NIMAR.uploads.single_zipfile_upload import UploadAutomationSuite
from NIMAR.env_variables import LOGIN_SUCCESS_WAIT, LOG_LEVEL
from NIMAR.logging_config import setup_logging


# Setup logging with file and console handlers
log_filepath = setup_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)


def run_otp_automation():
    """
    Run OTP login automation and then upload workflow.
    
    Returns:
        bool: True if both login and upload successful, False otherwise
    """
    try:
        # Initialize browser
        playwright = sync_playwright().start()
        launch_args = [
            "--ignore-certificate-errors",
            "--ignore-ssl-errors",
            "--disable-web-security",
            "--no-proxy-server",
            "--start-maximized"
        ]
        
        from NIMAR.env_variables import BROWSER_HEADLESS, BROWSER_IGNORE_HTTPS_ERRORS, BROWSER_NO_VIEWPORT
        
        browser_headless = BROWSER_HEADLESS if isinstance(BROWSER_HEADLESS, bool) else BROWSER_HEADLESS.lower() == "true"
        browser_ignore_https = BROWSER_IGNORE_HTTPS_ERRORS if isinstance(BROWSER_IGNORE_HTTPS_ERRORS, bool) else BROWSER_IGNORE_HTTPS_ERRORS.lower() == "true"
        browser_no_viewport = BROWSER_NO_VIEWPORT if isinstance(BROWSER_NO_VIEWPORT, bool) else BROWSER_NO_VIEWPORT.lower() == "true"
        
        browser = playwright.chromium.launch(headless=browser_headless, args=launch_args)
        context = browser.new_context(
            ignore_https_errors=browser_ignore_https,
            no_viewport=browser_no_viewport,
            viewport=None
        )
        page = context.new_page()
        
        # Run OTP login
        logger.info("=" * 60)
        logger.info("🔐 Starting OTP login automation...")
        logger.info("=" * 60)
        login_success = login_with_otp_sync(page)
        
        if not login_success:
            logger.error("❌ OTP login failed. Check logs for details.")
            browser.close()
            playwright.stop()
            return False
        
        logger.info("✅ OTP login completed successfully!")
        
        # Wait after login
        if LOGIN_SUCCESS_WAIT:
            login_success_wait = float(LOGIN_SUCCESS_WAIT)
            logger.info(f"⏳ Waiting {login_success_wait} seconds after login...")
            time.sleep(login_success_wait)
        
        # Run upload workflow
        logger.info("=" * 60)
        logger.info("📤 Starting upload workflow...")
        logger.info("=" * 60)
        
        # Create upload suite and use existing page
        suite = UploadAutomationSuite()
        suite.playwright = playwright
        suite.browser = browser
        suite.context = context
        suite.page = page
        
        # Set zip file path using ZIP_FILE from .env
        try:
            import os
            from NIMAR.env_variables import ZIP_FILE
            
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_file_dir)
            media_folder = os.path.join(project_root, "media")
            
            if ZIP_FILE:
                zip_file_path = os.path.join(media_folder, ZIP_FILE)
                if os.path.exists(zip_file_path):
                    suite.zip_file = zip_file_path
                    logger.info(f"✅ ZIP file found: {suite.zip_file}")
                else:
                    logger.warning(f"ZIP file not found at: {zip_file_path}")
            else:
                logger.warning("ZIP_FILE not set in .env file")
        except Exception as e:
            logger.warning(f"Could not pre-set zip file path: {e}")
        
        # Run upload workflow (without login, since we already logged in)
        # We need to modify the workflow to skip login
        upload_success = suite._run_upload_workflow()
        
        # Close browser
        try:
            if browser:
                browser.close()
            if playwright:
                playwright.stop()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
        
        if upload_success:
            logger.info("✅ Upload workflow completed successfully!")
            return True
        else:
            logger.error("❌ Upload workflow failed. Check logs for details.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during automation: {e}")
        return False


if __name__ == "__main__":
    # Run OTP login automation followed by upload workflow
    logger.info(f"📝 Logs are being saved to: {log_filepath}")
    logger.info("=" * 60)
    
    success = run_otp_automation()
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("🎉 SUCCESS: Login and upload workflow completed!")
        logger.info(f"📝 Full logs saved to: {log_filepath}")
        logger.info("=" * 60)
        logger.info("✅ SUCCESS: Login and upload workflow completed!")
    else:
        logger.error("\n" + "=" * 60)
        logger.error("❌ FAILED: Login or upload workflow had errors.")
        logger.error(f"📝 Full logs saved to: {log_filepath}")
        logger.error("=" * 60)
        logger.error("❌ FAILED: Login or upload workflow had errors.")
