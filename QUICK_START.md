# Route Analysis Dashboard - Quick Start Guide

## 🚀 Deploy in 3 Steps

### Step 1: Update GitHub Repository
```bash
cd /path/to/ethiopian-airlines-dashboard

# Copy these files from the deployment package:
# - src/models/route_analysis.py (NEW)
# - src/routes/route_analysis.py (NEW)
# - src/static/route-analysis.html (NEW)
# - src/main.py (REPLACE)
# - src/static/index.html (REPLACE)

git add .
git commit -m "Add Route Analysis dashboard"
git push origin main
```

### Step 2: Wait for Auto-Deployment
- Render will automatically deploy (2-3 minutes)
- Monitor at: https://dashboard.render.com
- Wait for "Deploy live" status

### Step 3: Upload Data
1. Visit: `https://ethiopian-airlines-dashboard.onrender.com/route-analysis`
2. Click "Upload Data"
3. Login: `admin` / `admin123`
4. Upload your Excel file
5. View the dashboard!

---

## 📊 What You Get

### 6 Metrics
- Total Routes
- Total Passengers (current week)
- Previous Week Passengers
- Week-over-Week Change %
- Top Route
- Busiest Day

### 5 Charts
- Top 10 Routes (Bar Chart)
- Daily Passenger Trend (Line Chart)
- Week-over-Week Comparison (Bar Chart)
- Passenger Distribution (Doughnut Chart)
- Growth Leaders (Horizontal Bar Chart)

---

## 📁 Excel File Format

Your Excel file should have:
- **Row 2**: Headers (POINTS, dates, GRAND TOTAL, PREVIOUS WEEK)
- **Row 3+**: Route data (airport codes, daily counts, totals)

Example:
```
POINTS | 2025-09-21 | 2025-09-22 | ... | GRAND TOTAL | PREVIOUS WEEK
ABV    | 11         | 5          | ... | 37          | 46
ADD    | 44         | 36         | ... | 393         | 291
```

The system automatically:
- Reads any sheet (uses first/active sheet)
- Calculates variance and growth %
- Identifies top routes and busiest days
- Handles different date formats

---

## ✅ Testing Checklist

After deployment:
- [ ] Home page shows "Route Analysis" option
- [ ] Route Analysis page loads
- [ ] Upload button works
- [ ] Admin login works
- [ ] Excel upload succeeds
- [ ] All metrics populate
- [ ] All charts display
- [ ] Charts are interactive
- [ ] Back to Home works

---

## 🔧 Troubleshooting

**Charts not showing?**
- Clear browser cache
- Wait 10 seconds after page load
- Check browser console for errors

**Upload fails?**
- Verify file is .xlsx or .xls
- Check file has data in expected format
- Ensure admin is logged in

**Render not deploying?**
- Check all files are committed to GitHub
- Manually trigger rebuild on Render
- Check Render logs for errors

---

## 📞 Quick Links

- **Live Site**: https://ethiopian-airlines-dashboard.onrender.com
- **Route Analysis**: https://ethiopian-airlines-dashboard.onrender.com/route-analysis
- **Render Dashboard**: https://dashboard.render.com
- **GitHub Repo**: https://github.com/aljbartee-ui/ethiopian-airlines-dashboard

---

**Ready to deploy? Follow Step 1-3 above!**

