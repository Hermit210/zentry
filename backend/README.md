# Zentry Cloud Backend API

A complete FastAPI backend for the Zentry Cloud platform with authentication, project management, and VM provisioning.

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Supabase account** (free tier works)

### 1. Install Dependencies

```bash
# Navigate to backend directory
cd backend

# Install Python packages
pip install -r requirements.txt
```

### 2. Set up Supabase Database

1. **Create Supabase Project:**
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Wait for setup to complete

2. **Run Database Schema:**
   - In Supabase dashboard, go to **SQL Editor**
   - Copy contents of `supabase_schema.sql`
   - Paste and run the SQL

3. **Get API Keys:**
   - Go to **Settings** → **API**
   - Copy your:
     - Project URL
     - `anon` public key  
     - `service_role` secret key

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Supabase credentials
nano .env
```

**Required .env variables:**
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJ... (your anon key)
SUPABASE_SERVICE_KEY=eyJ... (your service key)
SECRET_KEY=your-super-secret-jwt-key-min-32-chars
```

### 4. Run the Backend

```bash
# Start the development server
python main.py

# Or use uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Verify Installation

- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | Login user |
| GET | `/auth/me` | Get current user |
| POST | `/auth/logout` | Logout user |

### Project Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/` | Create project |
| GET | `/projects/` | List user projects |
| GET | `/projects/{id}` | Get project with VMs |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |

### Virtual Machine Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/vms/` | Create VM |
| GET | `/vms/` | List user VMs |
| GET | `/vms/{id}` | Get specific VM |
| POST | `/vms/{id}/start` | Start VM |
| POST | `/vms/{id}/stop` | Stop VM |
| DELETE | `/vms/{id}` | Terminate VM |
| GET | `/vms/pricing/info` | Get pricing info |

## 🧪 Testing the API

### 1. Using the Interactive Docs

Visit http://localhost:8000/docs for Swagger UI where you can test all endpoints interactively.

### 2. Using curl

**Create a user:**
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "password123"
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Create a project (with auth token):**
```bash
curl -X POST "http://localhost:8000/projects/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "My Project",
    "description": "Test project"
  }'
```

### 3. Using Postman

1. Import the OpenAPI spec from http://localhost:8000/openapi.json
2. Set up authentication with Bearer token
3. Test all endpoints

## 🏗️ Architecture

```
┌─────────────────────────────┐
│     FastAPI Application     │
├─────────────────────────────┤
│  ├── Authentication (JWT)   │
│  ├── User Management        │
│  ├── Project Management     │
│  └── VM Management          │
└─────────────────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   Supabase (PostgreSQL)     │
│  ├── users table            │
│  ├── projects table         │
│  ├── vms table              │
│  └── Row Level Security     │
└─────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_ANON_KEY` | Supabase anon key | Required |
| `SUPABASE_SERVICE_KEY` | Supabase service key | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | 30 |
| `API_HOST` | Server host | 0.0.0.0 |
| `API_PORT` | Server port | 8000 |
| `ENVIRONMENT` | Environment | development |
| `DEBUG` | Debug mode | true |
| `CORS_ORIGINS` | Allowed origins | localhost:3000 |

### VM Instance Types & Pricing

| Type | vCPUs | RAM | Price/Hour |
|------|-------|-----|------------|
| small | 1 | 1GB | $0.05 |
| medium | 2 | 4GB | $0.10 |
| large | 4 | 8GB | $0.20 |
| xlarge | 8 | 16GB | $0.40 |

### Supported VM Images

- `ubuntu-22.04` - Ubuntu 22.04 LTS
- `ubuntu-20.04` - Ubuntu 20.04 LTS  
- `centos-8` - CentOS 8
- `debian-11` - Debian 11
- `fedora-38` - Fedora 38

## 🔒 Security Features

- **JWT Authentication** with configurable expiry
- **Password Hashing** using bcrypt
- **Row Level Security** in Supabase
- **Input Validation** with Pydantic
- **CORS Protection** with configurable origins
- **SQL Injection Protection** via Supabase client
- **Rate Limiting** ready (can be added with slowapi)

## 🚀 Connecting to Frontend

Your frontend should make requests to:
- **Base URL**: `http://localhost:8000`
- **Auth Header**: `Authorization: Bearer <token>`
- **Content-Type**: `application/json`

Example frontend API client setup:
```javascript
const API_BASE = 'http://localhost:8000';

// Login and get token
const response = await fetch(`${API_BASE}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const { access_token } = await response.json();

// Use token for authenticated requests
const projectsResponse = await fetch(`${API_BASE}/projects/`, {
  headers: { 
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  }
});
```

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Failed**
- Check your Supabase URL and keys in `.env`
- Ensure Supabase project is active
- Verify the schema was created successfully

**2. Authentication Errors**
- Check JWT secret key is set and long enough (32+ chars)
- Verify token is being sent in Authorization header
- Check token hasn't expired

**3. CORS Errors**
- Add your frontend URL to `CORS_ORIGINS` in `.env`
- Restart the server after changing CORS settings

**4. Import Errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version is 3.11+

### Logs

The API logs all requests and errors. Check the console output for detailed error messages.

## 🧪 Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Structure

```
backend/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── database.py          # Database connection
├── models.py            # Pydantic models
├── auth.py              # Authentication utilities
├── routers/             # API route handlers
│   ├── auth.py          # Auth endpoints
│   ├── projects.py      # Project endpoints
│   └── vms.py           # VM endpoints
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── supabase_schema.sql  # Database schema
└── README.md           # This file
```

## 🎯 Production Deployment

For production deployment:

1. **Set environment to production**:
   ```env
   ENVIRONMENT=production
   DEBUG=false
   ```

2. **Use strong secrets**:
   - Generate secure JWT secret key
   - Use production Supabase project

3. **Configure CORS properly**:
   ```env
   CORS_ORIGINS=https://yourdomain.com
   ```

4. **Use a production ASGI server**:
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

---

## ✅ Backend is Ready!

Your Zentry Cloud backend is now fully functional with:
- ✅ Complete authentication system
- ✅ Project management
- ✅ VM provisioning simulation
- ✅ Automatic API documentation
- ✅ Database integration
- ✅ Security best practices

**Test it now at: http://localhost:8000/docs**