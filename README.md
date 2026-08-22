# AI Course Recommender

Welcome to the **AI Course Recommender** project! This platform is designed to assist Kenyan Form 4 graduates in discovering university and college courses that match their KCSE results and personal interests using AI-powered insights.

## project Overview

The project is a full-stack application consisting of:
- **Frontend**: A modern React application built with Vite and Vanilla CSS.
- **Backend**: A robust Django REST Framework (DRF) API integrated with Supabase for authentication and LangGraph for AI recommendation workflows.

### Key Features
- **AI-Powered Recommendations**: Real-time course suggestions based on actual KUCCPS requirements and student profiles.
- **Secure Authentication**: Integrated with Supabase for reliable user management and role-based access.
- **Admin Dashboard**: Comprehensive tools for managing users, viewing analytics, and monitoring AI chat logs.
- **Academic Tracking**: Students can manage their KCSE results and track their eligibility for various courses.

---

## 🏗️ Project Structure

```text
ai-course-recommender/
├── backend/            # Django REST Framework API
│   ├── apps/           # Modular Django applications
│   ├── core/           # Project configuration (settings, urls)
│   └── scripts/        # Data scraping and seeding utilities
├── frontend/           # React + Vite frontend
│   ├── src/            # Application source code
│   └── public/         # Static assets
└── README.md           # This file
```

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: >= 20.x
- **Python**: >= 3.12
- **PostgreSQL**: >= 14
- **Supabase Account**: For authentication and database management.

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/ai-course-recommender.git
   cd ai-course-recommender
   ```

2. **Backend Setup**:
   Refer to the [Backend README](./backend/README.md) for detailed instructions on setting up the Django environment, PostgreSQL database, and seeding data.

3. **Frontend Setup**:
   Refer to the [Frontend README](./frontend/README.md) for instructions on installing dependencies and running the Vite development server.

---

## 🧪 Testing & Quality Assurance

KeDira uses a robust multi-layered verification system to ensure reliability.

### 1. Backend Automated Testing (Django)
We have a comprehensive test suite (21 tests) covering Auth, Payments, AI Prompts, and Admin Analytics.

**Command to run tests:**
```bash
# From the root directory:
cd backend
venv/Scripts/python.exe run_tests.py
```

**What to expect (OK Status):**
- A green `✨ ALL TESTS PASSED SUCCESSFULLY! ✨` banner.
- All 21 tests should report `OK`.

### 2. Frontend Manual Verification (React)
As the frontend handles real-time WebSocket communication and complex UI states, we recommend manual smoke testing.

**Checklist:**
- [ ] **Auth**: Login via Supabase and verify dashboard access.
- [ ] **AI Recommendation**: Complete the 6-step prompt wizard; verify WebSocket status updates (0% -> 100%).
- [ ] **Payments**: Trigger an upgrade to "Mentor Elite" and verify M-Pesa STK push request is sent.
- [ ] **Admin Dashboard**: Verify analytics cards (conversion rates, usage trends) load with live data.

### 3. Integration "Golden Path"
The most critical test is the full flow:
`Sign Up` -> `Submit AI Prompt` -> `Trigger Limit (Explorer)` -> `Upgrade via M-Pesa` -> `Unlock Unlimited Prompts`.

---

## 🛠️ Technology Stack

- **Frontend**: React, Vite, Vanilla CSS, React Router, Axios.
- **Backend**: Django, Django REST Framework, LangGraph, OpenAI (GPT-4o-mini).
- **Database & Auth**: PostgreSQL, Supabase.
- **Deployment**: (e.g., Netlify for Frontend, Railway/Render for Backend - *Update as needed*).

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:
1. Create a feature branch: `feature/your-feature_YYYYMMDD`
2. Follow the established code style and naming conventions.
3. Ensure all tests pass before submitting a Pull Request.
4. Provide a clear description of your changes in the PR.

---

## 📝 License

This project is licensed under the [MIT License](LICENSE) (or specify your license).
