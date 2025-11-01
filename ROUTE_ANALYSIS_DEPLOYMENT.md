# Route Analysis Dashboard - Deployment Guide

## ✅ What's New

A complete **Route Analysis** dashboard has been added to your Ethiopian Airlines Analytics Portal with the following features:

### Features
- **6 Metric Cards**: Total Routes, Total Passengers, Previous Week, Week-over-Week Change, Top Route, Busiest Day
- **5 Interactive Charts**:
  - Top 10 Routes by Passengers (Bar Chart with current vs previous week)
  - Daily Passenger Trend (Line Chart)
  - Week-over-Week Comparison (Bar Chart for top 5 routes)
  - Passenger Distribution (Doughnut Chart)
  - Top 10 Routes by Growth Rate (Horizontal Bar Chart)
- **Admin Upload**: Secure Excel file upload via admin panel
- **Back to Home**: Easy navigation back to the main portal
- **Responsive Design**: Works on all devices
- **Ethiopian Airlines Branding**: Consistent with your existing dashboards

### Data Processing
- Automatically processes route analysis Excel files (any sheet name)
- Extracts route codes, daily passenger counts, weekly totals
- Calculates week-over-week variance and growth percentages
- Identifies top routes and busiest days
- Handles multiple date formats automatically

---

## 📋 Files Changed/Added

### New Files
1. `src/models/route_analysis.py` - Database model for route analysis data
2. `src/routes/route_analysis.py` - Backend routes and data processing
3. `src/static/route-analysis.html` - Frontend dashboard

### Modified Files
1. `src/main.py` - Added route analysis blueprint and route
2. `src/static/index.html` - Added Route Analysis option to home page

---

## 🚀 Deployment Steps

### Step 1: Update Your GitHub Repository

Since your Render deployment is connected to GitHub with auto-deployment, you just need to push these files:

```bash
# Navigate to your local repository
cd /path/to/ethiopian-airlines-dashboard

# Copy the new/modified files (provided in this deployment package)
# - Copy src/models/route_analysis.py
# - Copy src/routes/route_analysis.py
# - Copy src/static/route-analysis.html
# - Replace src/main.py
# - Replace src/static/index.html

# Add all changes to git
git add .

# Commit the changes
git commit -m "Add Route Analysis dashboard with charts and metrics"

# Push to GitHub
git push origin main
```

### Step 2: Render Auto-Deployment

Render will automatically detect the changes and deploy. This typically takes 2-3 minutes.

**Monitor the deployment:**
1. Go to https://dashboard.render.com
2. Click on your service: `ethiopian-airlines-dashboard`
3. Watch the "Events" tab for deployment progress
4. Wait for "Deploy live" status

### Step 3: Verify the Deployment

1. Visit your live site: `https://ethiopian-airlines-dashboard.onrender.com`
2. You should see **3 options** on the home page:
   - Sales Report
   - Flights Load
   - **Route Analysis** (NEW)
3. Click on "Route Analysis"

---

## 📤 How to Upload Route Analysis Data

### First Time Upload

1. **Login as Admin**:
   - Click "Upload Data" button on the Route Analysis page
   - You'll be redirected to admin login
   - Username: `admin`
   - Password: `admin123`

2. **Upload Excel File**:
   - After login, click "Upload Data" again
   - Select your route analysis Excel file (e.g., `routeanalysis.xlsx`)
   - Click "Upload"
   - Wait for success message

3. **View Dashboard**:
   - Page will automatically reload
   - All 6 metrics and 5 charts will display
   - Data is interactive - hover over charts for details

### Subsequent Uploads

- Click "Upload Data" button
- If still logged in as admin, modal opens directly
- If session expired, login again
- Upload new file (replaces previous data)

---

## 📊 Excel File Format

The system automatically processes Excel files with this structure:

### Expected Format
- **Row 1**: Empty (optional)
- **Row 2**: Headers (POINTS, dates, GRAND TOTAL, PREVIOUS WEEK, VARIANCE)
- **Row 3+**: Route data

### Example Structure
```
Row 2: POINTS | 2025-09-21 | 2025-09-22 | ... | GRAND TOTAL | PREVIOUS WEEK | VARIANCE
Row 3: ABV    | 11         | 5          | ... | 37          | 46            | -9
Row 4: ADD    | 44         | 36         | ... | 393         | 291           | 102
```

### What Gets Extracted
- Route codes (airport codes like ABV, ADD, ACC)
- Daily passenger counts (6 dates per week)
- Weekly totals (current and previous week)
- Variance calculations (automatic)
- Growth percentages (automatic)

---

## 🎨 Dashboard Features

### Metric Cards
1. **Total Routes**: Number of unique routes in the data
2. **Total Passengers**: Current week total
3. **Previous Week**: Previous week total for comparison
4. **Week-over-Week**: Change amount and percentage (color-coded: green for positive, red for negative)
5. **Top Route**: Route with most passengers
6. **Busiest Day**: Day with highest passenger count

### Interactive Charts
1. **Top 10 Routes**: Bar chart comparing current vs previous week
2. **Daily Trend**: Line chart showing passenger flow across the week
3. **Week Comparison**: Side-by-side comparison for top 5 routes
4. **Distribution**: Doughnut chart showing passenger share by route
5. **Growth Leaders**: Horizontal bar chart showing routes with highest growth rates

### Chart Interactions
- **Hover**: See exact values and percentages
- **Smooth Animations**: Charts animate on load
- **Responsive**: Adjusts to screen size
- **Ethiopian Colors**: Green, Yellow, Red branding

---

## 🔐 Security & Access

### Public Access
- Route Analysis page is **publicly accessible** (no password required)
- Anyone with the link can view the dashboard
- Data is read-only for public viewers

### Admin Access
- **Upload functionality** requires admin login
- Admin credentials:
  - Username: `admin`
  - Password: `admin123`
- Change password via admin panel after first login

### Session Management
- Admin sessions last 1 hour
- Auto-logout on browser close
- Re-login required for uploads after session expires

---

## 🧪 Testing Checklist

After deployment, verify:

- [ ] Home page shows 3 options (Sales, Flights Load, Route Analysis)
- [ ] Route Analysis page loads without errors
- [ ] "No Data Available" message shows before upload
- [ ] Upload button redirects to admin login
- [ ] Admin login works with correct credentials
- [ ] Excel file uploads successfully
- [ ] All 6 metric cards populate with data
- [ ] All 5 charts render correctly
- [ ] Charts are interactive (hover shows values)
- [ ] Back to Home button works
- [ ] Subsequent uploads replace previous data

---

## 🐛 Troubleshooting

### Charts Not Displaying
- **Symptom**: White boxes instead of charts
- **Solution**: This is fixed using `requestAnimationFrame` (same fix as Sales Dashboard)
- **If persists**: Clear browser cache and reload

### Upload Fails
- **Symptom**: Error message on upload
- **Check**: File is .xlsx or .xls format
- **Check**: File has data starting from row 2
- **Check**: Admin is logged in

### No Data After Upload
- **Symptom**: Upload succeeds but dashboard shows "No Data Available"
- **Check**: Excel file has route data in expected format
- **Check**: Database file has write permissions
- **Solution**: Check Render logs for processing errors

### Render Deployment Fails
- **Check**: All files are committed to GitHub
- **Check**: No syntax errors in Python files
- **Check**: Render build logs for specific errors
- **Solution**: Manually trigger rebuild on Render dashboard

---

## 📝 File Locations in Repository

```
ethiopian-airlines-dashboard/
├── src/
│   ├── main.py                          # ✏️ MODIFIED - Added route analysis blueprint
│   ├── models/
│   │   ├── route_analysis.py            # ✨ NEW - Database model
│   │   ├── sales.py                     # (existing)
│   │   └── user.py                      # (existing)
│   ├── routes/
│   │   ├── route_analysis.py            # ✨ NEW - Backend routes & processing
│   │   ├── sales_working.py             # (existing)
│   │   ├── charts_redesigned.py         # (existing)
│   │   └── ...                          # (other existing routes)
│   └── static/
│       ├── index.html                   # ✏️ MODIFIED - Added Route Analysis option
│       ├── route-analysis.html          # ✨ NEW - Dashboard frontend
│       ├── dashboard.html               # (existing - Sales)
│       └── ...                          # (other existing pages)
```

---

## 🎯 Next Steps

1. **Deploy the changes** following Step 1-3 above
2. **Upload your route analysis Excel file** via admin panel
3. **Share the link** with your team: `https://ethiopian-airlines-dashboard.onrender.com/route-analysis`
4. **Monitor usage** and gather feedback

---

## 💡 Tips

- Upload fresh data weekly to keep dashboard current
- Previous data is automatically archived when new file is uploaded
- Charts automatically adjust to data size (top 10, top 5, etc.)
- Growth chart highlights both positive (green) and negative (red) changes
- Distribution chart groups smaller routes into "Others" category

---

## ✅ Success Indicators

You'll know it's working when:
- Home page shows Route Analysis as third option
- Route Analysis dashboard loads with Ethiopian Airlines branding
- After upload, 6 metrics display actual numbers
- All 5 charts render with your route data
- Hovering over charts shows interactive tooltips
- Week-over-week changes show correct percentages
- Back to Home button returns to main portal

---

## 📞 Support

If you encounter issues:
1. Check Render deployment logs
2. Verify Excel file format matches expected structure
3. Clear browser cache and try again
4. Check that all files were committed to GitHub
5. Manually trigger Render rebuild if auto-deploy didn't work

---

**Deployment Date**: October 25, 2025  
**Version**: 1.0  
**Status**: ✅ Tested and Ready for Deployment

