# n8n Workflows for Personal Finance Automation

This directory contains n8n workflow templates for automating financial data ingestion and reporting.

## Overview

Two main workflows:

1. **drive_ingest.json** - Automated statement ingestion from Google Drive
2. **weekly_report.json** - Weekly financial summary generation and delivery

## Prerequisites

### Required Services

- n8n instance (self-hosted or cloud)
- Google Drive with API access
- OpenAI API account
- FastAPI backend running (see `/api` directory)
- Telegram Bot (optional, for notifications)

### Required npm Packages (for n8n)

If using self-hosted n8n, install these packages in your n8n instance:

```bash
npm install pdf-parse
```

## Setup Instructions

### 1. Install n8n

#### Docker (Recommended)

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

#### Docker Compose

Add to your `ops/docker-compose.yml`:

```yaml
n8n:
  image: n8nio/n8n:latest
  ports:
    - "5678:5678"
  environment:
    - N8N_BASIC_AUTH_ACTIVE=true
    - N8N_BASIC_AUTH_USER=${N8N_USER}
    - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    - WEBHOOK_URL=https://your-domain.com/
  volumes:
    - ~/.n8n:/home/node/.n8n
    - ./n8n/workflows:/workflows:ro
  restart: unless-stopped
```

### 2. Configure Credentials

Access n8n at `http://localhost:5678` and set up credentials:

#### Google Drive OAuth2 API

1. Go to **Credentials** → **New** → **Google Drive OAuth2 API**
2. Follow the OAuth2 setup:
   - Create project in Google Cloud Console
   - Enable Google Drive API
   - Create OAuth2 credentials (Web application)
   - Add authorized redirect URI: `http://localhost:5678/rest/oauth2-credential/callback`
   - Copy Client ID and Client Secret to n8n
3. Click **Connect** and authorize access
4. Name: `Google Drive Account`

#### OpenAI API

1. Go to **Credentials** → **New** → **OpenAI API**
2. Enter your OpenAI API key from https://platform.openai.com/api-keys
3. Name: `OpenAI Account`

#### HTTP Header Auth (for API)

1. Go to **Credentials** → **New** → **HTTP Header Auth**
2. Configure:
   - Name: `Authorization`
   - Value: `Bearer YOUR_API_JWT_TOKEN`
3. Name: `API Authentication`

#### Telegram API (Optional)

1. Create bot via [@BotFather](https://t.me/botfather)
2. Get bot token
3. Go to **Credentials** → **New** → **Telegram API**
4. Enter bot token
5. Name: `Telegram Bot`

### 3. Set Environment Variables

In n8n, set these environment variables (Settings → Environment Variables):

```bash
# API Configuration
API_BASE_URL=http://api:8080  # or http://localhost:8080

# OpenAI Configuration
OPENAI_MODEL=gpt-4o-mini

# Telegram Configuration (optional)
TELEGRAM_CHAT_ID=your_chat_id
DASHBOARD_URL=http://localhost:8080

# n8n Authentication (if using Docker)
N8N_USER=admin
N8N_PASSWORD=your_secure_password
```

**Finding your Telegram Chat ID:**

1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":123456789}` in the response

### 4. Import Workflows

#### Via UI

1. Go to **Workflows** → **Add Workflow** → **Import from File**
2. Select `drive_ingest.json`
3. Click **Import**
4. Repeat for `weekly_report.json`

#### Via CLI

```bash
# Copy workflows to n8n data directory
cp n8n/workflows/*.json ~/.n8n/workflows/

# Restart n8n
docker restart n8n
```

#### Via API

```bash
# Import drive_ingest workflow
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "Content-Type: application/json" \
  -u admin:your_password \
  -d @n8n/workflows/drive_ingest.json

# Import weekly_report workflow
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "Content-Type: application/json" \
  -u admin:your_password \
  -d @n8n/workflows/weekly_report.json
```

### 5. Configure Workflows

After importing, configure each workflow:

#### Drive Ingestion Workflow

1. Open **Finance - Google Drive Statement Ingestion**
2. Click on **Watch Google Drive Statements Folder** node
3. Select your Google Drive credential
4. Choose or create the `Statements/` folder
5. Save workflow

#### Weekly Report Workflow

1. Open **Finance - Weekly Summary Report**
2. Verify schedule (default: Monday 9 AM)
3. Adjust timezone if needed
4. Save workflow

### 6. Test Workflows

#### Test Drive Ingestion

1. Upload a sample CSV file to your Google Drive `Statements/` folder

Sample CSV format:
```csv
date,description,amount,direction,mcc,memo
2025-10-24,STARBUCKS 1234,-7.84,debit,5814,Coffee
2025-10-23,HY-VEE #1234,-45.67,debit,5411,Groceries
```

2. In n8n, open the workflow
3. Click **Execute Workflow**
4. Monitor execution in real-time
5. Check logs for any errors

#### Test Weekly Report (Manual)

1. Open **Finance - Weekly Summary Report**
2. Click **Execute Workflow**
3. Wait for completion
4. Check Telegram for notification (if configured)

### 7. Activate Workflows

1. Open each workflow
2. Toggle **Active** switch in top-right
3. Workflows will now run automatically

## Workflow Details

### Drive Ingestion Workflow

**Trigger:** Google Drive file creation in `Statements/` folder

**Processing Flow:**

1. **File Detection** → Identifies CSV/OFX or PDF files
2. **Branch A (CSV/OFX):**
   - Download file
   - Parse content
   - Normalize fields
   - Compute hash_id
   - POST to `/api/ingest`
   - POST to `/api/categorize/{id}`
   - If low confidence → Telegram review request
   - Auto-finalize high confidence
3. **Branch B (PDF):**
   - Download file
   - Extract text
   - OpenAI CSV extraction
   - Continue as Branch A
4. **Receipt Matching (Parallel):**
   - Search Drive for matching receipts
   - Link receipt URL to transaction

**Supported Formats:**
- CSV with headers: `date,description,amount,direction,mcc,memo`
- OFX (XML banking format)
- PDF bank statements

**Error Handling:**
- 3 retry attempts for HTTP requests
- 2-second backoff between retries
- Comprehensive error logging
- Optional Telegram error notifications

### Weekly Report Workflow

**Trigger:** Cron schedule (every Monday at 9:00 AM)

**Processing Flow:**

1. **Calculate Dates** → Previous Monday to Sunday
2. **Fetch Data** → GET `/api/report/summary?start_date=...&end_date=...`
3. **Format Metrics** → Calculate totals, averages, percentages
4. **AI Analysis** → OpenAI generates insights and habit suggestion
5. **Store Report** → POST to `/api/reports`
6. **Notify** → Send Telegram message (if configured)

**Generated Insights:**
- Weekly spending summary
- Top category and vendors
- Savings calculation
- One actionable habit improvement
- Positive reinforcement

**Customization:**
- Adjust cron schedule in trigger node
- Modify AI prompt in OpenAI node
- Change report format in formatting node

## Troubleshooting

### Common Issues

#### 1. Google Drive Not Triggering

**Symptoms:** New files uploaded but workflow doesn't run

**Solutions:**
- Verify workflow is **Active** (toggle in top-right)
- Check Google Drive credential is valid (test connection)
- Ensure folder path is correct (case-sensitive)
- Check n8n execution logs for errors
- Verify n8n has internet access

**Re-authorize Google Drive:**
```bash
# In n8n UI
1. Go to Credentials → Google Drive OAuth2 API
2. Click "Reconnect"
3. Authorize access again
```

#### 2. OpenAI API Errors

**Symptoms:** "401 Unauthorized" or "429 Rate Limit"

**Solutions:**
- Verify API key is valid and has credits
- Check rate limits: https://platform.openai.com/account/rate-limits
- Reduce request frequency
- Use cheaper model: `gpt-4o-mini` instead of `gpt-4`

**Check API Key:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### 3. API Connection Failures

**Symptoms:** "ECONNREFUSED" or timeout errors

**Solutions:**
- Verify API is running: `docker ps | grep api`
- Check API_BASE_URL environment variable
- Test API manually: `curl http://localhost:8080/api/health`
- Verify network connectivity between n8n and API containers
- Check firewall rules

**Test API Endpoint:**
```bash
# From n8n container
docker exec -it n8n curl http://api:8080/api/health

# From host
curl http://localhost:8080/api/health
```

#### 4. PDF Parsing Failures

**Symptoms:** "pdf-parse not found" or extraction errors

**Solutions:**
- Install pdf-parse in n8n container:
  ```bash
  docker exec -it n8n npm install pdf-parse
  docker restart n8n
  ```
- Verify PDF is text-based (not scanned image)
- Try OCR for image-based PDFs (not included by default)

#### 5. Telegram Notifications Not Working

**Symptoms:** Reports generated but no Telegram messages

**Solutions:**
- Verify `TELEGRAM_CHAT_ID` is set correctly
- Check bot token is valid
- Ensure bot has permission to send messages
- Test bot manually: send `/start` message

**Test Telegram Bot:**
```bash
curl -X POST https://api.telegram.org/bot<TOKEN>/sendMessage \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "YOUR_CHAT_ID", "text": "Test message"}'
```

#### 6. Workflow Execution Hangs

**Symptoms:** Workflow stuck in "Running" state

**Solutions:**
- Check n8n logs: `docker logs n8n`
- Increase timeout in HTTP request nodes
- Verify external services are responding
- Restart n8n: `docker restart n8n`
- Clear workflow execution history

#### 7. Hash Collision (Duplicate Transactions)

**Symptoms:** "hash_id already exists" error

**Solutions:**
- This is expected behavior for duplicate transactions
- API will return existing transaction ID
- Workflow continues normally
- Check if truly duplicate or hash collision

### Debugging

#### Enable Verbose Logging

In n8n environment:
```bash
N8N_LOG_LEVEL=debug
N8N_LOG_OUTPUT=console
```

#### View Execution Logs

1. Go to **Executions** in n8n
2. Click on execution to view
3. Inspect each node's input/output
4. Check error messages

#### Test Individual Nodes

1. Open workflow editor
2. Click **Execute Node** on specific node
3. Provide test input data
4. Inspect output

#### API Debugging

```bash
# Check API logs
docker logs -f api

# Test ingestion endpoint
curl -X POST http://localhost:8080/api/ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "txn_date": "2025-10-24",
    "amount_cents": 784,
    "currency": "USD",
    "direction": "debit",
    "raw_descriptor": "STARBUCKS 1234",
    "source_account": "test_account",
    "hash_id": "test123"
  }'
```

## Performance Optimization

### Reduce OpenAI Costs

1. Use `gpt-4o-mini` instead of `gpt-4` (10x cheaper)
2. Lower `maxTokens` in OpenAI nodes (current: 500-2000)
3. Cache common categorizations in API rules
4. Batch multiple transactions per API call

### Improve Processing Speed

1. Enable parallel execution for independent branches
2. Reduce retry attempts from 3 to 2
3. Lower wait times between retries
4. Use smaller AI models for simple tasks

### Scale for High Volume

1. Increase n8n worker threads:
   ```bash
   N8N_CONCURRENCY_PRODUCTION_LIMIT=10
   ```
2. Enable queue mode for large batches
3. Use webhook triggers instead of polling
4. Implement rate limiting in API

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for all secrets
3. **Enable HTTPS** for production n8n instances
4. **Rotate API keys** regularly
5. **Limit OAuth scopes** to minimum required
6. **Enable n8n authentication** (basic auth or SSO)
7. **Use read-only** Google Drive access where possible
8. **Validate webhook signatures** for external triggers

## Customization

### Modify CSV Format

Edit the **Parse CSV** node:
```json
{
  "options": {
    "delimiter": ",",
    "headerRow": true,
    "columns": ["date", "description", "amount"]
  }
}
```

### Change Report Schedule

Edit the **Schedule Trigger** node:
```javascript
// Weekly on Monday 9 AM
"0 9 * * 1"

// Daily at 8 AM
"0 8 * * *"

// Monthly on 1st at 9 AM
"0 9 1 * *"
```

### Add Custom Categories

Modify the AI prompt in **OpenAI Generate Insights**:
```
Taxonomy = [Groceries, Dining, Transport, YOUR_CUSTOM_CATEGORY, ...]
```

### Multiple Bank Accounts

Clone the workflow and configure different:
- Source folders (e.g., `Statements/Chase/`, `Statements/Amex/`)
- `source_account` values in normalization node
- Separate credentials if needed

## Support & Resources

- **n8n Documentation:** https://docs.n8n.io/
- **n8n Community:** https://community.n8n.io/
- **OpenAI API Docs:** https://platform.openai.com/docs/
- **Google Drive API:** https://developers.google.com/drive/api/
- **Telegram Bot API:** https://core.telegram.org/bots/api

## Workflow Updates

To update workflows after changes:

1. Export modified workflow from n8n UI
2. Save to `n8n/workflows/` directory
3. Commit changes to version control
4. Import updated workflow in other n8n instances

## License

Part of the Personal Finance Automation project. See root LICENSE file.

## Contributing

1. Test workflow changes in isolated n8n instance
2. Document new nodes and configuration changes
3. Update this README with new features
4. Submit pull request with workflow JSON and documentation
