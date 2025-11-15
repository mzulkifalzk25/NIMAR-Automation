# 🚀 NIMAR Automation Framework

**Complete Automation Solution for NIMAR Portal**

This is a comprehensive automation framework that provides complete automation scripts for the NIMAR portal. This framework uses a class-based architecture with clear separation of concerns, allowing easy addition of new features in the future.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Features](#features)
- [Architecture & Class-Based Design](#architecture--class-based-design)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Module Documentation](#module-documentation)
- [Environment Variables Reference](#environment-variables-reference)
- [Future Extensions](#future-extensions)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

NIMAR Automation Framework is a scalable and maintainable solution that provides:

- **OTP-based Login** - Automatically fetches OTP from Gmail via IMAP
- **File Upload Automation** - Uploads ZIP files to the portal
- **Upload Sequence Validation** - Validates file upload order
- **Live Stream Testing** - Tests live streams and creates clips
- **Metadata Management** - Automatic metadata filling
- **Class-Based Architecture** - Reusable classes with proper encapsulation and documentation
- **Environment-based Configuration** - Everything is configurable via `.env` file

This framework can be easily extended in the future to add new automation features.

---

## 📁 Project Structure

```
Automation/
├── README.md                    # Main documentation (this file)
├── requirements.txt             # Python dependencies
├── env                          # Environment variables (actual values - DO NOT COMMIT)
├── env.example                  # Environment variables template
│
├── auth/                        # Authentication Module
│   ├── otp.py                   # OTP login automation (NimarOTPAutomation class)
│   └── logs/                     # OTP login logs
│
├── uploads/                      # Upload Automation Module
│   ├── single-zipfile-upload.py # Single ZIP file upload (UploadAutomationSuite class)
│   ├── upload-sequence-validation.py # Upload sequence validation (SequenceValidationAutomation class)
│   └── logs/                     # Upload workflow logs
│
└── live/                         # Live Stream Module
    ├── live-test-save-clip.py   # Live stream testing and clip creation (LiveTestSaveClipAutomation class)
    └── logs/                     # Live stream logs
```

---

## ✨ Features

### 🔐 Authentication Module (`auth/`)
- **OTP-based Login**: Automatically fetches OTP from Gmail
- **Reusable Functions**: `login_with_otp_sync()` and `login_with_otp_async()` functions
- **Email Management**: Marks old emails as read before requesting new OTP
- **Error Handling**: Comprehensive error handling with logging

### 📤 Upload Module (`uploads/`)
- **Single ZIP Upload**: Complete workflow for ZIP file upload
- **Upload Sequence Validation**: Validates file upload order via modal navigation
- **Metadata Automation**: Automatic metadata form filling
- **Download Verification**: Verifies download of uploaded files
- **Circle Management**: Automatically opens QA Testing circle

### 📺 Live Stream Module (`live/`)
- **Live Stream Testing**: Tests live streams for all channels
- **Stream Time Tracking**: Tracks and compares stream time with PC time
- **Previous Day Streams**: Verifies previous day streams and tracks duration
- **Clip Creation**: Creates 5-minute clips and saves them
- **Dynamic Channel Detection**: Automatically detects all available channels

### ⚙️ Configuration
- **Environment Variables**: Everything is configurable via `.env` file
- **No Hardcoded Values**: All critical values are in environment variables
- **Script-Specific Variables**: Each variable is marked with which script(s) use it
- **Easy Customization**: Proper variable naming for easy understanding

---

## 🏗️ Architecture & Single Main Class Design

### Single Main Class Architecture

This framework uses a **single main class architecture** where each module has one main class that encapsulates all functionality. This architecture provides:

- ✅ **Single Entry Point** - One main class per module for easy usage
- ✅ **Encapsulated Functionality** - All helper methods are class methods
- ✅ **Clean Structure** - No module-level functions visible when classes are collapsed
- ✅ **Easy Maintenance** - All related functionality in one place
- ✅ **Future Extensibility** - Easy to add new methods to existing classes
- ✅ **Proper Documentation** - All classes and methods have comprehensive docstrings

### Available Main Classes & How to Use Them

#### 1. **OTP Login Main Class** (`auth/otp.py`)

**Module:** `auth.otp`

**Main Class:** `NimarOTPAutomation`

- **Purpose:** Main automation class for NIMAR OTP-based login workflow
- **Initialization:**
  ```python
  NimarOTPAutomation(env_path=None)
  ```
- **Methods:**
  - `run()` → Execute complete OTP login workflow
  - `_setup_logger()` → Configure logging (private method)
  - `mark_all_as_read()` → Mark all emails as read
  - `_extract_email_body(msg)` → Extract email body content (private method)
  - `get_latest_otp_after_request(request_time)` → Get OTP from Gmail
  - `login_async(page)` → Async login workflow
  - `login_sync(page)` → Sync login workflow
  - `display_env_variables()` → Display environment variables

**Module-level Functions (for backward compatibility):**
- `login_with_otp_sync(page, env_path=None)` → Sync OTP login wrapper function
- `login_with_otp_async(page, env_path=None)` → Async OTP login wrapper function

**Example (Standalone):**
```python
from auth.otp import NimarOTPAutomation

automation = NimarOTPAutomation()
success = automation.run()
if success:
    print("Login successful!")
```

**Example (Using wrapper function):**
```python
from auth.otp import login_with_otp_sync
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    success = login_with_otp_sync(page)
    if success:
        print("Login successful!")
```

**Note:** All functionality automatically loads environment variables from `.env` file. Logs are saved to `auth/logs/` directory.

#### 2. **Upload Main Class** (`uploads/single-zipfile-upload.py`)

**Module:** `uploads.single_zipfile_upload`

**Main Class:** `UploadAutomationSuite`

- **Purpose:** Main automation suite class for single ZIP file upload workflow
- **Initialization:**
  ```python
  UploadAutomationSuite(env_path=None)
  ```
- **Methods:**
  - `run()` → Execute complete upload workflow
  - `_setup_logger()` → Configure logging (private method)
  - `open_circle()` → Open QA Testing circle
  - `click_upload_button(zip_file)` → Click upload button and select file
  - `start_upload(zip_file, uploaded_filename)` → Start upload process
  - `fill_metadata_form()` → Fill metadata form
  - `submit_metadata_form()` → Submit metadata form
  - `open_and_verify_download(uploaded_filename)` → Open modal and verify download
  - `display_env_variables()` → Display environment variables

**Example (Standalone):**
```python
from uploads.single_zipfile_upload import UploadAutomationSuite

suite = UploadAutomationSuite()
success = suite.run()
if success:
    print("Upload completed successfully!")
```

**Note:** All functionality automatically loads environment variables from `.env` file. Logs are saved to `uploads/logs/` directory.

#### 3. **Upload Sequence Validation Main Class** (`uploads/upload-sequence-validation.py`)

**Module:** `uploads.upload_sequence_validation`

**Main Class:** `SequenceValidationAutomation`

- **Purpose:** Main automation suite class for upload sequence validation workflow
- **Initialization:**
  ```python
  SequenceValidationAutomation(env_path=None)
  ```
- **Methods:**
  - `run()` → Execute complete validation workflow
  - `_setup_logger()` → Configure logging (private method)
  - `display_env_variables()` → Display environment variables
  - `_initialize_browser()` → Initialize Playwright browser (private method)
  - `_upload_files()` → Upload files to portal (private method)
  - `_fill_and_submit_metadata()` → Fill and submit metadata form (private method)
  - `_validate_sequence()` → Validate file sequence via modal (private method)
  - `_extract_s3_url()` → Extract S3 bucket URL from modal HTML (private method)

**External Dependencies:**
- `login_with_otp_sync()` from `auth.otp` - OTP-based login
- Local `CircleHandler` class - Circle navigation

**Example (Standalone):**
```python
from uploads.upload_sequence_validation import SequenceValidationAutomation

automation = SequenceValidationAutomation()
success = automation.run()
if success:
    print("Validation completed successfully!")
```

**Note:** All functionality automatically loads environment variables from `.env` file. Logs are saved to `uploads/logs/` directory.

#### 4. **Live Stream Testing Main Class** (`live/live-test-save-clip.py`)

**Module:** `live.live_test_save_clip`

**Main Class:** `LiveTestSaveClipAutomation`

- **Purpose:** Main automation class for live stream testing and clip creation workflow
- **Initialization:**
  ```python
  LiveTestSaveClipAutomation(env_path=None)
  ```
- **Methods:**
  - `run()` → Execute complete workflow
  - `_setup_logger()` → Configure logging (private method)
  - `display_env_variables()` → Display environment variables
  - `get_all_channels()` → Get all available channels dynamically
  - `open_channel(channel_index, channel_name)` → Open a specific channel
  - `start_live_stream(channel_name)` → Start live stream for a channel
  - `track_live_stream_time(channel_name)` → Track live stream time and compare with PC time
  - `verify_previous_days_streams(channel_name, days)` → Verify previous day streams
  - `open_calendar()` → Open calendar for date selection
  - `set_previous_day_date()` → Set previous day date in calendar
  - `get_previous_day_stream()` → Get previous day stream
  - `return_to_live()` → Return to live stream view
  - `crop_and_save_clip()` → Crop 5-minute clip and save
  - `navigate_to_live_menu()` → Navigate to live menu
  - `go_back_to_channel_list()` → Go back to channel list
  - `process_all_channels()` → Process all channels (live time tracking + previous day verification)

**External Dependencies:**
- `login_with_otp_sync()` from `auth.otp` - OTP-based login

**Example (Standalone):**
```python
from live.live_test_save_clip import LiveTestSaveClipAutomation

automation = LiveTestSaveClipAutomation()
success = automation.run()
if success:
    print("Live stream testing completed successfully!")
```

**Note:** All functionality automatically loads environment variables from `.env` file. Logs are saved to `live/logs/` directory.

---

## 🛠️ Setup & Installation

### Prerequisites

- **Python 3.10+** installed
- **Gmail Account** with IMAP enabled
- **Gmail App Password** (generate from 2FA enabled account)

### Step 1: Clone/Download Project

```bash
# Navigate to project folder
cd Automation
```

### Step 2: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### Step 3: Configure Environment

```bash
# Copy env.example as env
cp env.example env

# Windows PowerShell:
Copy-Item env.example env
```

### Step 4: Fill Environment Variables

Open the `env` file and fill in your actual values. Each variable is marked with which script(s) use it:
- `[OTP]` = `auth/otp.py`
- `[UPLOAD]` = `uploads/single-zipfile-upload.py`
- `[VALIDATION]` = `uploads/upload-sequence-validation.py`
- `[LIVE]` = `live/live-test-save-clip.py`
- `[ALL]` = Used by multiple scripts

**Important:** **NEVER commit** the `env` file to Git!

---

## ⚙️ Configuration

### Environment Variables

All configuration is in the `.env` file. Each variable is marked with which script(s) use it. See the [Environment Variables Reference](#environment-variables-reference) section below for complete details.

**Key Categories:**
- Portal & Email Credentials `[ALL]`
- Browser Settings `[ALL]`
- OTP Login Timings `[OTP]`
- Upload Workflow Timings `[UPLOAD, VALIDATION]`
- File Upload Paths `[UPLOAD]`
- Metadata Form Fields `[UPLOAD, VALIDATION]`
- Validation Script Settings `[VALIDATION]`
- Live Stream Settings `[LIVE]`
- Logging `[ALL]`

**See `env.example` file for complete list with script indicators.**

---

## 🚀 Usage

### OTP Login Script

To run standalone OTP login:

```bash
python auth/otp.py
```

This script will:
1. Launch browser
2. Login to portal
3. Fetch OTP from Gmail
4. Verify OTP
5. Complete login

### Single ZIP Upload Script

To run complete upload workflow:

```bash
python uploads/single-zipfile-upload.py
```

This script will:
1. Perform OTP login (using `auth/otp.py` functions)
2. Open QA Testing circle
3. Upload ZIP file
4. Fill metadata
5. Verify download

### Upload Sequence Validation Script

To run upload sequence validation:

```bash
python uploads/upload-sequence-validation.py
```

This script will:
1. Perform OTP login
2. Open QA Testing circle
3. Upload multiple files
4. Fill metadata
5. Validate file sequence via modal navigation

### Live Stream Testing Script

To run live stream testing and clip creation:

```bash
python live/live-test-save-clip.py
```

This script will:
1. Perform OTP login
2. Navigate to live menu
3. Process all channels (track live time, verify previous days)
4. Create a 5-minute clip from second channel
5. Save clip with metadata

### Using Functions in Your Own Scripts

If you want to create your own script that uses existing functions:

```python
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import OTP login function
from auth.otp import login_with_otp_sync

# Setup Playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Use login function
    env_path = Path(__file__).resolve().parent / "env"
    success = login_with_otp_sync(page, env_path=env_path)
    
    if success:
        # Your automation logic here
        print("Login successful!")
    
    browser.close()
```

---

## 📚 Module Documentation

### Auth Module (`auth/`)

**Purpose:** OTP-based authentication automation

**File:** `auth/otp.py`

**Main Class:** `NimarOTPAutomation`

**Module-level Functions (for backward compatibility):**
- `login_with_otp_sync(page, env_path=None)` - Sync OTP login wrapper function
- `login_with_otp_async(page, env_path=None)` - Async OTP login wrapper function

**How to Import:**
```python
# Import main class
from auth.otp import NimarOTPAutomation

# Or import wrapper function (recommended for custom scripts)
from auth.otp import login_with_otp_sync
```

**Documentation:** See class and method docstrings in `auth/otp.py`

### Uploads Module (`uploads/`)

#### Single ZIP Upload

**Purpose:** File upload automation

**File:** `uploads/single-zipfile-upload.py`

**Main Class:** `UploadAutomationSuite`

**Main Methods:**
- `run()` - Execute complete upload workflow
- `open_circle()` - Opens QA Testing circle
- `click_upload_button(zip_file)` - Clicks upload button and selects file
- `start_upload(zip_file, uploaded_filename)` - Starts the upload process
- `fill_metadata_form()` - Fills metadata form (Post Title, Title, Description, Keywords)
- `submit_metadata_form()` - Submits the metadata form
- `open_and_verify_download(uploaded_filename)` - Opens modal and verifies download

**How to Import:**
```python
from uploads.single_zipfile_upload import UploadAutomationSuite
```

**Documentation:** See class and method docstrings in `uploads/single-zipfile-upload.py`

#### Upload Sequence Validation

**Purpose:** Upload sequence validation automation

**File:** `uploads/upload-sequence-validation.py`

**Main Class:** `SequenceValidationAutomation`

**Main Methods:**
- `run()` - Execute complete validation workflow
- `_setup_logger()` - Configure logging (private method)
- `display_env_variables()` - Display environment variables
- `_initialize_browser()` - Initialize Playwright browser (private method)
- `_upload_files()` - Upload files to portal (private method)
- `_fill_and_submit_metadata()` - Fill and submit metadata form (private method)
- `_validate_sequence()` - Validate file sequence via modal (private method)
- `_extract_s3_url()` - Extract S3 bucket URL from modal HTML (private method)

**External Dependencies:**
- `login_with_otp_sync()` from `auth.otp` - OTP-based login
- Local `CircleHandler` class - Circle navigation

**How to Import:**
```python
from uploads.upload_sequence_validation import SequenceValidationAutomation
```

**Documentation:** See class and method docstrings in `uploads/upload-sequence-validation.py`

### Live Stream Module (`live/`)

**Purpose:** Live stream testing and clip creation automation

**File:** `live/live-test-save-clip.py`

**Main Class:** `LiveTestSaveClipAutomation`

**Main Methods:**
- `run()` - Execute complete workflow
- `get_all_channels()` - Get all available channels dynamically
- `open_channel(channel_index, channel_name)` - Open a specific channel
- `start_live_stream(channel_name)` - Start live stream for a channel
- `track_live_stream_time(channel_name)` - Track live stream time and compare with PC time
- `verify_previous_days_streams(channel_name, days)` - Verify previous day streams
- `crop_and_save_clip()` - Crop 5-minute clip and save
- `process_all_channels()` - Process all channels (live time tracking + previous day verification)

**External Dependencies:**
- `login_with_otp_sync()` from `auth.otp` - OTP-based login

**How to Import:**
```python
from live.live_test_save_clip import LiveTestSaveClipAutomation
```

**Documentation:** See class and method docstrings in `live/live-test-save-clip.py`

---

## 🔧 Environment Variables Reference

### Portal & Email Credentials `[ALL]`
Used by: All scripts for login and OTP retrieval

- `PORTAL_URL` - NIMAR portal URL
- `USERNAME` - Portal username
- `PASSWORD` - Portal password
- `EMAIL_USER` - Gmail address
- `EMAIL_PASS` - Gmail App Password
- `EMAIL_SERVER` - IMAP server (default: imap.gmail.com)

### Browser Settings `[ALL]`
Used by: All scripts for browser configuration

- `BROWSER_HEADLESS` - Browser headless mode (true/false)
- `BROWSER_IGNORE_HTTPS_ERRORS` - Ignore HTTPS errors (true/false)
- `BROWSER_NO_VIEWPORT` - Viewport settings (true/false)

### OTP Login Timings `[OTP]`
Used by: `auth/otp.py`

- `OTP_CREDENTIAL_ENTRY_WAIT` - Wait after credential entry (ms)
- `OTP_BUTTON_TIMEOUT` - OTP button wait timeout (ms)
- `OTP_EMAIL_WAIT_TIME` - Email wait time (ms)
- `OTP_INPUT_DELAY` - OTP input delay between digits (ms)
- `OTP_VERIFY_BUTTON_TIMEOUT` - Verify button timeout (ms)
- `OTP_LOGIN_COMPLETE_WAIT` - Wait after login complete (ms)
- `OTP_RETRIES` - Maximum OTP retry attempts
- `OTP_DELAY` - Delay between OTP retries (seconds)

### Upload Workflow Timings `[UPLOAD, VALIDATION]`
Used by: `uploads/single-zipfile-upload.py`, `uploads/upload-sequence-validation.py`

- `WAIT_TIMEOUT` - General wait timeout (seconds)
- `UPLOAD_WAIT_TIME` - Upload processing wait time (seconds)
- `STEP_GAP_SECONDS` - Gap between steps (seconds)
- `LOGIN_SUCCESS_WAIT` - Wait after login success (seconds)
- `CIRCLES_CLICK_WAIT` - Wait after circles click (seconds)
- `QA_CIRCLE_OPEN_WAIT` - Wait after QA circle open (seconds)
- `UPLOAD_BUTTON_SCROLL_WAIT` - Wait after upload button scroll (seconds)
- `UPLOAD_CANCELED_DETECTION_TIMEOUT` - Upload canceled detection timeout (ms)
- `BROWSER_DIALOG_TIMEOUT` - Browser dialog timeout (seconds)
- `PORTAL_CONFIRM_WAIT` - Portal confirm wait (ms)
- `START_UPLOAD_ENABLED_CHECK_INTERVAL` - Start upload enabled check interval (seconds)
- `START_UPLOAD_SCROLL_WAIT` - Start upload scroll wait (seconds)
- `START_UPLOAD_CLICK_WAIT` - Start upload click wait (seconds)
- `ADD_METADATA_SCROLL_WAIT` - Add metadata scroll wait (seconds)
- `ADD_METADATA_CLICK_WAIT` - Add metadata click wait (seconds)
- `SUBMIT_FORM_WAIT` - Submit form wait (seconds)
- `SUBMIT_AFTER_WAIT` - Wait after submit (seconds)
- `MODAL_THUMBNAIL_SCROLL_WAIT` - Modal thumbnail scroll wait (seconds)
- `MODAL_OPEN_WAIT` - Wait after modal opens (seconds)
- `DOWNLOAD_BUTTON_SCROLL_WAIT` - Download button scroll wait (seconds)

### Retry Settings `[UPLOAD, VALIDATION]`
Used by: `uploads/single-zipfile-upload.py`, `uploads/upload-sequence-validation.py`

- `WAIT_AND_CLICK_START_MAX_RETRIES` - Start upload retries
- `CLICK_PORTAL_START_UPLOAD_MAX_RETRIES` - Portal start upload retries
- `START_UPLOAD_ENABLED_CHECK_MAX_ATTEMPTS` - Enabled check attempts

### File Upload Paths `[UPLOAD]`
Used by: `uploads/single-zipfile-upload.py`

- `DESKTOP_FOLDER` - Desktop folder name (e.g., "New folder")
- `ZIP_FILE` - ZIP file name (e.g., "ary.zip")
- `DOWNLOADS_FOLDER` - Downloads folder path (relative to USERPROFILE)
- `DESKTOP_PATH` - Desktop base path (usually Desktop)

### Circle Name `[UPLOAD, VALIDATION]`
Used by: `uploads/single-zipfile-upload.py`, `uploads/upload-sequence-validation.py`

- `CIRCLE_NAME` - Circle name to open (e.g., "QA Testing")

### Metadata Form Fields `[UPLOAD, VALIDATION]`
Used by: `uploads/single-zipfile-upload.py`, `uploads/upload-sequence-validation.py`

- `POST_TITLE` - Post title for metadata
- `CONTENT_TITLE` - Content title
- `DESCRIPTION` - Description text
- `KEYWORDS` - Keywords (comma-separated)

### Validation Script Settings `[VALIDATION]`
Used by: `uploads/upload-sequence-validation.py`

- `FILE_URL_1` - File path for validation (full path)
- `FILE_URL_2` - File path for validation (full path)
- `FILE_URL_3` - File path for validation (full path)
- `S3_BUCKET_URL` - S3 Bucket URL (fallback if dynamic extraction fails)

### Live Stream Settings `[LIVE]`
Used by: `live/live-test-save-clip.py`

- `LIVE_USE_SYSTEM_CHROME` - Use system Chrome (true/false)
- `LIVE_BROWSER_HEADLESS` - Browser headless mode for live script (true/false)
- `LIVE_USE_CHROME_CHANNEL` - Use Chrome channel (true/false)
- `WAIT_AFTER_GET_STREAM` - Wait after Get Stream click (seconds)

### Logging `[ALL]`
Used by: All scripts

- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)

**See `env.example` file for complete list with script indicators.**

---

## 🔮 Future Extensions

This framework can be easily extended in the future. Here are some ideas:

### Planned Modules

1. **Downloads Module** (`downloads/`)
   - Bulk file downloads
   - Download verification
   - File organization

2. **Reports Module** (`reports/`)
   - Automated report generation
   - Data extraction
   - Export functionality

3. **Bulk Operations Module** (`bulk/`)
   - Multiple file uploads
   - Batch processing
   - Queue management

4. **Testing Module** (`testing/`)
   - Automated test cases
   - Regression testing
   - Test reporting

### How to Add New Modules

1. **Create Module Folder:**
   ```bash
   mkdir new-module
   ```

2. **Create Script File:**
   ```python
   # new-module/my-script.py
   from auth.otp import login_with_otp_sync
   
   def my_automation(page):
       # Login using existing function
       login_success = login_with_otp_sync(page)
       
       if login_success:
           # Your automation logic
           pass
   ```

3. **Add to README:**
   - Module description
   - Usage examples
   - Configuration requirements

4. **Update env.example:**
   - Add new environment variables if needed
   - Mark which script uses each variable

---

## 🤝 Contributing

If you want to add new features:

1. **Follow Single Main Class Pattern:**
   - Create one main class per module
   - All helper methods should be class methods
   - No module-level functions visible when classes are collapsed
   - Reuse existing main classes or wrapper functions
   - No code duplication
   - Proper encapsulation and documentation

2. **Environment Variables:**
   - Avoid hardcoded values
   - Keep configurable values in `.env`
   - Update `env.example` with script indicators
   - Mark which script(s) use each variable

3. **Documentation:**
   - Update module README
   - Add class and method docstrings
   - Provide usage examples
   - Update main README.md

4. **Code Quality:**
   - Proper error handling
   - Add logging
   - Follow clean code practices
   - Make all prints/comments dynamic (no hardcoded script names)

---

## 🐛 Troubleshooting

### Common Issues

#### 1. OTP Not Received
- **Check:** Is Gmail IMAP enabled?
- **Check:** Is App Password correct?
- **Solution:** Increase `OTP_RETRIES` and `OTP_DELAY`

#### 2. Login Failed
- **Check:** Is Portal URL correct?
- **Check:** Are Username/Password correct?
- **Check:** Is network connection stable?

#### 3. Upload Failed
- **Check:** Is ZIP file path correct?
- **Check:** Is `UPLOAD_WAIT_TIME` sufficient?
- **Check:** Is Circle name correct?

#### 4. Import Errors
- **Check:** Is `sys.path` properly set?
- **Check:** Are dependencies installed?
- **Solution:** `pip install -r requirements.txt`

#### 5. Live Stream Not Loading
- **Check:** Is `LIVE_USE_SYSTEM_CHROME` set correctly?
- **Check:** Is `LIVE_BROWSER_HEADLESS` set to false?
- **Check:** Are browser permissions configured?

### Logs

All logs are automatically generated:

- **OTP Logs:** `auth/logs/otp_*.log`
- **Upload Logs:** `uploads/logs/single-zipfile-upload_*.log`
- **Validation Logs:** `uploads/logs/upload-sequence-validation_*.log`
- **Live Stream Logs:** `live/logs/live-test-save-clip_*.log`

Check logs to debug issues.

---

## 📝 License & Credits

**Author:** Rabbia Gillani SQA  
**Version:** 3.0.0  
**Date:** 2025-11-12

**Framework Features:**
- Class-based architecture
- Reusable classes with proper encapsulation
- Environment-based configuration
- Comprehensive logging
- Future-extensible design
- No hardcoded values
- Dynamic script references

---

## 📞 Support

If you have any issues or questions:

1. Check logs
2. Verify environment variables
3. Review documentation
4. Read error messages carefully

---

## 🎉 Summary

This NIMAR Automation Framework provides:

✅ **Complete Solution** - Everything from OTP login to upload and live stream testing  
✅ **Modular Design** - Reusable classes and functions  
✅ **Easy to Extend** - Future features can be easily added  
✅ **Well Documented** - Complete documentation with docstrings  
✅ **Configurable** - Everything controlled via `.env` with script indicators  
✅ **Production Ready** - Error handling and logging  
✅ **No Hardcoded Values** - All critical values in environment variables  
✅ **Dynamic References** - No hardcoded script names in logs/comments

**Happy Automating! 🚀**

---

*Last Updated: 2025-11-12*
