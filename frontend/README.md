# AI Course Recommender - Frontend

This is the **frontend** of the AI Course Recommender project, built with **React** and **Vite**.  
The frontend connects to the backend APIs (Django) to provide course recommendations based on user inputs.  

> ⚠️ **Important:** This project is part of the **main `ai-course-recommender` repository**.  
> Contributors should always **refer to the design documents, diagrams, and architecture notes** before implementing changes.

---

## 🚀 Getting Started

### 1. Prerequisites

- **Node.js** >= 24.12.0  
- **npm** (comes with Node.js)  
- Backend API running (see backend repo)  

Check Node and npm versions:

```bash
node -v
npm -v
````

---

### 2. Installation & Setup

1. Clone the **main repository** (frontend is part of it):

```bash
git clone <main-repo-url>
cd ai-course-recommender/frontend
```

2. Install dependencies:

```bash
npm install
```

3. Create `.env` file (already included, but confirm values):

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

4. Start the development server:

```bash
npm run dev
```

The app should now be running at: [http://localhost:5173](http://localhost:5173)
---

### 3. Folder Structure (Must Remain)

```
frontend/
├── src/
│   ├── api/                 # API service wrappers
│   ├── assets/              # Images, fonts, icons
│   ├── components/
│   │   ├── common/          # Reusable UI components
│   │   └── layout/          # Layout components (Header, Footer, etc.)
│   ├── pages/
│   │   ├── auth/            # Login/Register pages
│   │   └── dashboard/       # Dashboard and recommendations
│   ├── routes/              # React Router route components
│   ├── context/             # Global state (Auth, Theme, etc.)
│   ├── hooks/               # Custom React hooks
│   └── utils/               # Helper functions & constants
├── .env
├── package.json
└── vite.config.js
```

> **Note:** The folder structure is **fixed** and must be **maintained**.
> Contributors **cannot restructure** without confirming with project architecture/design documents.

---


## 4. Contribution Guidelines

To ensure consistency and maintainability across the frontend, all contributors must follow these guidelines:

### Review Project Documentation First
Before starting any work, always consult the **project design documents, diagrams, API specifications, and class models**.  
Understanding the overall architecture ensures that your contributions align with the project standards.

### Branching Workflow
For new features or changes, create a dedicated **feature branch** from `main`.  

Feature branch names must follow this format

    ```
    feature/<short-description>_<YYYYMMDD>
    ````

    Example:

    ```
    git checkout -b feature/user-auth_20260107
    ````

Only merge into `main` after your work is complete, tested, and reviewed.

### Naming & File Conventions

* Follow the established folder structure in `src/` strictly.
* Component files should be **PascalCase** (e.g., `LoginForm.jsx`).
* Utility functions and hooks should be **camelCase** (e.g., `useAuth.js`, `formatDate.js`).

### Local Testing

Always run the development server to verify your changes:

```bash
npm run dev
```

Ensure your changes do not break existing functionality.

### Pull Requests (PRs)

* Submit PRs with **clear, descriptive titles and detailed descriptions**.
* Reference **relevant design documents, API specs, or diagrams** in the PR.
* PRs should be reviewed and approved before merging into `main`.

### Collaboration & Communication

* If a feature overlaps with ongoing work, coordinate with other contributors to avoid conflicts.
* When in doubt, always **check documentation** or ask the maintainers.




---


### 6. Scaling Strategy

This frontend is designed to **grow with the project**:

* **Modular components:** Keep UI components reusable and decoupled.
* **Context & hooks:** Centralize state and logic to avoid prop drilling.
* **API services:** All backend communication goes through `src/api` for easy swapping or versioning.
* **Routing structure:** Clear separation of `auth`, `dashboard`, and other modules.
* **Documentation-first approach:** New features must reference **design docs, diagrams, and backend API specs**.
* **Future-proofing:** Ready for **TypeScript migration**, **unit testing**, and **multi-team collaboration**.

---

### 7. Recommended Tools & Libraries

* **React Router v6+** – Routing
* **Axios** – API calls
* **Tailwind CSS / MUI / shadcn/ui** – UI components
* **React Context / Zustand** – State management
* **Vite** – Fast build & hot reload
---

