# River Basin Hydrological Event Platform

# Overview

This project implements a Django-based hydrological event analysis platform that ingests hourly rainfall and temperature data for multiple river basins, detects rainfall events, and exposes analytics APIs for querying observations and detected events.

The system includes:

• Data ingestion pipeline for CSV datasets  
• Rainfall event detection algorithm  
• REST APIs for querying observations and events  
• Redis caching for high-traffic endpoints  

## Tech Stack

Backend: Django + Django REST Framework  
Database: MySQL  
Caching: Redis  
Language: Python 3.x  

### Project Setup Instructions

1. **Clone the repository**

```bash
git clone (https://github.com/ShaliniMS482/River-Basin-Platform.git)
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate   # For Linux/macOS
venv\Scripts\activate     # For Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure database**

```bash
Update database settings in settings.py for MySQL.
```

5. **Run migrations**

```bash
python manage.py migrate
```

6. **Start Redis server**

```bash
redis-server
```

7. **Run the Django server**

```bash
python manage.py runserver
```
