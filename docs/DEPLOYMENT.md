# Deployment Guide - Ethiopian Airlines Dashboard

## Complete Repository Deployment

This guide explains how to deploy the complete Ethiopian Airlines Dashboard to a new GitHub repository and Render.

## What's Included

This repository contains EVERYTHING needed to run the dashboard:

- ✅ All Python backend files (models, routes, main app)
- ✅ All HTML/CSS/JS frontend files
- ✅ Database models and migrations
- ✅ Authentication system
- ✅ Sales analytics
- ✅ Flight load analysis
- ✅ Route analysis
- ✅ Manifest integration (NEW)
- ✅ Manual forecast interface (NEW)
- ✅ Smart override logic
- ✅ Ethiopian Airlines branding
- ✅ Deployment configuration (requirements.txt, render.yaml)

**Total: 40+ files, fully functional**

## Deployment Options

### Option 1: Deploy to New GitHub Repository (Recommended)

1. **Create New Repository on GitHub**
   - Go to: https://github.com/new
   - Name: `ethiopian-airlines-dashboard-v2` (or any name)
   - Description: "Ethiopian Airlines Flight Operations Dashboard"
   - Public or Private: Your choice
   - DO NOT initialize with README (we have one)
   - Click "Create repository"

2. **Upload Files**
   - Download the attached `NEW_REPOSITORY.tar.gz`
   - Extract all files
   - Upload to GitHub:
     - Option A: Use GitHub Desktop
     - Option B: Use git command line
     - Option C: Use GitHub web interface (drag and drop)

3. **Connect to Render**
   - Go to: https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`
   - Click "Create Web Service"
   - Wait 5-10 minutes for deployment

4. **Done!**
   - Your dashboard will be live at: `https://your-app-name.onrender.com`

### Option 2: Replace Existing Repository

1. **Backup Current Repository**
   - Download or clone your current repository
   - Save it somewhere safe

2. **Delete All Files**
   - Go to your GitHub repository
   - Delete all existing files

3. **Upload New Files**
   - Extract `NEW_REPOSITORY.tar.gz`
   - Upload all files to GitHub

4. **Render Auto-Deploys**
   - Render will detect changes
   - Automatically redeploy
   - Wait 5-10 minutes

## File Structure

```
ethiopian-airlines-dashboard/
├── src/
│   ├── models/           (5 files - database models)
│   ├── routes/           (8 files - API endpoints)
│   ├── static/           (20+ files - HTML/CSS/JS)
│   ├── __init__.py
│   └── main.py
├── docs/
│   └── DEPLOYMENT.md     (this file)
├── requirements.txt      (Python dependencies)
├── render.yaml           (Render config)
├── .gitignore
└── README.md
```

## Post-Deployment Steps

### 1. Verify Database Tables

Check Render logs for:
```
✅ Database tables created successfully!
✅ Created 10 default airports
```

### 2. Test All Pages

Visit these URLs:
- `/` - Home page
- `/dashboard` - Sales dashboard
- `/flight-load` - Flight load menu
- `/flight-load/load-factor` - Load factor page
- `/flight-load/route-analysis` - Route analysis
- `/flight-load/forecast` - Forecast interface (NEW)
- `/flight-load/manifest-dashboard` - Manifest dashboard (NEW)

### 3. Test Admin Login

1. Go to Sales Dashboard
2. Login with:
   - Username: `al.jbartee@gmail.com`
   - Password: `B1m2a3i4!`
3. Verify you can upload data

### 4. Test Manifest Integration

1. Go to `/flight-load/forecast`
2. Select date range
3. Enter forecast data
4. Save
5. Upload a manifest for one of the dates
6. Verify that date turns green

## Environment Variables

Render automatically sets:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Session encryption key
- `PORT` - Application port

No manual configuration needed!

## Database

Render creates a PostgreSQL database with these tables:
- `users` - User accounts
- `admin_users` - Admin accounts
- `sales_data` - Sales records
- `flight_load_records` - Load factor data
- `route_analysis_weeks` - Route analysis data
- `route_analysis_uploads` - Upload tracking
- `daily_manifests` - Manifest data (NEW)
- `route_forecasts` - Manual forecasts (NEW)
- `airport_master` - Airport list (NEW)

## Troubleshooting

### If deployment fails:

1. **Check Render logs**
   - Go to Render dashboard
   - Click on your service
   - View logs for errors

2. **Common issues**:
   - Missing requirements.txt → Already included
   - Database connection error → Render handles this
   - Import errors → Check file paths

### If pages don't load:

1. **Check static folder path**
   - main.py should have: `static_folder='static'`
   - NOT: `static_folder='src/static'`

2. **Check routes**
   - All routes should be registered in main.py
   - Blueprints should have correct URL prefixes

### If data doesn't save:

1. **Check database connection**
   - Verify DATABASE_URL is set
   - Check Render logs for database errors

2. **Check authentication**
   - Sales data requires admin login
   - Manifest upload requires admin login

## Updating the Application

To update after deployment:

1. Make changes to files locally
2. Push to GitHub
3. Render auto-deploys (takes 3-5 minutes)
4. Check logs to verify successful deployment

## Backup and Restore

### Backup Database

Render provides automatic backups. To manual backup:
1. Go to Render dashboard
2. Click on database
3. Click "Backups"
4. Create manual backup

### Restore Database

1. Go to Render dashboard
2. Click on database
3. Click "Backups"
4. Select backup to restore

## Security

- Admin credentials stored in code (for demo)
- In production, use environment variables
- Enable HTTPS (Render provides free SSL)
- Use strong SECRET_KEY (Render generates automatically)

## Performance

- Render free tier: 512MB RAM, shared CPU
- Sufficient for moderate traffic
- For high traffic, upgrade to paid tier

## Monitoring

Render provides:
- Real-time logs
- Performance metrics
- Error tracking
- Uptime monitoring

## Support

For deployment issues:
- Check Render documentation: https://render.com/docs
- Contact: al.jbartee@gmail.com

## Summary

**This is a COMPLETE, ready-to-deploy repository.**

Just upload to GitHub, connect to Render, and everything works!

No additional configuration needed. All features included.

