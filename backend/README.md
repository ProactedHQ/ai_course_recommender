# AI Course Recommender - Backend

Django REST Framework backend for the AI Course Recommender system. Provides KCSE-based course recommendations using KUCCPS data.

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python** >= 3.12
- **PostgreSQL** >= 14
- **pip** (Python package manager)

### 2. Database Setup

Create the PostgreSQL database and user:

```bash
psql -U postgres
```

```sql
CREATE DATABASE ai_course_recommeder;
CREATE USER proacted_admin WITH PASSWORD 'ProActEd2026';
ALTER ROLE proacted_admin SET client_encoding TO 'utf8';
ALTER ROLE proacted_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE proacted_admin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ai_course_recommeder TO proacted_admin;

-- Connect to database and grant schema permissions
\c ai_course_recommeder
GRANT ALL PRIVILEGES ON SCHEMA public TO proacted_admin;
GRANT CREATE ON DATABASE ai_course_recommeder TO proacted_admin;
ALTER SCHEMA public OWNER TO proacted_admin;
\q
```

### 3. Installation

```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
# Recommended: Username: ProActEd, Email: proacted641@gmail.com, Password: ProActEd
```

### 4. Seed Database

Populate with KCSE subjects, KUCCPS institutions, and cluster groups:

```bash
python manage.py seed_data
```

**Expected Output:**
- ✅ 31 KCSE Subjects
- ✅ 499 KUCCPS Institutions
- ✅ 20 Cluster Groups

📖 **Detailed Seeding Guide**: See [SEEDING_GUIDE.md](./SEEDING_GUIDE.md)

### 5. Run Development Server

```bash
python manage.py runserver
```

Server will be available at: http://localhost:8000

---

## 📊 Database Models

### Users App
- **CustomUser**: Extended user model with student/admin flags

### Students App
- **StudentProfile**: KCSE student details (index number, year, mean grade)
- **Subject**: KCSE subjects (101-English, 121-Math, etc.)
- **AcademicResult**: Student grades per subject
- **StudentAttribute**: Skills, interests, hobbies, learning styles
- **CareerGoal**: Student career aspirations

### Universities App
- **Institution**: Universities and colleges (UoN, JKUAT, etc.)
- **ClusterGroup**: KUCCPS clusters (Law, Engineering, Medicine, etc.)
- **Programme**: Degree/diploma courses
- **ProgrammeRequirement**: Subject prerequisites per programme
- **CutOffPoint**: Historical weighted cluster points

---

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - JWT token login
- `POST /api/auth/refresh/` - Refresh JWT token

### Universities
- `GET /api/institutions/` - List institutions (search: name, code, location)
- `GET /api/programmes/` - List programmes (search: name, kuccps_code)
- `GET /api/clusters/` - List cluster groups

### Students
- `GET /api/subjects/` - List all KCSE subjects
- `GET/POST /api/profiles/` - Student profile (authenticated)
- `GET/POST /api/grades/` - Academic results (authenticated)

**API Documentation**: Visit http://localhost:8000/api/ when server is running

---

## 🗂️ Project Structure

```
backend/
├── apps/
│   ├── students/          # Student-related models and APIs
│   ├── universities/      # Institution and programme models
│   └── users/             # Custom user authentication
├── course_recomeder_backend/
│   ├── settings.py        # Django settings
│   └── urls.py           # URL routing
├── scripts/
│   ├── scrape_kuccps_institutions.py  # KUCCPS web scraper
│   ├── institutions_data.json         # Scraped data (499 institutions)
│   ├── clear_seed_data.py            # Database cleanup
│   └── validate.py                    # Data validation
├── manage.py
├── requirements.txt
├── README.md              # This file
└── SEEDING_GUIDE.md      # Detailed seeding instructions
```

---

## 🧪 Testing & Validation

### Validate Seed Data

```bash
python manage.py shell < scripts/validate.py
```

### Django Admin

Access admin panel at http://localhost:8000/admin
- Username: `ProActEd` (or your superuser)
- Password: `ProActEd` (or your password)

### Check API

```bash
# Get all subjects
curl http://localhost:8000/api/subjects/

# Get all institutions
curl http://localhost:8000/api/institutions/

# Get all clusters
curl http://localhost:8000/api/clusters/
```

---

## 🛠️ Development

### Adding New Features

1. **Create feature branch**: `git checkout -b feature/your-feature_YYYYMMDD`
2. **Make changes** in appropriate app directory
3. **Create/update migrations**: `python manage.py makemigrations`
4. **Run migrations**: `python manage.py migrate`
5. **Test thoroughly**
6. **Submit PR** with clear description

### Code Style

- Follow PEP 8
- Use meaningful variable/function names
- Add docstrings to models and views
- Keep serializers in `serializers.py`
- Keep views in `views.py`

### Database Changes

After model changes:
```bash
python manage.py makemigrations
python manage.py migrate
```

To reset database (⚠️ destructive):
```bash
python manage.py flush
python manage.py migrate
python manage.py seed_data
```

---

## 📦 Dependencies

Key packages (see `requirements.txt` for full list):
- **Django 6.0** - Web framework
- **djangorestframework 3.16.1** - REST API
- **djangorestframework-simplejwt 5.5.1** - JWT authentication
- **psycopg2-binary 2.9.11** - PostgreSQL adapter
- **django-cors-headers 4.9.0** - CORS handling
- **beautifulsoup4 4.12.3** - Web scraping (for KUCCPS data)
- **requests 2.32.3** - HTTP library

---

## 🔒 Security Notes

- ⚠️ **DEBUG = True** in settings.py - Change to False in production
- ⚠️ **SECRET_KEY** is exposed - Generate new one for production
- ⚠️ **Database credentials** in settings.py - Use environment variables in production
- ✅ **CORS** is configured for localhost:5173 (React dev server)

---

## 🚢 Deployment

Before deploying to production:

1. Set `DEBUG = False` in settings.py
2. Generate new `SECRET_KEY`
3. Move database credentials to environment variables
4. Update `ALLOWED_HOSTS`
5. Configure CORS for production frontend URL
6. Set up static file serving
7. Use production-grade WSGI server (gunicorn, uWSGI)

---

## 🐛 Troubleshooting

### Database Connection Errors
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in `settings.py`
- Ensure database exists: `psql -l | grep ai_course_recommeder`

### Migration Errors
```bash
# Reset migrations (⚠️ destroys data)
python manage.py migrate --fake students zero
python manage.py migrate --fake universities zero
python manage.py migrate
```

### Seed Data Issues
See [SEEDING_GUIDE.md](./SEEDING_GUIDE.md) for comprehensive troubleshooting

---

## 📚 Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **DRF Documentation**: https://www.django-rest-framework.org/
- **KUCCPS Website**: https://students.kuccps.net/
- **Project Design Docs**: See main repository

---

## 🤝 Contributing

1. Review project architecture and design documents
2. Follow the branching workflow (feature branches)
3. Consult [SEEDING_GUIDE.md](./SEEDING_GUIDE.md) for database seeding
4. Write clear commit messages
5. Submit PRs with detailed descriptions
6. Ensure tests pass and data validates

---

## 📝 License

See main repository for license information.
