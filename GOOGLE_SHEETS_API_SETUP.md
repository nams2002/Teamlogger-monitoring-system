# Google Sheets API Setup Guide

This guide will help you set up Google Sheets API access for the TeamLogger monitoring system. This enables automatic detection of company-wide holidays across multiple month sheets.

## 🎯 Why Use Google Sheets API?

- ✅ Access **all month tabs** dynamically (Oct 25, Nov 25, Dec 25, etc.)
- ✅ Automatically detect **company-wide holidays** (like Oct 2-3, 2025)
- ✅ No need to manually configure GIDs for each month
- ✅ More reliable and faster than CSV export

---

## 📋 Step-by-Step Setup

### **Step 1: Enable Google Sheets API**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project:
   - Click the project dropdown at the top
   - Click **"New Project"**
   - Name it: `TeamLogger Monitor`
   - Click **"Create"**
3. Make sure your new project is selected
4. Go to **"APIs & Services"** → **"Library"** (left sidebar)
5. Search for **"Google Sheets API"**
6. Click on it and click **"Enable"**

### **Step 2: Create Service Account**

1. Go to **"APIs & Services"** → **"Credentials"** (left sidebar)
2. Click **"Create Credentials"** → **"Service Account"**
3. Fill in the details:
   - **Service account name**: `teamlogger-monitor`
   - **Service account ID**: (auto-filled)
   - **Description**: `Service account for TeamLogger monitoring system`
4. Click **"Create and Continue"**
5. **Grant this service account access to project** (optional):
   - Skip this step, click **"Continue"**
6. **Grant users access to this service account** (optional):
   - Skip this step, click **"Done"**

### **Step 3: Generate JSON Key**

1. You'll see your service account in the list
2. Click on the service account email (looks like `teamlogger-monitor@project-id.iam.gserviceaccount.com`)
3. Go to the **"Keys"** tab
4. Click **"Add Key"** → **"Create new key"**
5. Select **"JSON"** format
6. Click **"Create"**
7. A JSON file will be downloaded to your computer (e.g., `project-id-abc123.json`)

### **Step 4: Save the Credentials File**

1. In your TeamLogger project folder, create a `credentials` folder:
   ```
   Teamlogger-monitoring-system-main/
   ├── credentials/
   │   └── google-sheets-service-account.json  ← Put your file here
   ├── src/
   ├── config/
   └── ...
   ```

2. Rename the downloaded JSON file to: `google-sheets-service-account.json`

3. Move it to the `credentials/` folder

### **Step 5: Share Your Google Sheet**

1. Open the downloaded JSON file in a text editor
2. Find the `"client_email"` field (around line 5-10)
3. Copy the email address (looks like: `teamlogger-monitor@project-id.iam.gserviceaccount.com`)
4. Open your **Leave Tracker Google Sheet**
5. Click the **"Share"** button (top right)
6. Paste the service account email
7. Set permission to **"Viewer"** (read-only is enough)
8. **Uncheck** "Notify people" (it's a service account, not a real person)
9. Click **"Share"** or **"Send"**

### **Step 6: Install Required Python Libraries**

Run this command in your terminal:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### **Step 7: Enable API in Your Application**

Edit your `.env` file and set:

```env
USE_GOOGLE_SHEETS_API=true
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials/google-sheets-service-account.json
```

### **Step 8: Test the Setup**

Run the test script:

```bash
python debug_holiday_detection.py
```

You should see:
```
✅ Google Sheets API initialized successfully
✅ Detected company holiday on 2025-10-02 Thursday (20/20 employees)
✅ Detected company holiday on 2025-10-03 Friday (20/20 employees)
🎯 RESULT: 2 company holidays detected
✅ SUCCESS: Both Oct 2 and Oct 3 detected as holidays!
```

---

## 🔒 Security Notes

- ✅ The `credentials/` folder is already in `.gitignore` - your credentials won't be committed to git
- ✅ The service account only has **read access** to your sheet
- ✅ You can revoke access anytime by removing the service account from the sheet's sharing settings

---

## 🐛 Troubleshooting

### Error: "Credentials file not found"
- Make sure the file is in `credentials/google-sheets-service-account.json`
- Check the path in your `.env` file

### Error: "Permission denied" or "403 Forbidden"
- Make sure you shared the sheet with the service account email
- Check that the email in the JSON file matches the one you shared with

### Error: "Module not found: google.oauth2"
- Run: `pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client`

### Still using CSV export?
- Check that `USE_GOOGLE_SHEETS_API=true` in your `.env` file
- Check the logs - you should see "✅ Using Google Sheets API for multi-sheet access"

---

## 📊 How It Works

Once configured, the system will:

1. **Automatically detect** which months are needed (e.g., Sept 29 - Oct 5 needs both "Sep 25" and "Oct 25" sheets)
2. **Fetch data** from each month sheet using the API
3. **Detect company holidays** by checking if >70% of employees have "Holiday" marked on a specific day
4. **Adjust required hours** for everyone on company holiday days

For example:
- **Normal week**: 5 days × 8 hours = 40 hours required
- **Week with 2 company holidays**: 3 days × 8 hours = 24 hours required
- **With 3-hour buffer**: 21 hours acceptable minimum

---

## 🎉 Benefits

After setup, you'll get:
- ✅ Automatic holiday detection across all months
- ✅ Fair hour requirements during holiday weeks
- ✅ No manual GID configuration needed
- ✅ Works seamlessly with cross-month weeks (like Sept 29 - Oct 5)

---

## 📞 Need Help?

If you encounter any issues, check:
1. The service account email is correctly shared with the sheet
2. The credentials file is in the right location
3. The required Python packages are installed
4. `USE_GOOGLE_SHEETS_API=true` in `.env`

