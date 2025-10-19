# Ethiopian Airlines Sales Analytics Dashboard

A modern, interactive web application for visualizing Ethiopian Airlines daily sales reports with dynamic charts and real-time analytics.

![Ethiopian Airlines](https://img.shields.io/badge/Ethiopian%20Airlines-Sales%20Dashboard-5C8C4C)
![Flask](https://img.shields.io/badge/Flask-3.1.1-blue)
![Python](https://img.shields.io/badge/Python-3.11-blue)

---

## 🌟 Features

### 📊 Four Interactive Charts

1. **Sales Report - Time Trend** - Line chart with Daily/Monthly aggregation
2. **Sales by Agent** - Top 10 performing agents bar chart
3. **Sales by Day of Week** - Weekly sales patterns analysis
4. **Sales by Hour** - 24-hour sales distribution

### 🎨 Ethiopian Airlines Branding

- Official color scheme (Green #5C8C4C, Yellow #FCCC2C, Red #C4242B)
- Modern glassmorphism design
- Animated gradient backgrounds
- Responsive mobile-friendly layout

### 🔐 Security

- Admin-only file upload (username: `admin`, password: `admin123`)
- Public read-only chart access
- Session-based authentication
- Secure file handling

### 💰 Currency Display

All revenue displayed in **KWD (Kuwaiti Dinar)**

---

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python3 src/main.py

# Access at http://localhost:5000
```

### Production Deployment

```bash
# Run with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 src.main:app
```

---

## 🌐 Deployment

### Recommended: Render.com (Free)

1. Push code to GitHub
2. Sign up at [Render.com](https://render.com)
3. Create new Web Service from your repo
4. Add persistent disk (1GB) at `/opt/render/project/src/database`
5. Set environment variable: `SECRET_KEY`
6. Deploy!

**Your app will be live at**: `https://your-app.onrender.com`

See [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) for detailed instructions.

---

## 📖 Usage

### Public Users
- View all 4 interactive charts
- Toggle between Revenue/Tickets
- Apply date range filters
- Switch Daily/Monthly view

### Administrators
1. Login (admin/admin123)
2. Upload Excel file (.xlsx)
3. Charts auto-update

---

## 🏗️ Architecture

- **Backend**: Flask 3.1.1 + SQLAlchemy + Gunicorn
- **Database**: SQLite
- **Frontend**: HTML/CSS/JavaScript (Vanilla)
- **Charts**: Custom SVG generation

---

## 📦 Project Structure

```
sales_dashboard/
├── src/
│   ├── main.py                 # Flask application
│   ├── models/                 # Database models
│   ├── routes/                 # API endpoints
│   ├── static/index.html       # Frontend UI
│   └── database/app.db         # SQLite database
├── Procfile                    # Deployment config
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask secret key |
| `FLASK_ENV` | Yes | production/development |

---

## 📊 Excel File Format

Required columns:
- `DATE`, `TIME 24HRS`, `Time`, `INCOME`
- `Issuing agent`, `FOP`, `Ticket Number`, `Day`

---

## 🎯 Features Summary

✅ 4 Interactive Charts  
✅ Ethiopian Airlines Branding  
✅ Admin Upload + Public Viewing  
✅ KWD Currency Display  
✅ Revenue/Tickets Toggles  
✅ Date Range Filtering  
✅ Production Ready  

---

## 📞 Support

- **Admin**: admin / admin123
- **Docs**: See DEPLOYMENT_GUIDE.md
- **Issues**: Check application logs

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: October 19, 2025

Made with ❤️ for Ethiopian Airlines

