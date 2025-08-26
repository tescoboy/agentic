# Troubleshooting Guide

This guide helps you resolve common issues when using the AdCP Demo Orchestrator.

## Common Issues

### Missing API Key

**Problem**: `AIConfigError: Missing API key for Gemini AI provider`

**Symptoms**:
- AI ranking fails with configuration errors
- Agent settings page shows API key errors
- Orchestrator returns AI configuration errors

**Solution**:
1. Set your Gemini API key in the `.env` file:
   ```bash
   GEMINI_API_KEY=your_actual_api_key_here
   ```
2. Restart the application
3. Verify the key is valid by testing a simple ranking request

**Prevention**: Always set the API key before starting the application

### No Products Found

**Problem**: `No products found for tenant '{tenant_slug}'. Please add products before using AI evaluation.`

**Symptoms**:
- MCP ranking endpoints return 422 errors
- Orchestrator shows "no products" errors for tenants
- Buyer interface shows empty product lists

**Solution**:
1. Navigate to `/tenant/{id}/products`
2. Add products manually or via CSV import
3. Verify products are visible in the product list
4. Check that the tenant has the correct ID

**Prevention**: Always add products before testing AI ranking

### CSV Import Errors

**Problem**: Various CSV validation errors during bulk import

**Common Errors**:
- `Missing required columns: product_id, name`
- `Duplicate product_id found: {id}`
- `Row {n}: {field} - Field cannot be empty`

**Solution**:
1. Download a fresh CSV template from `/tenant/{id}/products/template.csv`
2. Ensure all required columns are present
3. Check for duplicate product IDs within the tenant
4. Fill in all required fields
5. Validate data formats (prices as decimals, etc.)

**Prevention**: Use the provided template and validate data before upload

### Timeout Errors

**Problem**: `AITimeoutError: Request timed out` or `408 Request Timeout`

**Symptoms**:
- AI ranking requests take too long
- Orchestrator shows timeout errors
- Circuit breaker opens for slow agents

**Solution**:
1. Increase timeout in agent settings:
   ```bash
   # In .env file
   ORCH_TIMEOUT_MS_DEFAULT=15000  # Increase from 8000
   ```
2. Check AI provider status and response times
3. Reduce prompt complexity or product count
4. Monitor network connectivity

**Prevention**: Set appropriate timeouts based on your AI provider's performance

### Circuit Breaker Issues

**Problem**: `Circuit breaker is open for agent '{agent}'`

**Symptoms**:
- Repeated failures for the same agent
- Orchestrator skips failing agents
- Error messages mention circuit breaker

**Solution**:
1. Wait for the circuit breaker TTL to expire (default: 60 seconds)
2. Fix the underlying issue (API key, network, etc.)
3. Reset circuit breaker by restarting the application
4. Check agent endpoint availability

**Prevention**: Monitor agent health and fix issues promptly

### Database File Missing

**Problem**: `No such table 'tenants'` or database connection errors

**Symptoms**:
- Application fails to start
- Database queries fail
- Tables don't exist

**Solution**:
1. Initialize the database:
   ```bash
   python -c "from app.db import init_db; init_db()"
   ```
2. Check database file permissions:
   ```bash
   ls -la ./data/adcp_demo.sqlite3
   ```
3. Ensure the `data/` directory exists:
   ```bash
   mkdir -p data
   ```

**Prevention**: Always run database initialization after setup

### CORS Issues in Debug Mode

**Problem**: CORS errors when `DEBUG=1` is set

**Symptoms**:
- Browser console shows CORS errors
- API calls fail from browser
- Cross-origin request blocked

**Solution**:
1. CORS is intentionally disabled for server-to-server communication
2. For browser testing, set `DEBUG=1` in `.env`
3. Use proper CORS headers in production
4. Test API endpoints directly, not from browser

**Prevention**: Understand that CORS is for browser testing only

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Symptoms**:
- Tests fail to run
- Application can't find modules
- Import errors in Python

**Solution**:
1. Set the Python path:
   ```bash
   export PYTHONPATH=.
   ```
2. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
3. Run tests with explicit path:
   ```bash
   PYTHONPATH=. pytest
   ```

**Prevention**: Always use the virtual environment and set PYTHONPATH

### Port Already in Use

**Problem**: `[Errno 48] Address already in use`

**Symptoms**:
- Application fails to start
- Port 8000 is occupied

**Solution**:
1. Use a different port:
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```
2. Find and stop the process using port 8000:
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```
3. Check for other running instances

**Prevention**: Check for running processes before starting

### Tenant Context Issues

**Problem**: Wrong tenant context or missing tenant selection

**Symptoms**:
- Products appear for wrong tenant
- Agent settings show wrong tenant
- Tenant mismatch errors

**Solution**:
1. Select the correct tenant from the navbar dropdown
2. Clear browser cookies and restart
3. Verify tenant ID in URLs matches your tenant
4. Check tenant exists in the database

**Prevention**: Always verify tenant context before making changes

### AI Provider Errors

**Problem**: Various AI provider-specific errors

**Common Issues**:
- `AIRequestError: Invalid response from AI provider`
- `AIConfigError: Model not found`
- Rate limiting errors

**Solution**:
1. Check AI provider status and quotas
2. Verify model name in agent settings
3. Reduce request frequency
4. Check API key permissions

**Prevention**: Monitor AI provider status and set appropriate rate limits

## Debugging Steps

### 1. Check Application Logs
```bash
# Start with verbose logging
uvicorn app.main:app --reload --log-level debug
```

### 2. Verify Environment Variables
```bash
# Check all environment variables are set
python -c "from app.config import settings; print(settings)"
```

### 3. Test Database Connection
```bash
# Verify database is accessible
python -c "from app.db import get_engine; engine = get_engine(); print('Database OK')"
```

### 4. Test AI Provider
```bash
# Test AI provider directly
python -c "from app.ai.gemini import rank_products; print('AI Provider OK')"
```

### 5. Check File Permissions
```bash
# Ensure data directory is writable
ls -la data/
chmod 755 data/
```

## Performance Issues

### Slow Orchestration
**Causes**:
- Too many agents being called
- High AI provider latency
- Network issues

**Solutions**:
1. Reduce concurrency: `ORCH_CONCURRENCY=4`
2. Increase timeouts: `ORCH_TIMEOUT_MS_DEFAULT=15000`
3. Use fewer agents in requests
4. Monitor AI provider performance

### Memory Issues
**Causes**:
- Large CSV imports
- Too many concurrent requests
- Memory leaks

**Solutions**:
1. Limit CSV file size (max 1000 rows)
2. Reduce concurrent requests
3. Restart application periodically
4. Monitor memory usage

## Getting Help

### Before Asking for Help
1. Check this troubleshooting guide
2. Review application logs
3. Verify environment configuration
4. Test with minimal data
5. Check for known issues

### Information to Provide
When reporting issues, include:
- Error message (exact text)
- Steps to reproduce
- Environment details (OS, Python version)
- Configuration (relevant parts of `.env`)
- Application logs
- Sample data (if applicable)

### Support Channels
- Check the documentation first
- Review test cases for examples
- Check application logs for details
- Verify configuration matches examples

## Prevention Checklist

- [ ] Set up environment variables correctly
- [ ] Initialize database before first use
- [ ] Add products before testing AI features
- [ ] Use appropriate timeouts
- [ ] Monitor AI provider status
- [ ] Keep CSV files under size limits
- [ ] Verify tenant context
- [ ] Test with small datasets first
- [ ] Check file permissions
- [ ] Use virtual environment consistently

## Preflight Check Mappings

Each preflight check corresponds to specific troubleshooting steps:

### Database File Check
- **Status**: `fail` - Database file not accessible or writable
- **Fix**: Check file permissions and disk space
- **Path**: See `DATABASE_URL` in your `.env` file

### Database Tables Check  
- **Status**: `fail` - Required tables missing
- **Fix**: Run database initialization: `python -c "from app.db import init_db; init_db()"`
- **Tables**: tenants, products, agent_settings, external_agents

### Reference Repositories Check
- **Status**: `warn` - Missing reference repositories
- **Fix**: Clone required repos: `/reference/salesagent` and `/reference/adcp`
- **Impact**: Default prompts may not work correctly

### Default Prompt File Check
- **Status**: `fail` - Prompt file missing or unreadable
- **Fix**: Ensure `app/resources/default_sales_prompt.txt` exists and is readable
- **Source**: Copy from `/reference/salesagent` repository

### API Key Check
- **Status**: `warn` - GEMINI_API_KEY not configured
- **Fix**: Set `GEMINI_API_KEY=your_key` in `.env` file
- **Impact**: AI ranking will fail, but system will start

### Tenants Check
- **Status**: `warn` - No tenants found
- **Fix**: Create at least one tenant via `/tenants`
- **Impact**: No agents available for orchestration

## Debugging Steps

### 1. Check Preflight Status
```bash
curl http://localhost:8000/preflight
```

### 2. Enable Debug Logging
```bash
# In .env file
DEBUG=1
```

### 3. Monitor Console Logs
- Open browser developer tools
- Look for `[ADCP]` prefixed messages
- Check for request IDs in logs

### 4. Check Request IDs
- Every response includes `X-Request-ID` header
- Use this ID to trace requests through logs
- Request ID is also available in page meta tags

### 5. Test Individual Components
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test MCP endpoint (replace with actual tenant slug)
curl http://localhost:8000/mcp/agents/your-tenant-slug/rank \
  -H "Content-Type: application/json" \
  -d '{"brief": "test brief"}'
```

## Performance Issues

### Slow AI Responses
- Increase timeout settings
- Check AI provider status
- Reduce prompt complexity
- Monitor network latency

### High Memory Usage
- Check for memory leaks in long-running processes
- Monitor database connection pooling
- Review log file sizes

### Database Performance
- Check SQLite file size and fragmentation
- Monitor query performance
- Consider database optimization

## Getting Help

### Log Files
- Application logs are written to stdout
- Request IDs help trace specific issues
- Enable DEBUG mode for detailed logging

### Common Error Codes
- `400`: Bad Request - Check input validation
- `404`: Not Found - Verify URLs and tenant slugs
- `408`: Timeout - Increase timeout settings
- `422`: Validation Error - Check request format
- `500`: Internal Error - Check logs for details
- `502`: Bad Gateway - AI provider issues

### Support Checklist
Before seeking help, ensure you have:
- [ ] Run preflight checks (`/preflight/ui`)
- [ ] Checked application logs
- [ ] Verified environment configuration
- [ ] Tested with minimal data
- [ ] Documented error messages and request IDs

## Prevention Checklist

### Before Starting
- [ ] Set all required environment variables
- [ ] Verify database permissions
- [ ] Check AI provider access
- [ ] Test network connectivity

### During Operation
- [ ] Monitor preflight status regularly
- [ ] Check console logs for errors
- [ ] Verify tenant and product data
- [ ] Test agent endpoints periodically

### Maintenance
- [ ] Backup database regularly
- [ ] Update API keys when needed
- [ ] Monitor disk space usage
- [ ] Review and rotate logs
