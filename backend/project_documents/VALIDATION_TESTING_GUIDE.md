## API Input Validation - Manual Testing Guide

Test the validation by making API requests with invalid data. All invalid requests should return **400 Bad Request** with clear error messages.

---

### Prerequisites

1. Start the development server:
   ```bash
   cd backend
   python manage.py runserver
   ```

2. Have `curl` or Postman installed

---

### Test 1: User Registration - Short Password

**Endpoint**: `POST /api/auth/register/`

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "12345"
  }'
```

**Expected Response** (400 Bad Request):
```json
{
  "password": ["Password must be at least 8 characters long."]
}
```

---

### Test 2: User Registration - Duplicate Email

First, create a user with a valid email. Then try again with the same email:

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser2",
    "email": "test@example.com",
    "password": "ValidPass123"
  }'
```

**Expected Response** (400 Bad Request):
```json
{
  "email": ["A user with this email already exists."]
}
```

---

### Test 3: Student Profile - Invalid KCSE Year

**Endpoint**: `POST /api/profiles/`  
**Auth**: Required (use JWT token)

```bash
curl -X POST http://localhost:8000/api/profiles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "kcse_year": 1900,
    "kcse_index_number": "12345678"
  }'
```

**Expected Response** (400 Bad Request):
```json
{
  "kcse_year": ["KCSE Year must be between 1980 and 2026"]
}
```

---

### Test 4: Academic Result - Invalid Grade

**Endpoint**: `POST /api/grades/`  
**Auth**: Required (must have student profile)

```bash
curl -X POST http://localhost:8000/api/grades/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "subject": 1,
    "grade": "F"
  }'
```

**Expected Response** (400 Bad Request):
```json
{
  "grade": ["Invalid grade. Choices are: A, A-, B+, B, B-, C+, C, C-, D+, D, D-, E"]
}
```

---

### Test 5: Academic Result - Duplicate Subject

First add a grade for a subject, then try to add another grade for the same subject:

```bash
# First request (should succeed)
curl -X POST http://localhost:8000/api/grades/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "subject": 1,
    "grade": "A"
  }'

# Second request (should fail)
curl -X POST http://localhost:8000/api/grades/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "subject": 1,
    "grade": "B+"
  }'
```

**Expected Response** (400 Bad Request):
```json
{
  "subject": ["You have already added a result for this subject."]
}
```

---

### Test 6: Academic Result - Valid Grade (Should Pass)

```bash
curl -X POST http://localhost:8000/api/grades/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "subject": 2,
    "grade": "A-"
  }'
```

**Expected Response** (201 Created):
```json
{
  "id": 1,
  "subject": 2,
  "subject_name": "Kiswahili",
  "grade": "A-",
  "points": 11
}
```

**✅ Note**: Points are automatically calculated (A- = 11)

---

### Test 7: Student Profile - Invalid Mean Grade

```bash
curl -X POST http://localhost:8000/api/profiles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "kcse_year": 2024,
    "mean_grade": "X",
    "kcse_index_number": "12345678"
  }'
```

**Expected Response**(400 Bad Request):
```json
{
  "mean_grade": ["Invalid mean grade. Choices are: A, A-, B+, B, B-, C+, C, C-, D+, D, D-, E"]
}
```

---

## Success Criteria

✅ All invalid data is rejected with 400 Bad Request  
✅ Error messages clearly explain what went wrong  
✅ Valid data is accepted and processed correctly  
✅ Grade points are calculated automatically  
✅ Duplicate subjects are prevented

---

## Notes

- **JWT Authentication**: Get token first via `/api/auth/login/`
- **Student Profile Required**: Create profile before adding grades
- **Points Auto-Calculation**: A=12, A-=11, ..., E=1
