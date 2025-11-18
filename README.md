# AI Nutrition Coach Backend

A Django REST API backend for the AI Nutrition Coach application with Google Gemini integration.

## Features

- **JWT Authentication** with refresh tokens
- **AI Nutrition Analysis** using Google Gemini 2.0 Flash
- **Smart Caching** with Redis and database fallback
- **Rate Limiting** for API protection
- **Environment-based Configuration** for dev/prod
- **Production Ready** with Railway deployment support

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh JWT token

### User Management
- `GET /api/user/me/` - Get current user info
- `GET/PUT /api/user/update/` - Update user profile

### AI Nutrition
- `POST /api/ai/advice/` - Get AI nutrition analysis
  ```json
  {
    "meal": "2 eggs, banana, oats"
  }
  ```

### Meals
- `POST /api/meals/add/` - Add new meal
- `GET /api/meals/today/` - Get today's meals
- `GET /api/meals/weekly/` - Get weekly meals
- `GET/PUT/DELETE /api/meals/<id>/` - Meal CRUD operations

### Schedule
- `POST /api/schedule/create/` - Create schedule item
- `GET /api/schedule/list/` - List schedule items
- `GET/PUT/DELETE /api/schedule/<id>/` - Schedule CRUD operations

### Settings
- `GET/PUT /api/settings/` - App settings management

### Dashboard
- `GET /api/stats/` - Dashboard statistics

## Setup Instructions

### 1. Environment Setup

Copy the environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# AI Configuration
AI_API_KEY=your_actual_gemini_api_key

# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## AI Service Configuration

### Development (Mock Mode)
When `AI_API_KEY` is set to `YOUR_GEMINI_API_KEY` or not configured, the system uses intelligent mock responses based on meal keywords.

### Production (Real AI)
1. Get a Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)
2. Set `AI_API_KEY=your_actual_api_key` in `.env`
3. The system will use real Gemini 2.0 Flash analysis

## Rate Limiting

- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour  
- **AI endpoint**: 10 requests/hour (configurable via `AI_RATE_LIMIT`)

## Caching Strategy

### Two-Layer Caching
1. **Redis Cache** (fast, in-memory)
2. **Database Cache** (persistent, survives restarts)

### Cache Duration
- AI analysis results: 24 hours
- Automatic cleanup of expired entries

## Deployment

### Railway (Recommended)

1. Push your code to GitHub
2. Connect your repository to Railway
3. Railway will automatically detect the Django app
4. Set environment variables in Railway dashboard:
   - `AI_API_KEY`: Your Gemini API key
   - `SECRET_KEY`: Django secret key
   - `DATABASE_URL`: PostgreSQL connection (Railway provides this)
   - `DEBUG`: False
   - `ALLOWED_HOSTS`: `.railway.app,.railway.internal`

### Manual Deployment

```bash
# Install production dependencies
pip install -r requirements.txt

# Set environment variables
export DEBUG=False
export SECRET_KEY=your-production-secret
export DATABASE_URL=postgresql://user:pass@host:port/db

# Run with Gunicorn
gunicorn backend.wsgi:application --bind 0.0.0.0:8000
```

## API Usage Examples

### Register User
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepass123",
    "password_confirm": "securepass123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepass123"
  }'
```

### Get AI Nutrition Advice
```bash
curl -X POST http://localhost:8000/api/ai/advice/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "meal": "grilled chicken salad with olive oil dressing"
  }'
```

## Security Features

- **JWT Authentication** with token rotation
- **CORS Protection** configured for frontend domain
- **Rate Limiting** prevents API abuse
- **Input Validation** on all endpoints
- **SQL Injection Protection** via Django ORM
- **Environment Variable Security** for API keys

## Monitoring & Logging

- **Django Logging** to `debug.log`
- **AI Service Logging** for monitoring API calls
- **Cache Hit Logging** for performance tracking
- **Error Tracking** with detailed stack traces

## Development Tips

1. **Use Mock AI**: Keep `AI_API_KEY=YOUR_GEMINI_API_KEY` for development
2. **Check Logs**: Monitor `debug.log` for issues
3. **Test Endpoints**: Use Django admin at `/admin/`
4. **Clear Cache**: Use `/api/admin/cleanup-cache/` endpoint

## Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure production database (PostgreSQL)
- [ ] Set real `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set `AI_API_KEY` for real AI analysis
- [ ] Configure Redis for caching
- [ ] Set up monitoring and logging
- [ ] Test all endpoints
- [ ] Configure CORS for production domain

## Support

For issues and questions:
1. Check `debug.log` for error details
2. Verify environment variables are set correctly
3. Ensure all dependencies are installed
4. Test with mock AI first, then real API key

## License

MIT License - see LICENSE file for details.
