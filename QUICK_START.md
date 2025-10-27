# Quick Start - 3 Steps to Deploy

## Step 1: Update GitHub

1. Extract the zip file to your computer
2. Copy the `src/` folder to your local repository (overwrite existing)
3. Run these commands:
   ```bash
   git add .
   git commit -m "Restructure Flight Load navigation"
   git push origin main
   ```

## Step 2: Wait for Render

1. Go to https://dashboard.render.com
2. Wait for "Deploy live" (2-3 minutes)

## Step 3: Test

1. Visit: https://ethiopian-airlines-dashboard.onrender.com
2. Click "Flights Load" → Should see menu with 2 options
3. Test both "Load Factor" and "Route Analysis"
4. Upload your Excel file on Route Analysis page

## ✅ Done!

**New Navigation:**
- Home → Flight Load → Load Factor
- Home → Flight Load → Route Analysis

**What Changed:**
- Route Analysis moved under Flight Load
- Added menu page for Flight Load section
- Better organization and navigation

**What Stayed Same:**
- All functionality works exactly the same
- Data processing unchanged
- Charts and metrics unchanged
- Excel upload unchanged

---

## Need Help?

See `DEPLOYMENT_GUIDE.md` for detailed instructions and troubleshooting.

