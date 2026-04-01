# 📤 Upload HSI Backup to Google Drive - Step-by-Step Guide

## Current Status
- **Backup File**: `/root/.openclaw/workspace/hsi_backup_20260225_0208.csv` (677K)
- **Size**: 13,865 rows of HSI data (1969-2026)
- **Google Auth**: ✅ Already configured in OpenClaw (for Gemini API)

---

## Option 1: Manual Upload via Web (Quickest - No Setup)

### Steps:
1. Open browser and go to: **https://drive.google.com**
2. Sign in with your Google account
3. Click **"+ New"** → **"File upload"**
4. Navigate to and select: `hsi_backup_20260225_0208.csv`
5. Wait for upload to complete
6. (Optional) Right-click file → **"Share"** → Copy link

**Time**: ~2 minutes  
**Difficulty**: ⭐ Easy

---

## Option 2: Using rclone (Best for Automation)

### Step 1: Install rclone
```bash
# For Linux (Debian/Ubuntu)
curl https://rclone.org/install.sh | sudo bash

# For macOS
brew install rclone

# Or download from: https://rclone.org/downloads/
```

### Step 2: Configure Google Drive
```bash
rclone config
```
Follow the prompts:
1. `n` - New remote
2. Name: `gdrive`
3. Storage: Select `google drive` (usually option 10-15)
4. Client ID: Press Enter (use default)
5. Client Secret: Press Enter (use default)
6. Scope: Select `drive` (full access)
7. Root folder ID: Press Enter (use root)
8. Service Account File: Press Enter (skip)
9. **A browser will open** - authorize with your Google account
10. Copy the authorization code and paste it back
11. Confirm: `y`

### Step 3: Upload File
```bash
rclone copy /root/.openclaw/workspace/hsi_backup_20260225_0208.csv gdrive:/HSI_Backups/
```

### Step 4: Verify Upload
```bash
rclone ls gdrive:/HSI_Backups/
```

**Time**: 10-15 minutes (first-time setup)  
**Difficulty**: ⭐⭐⭐ Medium  
**Benefit**: Can automate future uploads!

---

## Option 3: Using Google Drive CLI (gdrive)

### Step 1: Install gdrive
```bash
# Download latest release
wget https://github.com/glotlabs/gdrive/releases/download/v2.1.1/gdrive_linux_amd64
chmod +x gdrive_linux_amd64
sudo mv gdrive_linux_amd64 /usr/local/bin/gdrive
```

### Step 2: Authenticate
```bash
gdrive about
```
- A browser will open for authorization
- Copy the verification code back to terminal

### Step 3: Upload
```bash
gdrive upload /root/.openclaw/workspace/hsi_backup_20260225_0208.csv
```

**Time**: 5-10 minutes  
**Difficulty**: ⭐⭐ Easy-Medium

---

## Option 4: Python Script (For Developers)

### Prerequisites
Need to install Google Drive API packages first.

### Step 1: Enable Google Drive API
1. Go to: **https://console.cloud.google.com/apis/library/drive.googleapis.com**
2. Select your project (or create new)
3. Click **"Enable"**

### Step 2: Create Credentials
1. Go to: **https://console.cloud.google.com/apis/credentials**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Download the JSON file as `credentials.json`

### Step 3: Run Upload Script
Save this as `upload_to_drive.py`:

```python
#!/usr/bin/env python3
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
BACKUP_FILE = '/root/.openclaw/workspace/hsi_backup_20260225_0208.csv'

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
    
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {'name': os.path.basename(BACKUP_FILE)}
    media = MediaFileUpload(BACKUP_FILE, resumable=True)
    
    file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
    
    print(f"✅ Upload complete!")
    print(f"File ID: {file.get('id')}")
    print(f"View URL: {file.get('webViewLink')}")

if __name__ == '__main__':
    main()
```

Run it:
```bash
python3 upload_to_drive.py
```

**Time**: 15-20 minutes  
**Difficulty**: ⭐⭐⭐⭐ Advanced  
**Benefit**: Fully customizable

---

## 🎯 My Recommendation

**For one-time upload**: Use **Option 1** (Manual via web) - fastest, no setup

**For recurring uploads**: Use **Option 2** (rclone) - set up once, automate forever

---

## 📋 Want Me to Automate This?

Once you have rclone configured, I can:
1. Add Google Drive upload to the weekly cron job
2. Automatically upload backups every Monday
3. Send you the download link via email/message

Just let me know which option you choose, and if you want help with the setup! 🚀

---

*Generated: 2026-02-25 03:05 UTC*
