# Flight Load Navigation Restructure - Deployment Guide

## 🎯 What Changed

### Navigation Structure

**BEFORE:**
```
Home
├── Sales Report
├── Flight Load (direct to load factor)
└── Route Analysis (standalone)
```

**AFTER:**
```
Home
├── Sales Report
└── Flight Load (menu page)
    ├── Load Factor
    └── Route Analysis
```

### Files Modified/Created

#### New Files:
1. **src/static/flight-load-menu.html** - New menu page for Flight Load section
2. **src/static/flight-load-factor.html** - Load factor page (moved from flight-load.html)
3. **src/static/flight-load-route-analysis.html** - Route analysis under Flight Load

#### Modified Files:
1. **src/static/index.html** - Removed standalone Route Analysis card
2. **src/main.py** - Updated routes for new navigation structure

### URL Changes

| Old URL | New URL | Status |
|---------|---------|--------|
| `/` | `/` | ✅ Same (home page) |
| `/sales-report` | `/sales-report` | ✅ Same |
| `/flight-load` | `/flight-load` | ⚠️ Now shows menu page |
| N/A | `/flight-load/load-factor` | ✨ New (load factor dashboard) |
| `/route-analysis` | `/flight-load/route-analysis` | ⚠️ Moved (redirects automatically) |

---

## 📦 Deployment Steps

### Step 1: Backup Current Files (Optional but Recommended)

Before deploying, you can backup your current GitHub repository:

```bash
# On your local machine or GitHub web interface
# Create a new branch called "backup-before-restructure"
```

### Step 2: Update Your GitHub Repository

1. **Download the deployment package** (attached zip file)

2. **Extract the files** to your local computer

3. **Navigate to your local repository**:
   ```bash
   cd path/to/ethiopian-airlines-dashboard
   ```

4. **Copy the updated files**:
   - Copy all files from the extracted `src/` folder to your repository's `src/` folder
   - Overwrite when prompted

5. **Verify the new files exist**:
   ```bash
   ls src/static/flight-load-menu.html
   ls src/static/flight-load-factor.html
   ls src/static/flight-load-route-analysis.html
   ```

6. **Commit and push to GitHub**:
   ```bash
   git add .
   git commit -m "Restructure Flight Load navigation with menu page"
   git push origin main
   ```

### Step 3: Wait for Render Deployment

1. Go to https://dashboard.render.com
2. Click on your service "ethiopian-airlines-dashboard"
3. Watch the "Events" tab - you should see "Deploy started"
4. Wait for "Deploy live" (usually 2-3 minutes)

### Step 4: Verify Deployment

1. **Test Home Page**:
   - Visit: https://ethiopian-airlines-dashboard.onrender.com
   - Should see only 2 cards: "Sales Report" and "Flights Load"
   - ✅ "Route Analysis" card should be GONE

2. **Test Flight Load Menu**:
   - Click "Flights Load" from home
   - Should see menu page with 2 options:
     - Load Factor
     - Route Analysis
   - ✅ Both should have "Active" badges

3. **Test Load Factor**:
   - Click "Load Factor" from Flight Load menu
   - Should see the load factor dashboard
   - ✅ Should have 2 buttons: "← Back to Flight Load" and "🏠 Home"

4. **Test Route Analysis**:
   - Click "Route Analysis" from Flight Load menu
   - Should see the route analysis dashboard
   - ✅ Should have 2 buttons: "← Back to Flight Load" and "🏠 Home"

5. **Test Data Upload**:
   - On Route Analysis page, click "📤 Upload Data"
   - Upload your `routeanalysis.xlsx` file
   - ✅ Should see metrics and charts populate

---

## 🔍 Troubleshooting

### Issue: "Not Found" Error

**Symptom**: Clicking any link shows "Not Found"

**Solution**:
1. Check Render logs for errors
2. Verify all files were pushed to GitHub
3. Check that main.py has the redirect import:
   ```python
   from flask import Flask, send_from_directory, session, request, jsonify, redirect
   ```

### Issue: Old Route Analysis URL Not Working

**Symptom**: `/route-analysis` shows 404

**Solution**: This is expected! The old URL now redirects to `/flight-load/route-analysis`. Clear your browser cache and try again.

### Issue: Charts Not Displaying on Route Analysis

**Symptom**: Metrics show but charts are blank

**Solution**:
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify you uploaded a valid Excel file
4. Check that the Excel file has the correct structure (POINTS column, date columns, GRAND TOTAL, PREVIOUS WEEK, VARIANCE)

### Issue: Back Buttons Overlapping

**Symptom**: Navigation buttons are stacked or overlapping

**Solution**: This is a CSS issue. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R) and reload.

---

## 📊 Route Analysis Excel File Format

Your Excel file should have this structure:

| POINTS | 2025-09-21 | 2025-09-22 | ... | GRAND TOTAL | PREVIOUS WEEK | VARIANCE |
|--------|------------|------------|-----|-------------|---------------|----------|
| ABV    | 11         | 5          | ... | 37          | 46            | -9       |
| ADD    | 44         | 36         | ... | 393         | 291           | 102      |
| ACC    | 59         | 62         | ... | 220         | 254           | -34      |

**Requirements**:
- ✅ First column must be "POINTS" (route codes)
- ✅ Date columns can be any date format
- ✅ Must have "GRAND TOTAL", "PREVIOUS WEEK", and "VARIANCE" columns
- ✅ Works with any sheet name (uses active/first sheet)
- ✅ Handles any number of routes and dates

---

## 🎨 What You'll See After Deployment

### Home Page
- **Sales Report** card (green gradient icon)
- **Flights Load** card (yellow gradient icon)
- Description updated to mention "Load Factor tracking and Route Analysis"

### Flight Load Menu
- Clean menu page with Ethiopian Airlines branding
- Two large cards:
  - **Load Factor** (📈 icon) - with feature list
  - **Route Analysis** (🌍 icon) - with feature list
- "Back to Home" button in top-left

### Load Factor Dashboard
- Same as before, but with updated navigation
- Two buttons: "← Back to Flight Load" and "🏠 Home"

### Route Analysis Dashboard
- 6 metric cards at top
- 5 interactive charts
- Upload button for admin
- Two buttons: "← Back to Flight Load" and "🏠 Home"

---

## ✅ Testing Checklist

After deployment, verify:

- [ ] Home page shows 2 options (not 3)
- [ ] Flight Load menu page loads correctly
- [ ] Load Factor page accessible from menu
- [ ] Route Analysis page accessible from menu
- [ ] Back buttons work on all pages
- [ ] Old `/route-analysis` URL redirects to new location
- [ ] Excel upload works on Route Analysis page
- [ ] Charts display after upload
- [ ] Metrics calculate correctly

---

## 📞 Support

If you encounter any issues:

1. Check the Render logs first
2. Verify all files are in GitHub
3. Clear browser cache
4. Try in incognito/private mode

All backend logic remains the same - only navigation structure changed!

