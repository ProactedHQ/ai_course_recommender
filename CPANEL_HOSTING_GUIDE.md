# Project Architecture & cPanel Hosting Guide

This document provides a comprehensive overview of the **AI Course Recommender** project structure and the requirements for hosting it on a cPanel-based environment.

---

## 1. Project Architecture

The project follows a modern decoupled architecture:

### **Frontend (React + Vite)**
- **Technology:** React 19, Vite, Axios, Lucide React, React Router.
- **Authentication:** Integrated with Supabase (Client-side JWT handling).
- **Communication:** Communicates with the Django Backend via REST API.
- **Build Output:** Static HTML/CSS/JS files generated in the `dist/` directory.

### **Backend (Django REST Framework)**
- **Technology:** Django 6.0, Django REST Framework (DRF).
- **Database:** PostgreSQL (currently hosted on Supabase).
- **Authentication:** Custom Supabase JWT Authentication for protected endpoints.
- **Features:**
  - AI Recommendation Engine.
  - PayHero integration (M-Pesa STK push) for subscriptions.
  - Redis for caching and WebSockets (optional support).
  - Swagger/OpenAPI documentation (drf-spectacular).

### **Infrastructure**
- **Hosting Preference:** cPanel (Shared Hosting or VPS).
- **External Services:** 
  - **Supabase:** Used for user management/auth and the PostgreSQL database.
  - **M-Pesa:** Used for payment processing.

---

## 2. Project Structure

```text
ai-course-recommender/
├── frontend/               # React application
│   ├── src/                # Component and logic source files
│   ├── public/             # Static assets
│   ├── .env                # Frontend environment variables
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite build configuration
├── backend/                # Django application
│   ├── apps/               # Custom Django apps (users, students, universities, etc.)
│   ├── course_recomeder_backend/ # Main project settings and configuration
│   ├── static/             # Static files (CSS, JS, Images)
│   ├── templates/          # HTML templates
│   ├── .env                # Backend environment variables
│   ├── requirements.txt    # Python dependencies
│   └── manage.py           # Django management script
└── README.md               # Root documentation
```

---

## 3. Deployment Requirements for cPanel

To host this project successfully on cPanel, ensure your hosting plan meets these requirements:

### **General Requirements**
- **Subdomain/Domain:** You will likely need one domain for the frontend (e.g., `app.example.com` or `example.com`) and another (or a path) for the backend API (e.g., `api.example.com`).
- **SSL Certificate:** Required for both Frontend and Backend (especially for Supabase and M-Pesa integrations).

### **Backend (Python App)**
- **Python Version:** 3.10+ (Recommended).
- **Phusion Passenger:** Required for running Django on cPanel.
- **Virtual Environment:** Must be created through the cPanel "Setup Python App" tool.
- **Environment Variables:** Supported via the cPanel Python interface or a `.env` file.
- **Static File Handling:** Ability to run `python manage.py collectstatic`.

### **Frontend (Static Hosting)**
- **Node.js:** Needed only for building the project (can be done locally before upload).
- **Public Directory:** Usually `public_html` or a subdomain folder.

### **Database & Services**
- **PostgreSQL:** The project uses a remote Supabase DB, so no local cPanel database is strictly required unless you migrate it.
- **Redis:** Required for WebSockets (Channels) and Caching. If your cPanel host doesn't provide Redis, the backend is configured to fallback to in-memory caching and disable WebSockets gracefully.

---

## 4. Step-by-Step Hosting Guide

### **Step 1: Build the Frontend**
1. Navigate to the `frontend/` folder locally.
2. Update `frontend/.env` with your production backend URL:
   ```env
   VITE_API_BASE_URL=https://api.yourdomain.com
   ```
3. Run `npm install` and `npm run build`.
4. Upload the contents of the `frontend/dist/` folder to your domain's root (e.g., `public_html`).

### **Step 2: Set Up Backend (Python App)**
1. Log in to cPanel and search for **"Setup Python App"**.
2. Create a new application:
   - **Python Version:** Select 3.10 or higher.
   - **Application root:** `backend` (or the path where you uploaded the backend files).
   - **Application URL:** `api.yourdomain.com`.
3. After creating the app, copy the command to enter the virtual environment (provided at the top of the interface).
4. Via SSH or cPanel Terminal:
   - Enter the virtual environment.
   - Run `pip install -r requirements.txt`.

### **Step 3: Configure Environment Variables**

> The complete, current list (including `OPENAI_API_KEY`, the `PAYHERO_*` variables and
> `PAYHERO_CALLBACK_SECRET`) is in [SYSTEM_REFERENCE.md §2](./SYSTEM_REFERENCE.md#2-configuration-environment-variables).
> The live `settings.py` reads only the cPanel Python App variables, not `backend/.env`.

Create these variables in your cPanel Python App interface or upload a `.env` file to each directory:

#### **Backend (.env)**
| Key | Description |
|---|---|
| `SECRET_KEY` | A unique, secret string for Django security. |
| `DEBUG` | Set to `False` in production. |
| `ALLOWED_HOSTS` | Comma-separated domains (e.g., `api.yourdomain.com,yourdomain.com`). |
| `DATABASE_URL` | PostgreSQL connection string (from Supabase). |
| `SUPABASE_JWT_SECRET` | Secret key for JWT verification (from Supabase settings). |
| `OPENAI_API_KEY` | OpenAI key for the recommendation engine. |
| `PAYHERO_CHANNEL_ID` | PayHero payment channel ID. |
| `PAYHERO_API_USERNAME` | PayHero API username. |
| `PAYHERO_API_PASSWORD` | PayHero API password. |
| `PAYHERO_CALLBACK_URL` | `https://api.yourdomain.com/api/subscriptions/confirmation/` |
| `PAYHERO_CALLBACK_SECRET` | Long random string that authenticates PayHero callbacks. |

#### **Frontend (.env)**
| Key | Description |
|---|---|
| `VITE_SUPABASE_URL` | Your Supabase Project URL. |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase Anonymous Key. |
| `VITE_API_BASE_URL` | The URL of your backend (e.g., `https://api.yourdomain.com`). |

### **Step 4: WSGI Configuration**
cPanel uses a `passenger_wsgi.py` file. Create this file in your backend root and point it to your Django project:
```python
import os
import sys

# Add your project directory to the sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Django application
from course_recomeder_backend.wsgi import application
```

### **Step 5: Finalize Backend**
In the virtual environment, run:
1. `python manage.py migrate` (To ensure the database is up to date).
2. `python manage.py collectstatic` (To aggregate static files in `STATIC_ROOT`).

---

## 5. Important Notes
- **CORS:** Ensure `CORS_ALLOWED_ORIGINS` in `backend/course_recomeder_backend/settings.py` includes your production frontend URL.
- **WebSockets:** If you need real-time features, you must use a VPS with Daphne/Gunicorn and Redis, as standard cPanel WSGI does not support WebSockets.
