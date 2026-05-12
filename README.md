# 🏍️ Boda Management & Security System (Django Backend)

A **production-grade backend system** for managing boda riders, guest riders, stages, fines, tracking, security monitoring, and real-time operations.

This system is built using **Django + Django REST Framework** with scalable architecture supporting:
- Role-based access control
- Real-time tracking (WebSockets)
- Background processing (Celery)
- High-performance caching (Redis)
- Security monitoring & fraud detection

---

# 🚀 Core Features

## 👤 User Management
- Custom user model (no email dependency)
- Role-based system:
  - Super Admin
  - Stage Chairman
  - Stage Secretary
  - Stage Defense
  - Rider
  - Guest Rider

---

## 🏍️ Rider System
- Registered riders linked to stages
- Guest riders tracked without stage assignment
- Profile management
- Identity verification
- Location tracking

---

## 📍 Live Tracking System
- Real-time GPS tracking
- Movement history logs
- Stage entry/exit monitoring
- Suspicious movement detection

---

## 💰 Fines System
- Automated fine issuance
- Guest rider penalties
- Rider penalties
- Payment tracking
- Fine categories:
  - Speeding
  - Illegal stage usage
  - Suspicious activity
  - Blacklist violation

---

## 🏢 Stage Management
- Stage registration system
- Leadership assignment:
  - Chairman
  - Secretary
  - Defense
- Geographic mapping
- Rider allocation per stage

---

## 🔐 Security System
- Suspicious activity scoring
- Auto-blacklisting system
- Fraud detection engine
- Security alerts

---

## 📢 Notifications System
- SMS notifications
- In-app alerts
- Real-time event notifications
- Fine alerts
- Security warnings

---

## 📡 Real-Time Features
- WebSocket-based live tracking
- Instant notification delivery
- Admin live dashboard updates

---

## 📊 Analytics Module
- Rider activity analytics
- Stage performance reports
- Security statistics
- Fine collection reports

---

## 📄 Announcements System
- Admin announcements
- Security alerts
- General communication
- Emergency alerts (death, incidents, meetings)

---

# 🧱 System Architecture

---

# ⚙️ Tech Stack

## Backend
- Django 4+
- Django REST Framework

## Database
- PostgreSQL (recommended)

## Background Processing
- Celery
- Redis (broker + cache)

## Real-Time Communication
- Django Channels (WebSockets)

## Caching Layer
- Redis

---

# 🔐 Role-Based Access Control

The system uses **strict role-based access control (RBAC)**.

| Role | Permissions |
|------|-------------|
| Super Admin | Full system access |
| Stage Chairman | Manage stage + riders oversight |
| Stage Secretary | Administrative reporting |
| Stage Defense | Security enforcement |
| Rider | Self-service profile + tracking |
| Guest Rider | Limited access + monitoring only |

---

# 🏍️ Rider System Design

## Registered Riders
- Assigned to a stage
- Full profile with verification
- Can receive fines
- Can be tracked in real-time

## Guest Riders
- Not assigned to any stage
- Fully tracked via GPS
- Higher security monitoring
- Can receive fines
- Can be blacklisted

---

# 📍 Tracking System

## Features
- Real-time GPS updates
- Movement history logs
- Stage entry/exit detection
- Suspicious behavior detection

## Powered by
- WebSockets (live updates)
- Redis pub/sub
- Celery background processing

---

# 💰 Fines System

## Fine Triggers
- Speed violations
- Illegal stage usage
- Suspicious movement patterns
- Unregistered guest rider activity
- Security flags

## Workflow
1. Event detected (tracking/security)
2. Fine generated (automated or manual)
3. Stored in database
4. Notification sent (Celery)
5. Payment tracked

---

# 🔐 Security System

## Core Features
- Fraud detection engine
- Suspicious activity scoring
- Auto-blacklisting system
- Real-time alerts

## Risk Scoring
Each user has:
- `suspicious_activity_score`
- Blacklist status
- Security event history

---

# 📡 Real-Time System

## WebSockets Used For:
- Live rider tracking
- Security alerts
- Admin dashboard updates
- Instant notifications

---

# 📢 Notifications System

## Types
- Fine alerts
- Security warnings
- Stage announcements
- System alerts

## Delivery Methods
- WebSocket (real-time)
- SMS (future integration)
- In-app notifications

---

# 📊 Analytics System

## Reports
- Rider activity reports
- Stage performance analytics
- Fine collection statistics
- Security event summaries

---

# 📦 Installation

## 1. Clone Repository

```bash
git clone https://github.com/calvinoke/Boda-django-backend.git
cd Boda-django-backend

2. Create Virtual Environment
python -m venv env
source env/bin/activate   # Mac/Linux
env\Scripts\activate      # Windows

3. Install Dependencies
pip install -r requirements.txt

4. Run Migrations
python manage.py makemigrations
python manage.py migrate

5. Create Super User
python manage.py createsuperuser

6. Run Development Server
python manage.py runserver

⚡ Background Services Setup
Start Redis

Start Celery Worker
celery -A config worker -l info
Start Celery Beat (Scheduled Tasks)
celery -A config beat -l info

🔌 API Base URL
/api/

🧠 Future Enhancements
Flutter mobile application
AI-based fraud detection system
License plate recognition (camera integration)
Geo-fencing for stages
Payment integration system
National boda registry integration

👨‍💻 Author

Developed by Calvin Backend Systems

📜 License

MIT License – for educational and production use.

# 🧠 System Architecture Diagram

Below is the high-level architecture of the system:
                ┌──────────────────────┐
                │   Flutter Mobile App │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   Django REST API    │
                │  (All 13 Apps)       │
                └───────┬───────┬──────┘
                        │       │
    ┌───────────────────┘       └────────────────────┐
    ▼                                                ▼



---

# ⚡ 2. REAL-TIME EVENT SYSTEM (VERY IMPORTANT)

This is what makes your system “Uber-level boda system”.

---

## 📡 WebSocket Event Types

Add this section:

```md
# 📡 Real-Time WebSocket Events

The system uses Django Channels for real-time communication.

## 🔔 Event Types

### 1. Rider Location Update
```json
{
  "event": "location_update",
  "user_id": 12,
  "latitude": 0.3476,
  "longitude": 32.5825,
  "timestamp": "2026-05-12T10:00:00Z"
}

2. Guest Rider Tracking Alert
{
  "event": "guest_rider_movement",
  "risk_level": "high",
  "area": "Nakawa",
  "suspicious_activity_score": 80
}

3. Fine Issued Event
{
  "event": "fine_issued",
  "user_id": 12,
  "amount": 50000,
  "reason": "Illegal stage entry"
}

4. Security Alert
{
  "event": "security_alert",
  "severity": "critical",
  "message": "Suspicious rider movement detected"
}


---

# ⚙️ 3. DOCKER SETUP (PRODUCTION READY)

Now we add full infrastructure setup.

---

## 📦 docker-compose.yml

```yaml
version: "3.9"

services:

  backend:
    build: .
    container_name: boda_backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    container_name: boda_db
    environment:
      POSTGRES_DB: boda_db
      POSTGRES_USER: boda_user
      POSTGRES_PASSWORD: boda_pass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7
    container_name: boda_redis
    ports:
      - "6379:6379"

  celery:
    build: .
    container_name: boda_celery
    command: celery -A config worker -l info
    depends_on:
      - redis
      - db
    volumes:
      - .:/app

  celery-beat:
    build: .
    container_name: boda_celery_beat
    command: celery -A config beat -l info
    depends_on:
      - redis
      - db
    volumes:
      - .:/app

volumes:
  pgdata:

# ⚙️ Celery Configuration

Celery is used for background processing:

## Tasks handled:
- Sending notifications
- Processing fines
- Security scoring
- Analytics generation
- Verification workflows

## Broker:
Redis

## Example task:

🔌 6. WEBSOCKETS SETUP (CHANNELS)
# 🔌 WebSockets (Django Channels)

Used for real-time:

- Tracking riders
- Security alerts
- Notifications
- Admin dashboard updates

## Layer:
- Redis channel layer
- Django Channels consumers

# 🧱 Final Stack Overview

📊 7. FINAL PRODUCTION STACK SUMMARY

| Layer | Technology |
|------|------------|
| API | Django REST Framework |
| DB | PostgreSQL |
| Cache | Redis |
| Async Tasks | Celery |
| Real-time | Django Channels |
| Mobile App | Flutter |
| Deployment | Docker |




