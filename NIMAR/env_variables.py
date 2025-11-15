import os

from dotenv import load_dotenv


# Load .env file and override existing environment variables
# This is important on Windows where USERNAME is a system variable
load_dotenv(override=True)


def _get_bool(key: str, default: bool = False) -> bool:
    """Convert environment variable to boolean."""
    value = os.getenv(key)
    if value is None:
        return default
    return str(value).lower() in ('true', '1', 'yes', 'on')


def _get_int(key: str, default: int = None) -> int:
    """Convert environment variable to integer."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float(key: str, default: float = None) -> float:
    """Convert environment variable to float."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


# --- Portal / App Credentials [ALL] ---
PORTAL_URL = os.getenv('PORTAL_URL')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

# --- Email (Gmail IMAP) [ALL] ---
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
EMAIL_SERVER = os.getenv('EMAIL_SERVER')

# --- Browser Settings [ALL] ---
BROWSER_HEADLESS = _get_bool('BROWSER_HEADLESS', False)
BROWSER_IGNORE_HTTPS_ERRORS = _get_bool('BROWSER_IGNORE_HTTPS_ERRORS', True)
BROWSER_NO_VIEWPORT = _get_bool('BROWSER_NO_VIEWPORT', True)

# --- OTP Login Timings [OTP] ---
OTP_CREDENTIAL_ENTRY_WAIT = _get_int('OTP_CREDENTIAL_ENTRY_WAIT', 4000)
OTP_BUTTON_TIMEOUT = _get_int('OTP_BUTTON_TIMEOUT', 30000)
OTP_EMAIL_WAIT_TIME = _get_int('OTP_EMAIL_WAIT_TIME', 10000)
OTP_INPUT_DELAY = _get_int('OTP_INPUT_DELAY', 200)
OTP_VERIFY_BUTTON_TIMEOUT = _get_int('OTP_VERIFY_BUTTON_TIMEOUT', 8000)
OTP_LOGIN_COMPLETE_WAIT = _get_int('OTP_LOGIN_COMPLETE_WAIT', 3000)
OTP_RETRIES = _get_int('OTP_RETRIES', 15)
OTP_DELAY = _get_int('OTP_DELAY', 5)
# Manual OTP (if set, will use this instead of retrieving from email)
MANUAL_OTP = os.getenv('MANUAL_OTP')

# --- Upload Workflow Timings [UPLOAD, VALIDATION] ---
WAIT_TIMEOUT = _get_int('WAIT_TIMEOUT', 20)
UPLOAD_WAIT_TIME = _get_int('UPLOAD_WAIT_TIME', 20)
STEP_GAP_SECONDS = _get_int('STEP_GAP_SECONDS', 2)
LOGIN_SUCCESS_WAIT = _get_int('LOGIN_SUCCESS_WAIT', 5)
CIRCLES_CLICK_WAIT = _get_int('CIRCLES_CLICK_WAIT', 3)
QA_CIRCLE_OPEN_WAIT = _get_int('QA_CIRCLE_OPEN_WAIT', 3)
UPLOAD_BUTTON_SCROLL_WAIT = _get_int('UPLOAD_BUTTON_SCROLL_WAIT', 1)
UPLOAD_CANCELED_DETECTION_TIMEOUT = _get_int('UPLOAD_CANCELED_DETECTION_TIMEOUT', 3000)
BROWSER_DIALOG_TIMEOUT = _get_float('BROWSER_DIALOG_TIMEOUT', 5.0)
PORTAL_CONFIRM_WAIT = _get_int('PORTAL_CONFIRM_WAIT', 4000)
START_UPLOAD_ENABLED_CHECK_INTERVAL = _get_float('START_UPLOAD_ENABLED_CHECK_INTERVAL', 0.3)
START_UPLOAD_SCROLL_WAIT = _get_float('START_UPLOAD_SCROLL_WAIT', 0.5)
START_UPLOAD_CLICK_WAIT = _get_int('START_UPLOAD_CLICK_WAIT', 3)
ADD_METADATA_SCROLL_WAIT = _get_float('ADD_METADATA_SCROLL_WAIT', 0.5)
ADD_METADATA_CLICK_WAIT = _get_int('ADD_METADATA_CLICK_WAIT', 2)
SUBMIT_FORM_WAIT = _get_int('SUBMIT_FORM_WAIT', 6)
SUBMIT_AFTER_WAIT = _get_int('SUBMIT_AFTER_WAIT', 10)
MODAL_THUMBNAIL_SCROLL_WAIT = _get_int('MODAL_THUMBNAIL_SCROLL_WAIT', 1)
MODAL_OPEN_WAIT = _get_int('MODAL_OPEN_WAIT', 10)
DOWNLOAD_BUTTON_SCROLL_WAIT = _get_float('DOWNLOAD_BUTTON_SCROLL_WAIT', 0.3)

# --- Retry Settings [UPLOAD, VALIDATION] ---
WAIT_AND_CLICK_START_MAX_RETRIES = _get_int('WAIT_AND_CLICK_START_MAX_RETRIES', 2)
CLICK_PORTAL_START_UPLOAD_MAX_RETRIES = _get_int('CLICK_PORTAL_START_UPLOAD_MAX_RETRIES', 3)
START_UPLOAD_ENABLED_CHECK_MAX_ATTEMPTS = _get_int('START_UPLOAD_ENABLED_CHECK_MAX_ATTEMPTS', 10)

# --- File Upload Paths [UPLOAD] ---
DESKTOP_FOLDER = os.getenv('DESKTOP_FOLDER')
ZIP_FILE = os.getenv('ZIP_FILE')
DESKTOP_PATH = os.getenv('DESKTOP_PATH')
DOWNLOADS_FOLDER = os.getenv('DOWNLOADS_FOLDER', 'Downloads')

# --- Circle Name [UPLOAD, VALIDATION] ---
CIRCLE_NAME = os.getenv('CIRCLE_NAME')

# --- Metadata Form Fields [UPLOAD, VALIDATION] ---
POST_TITLE = os.getenv('POST_TITLE')
CONTENT_TITLE = os.getenv('CONTENT_TITLE')
DESCRIPTION = os.getenv('DESCRIPTION')
KEYWORDS = os.getenv('KEYWORDS')

# --- Validation Script Settings [VALIDATION] ---
FILE_URL_1 = os.getenv('FILE_URL_1')
FILE_URL_2 = os.getenv('FILE_URL_2')
FILE_URL_3 = os.getenv('FILE_URL_3')
S3_BUCKET_URL = os.getenv('S3_BUCKET_URL')

# --- Logging [ALL] ---
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# --- Live Stream Settings [LIVE] ---
LIVE_USE_SYSTEM_CHROME = _get_bool('LIVE_USE_SYSTEM_CHROME', True)
LIVE_BROWSER_HEADLESS = _get_bool('LIVE_BROWSER_HEADLESS', False)
LIVE_USE_CHROME_CHANNEL = _get_bool('LIVE_USE_CHROME_CHANNEL', False)
WAIT_AFTER_GET_STREAM = _get_int('WAIT_AFTER_GET_STREAM', 5)

# --- Elastic Search & Advanced Search Settings [ELASTIC_SEARCH] ---
ELASTIC_SEARCH_FUZZY_THRESHOLD = _get_int('ELASTIC_SEARCH_FUZZY_THRESHOLD', 70)
ELASTIC_SEARCH_NOISE_WORDS = os.getenv('ELASTIC_SEARCH_NOISE_WORDS')
ELASTIC_SEARCH_PAGE_LOAD_TIMEOUT = _get_int('ELASTIC_SEARCH_PAGE_LOAD_TIMEOUT', 20000)
ELASTIC_SEARCH_ELEMENT_WAIT_TIMEOUT = _get_int('ELASTIC_SEARCH_ELEMENT_WAIT_TIMEOUT', 10000)
ELASTIC_SEARCH_SCROLL_PAUSE_TIME = _get_int('ELASTIC_SEARCH_SCROLL_PAUSE_TIME', 500)
ELASTIC_SEARCH_DEFAULT_KEYWORD = os.getenv('ELASTIC_SEARCH_DEFAULT_KEYWORD', 'news')
