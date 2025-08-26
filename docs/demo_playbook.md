# Demo Playbook

This playbook provides step-by-step instructions for running a complete AdCP Demo Orchestrator demonstration.

## Prerequisites

1. **System Setup**: Follow `docs/setup.md` to install and configure the system
2. **API Key**: Ensure `GEMINI_API_KEY` is set in your `.env` file
3. **Preflight Check**: Visit `/preflight/ui` to verify system readiness

## Demo Flow

### Step 1: System Verification
1. **Visit Preflight Page**: Navigate to `/preflight/ui`
2. **Check Status**: Ensure all checks show "OK" or "WARN" (no "FAIL")
3. **Fix Issues**: Address any failures before proceeding

### Step 2: Create Tenants
1. **Navigate to Tenants**: Go to `/tenants`
2. **Create Publisher A**: 
   - Name: "Sports Publisher"
   - Slug: "sports-pub"
3. **Create Publisher B**:
   - Name: "Tech Publisher" 
   - Slug: "tech-pub"

### Step 3: Add Products
1. **Select Sports Publisher**: Use tenant switcher in navbar
2. **Bulk Import**: 
   - Go to Products page
   - Download CSV template
   - Add 5-10 sports-related products (basketball ads, football sponsorships, etc.)
   - Upload CSV file
3. **Select Tech Publisher**: Switch to tech publisher
4. **Bulk Import**: Add 5-10 tech-related products (mobile ads, software promotions, etc.)

### Step 4: Configure AI Agents
1. **Sports Publisher Agent**:
   - Go to `/tenant/{sports-pub-id}/agent`
   - Set custom prompt: "You are a sports advertising specialist. Focus on athletic performance, team spirit, and sports culture."
   - Save settings
2. **Tech Publisher Agent**:
   - Go to `/tenant/{tech-pub-id}/agent`
   - Set custom prompt: "You are a technology advertising specialist. Focus on innovation, efficiency, and digital transformation."
   - Save settings

### Step 5: Add External Agents (Optional)
1. **Navigate to External Agents**: Go to `/external-agents`
2. **Add External Agent**:
   - Name: "Demo External Agent"
   - Base URL: `https://api.example.com/adcp`
   - Enable: Yes
3. **Note**: External agents require actual AdCP-compliant endpoints

### Step 6: Run Buyer Demo
1. **Navigate to Buyer Page**: Go to `/buyer`
2. **Enter Brief**: 
   ```
   "I need advertising for a new fitness app targeting young professionals aged 25-35. 
   Budget is $50,000 for a 3-month campaign. Looking for high engagement and brand awareness."
   ```
3. **Select Agents**: Choose both internal publishers (default selected)
4. **Submit**: Click "Get Recommendations"
5. **Review Results**: 
   - Check that both agents returned different products
   - Verify reasons are relevant to each agent's specialization
   - Note the different perspectives from sports vs tech publishers

### Step 7: Show MCP Endpoints
1. **Sports Publisher Agent Page**: Go to `/tenant/{sports-pub-id}/agent`
2. **Show Endpoint URL**: Point out the MCP endpoint URL
3. **Explain**: This is how third parties can call this agent directly
4. **Test Direct Call**: Use curl or Postman to call the endpoint directly

### Step 8: Demonstrate Orchestration
1. **Direct Orchestrator Call**: Use the API directly
   ```bash
   curl -X POST http://localhost:8000/orchestrate \
     -H "Content-Type: application/json" \
     -d '{
       "brief": "Campaign for eco-friendly products targeting environmentally conscious consumers",
       "internal_tenant_slugs": ["sports-pub", "tech-pub"],
       "timeout_ms": 10000
     }'
   ```
2. **Show Aggregation**: Demonstrate how results are combined from multiple agents

## Demo Tips

### Enable Console Logging
- Set `DEBUG=1` in your `.env` file
- Open browser developer tools
- Watch for `[ADCP]` console messages during interactions

### Common Demo Scenarios
1. **Partial Failures**: Show how one agent failing doesn't break the others
2. **Timeout Handling**: Demonstrate circuit breaker behavior
3. **Different Briefs**: Try various briefs to show agent specialization

### Troubleshooting
- **No AI Results**: Check `GEMINI_API_KEY` is set
- **Empty Results**: Ensure products exist for selected tenants
- **Timeout Errors**: Increase `timeout_ms` in advanced options

## Demo Script

### Opening
"Welcome to the AdCP Demo Orchestrator. This system demonstrates how multiple publisher sales agents can be orchestrated to provide comprehensive advertising recommendations for buyer briefs."

### Key Points to Highlight
1. **Multi-Tenancy**: Each publisher has their own products and AI configuration
2. **Agent Specialization**: Different prompts create specialized recommendations
3. **AdCP Compliance**: All communication follows the AdCP protocol
4. **Fault Tolerance**: Circuit breakers and timeouts ensure reliability
5. **Extensibility**: External agents can be easily added

### Closing
"The AdCP Demo Orchestrator shows how publishers can maintain their unique voice while participating in a unified advertising ecosystem. The system is production-ready and can scale to handle thousands of publishers and millions of briefs."
