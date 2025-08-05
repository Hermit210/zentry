# Zentry Cloud Platform

A developer-first cloud platform competitor to Google Cloud Platform, built with FastAPI backend and Supabase database.

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.11+** for the backend
- **Node.js 18+** for the frontend  
- **Supabase account** (free tier works fine)

### 1. Supabase Setup

1. Go to [supabase.com](https://supabase.com) and create a new project
2. In your Supabase dashboard, go to **SQL Editor**
3. Copy and paste the contents of `supabase-setup.sql` and run it
4. Go to **Settings > API** and copy:
   - Project URL
   - `anon` public key
   - `service_role` secret key

### 2. Backend Setup (FastAPI + Supabase)

```bash
# 1. Create environment file
cp backend/.env.example backend/.env

# 2. Edit backend/.env with your Supabase credentials
# SUPABASE_URL=https://your-project-id.supabase.co
# SUPABASE_ANON_KEY=your-anon-key
# SUPABASE_SERVICE_KEY=your-service-key

# 3. Install Python dependencies
pip install -r backend/requirements.txt

# 4. Start the backend server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Or use the PowerShell script:**
```powershell
powershell -ExecutionPolicy Bypass -File start-backend.ps1
```

### 3. Frontend Setup (Next.js)

```bash
# 1. Create environment file
cp .env.local.example .env.local

# 2. Install Node.js dependencies
npm install

# 3. Start the frontend
npm run dev
```

**Or use the PowerShell script:**
```powershell
powershell -ExecutionPolicy Bypass -File start-frontend.ps1
```

### 4. Access Your Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🏗️ Architecture

```
┌─────────────────────────────┐
│     Frontend (Next.js)      │ ← http://localhost:3000
└────────────┬────────────────┘
             │ HTTP/REST API
┌────────────▼────────────────┐
│   Backend (FastAPI)         │ ← http://localhost:8000
│   ├── Authentication        │
│   ├── User Management       │
│   ├── Project Management    │
│   └── VM Management         │
└────────────┬────────────────┘
             │ SQL queries
┌────────────▼────────────────┐
│   Database (Supabase)       │
│   ├── Users table           │
│   ├── Projects table        │
│   ├── VMs table             │
│   └── Row Level Security    │
└─────────────────────────────┘
```

## 📁 Project Structure

```
zentry/
├── app/                    # Next.js frontend pages
├── components/             # React components
├── lib/                    # Frontend utilities (API client)
├── backend/               # FastAPI backend
│   ├── main.py           # Main FastAPI application
│   ├── requirements.txt  # Python dependencies
│   └── .env             # Environment variables
├── supabase-setup.sql    # Database schema
├── start-backend.ps1     # Backend startup script
├── start-frontend.ps1    # Frontend startup script
└── README.md
```

## 🛠️ Technology Stack

### Frontend
- **Next.js 14** with TypeScript
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **Axios** for API calls
- **Supabase JS** client (optional)

### Backend
- **FastAPI** with Python 3.11+
- **Supabase** as PostgreSQL database
- **JWT** authentication
- **Bcrypt** password hashing
- **Pydantic** for data validation
- **CORS** enabled for frontend

### Database
- **Supabase** (PostgreSQL)
- **Row Level Security** (RLS) policies
- **UUID** primary keys
- **Automatic timestamps**

## 🔧 Environment Variables

### Backend (.env)
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SECRET_KEY=your-jwt-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## 🚀 API Endpoints

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

### Projects
- `GET /projects` - List user projects
- `POST /projects` - Create new project

### Virtual Machines
- `GET /vms` - List user VMs
- `POST /vms` - Create new VM
- `DELETE /vms/{vm_id}` - Delete VM

### System
- `GET /` - API status
- `GET /health` - Health check with database status

## 🧪 Testing the Setup

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Create a Test User**:
   ```bash
   curl -X POST http://localhost:8000/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","name":"Test User","password":"password123"}'
   ```

3. **Login**:
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password123"}'
   ```

## 🔒 Security Features

- **JWT Authentication** with expiration
- **Password Hashing** with bcrypt
- **Row Level Security** in Supabase
- **CORS** properly configured
- **Input Validation** with Pydantic
- **SQL Injection Protection** via Supabase client

## 🎯 Current Features

✅ **Completed:**
- User registration and authentication
- JWT-based session management
- Project creation and management
- VM simulation with credit system
- Supabase database integration
- Modern responsive UI
- API documentation

🚧 **Next Steps:**
- Real VM provisioning with KubeVirt
- Payment integration
- Advanced monitoring
- Email verification
- Password reset functionality

## 🤝 Development

This project is set up for easy local development without Docker. All data is stored in Supabase, and both frontend and backend support hot reloading.

For production deployment, see the `infrastructure/` directory for Terraform configurations.