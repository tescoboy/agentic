# Deployment Guide

This guide covers deploying the AdCP Demo Orchestrator to production environments.

## Platform Recommendations

### Recommended: Render
Render is the recommended platform for this monolith application:

**Advantages**:
- Native Python support
- Automatic HTTPS
- Built-in environment variable management
- Persistent disk storage for SQLite
- Simple deployment from Git

**Configuration**:
```yaml
# render.yaml
services:
  - type: web
    name: adcp-demo-orchestrator
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: DATABASE_URL
        value: sqlite:///./data/adcp_demo.sqlite3
      - key: SERVICE_BASE_URL
        value: https://your-app-name.onrender.com
```

### Alternative: Railway
Railway provides similar benefits to Render:

**Configuration**:
- Set environment variables in Railway dashboard
- Use `railway up` for deployment
- Configure persistent storage for database

### Alternative: Heroku
Heroku works but has limitations:

**Limitations**:
- Ephemeral filesystem (SQLite data lost on restart)
- Requires PostgreSQL for persistence
- More complex setup

**Workarounds**:
- Use external database (PostgreSQL)
- Implement data backup/restore
- Use add-ons for file storage

## Environment Variables

### Required Variables
```bash
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Database (for SQLite)
DATABASE_URL=sqlite:///./data/adcp_demo.sqlite3

# Service Configuration
SERVICE_BASE_URL=https://your-domain.com
ADCP_VERSION=adcp-demo-0.1

# Orchestrator Settings
ORCH_TIMEOUT_MS_DEFAULT=8000
ORCH_CONCURRENCY=8
CB_FAILURE_THRESHOLD=3
CB_TTL_SECONDS=60
```

### Optional Variables
```bash
# Debug Mode (disable in production)
DEBUG=0

# Port (usually set by platform)
PORT=8000

# Log Level
LOG_LEVEL=INFO
```

## Deployment Steps

### 1. Prepare Application
```bash
# Ensure all tests pass
pytest

# Check code quality
ruff check app/ tests/
black app/ tests/
mypy app/

# Verify preflight checks
python -c "from app.services.preflight import run_checks; print(run_checks())"
```

### 2. Platform-Specific Setup

#### Render
1. **Connect Repository**: Link your Git repository to Render
2. **Configure Environment**: Set all required environment variables
3. **Deploy**: Render will automatically deploy on push
4. **Verify**: Check `/health` and `/preflight/ui` endpoints

#### Railway
1. **Install CLI**: `npm install -g @railway/cli`
2. **Login**: `railway login`
3. **Initialize**: `railway init`
4. **Deploy**: `railway up`
5. **Set Variables**: Configure environment in dashboard

#### Heroku
1. **Install CLI**: `brew install heroku/brew/heroku`
2. **Login**: `heroku login`
3. **Create App**: `heroku create your-app-name`
4. **Set Variables**: `heroku config:set GEMINI_API_KEY=your_key`
5. **Deploy**: `git push heroku main`

### 3. Post-Deployment Verification
```bash
# Health check
curl https://your-domain.com/health

# Preflight checks
curl https://your-domain.com/preflight

# Test orchestration
curl -X POST https://your-domain.com/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"brief": "test brief", "internal_tenant_slugs": []}'
```

## Vercel Caveats

**Not Recommended** for this application due to:

1. **Serverless Limitations**: 
   - Cold starts affect performance
   - Function timeout limits (10s default)
   - No persistent file system

2. **SQLite Issues**:
   - Database file lost between requests
   - No persistent storage
   - Requires external database

3. **WebSocket/SSE Limitations**:
   - Not suitable for real-time features
   - Connection timeouts

**If Using Vercel**:
- Use external PostgreSQL database
- Implement proper connection pooling
- Handle cold starts gracefully
- Consider function timeout limits

## Production Considerations

### Security
1. **Environment Variables**: Never commit secrets to Git
2. **HTTPS**: Ensure all traffic uses HTTPS
3. **CORS**: Configure CORS appropriately for your domain
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Input Validation**: All inputs are validated, but review for your use case

### Performance
1. **Database**: Consider PostgreSQL for high-traffic deployments
2. **Caching**: Implement Redis for session storage
3. **CDN**: Use CDN for static assets
4. **Monitoring**: Set up application monitoring and alerting

### Monitoring
1. **Health Checks**: Monitor `/health` endpoint
2. **Preflight Checks**: Regular system health verification
3. **Logs**: Centralized logging with request ID tracking
4. **Metrics**: Track orchestration performance and errors

### Backup Strategy
1. **Database**: Regular backups of SQLite file or PostgreSQL
2. **Configuration**: Version control for configuration files
3. **Environment**: Document all environment variables
4. **Recovery**: Test restore procedures regularly

## Scaling Considerations

### Horizontal Scaling
- Use external database (PostgreSQL)
- Implement session storage (Redis)
- Use load balancer for multiple instances
- Configure proper CORS for multiple domains

### Vertical Scaling
- Increase memory allocation
- Optimize database queries
- Implement connection pooling
- Monitor resource usage

### Microservices Migration
If scaling beyond monolith:
1. **Split by Domain**: Separate tenant, product, and orchestration services
2. **API Gateway**: Implement API gateway for routing
3. **Service Discovery**: Use service discovery for inter-service communication
4. **Data Consistency**: Implement eventual consistency patterns

## Troubleshooting Deployment

### Common Issues
1. **Environment Variables**: Verify all required variables are set
2. **Port Configuration**: Ensure port matches platform requirements
3. **Database Permissions**: Check database file permissions
4. **Network Access**: Verify AI provider access from deployment platform

### Debug Steps
1. **Check Logs**: Review application logs for errors
2. **Preflight Check**: Run `/preflight` endpoint
3. **Health Check**: Verify `/health` endpoint
4. **Environment**: Confirm environment variables are loaded

### Support
- Check platform-specific documentation
- Review application logs with request IDs
- Test locally with same environment variables
- Verify all dependencies are in `requirements.txt`
