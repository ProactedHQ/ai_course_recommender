# Database Seeding Guide

This guide explains how to populate the database with comprehensive KUCCPS/KCSE data including subjects, institutions, and cluster groups.

---

## Overview

The seeding system provides:
- **31 KCSE Subjects** across 5 groups (Compulsory, Sciences, Humanities, Technical, Languages/Business)
- **499 KUCCPS Institutions** (42 public universities, 29 private universities, 428 TVET colleges)
- **20 Official Cluster Groups** (CLUSTER_1 through CLUSTER_20)

---

## Prerequisites

1. **Database setup**: Ensure PostgreSQL is running with the `ai_course_recommeder` database created
2. **Dependencies installed**: Run `pip install -r requirements.txt`
3. **Migrations applied**: Run `python manage.py migrate`

---

## Quick Start

### Option 1: Standard Seeding (Recommended for New Setup)

```bash
cd backend
python manage.py seed_data
```

This will populate your database with all seed data.

**Expected Output:**
```
✅ Subjects seeded: 31 total
✅ Institutions seeded: 499 total
✅ Clusters seeded: 20 total
```

---

### Option 2: Clean Reseed (for existing database with old data)

If your database already has seed data and you want to start fresh:

```bash
# Step 1: Clear existing data
python manage.py shell < scripts/clear_seed_data.py

# Step 2: Run seed command
python manage.py seed_data
```

---

## Advanced: Scraping Fresh Institution Data

The institution data is scraped from the official KUCCPS website. To fetch the latest data:

```bash
cd backend/scripts
python scrape_kuccps_institutions.py
```

**Output**: `institutions_data.json` with ~499 institutions

The seed command automatically uses this JSON file if it exists, otherwise it falls back to hardcoded data.

---

## Validation

After seeding, verify the data was populated correctly:

```bash
python manage.py shell < scripts/validate.py
```

**Expected Output:**
```
Subjects: 31 total
  GP1: 5
  GP2: 4
  GP3: 5
  GP4: 12
  GP5: 5

Institutions: 499 total
  PUBLIC: 42
  PRIVATE: 29
  TVET: 428

Clusters: 20 total
```

---

## Seed Data Details

### Subjects (31)

| Group | Count | Examples |
|-------|-------|----------|
| GP1 (Compulsory) | 5 | English, Kiswahili, Math A, Math B, Kenya Sign Language |
| GP2 (Sciences) | 4 | Biology, Physics, Chemistry, General Science |
| GP3 (Humanities) | 5 | History, Geography, CRE, IRE, HRE |
| GP4 (Technical) | 12 | Agriculture, Computer Studies, Aviation Technology, etc. |
| GP5 (Languages/Business) | 5 | French, German, Arabic, Music, Business Studies |

### Institutions (499)

Scraped from https://students.kuccps.net/institutions/

| Type | Count | Description |
|------|-------|-------------|
| PUBLIC | 42 | Public universities (UoN, JKUAT, KU, etc.) |
| PRIVATE | 29 | Private universities (Strathmore, USIU, etc.) |
| TVET | 428 | Technical colleges and polytechnics |

### Cluster Groups (20)

Official KUCCPS clusters from CLUSTER_1 to CLUSTER_20:
- CLUSTER_1: Law & Related
- CLUSTER_2: Business, Hospitality & Related
- CLUSTER_7: Computing, IT & Related
- CLUSTER_13: Medicine, Health, Veterinary Medicine & Related
- *(and 16 more...)*

---

## Troubleshooting

### Issue: "No module named 'beautifulsoup4'"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "Database connection error"
**Solution**: Verify PostgreSQL is running and credentials in `settings.py` are correct

### Issue: "Subjects count is wrong"
**Solution**: Clear and reseed
```bash
python manage.py shell < scripts/clear_seed_data.py
python manage.py seed_data
```

### Issue: "Institution scraper fails"
**Solution**: The scraper has a fallback mechanism. It will use 21 hardcoded institutions if scraping fails. This is acceptable for development.

---

## File Structure

```
backend/
├── apps/
│   └── students/
│       └── management/
│           └── commands/
│               └── seed_data.py          # Main seed command
├── scripts/
│   ├── scrape_kuccps_institutions.py    # KUCCPS web scraper
│   ├── institutions_data.json           # Scraped data (499 institutions)
│   ├── clear_seed_data.py              # Database cleanup script
│   └── validate.py                      # Validation script
└── requirements.txt                     # Includes beautifulsoup4, requests
```

---

## For Contributors

### Modifying Seed Data

**To add/remove subjects:**
1. Edit `apps/students/management/commands/seed_data.py`
2. Update the `subjects` list (around line 13)
3. Run reseed: `python manage.py shell < scripts/clear_seed_data.py && python manage.py seed_data`

**To update clusters:**
1. Edit `apps/students/management/commands/seed_data.py`
2. Update the `clusters` list (around line 130)
3. Run reseed (same as above)

**To refresh institutions:**
1. Run scraper: `cd scripts && python scrape_kuccps_institutions.py`
2. Verify `institutions_data.json` has correct data
3. Run seed: `python manage.py seed_data`

### Best Practices

- ✅ Always validate after seeding: `python manage.py shell < scripts/validate.py`
- ✅ Use `get_or_create` pattern (prevents duplicates on re-runs)
- ✅ Document any changes to seed data in PR descriptions
- ✅ Test on a separate database before committing changes

---

## Questions?

Refer to the main project documentation or reach out to project maintainers.
