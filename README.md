# Ethiopian Airlines Dashboard

A comprehensive web-based dashboard for Ethiopian Airlines flight operations, sales analytics, load factor analysis, and route forecasting.

## Features

### 1. Sales Analytics
- Upload daily sales reports (Excel format)
- View revenue and passenger trends
- Interactive charts and visualizations
- Admin authentication required for data upload

### 2. Flight Load Factor Analysis
- Upload flight load data (Excel format)
- Track load factors for flights 620 (inbound) and 621 (outbound)
- Dynamic date range filtering
- Business and economy class breakdown
- Accurate passenger calculations

### 3. Route Analysis
- Upload route analysis data (Excel format)
- Track passenger numbers by destination
- Weekly comparisons and variance analysis
- Historical data tracking

### 4. Manifest Integration (NEW)
- Upload daily flight manifests with actual passenger data
- Smart override logic: Manifest data overrides Excel forecasts
- Route breakdown by destination
- Automatic load factor calculations

### 5. Manual Forecast Interface (NEW)
- Excel-friendly data entry interface
- Select date range and direction (inbound/outbound)
- Dynamic table with date columns
- Airport dropdown + add new airports
- Copy entire table to Excel with one click
- Color-coded cells:
  - 🟢 Green = Manifest-confirmed (actual data)
  - 🟡 Yellow = Forecast (manual entry)
- Data persistence across sessions

## Technology Stack

- **Backend**: Python 3.11, Flask 3.0
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js
- **Excel Processing**: openpyxl
- **Deployment**: Render.com

## Project Structure

```
ethiopian-airlines-dashboard/
├── src/
│   ├── models/
│   │   ├── user.py              # User and admin models
│   │   ├── sales.py             # Sales data model
│   │   ├── flight_load.py       # Flight load records
│   │   ├── route_analysis.py    # Route analysis data
│   │   └── manifest.py          # Manifest and forecast models (NEW)
│   ├── routes/
│   │   ├── user.py              # User authentication
│   │   ├── admin_fixed.py       # Admin panel
│   │   ├── sales_working.py     # Sales endpoints (with auth)
│   │   ├── charts_redesigned.py # Chart data endpoints
│   │   ├── flight_load.py       # Flight load endpoints
│   │   ├── route_analysis.py    # Route analysis endpoints
│   │   └── manifest.py          # Manifest and forecast endpoints (NEW)
│   ├── static/
│   │   ├── index.html           # Home page
│   │   ├── dashboard.html       # Sales dashboard
│   │   ├── flight-load-menu.html        # Flight load menu
│   │   ├── flight-load-factor.html      # Load factor page
│   │   ├── flight-load-route-analysis.html  # Route analysis page
│   │   ├── forecast-interface.html      # Manual forecast page (NEW)
│   │   └── manifest-dashboard.html      # Manifest upload page (NEW)
│   ├── __init__.py
│   └── main.py                  # Flask application
├── requirements.txt             # Python dependencies
├── render.yaml                  # Render deployment config
├── .gitignore
└── README.md                    # This file
```

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/aljbartee-ui/ethiopian-airlines-dashboard.git
cd ethiopian-airlines-dashboard
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python -m src.main
```

5. Open browser to `http://localhost:5000`

### Deployment to Render

1. Push code to GitHub
2. Connect repository to Render
3. Render will automatically:
   - Create PostgreSQL database
   - Install dependencies
   - Run database migrations
   - Start the application

## Usage

### Admin Access

Default admin credentials:
- **Username**: `al.jbartee@gmail.com`
- **Password**: `B1m2a3i4!`

### Uploading Data

1. **Sales Report**:
   - Go to Sales Dashboard
   - Login as admin
   - Upload Excel file with columns: Date, Revenue, Passengers

2. **Flight Load Factor**:
   - Go to Flight Load → Load Factor
   - Upload Excel file with flight 620/621 data
   - Data stored as forecast (can be overridden by manifest)

3. **Route Analysis**:
   - Go to Flight Load → Route Analysis
   - Upload Excel file with route data

4. **Flight Manifest**:
   - Go to Flight Load → Manifest Dashboard
   - Upload manifest with actual passenger data
   - Overrides forecast for that specific date

### Manual Forecast Entry

1. Go to Flight Load → Forecast Interface
2. Select date range (start and end dates)
3. Choose direction (inbound or outbound)
4. Click "Load Data"
5. Enter passenger numbers for each airport/date
6. Click "Save Forecast"
7. Use "Copy to Excel" to export data

### Smart Override Logic

```
Excel Upload → Forecast Data (Yellow)
↓
Manifest Upload → Actual Data (Green, overrides forecast)
↓
Excel Re-upload → Updates forecasts only (does NOT override manifest)
```

## API Endpoints

### Sales
- `POST /api/sales/login` - Admin login
- `POST /api/sales/upload` - Upload sales data (admin only)
- `GET /api/sales/data` - Get sales data (admin only)

### Flight Load
- `POST /flight-load/api/upload` - Upload load factor data
- `GET /flight-load/api/data` - Get load factor data

### Route Analysis
- `POST /flight-load/api/route-analysis/upload` - Upload route data
- `GET /flight-load/api/route-analysis/data` - Get route data

### Manifest (NEW)
- `POST /flight-load/api/manifest/upload` - Upload manifest
- `GET /flight-load/api/manifest/data` - Get manifest data

### Forecast (NEW)
- `POST /flight-load/api/forecast/save` - Save manual forecast
- `GET /flight-load/api/forecast/data` - Get combined forecast + manifest data

### Airports (NEW)
- `GET /flight-load/api/airports/list` - List airports
- `POST /flight-load/api/airports/add` - Add new airport

## Database Models

### DailyManifest
- Stores actual passenger data from manifests
- Includes route breakdown by destination
- Calculates load factors automatically
- One record per flight per date

### RouteForecast
- Stores manual forecast data
- Separate from manifest data
- One record per airport per date per direction

### AirportMaster
- Master list of airport codes
- Used for dropdown in forecast interface
- 10 default airports pre-loaded

## Color Scheme (Ethiopian Airlines Brand)

- **Primary Green**: `#2d5016`
- **Light Green**: `#4a7c2a`
- **Dark Green**: `#1a3009`
- **Yellow**: `#ffd700`
- **Red**: `#dc143c`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

Proprietary - Ethiopian Airlines

## Support

For issues or questions, contact: al.jbartee@gmail.com

## Version History

- **v2.0** (November 2024)
  - Added manifest integration
  - Added manual forecast interface
  - Implemented smart override logic
  - Added Excel-friendly copy/paste
  - Enhanced Ethiopian Airlines branding
  - Fixed calculation accuracy
  - Added sales authentication

- **v1.0** (Initial Release)
  - Sales analytics
  - Flight load factor analysis
  - Route analysis
  - Basic admin panel

