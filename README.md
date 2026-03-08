# River Basin Hydrological Event Platform

# Overview

This project implements a Django-based hydrological event analysis platform that ingests hourly rainfall and temperature data for multiple river basins, detects rainfall events, and exposes analytics APIs for querying observations and detected events.

The system includes:

• Data ingestion pipeline for CSV datasets  
• Rainfall event detection algorithm  
• REST APIs for querying observations and events  
• Redis caching for high-traffic endpoints  

## Tech Stack

 - Backend: Django + Django REST Framework  
 - Database: MySQL  
 - Caching: Redis  
 - Language: Python 3.x  

### Project Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/ShaliniMS482/River-Basin-Platform.git
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

Update database settings in settings.py for MySQL.

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

#### Design Decisions

1. **Data Model Design (Part A)**

The system is designed to store hydrological observations and detect rainfall events across multiple basins. The schema separates metadata entities from time-series data to maintain flexibility and scalability.

**Basin**

Represents a hydrological basin where environmental observations are recorded.

Fields:

    - basin_id – Unique identifier for the basin

    - name – Basin name

    - metadata – Optional JSON field for storing additional information such as location, region, or descriptive attributes

A basin can have many observations and many rainfall events.

Relationship:

    - One Basin - Many Observations

    - One Basin - Many RainfallEvents

**MeasurementType**

Defines the type of environmental measurement being recorded.

Fields:

    - name – Name of the measurement type (e.g., Rainfall, Temperature)

    - unit – Unit of measurement (e.g., mm/hr, °C)

Separating measurement types allows the system to easily support additional environmental variables in the future.

Relationship:

    - One MeasurementType - Many Observations

**Observation**

Stores time-series environmental measurements collected for each basin.

Fields:

    - basin – Foreign key to Basin

    - measurement_type – Foreign key to MeasurementType

    - timestamp – Time when the observation was recorded

    - value – Measured value

    - source – Optional field indicating the data source

Constraints and indexing:

- **Unique constraint on (basin, measurement_type, timestamp)** ensures that duplicate observations cannot be inserted.

- **Composite index on (basin, timestamp, measurement_type)** improves performance for queries scanning ordered time-series data, which is critical for rainfall event detection.

Relationship:

    - Many Observations - One Basin

    - Many Observations - One MeasurementType

**RainfallEvent**

Represents a detected rainfall event derived from rainfall observations.

Fields:

    - basin – Basin where the event occurred

    - start_timestamp – Event start time

    - end_timestamp – Event end time

    - duration_hours – Duration of the rainfall event

    - peak_value – Maximum rainfall intensity during the event

    - total_volume – Total rainfall accumulated during the event

    - min_dry_gap_used – Minimum dry gap used to segment events

    - detected_at – Timestamp when the event detection was executed

Constraints:

- **Unique constraint on (basin, start_timestamp, min_dry_gap_used)** ensures that the same rainfall event is not stored multiple times for the same basin and segmentation parameter.

Relationship:

    - Many RainfallEvents - One Basin

**Indexing Strategy**

A composite index on: (basin, timestamp, measurement_type) is used on the Observation table.

This index is important because the rainfall event detection algorithm scans time-ordered observations for each basin, and the index significantly improves query performance when filtering and ordering large time-series datasets.

**ER Diagram**

The ER diagram for the system is included in the submission folder: 
    `submission_images/er_diagram.png`

2. **Data Ingestion Pipeline (Part B)**

- **Ingestion Method**

The project implements a Django management command to ingest the provided rainfall and temperature CSV datasets into the database.

The command reads both files, normalizes the timestamps, maps basin identifiers, and inserts the observations into the Observation table.

- **Download Dataset**

Download the provided CSV files from the following link:

https://drive.google.com/drive/folders/147xiXrj-0u7HkvRFlzbAq6h8L_zOsJua

File used:
- january_data_rain.csv
- january_data_temp.csv

**Place Files in Project Directory**

After downloading the files, place them in the root project directory (same location as manage.py).

Example structure:

    river-basin-platform/
    │
    ├── manage.py
    ├── january_data_rain.csv
    ├── january_data_temp.csv
    ├── hydrology/
    ├── settings.py

- **Run the Ingestion Command**

Run the Ingestion Command: 

```bash
python manage.py ingest_observations --rainfall january_data_rain.csv --temperature january_data_temp.csv
```

This command will ingest both rainfall and temperature observations into the database.

- **Sample Output Logs**

Example successful run:

    Ingestion complete
    Rows ingested: 1488
    Rows skipped: 0
    Errors: 0

Example run with errors:

    Row error: {'datetime': 'invalid', 'value': 'abc'} | Error: Invalid datetime format

    Ingestion complete
    Rows ingested: 1486
    Rows skipped: 1
    Errors encountered: 1

Screenshot of the execution log is included in the **submission folder** as:

`submission_images/ingest_observations_report.png`

3. **Django REST API (DRF) (Part C)**

**API Overview**

The platform exposes a set of REST APIs built using **Django REST Framework (DRF)** for managing basins, observations, rainfall events, and hydrological analytics.

All endpoints are accessible under the base path:

`/api/`

A Postman collection containing all API requests is included in the repository:

`postman/river_basin_api_collection.json`

This collection can be imported into Postman to test all endpoints.

- **C1. CRUD APIs**

The following standard CRUD APIs are implemented.

**Basins**

- GET	- /api/basins/	- List all basins
- POST	- /api/basins/ -	Create a basin
- GET	- /api/basins/{id}/	- Retrieve basin details
- PUT	- /api/basins/{id}/	- Update basin
- DELETE	- /api/basins/{id}/ - 	Delete basin

**Observations**

Handles both rainfall and temperature observations.

- GET	- /api/observations/	- List observations
- POST	- /api/observations/	- Create observation
- GET	- /api/observations/{id}/ - 	Retrieve observation
- PUT	- /api/observations/{id}/	- Update observation
- DELETE - 	/api/observations/{id}/	- Delete observation

**Filtering supported:**

- measurement_type
- date range
- value greater than / less than

**Rainfall Events**

Rainfall events are **generated only by the detection endpoint.**

- GET - 	/api/events/	- List events
- GET	/api/events/{id}/	- Retrieve event
- DELETE -	/api/events/{id}/ -	Delete event

**C2. Analytics / Query APIs**

**Timeseries Endpoint**

Retrieve hourly rainfall or temperature observations for a basin within a date range.

- GET /api/basins/{id}/timeseries/?measurement_type=rainfall&from=2019-01-01&to=2019-01-31

Example response:

    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "timestamp": "2019-01-01T10:00:00Z",
                "value": 10.0,
                "unit": "mm",
                "event_id": null
            },
        ]
    }

If the observation does not belong to a rainfall event:

`event_id = null`

**Event Detection Endpoint**

This endpoint scans rainfall observations and detects rainfall events.

- POST - /api/basins/{id}/detect-events/?min_dry_gap_hours=6

Response Example

    {
        "total_events_detected": 13,
        "basin_id": 2,
        "min_dry_gap_hours": 4,
        "scan_start": "2019-01-01T00:00:00Z",
        "scan_end": "2019-01-31T23:00:00Z"
    }

**Idempotency**

Before detection runs, the system deletes any previously detected events for the same: `basin + min_dry_gap_hours`

This ensures **re-running detection does not create duplicate events.**

**Event List Endpoint**

Retrieve all detected events for a basin.

- GET - /api/basins/{id}/events/?min_dry_gap_hours=6&min_total_volume=0.5

Response includes:

    start_timestamp
    end_timestamp
    duration_hours
    peak_value
    total_volume
 
Sample response:

    {
        "id": 26,
        "start_timestamp": "2019-01-31T05:00:00Z",
        "end_timestamp": "2019-01-31T23:00:00Z",
        "duration_hours": 12,
        "peak_value": 0.111615092,
        "total_volume": 0.615154619
    }

**Event Timeseries Endpoint**

Retrieve rainfall observations within a specific event window.

- GET /api/events/{event_id}/timeseries/

Returns the hourly rainfall data between:

start_timestamp - end_timestamp

Sample Respose:

    {
        "timestamp": "2019-01-31T05:00:00Z",
        "value": 0.074410066
    }


**Basin Event Summary**

Provides aggregated statistics across all events for a basin.

- GET /api/basins/{id}/event-summary/

Example response:

    {
        "total_events": 10,
        "mean_duration": 7.9,
        "mean_total_volume": 0.9187411976999998,
        "peak_event": 22,
        "longest_event": 23,
        "min_dry_gap_hours": "6"
    }

**Event Detection Algorithm**

Rainfall events are detected using a **sequential scan algorithm** over ordered rainfall observations.

Algorithm steps:

- Retrieve all rainfall observations for a basin ordered by timestamp.

- Iterate through the observations sequentially.

- When a non-zero rainfall value is encountered and no event is active, a new rainfall event begins.

- While rainfall values remain greater than zero, the current event is extended and statistics are updated.

- When a zero rainfall value is encountered, a dry-hour counter is incremented.

- If the number of consecutive dry hours reaches the configured minimum dry gap threshold, the current event is closed.

- The event is recorded using the last non-zero rainfall timestamp as the event end time.

For each event compute:

    - start_timestamp – first non-zero rainfall observation
    - end_timestamp – last non-zero rainfall observation
    - duration_hours – number of rainfall observations in the event
    - peak_value – maximum rainfall intensity during the event
    - total_volume – sum of rainfall values across the event

- Save the computed event to the RainfallEvent table.

This approach efficiently detects **maximal contiguous rainfall** sequences separated by configurable dry gaps.

**Idempotency**

Before inserting newly detected events, existing events for the same:
(basin, min_dry_gap_hours) are removed. This ensures that re-running the detection process produces consistent results without duplicate events.

**Performance**

Observations are scanned in timestamp order, which is optimized using a composite index on: (basin, timestamp, measurement_type)

This allows efficient sequential reads of time-series data for each basin.

**C3. Pagination & Filtering**

All list endpoints support pagination.

Default page size: 20 records per page

Example: GET /api/events/?page=2

**Search / Filters**

Basin filters: id, name

Observation filters: measurement_type, date range, value greater than, value less than

Event filters: basin, min_dry_gap_hours, min_total_volume, date range

**API Testing**

All endpoints can be tested using the provided Postman collection.

Location: `postman/river_basin_api_collection.json`

Import this file into Postman to access pre-configured API requests.

4. **Redis Caching (Part D)**

**Cache Strategy**

Redis is used as a caching backend to improve the performance of high-traffic analytical endpoints that frequently query large observation datasets. Caching reduces repeated database queries and significantly improves API response time.

**Cached Endpoints**

The following endpoints are cached.

1. **Timeseries Endpoint**

Returns hourly observations for a basin within a date range.

- GET /api/basins/{id}/timeseries/

Cache key format:

basin:{id}:timeseries:{measurement_type}:{from}:{to}

Example:

basin:2046:timeseries:rainfall:2019-01-01:2019-01-31

2. **Event List Endpoint**

Returns detected rainfall events for a basin.

- GET /api/basins/{id}/events

Cache key format:

basin:{id}:events:{min_dry_gap_hours}

Example:

basin:2046:events:6

3. **Basin Event Summary Endpoint**

Returns aggregated rainfall event statistics.

- GET /api/basins/{id}/event-summary

Cache key format:

basin:{id}:event-summary

**Cache Expiry (TTL)**

Cached responses are stored in Redis with a **Time To Live (TTL) of 600 seconds (10 minutes).**

This ensures cached data expires automatically and is refreshed periodically.

**Cache Invalidation**

Cache entries are invalidated when:

- New observations are ingested for a basin
- Rainfall event detection is executed

When either operation occurs, all cache keys related to the basin are cleared. This ensures that subsequent API requests retrieve fresh data.

**Redis Setup**

Start the Redis server before running the application: redis-server

5. **Testing and Code Quality (Part E)**

The project includes unit tests implemented using **pytest and pytest-django**.

Coverage includes:
- Event detection logic
- Timeseries API responses
- CSV ingestion idempotency
- Event re-detection idempotency

**Run the full test suite with:**

```bash
pytest
```