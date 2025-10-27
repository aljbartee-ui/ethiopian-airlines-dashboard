# Route Analysis Dashboard - Quick Start

## 🚀 3-Step Deployment

### Step 1: Push to GitHub
```bash
cd /path/to/ethiopian-airlines-dashboard
git add .
git commit -m "Add Route Analysis dashboard"
git push origin main
```

### Step 2: Wait for Render
- Go to https://dashboard.render.com
- Wait for "Deploy live" (2-3 minutes)

### Step 3: Test
- Visit: https://ethiopian-airlines-dashboard.onrender.com
- Click: Flight Load → Route Analysis
- Upload: routeanalysis.xlsx
- View: Charts and metrics

---

## ✅ What You Get

### 6 Metric Cards
1. Total Routes
2. Total Passengers (with growth %)
3. Previous Week
4. Top Route (with city/country)
5. Busiest Day
6. Week Period

### 5 Interactive Charts
1. Top 10 Destinations (Bar)
2. Daily Passenger Trend (Line)
3. Current vs Previous Week (Bar)
4. Passenger Distribution (Doughnut)
5. Top 10 Growth Rates (Horizontal Bar)

### Features
- ✅ Airport code identification (ACC → Accra, Ghana)
- ✅ 2,000+ airports in database
- ✅ Week-over-week growth tracking
- ✅ Interactive hover tooltips
- ✅ Ethiopian Airlines branding
- ✅ Mobile responsive

---

## 📊 Tested Results

**Your Excel File (21sep-28sep25):**
- 82 routes parsed ✅
- 223 total passengers ✅
- +5.69% growth ✅
- Top route: ACC (Accra, Ghana) ✅
- All charts working ✅

---

## 🔧 Files Changed

**New Files:**
- src/utils/airport_lookup.py
- src/models/route_analysis.py
- src/routes/route_analysis.py
- src/static/flight-load-route-analysis.html
- src/static/flight-load-menu.html
- src/static/flight-load-factor.html

**Updated Files:**
- src/main.py
- src/static/index.html

---

## 🎯 Navigation Structure

```
Home
├── Sales Report
└── Flight Load (menu)
    ├── Load Factor
    └── Route Analysis ← NEW!
```

---

## 📝 Excel Format

**Required Structure:**
```
Row 1: Empty
Row 2: POINTS | Date1 | Date2 | ... | GRAND TOTAL | PREVIOUS WEEK | VARIANCE
Row 3+: CODE  | pax1  | pax2  | ... | total       | prev          | var
```

**Supported:**
- .xlsx and .xls files
- Multiple sheets (uses active sheet)
- Any date format
- Missing GRAND TOTAL (auto-calculated)

---

## ❓ Troubleshooting

**Charts not showing?**
- Check browser console (F12)
- Verify upload was successful
- Check Render logs

**404 Not Found?**
- Verify GitHub push completed
- Check Render deployment finished
- Clear browser cache

**Airport shows "Unknown"?**
- Code not in database (2,000+ included)
- Can add custom codes if needed

---

## 📞 Need Help?

See **DEPLOYMENT_GUIDE.md** for:
- Detailed instructions
- Troubleshooting guide
- API documentation
- Security features
- Future enhancements

---

**Ready to Deploy!** 🎉

