# Usage Guide

User guide for the Personal Finance Automation system - from first transaction to monthly reports.

## Table of Contents

- [Getting Started](#getting-started)
- [Dashboard Overview](#dashboard-overview)
- [Adding Transactions](#adding-transactions)
- [Understanding Categories](#understanding-categories)
- [Manual Categorization](#manual-categorization)
- [Viewing Reports](#viewing-reports)
- [Managing Vendors](#managing-vendors)
- [Working with Alerts](#working-with-alerts)
- [Receipt Management](#receipt-management)
- [Customizing Rules](#customizing-rules)
- [Tips & Best Practices](#tips--best-practices)
- [Common Workflows](#common-workflows)
- [FAQ](#faq)

## Getting Started

### First-Time Setup

1. **Access the dashboard** at http://localhost:8080
2. **Verify connectivity** - should see welcome screen
3. **Upload your first statement** (see [Adding Transactions](#adding-transactions))
4. **Review categorization** in the Review Queue
5. **Explore reports** to see your spending patterns

### Dashboard Tour

The dashboard has five main sections:

1. **Overview Cards** - Quick stats (income, expenses, savings)
2. **Category Breakdown** - Donut chart of spending by category
3. **Top Vendors** - Where your money goes
4. **Recent Transactions** - Latest activity
5. **Review Queue** - Transactions needing review

## Dashboard Overview

### Overview Cards

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Income     │  │   Expenses   │  │   Savings    │
│   $5,432     │  │   $3,210     │  │   $2,222     │
│   +12% ↑     │  │   -5% ↓      │  │   +25% ↑     │
└──────────────┘  └──────────────┘  └──────────────┘
```

- **Income**: Total credits (salary, refunds, transfers in)
- **Expenses**: Total debits (purchases, bills, subscriptions)
- **Savings**: Income minus expenses
- **Trend**: Percentage change vs. last month

### Category Breakdown

Interactive donut chart showing:
- **Spending by category** - Click to drill down
- **Percentage of total** - Hover for details
- **Monthly comparison** - See trends

Top categories typically:
1. Groceries (20-30%)
2. Dining (10-15%)
3. Rent/Mortgage (25-35%)
4. Utilities (5-10%)
5. Transportation (5-10%)

### Top Vendors

List of merchants with most spending:
```
1. Hy-Vee              $420.50  (Groceries)
2. Amazon              $385.20  (Shopping)
3. Starbucks           $156.80  (Dining > Coffee)
4. Shell               $125.40  (Fuel)
5. Netflix             $15.99   (Subscriptions)
```

### Recent Transactions

Real-time feed of latest transactions:
```
Date       Vendor           Amount    Category          Status
---------- ---------------- --------- ----------------- ----------
2025-10-26 Hy-Vee           $45.23    Groceries         Finalized
2025-10-26 Starbucks        $6.75     Dining > Coffee   Finalized
2025-10-25 Amazon           $129.99   Shopping          Review
2025-10-25 Shell #1234      $42.00    Fuel              Finalized
```

### Review Queue

Transactions requiring manual review:
- **Low confidence** (<80%) - AI uncertain
- **High value** (>$50) - Double-check important purchases
- **New vendors** - First-time merchants
- **Anomalies** - Unusual patterns

## Adding Transactions

### Method 1: Google Drive (Recommended)

**Automatic ingestion via n8n workflow:**

1. Drop statement in Google Drive: `Finance/Statements/`
2. n8n detects new file within 1 minute
3. Parses transactions (CSV/PDF/OFX)
4. POSTs to API for categorization
5. Appears in dashboard within 2 minutes

**Supported formats:**
- **CSV**: Most bank exports
- **PDF**: Statement PDFs with text layer
- **OFX**: Quicken/Mint format

**Folder structure:**
```
Finance/
├── Statements/
│   ├── 2025-10/
│   │   ├── visa_oct.csv
│   │   ├── amex_oct.pdf
│   │   └── checking_oct.ofx
│   └── 2025-11/
└── Receipts/
    └── 2025-10/
```

### Method 2: Manual Upload (Dashboard)

1. Click **"Upload Statement"** button
2. Select file from your computer
3. Choose **source account** (visa_primary, amex, checking)
4. Click **"Upload & Process"**
5. Wait for processing (5-30 seconds depending on size)
6. Review results in dashboard

### Method 3: API (Advanced)

**Single transaction:**

```bash
curl -X POST http://localhost:8080/api/ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "txn_date": "2025-10-26",
    "amount_cents": 4523,
    "currency": "USD",
    "direction": "debit",
    "raw_descriptor": "HY-VEE #1234 DES MOINES IA",
    "source_account": "visa_primary",
    "mcc": "5411",
    "memo": "Weekly groceries",
    "hash_id": "a1b2c3d4e5f6789..."
  }'
```

**Response:**

```json
{
  "id": 1523,
  "status": "ingested",
  "category": "Groceries",
  "confidence": 0.95
}
```

### Understanding Hash IDs

Transactions are deduplicated using SHA-256 hash:

```
hash_id = sha256(date + amount_cents + descriptor + account)
```

This prevents duplicate imports when re-uploading statements.

## Understanding Categories

### Category Taxonomy

**Core Categories:**

| Category | Subcategories | Examples |
|----------|---------------|----------|
| **Groceries** | Supermarket, Organic, Wholesale | Hy-Vee, Whole Foods, Costco |
| **Dining** | Restaurant, Fast Food, Coffee | Chipotle, McDonald's, Starbucks |
| **Transport** | Rideshare, Taxi, Public Transit | Uber, Lyft, Metro |
| **Fuel** | Gas Station, Car Wash | Shell, BP, Sinclair |
| **Utilities** | Electric, Gas, Water, Trash | MidAmerican Energy |
| **Rent/Mortgage** | Rent, Mortgage Payment | Monthly housing |
| **Internet** | ISP, Hosting | Mediacom, AWS |
| **Mobile** | Cell Phone | Verizon, T-Mobile |
| **Subscriptions** | Streaming, Software, Memberships | Netflix, Spotify, Adobe |
| **Shopping** | Online, Retail, Clothing | Amazon, Target, Macy's |
| **Healthcare** | Pharmacy, Doctor, Dental | CVS, Clinic |
| **Pets** | Vet, Pet Store, Pet Food | Petco, VCA |
| **Gifts/Charity** | Donations, Gifts | Red Cross, Birthday gifts |
| **Entertainment** | Movies, Concerts, Events | AMC Theaters |
| **Travel-Air** | Airlines, Airfare | Delta, United |
| **Travel-Hotel** | Hotels, Lodging | Marriott, Airbnb |
| **Travel-Other** | Rental Cars, Travel Misc | Hertz, tour packages |
| **Income** | Salary, Refunds, Bonuses | Paycheck deposits |
| **Transfers** | Internal, Savings, Payments | Own account transfers |
| **Savings** | Investment, Savings Account | 401k, IRA |

### Categorization Flow

```
Transaction received
    │
    ▼
┌─────────────────────────┐
│ Step 1: Apply Rules     │  (70% success rate)
│ - MCC code matching     │
│ - Vendor regex          │
│ - Amount patterns       │
└──────────┬──────────────┘
           │ No match
           ▼
┌─────────────────────────┐
│ Step 2: OpenAI          │  (30% of transactions)
│ - GPT-4o-mini analysis  │
│ - Confidence scoring    │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Step 3: Review Queue    │  (if needed)
│ - Confidence < 0.80     │
│ - Amount > $50          │
│ - New vendor            │
└─────────────────────────┘
```

### Confidence Scores

- **1.00** - Rule match (deterministic)
- **0.90-0.99** - High confidence AI
- **0.80-0.89** - Medium confidence AI → Review
- **0.70-0.79** - Low confidence AI → Review
- **<0.70** - Very uncertain → Review

## Manual Categorization

### Review Queue

Access at: http://localhost:8080/review

**Transaction card shows:**

```
┌──────────────────────────────────────────────┐
│ AMAZON.COM MKTP US         $129.99           │
│ Date: 2025-10-25           Confidence: 72%   │
│                                              │
│ AI Suggestion: Shopping > Online             │
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ Category:     [Shopping ▼]               │ │
│ │ Subcategory:  [Online ▼]                 │ │
│ │ Notes:        [Optional notes...]        │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ [✓ Accept]  [✏️ Modify]  [❌ Reject]        │
└──────────────────────────────────────────────┘
```

### Finalizing Transactions

**Option 1: Accept AI Suggestion**

Click **"Accept"** to finalize with AI category.

**Option 2: Modify Category**

1. Select different **category** from dropdown
2. Choose **subcategory** (appears after category selection)
3. Add **notes** (optional)
4. Click **"Finalize"**

**Option 3: Reject (Rare)**

Use for erroneous transactions that shouldn't be categorized.

### Batch Review

Review multiple transactions:

1. Click **"Select Multiple"** checkbox
2. Choose transactions to review
3. Select **"Bulk Action"** dropdown:
   - Apply category to all
   - Mark all as reviewed
   - Export selection

## Viewing Reports

### Monthly Summary

**Access:** http://localhost:8080/report/summary?month=2025-10

**Includes:**

1. **Overview Metrics**
   - Total income
   - Total expenses
   - Net savings
   - Savings rate %

2. **Category Breakdown**
   - Spending by category
   - Percentage of total
   - Change vs. last month

3. **Top Vendors**
   - Highest spending merchants
   - Total per vendor
   - Transaction count

4. **Daily Spending Trend**
   - Line chart of daily totals
   - Running average
   - Spending spikes highlighted

5. **Insights**
   - AI-generated observations
   - Spending patterns
   - Recommendations

### Custom Date Ranges

Use API for custom ranges:

```bash
curl "http://localhost:8080/api/report/summary?start_date=2025-10-01&end_date=2025-10-31"
```

### Exporting Data

**CSV Export:**

```bash
curl "http://localhost:8080/api/transactions?month=2025-10&format=csv" > transactions.csv
```

**JSON Export:**

```bash
curl "http://localhost:8080/api/transactions?month=2025-10" > transactions.json
```

## Managing Vendors

### Canonical Vendor Names

The system normalizes messy merchant names:

**Original → Canonical**
- `STARBUCKS STORE #1234` → `Starbucks`
- `AMAZON.COM MKTP US*AB12CD` → `Amazon`
- `SQ *COFFEE SHOP` → `Square: Coffee Shop`
- `TST* RESTAURANT NAME` → `Toast: Restaurant Name`

### Adding Vendor Aliases

**Via API:**

```bash
curl -X POST http://localhost:8080/api/vendors \
  -H "Content-Type: application/json" \
  -d '{
    "canonical_vendor": "Starbucks",
    "default_category": "Dining",
    "default_subcat": "Coffee",
    "aliases": [
      "STARBUCKS",
      "SBUX",
      "SBX",
      "STARBUCKS COFFEE"
    ]
  }'
```

**Via Database:**

```sql
INSERT INTO vendors (canonical_vendor, default_category, default_subcat, aliases)
VALUES (
  'Starbucks',
  'Dining',
  'Coffee',
  ARRAY['STARBUCKS', 'SBUX', 'SBX', 'STARBUCKS COFFEE']
);
```

### Viewing All Vendors

```bash
curl http://localhost:8080/api/vendors
```

## Working with Alerts

### Alert Types

**1. New Vendor Over Threshold**

Triggered when first transaction with vendor >$50:

```json
{
  "type": "new_vendor_over_threshold",
  "vendor": "Acme Gym",
  "amount_cents": 9999,
  "date": "2025-10-26",
  "action": "Review this new recurring charge"
}
```

**2. Duplicate Transaction**

Same hash_id detected:

```json
{
  "type": "duplicate_detected",
  "transaction_id": 1234,
  "duplicate_of": 1230,
  "action": "Check if this is a duplicate import"
}
```

**3. Spending Spike**

Z-score >2.0 for category:

```json
{
  "type": "spending_spike",
  "category": "Dining",
  "amount_cents": 45000,
  "avg_cents": 25000,
  "z_score": 2.3,
  "action": "Unusual spending in this category"
}
```

**4. Missing Receipt**

High-value transaction without receipt:

```json
{
  "type": "missing_receipt",
  "transaction_id": 1235,
  "vendor": "Best Buy",
  "amount_cents": 89999,
  "action": "Add receipt from Google Drive"
}
```

### Viewing Alerts

**Dashboard:** Red notification badge shows count

**API:**

```bash
curl http://localhost:8080/api/alerts
```

### Dismissing Alerts

Click **"Dismiss"** on each alert or mark as reviewed.

## Receipt Management

### Linking Receipts

**Automatic (via n8n):**

1. Upload receipt image to `Finance/Receipts/YYYY-MM/`
2. n8n workflow matches by date and amount (±10%)
3. Updates transaction with `receipt_url`

**Manual:**

1. Open transaction detail
2. Click **"Add Receipt"**
3. Enter Google Drive file URL
4. Save

### Receipt Naming Convention

```
Finance/Receipts/2025-10/
├── 2025-10-26_starbucks_6.75.jpg
├── 2025-10-26_hyvee_45.23.pdf
└── 2025-10-25_amazon_129.99.jpg
```

**Format:** `YYYY-MM-DD_vendor_amount.ext`

### Viewing Receipts

Click **"View Receipt"** on transaction to open Google Drive link.

## Customizing Rules

### Rule Structure

Rules are JSON-based with priority ordering:

```json
{
  "priority": 10,
  "active": true,
  "condition": {
    "mcc": ["5411", "5422"]
  },
  "action": {
    "category": "Groceries",
    "subcategory": "Supermarket"
  }
}
```

### Creating Rules

**Via API:**

```bash
curl -X POST http://localhost:8080/api/rules \
  -H "Content-Type: application/json" \
  -d '{
    "priority": 50,
    "active": true,
    "condition": {
      "descriptor_contains": "NETFLIX"
    },
    "action": {
      "category": "Subscriptions",
      "subcategory": "Streaming"
    }
  }'
```

**Via Database:**

```sql
INSERT INTO rules (priority, condition, action, active)
VALUES (
  50,
  '{"descriptor_contains": "NETFLIX"}',
  '{"category": "Subscriptions", "subcategory": "Streaming"}',
  true
);
```

### Rule Conditions

**Available condition types:**

- `mcc` - Merchant category code list
- `descriptor_contains` - Case-insensitive substring
- `descriptor_regex` - Regular expression
- `amount_min_cents` - Minimum amount
- `amount_max_cents` - Maximum amount
- `account` - Source account filter
- `direction` - "debit" or "credit"

**Examples:**

```json
// Match any grocery store MCC
{"mcc": ["5411", "5422", "5499"]}

// Match Starbucks locations
{"descriptor_regex": "STARBUCKS.*"}

// Match large transactions
{"amount_min_cents": 50000}

// Match specific account
{"account": "amex_blue_cash"}

// Combine multiple conditions (AND)
{
  "mcc": ["5812"],
  "amount_max_cents": 2000
}
```

### Rule Priority

Lower number = higher priority (processed first):

- **1-10**: Critical rules (overrides)
- **11-50**: Standard rules (common patterns)
- **51-100**: Low priority (fallbacks)

## Tips & Best Practices

### Transaction Upload

✅ **DO:**
- Upload complete monthly statements
- Use consistent file naming
- Keep statements in Google Drive organized by month
- Review new vendors immediately

❌ **DON'T:**
- Upload partial statements (causes duplicate confusion)
- Mix multiple accounts in one file
- Delete statements after upload (keep for records)
- Ignore review queue

### Categorization

✅ **DO:**
- Review high-value transactions (>$50)
- Add notes for unusual purchases
- Update rules for recurring patterns
- Keep vendor aliases updated

❌ **DON'T:**
- Accept low-confidence AI suggestions blindly
- Create overly specific categories
- Ignore anomaly alerts
- Skip monthly review

### Reports & Analysis

✅ **DO:**
- Review monthly summary for patterns
- Set spending goals per category
- Track savings rate trend
- Export data for tax purposes

❌ **DON'T:**
- Obsess over daily fluctuations
- Create too many subcategories
- Ignore seasonal patterns

### Security

✅ **DO:**
- Use strong, unique passwords
- Access via VPN/Tailscale
- Regular backups
- Monitor for suspicious transactions

❌ **DON'T:**
- Share API keys
- Expose dashboard publicly
- Store passwords in plaintext
- Skip security updates

## Common Workflows

### Weekly Review Routine

**Every Monday:**

1. Check **Review Queue** (5 min)
2. Finalize pending transactions
3. Review **Alerts** (2 min)
4. Check **Top Vendors** for surprises
5. Quick **category scan** for anomalies

**Time: ~10 minutes**

### Monthly Close Routine

**First of each month:**

1. Upload **all bank statements** for previous month
2. Wait for processing (2-5 minutes)
3. Review **all transactions** from last month
4. Finalize **review queue**
5. Generate **monthly report**
6. Export data for **personal records**
7. Review **spending vs. budget**
8. Adjust **rules** if needed

**Time: ~30-45 minutes**

### Quarterly Analysis

**Every 3 months:**

1. Export **quarterly CSV**
2. Compare **quarter-over-quarter** trends
3. Review **vendor changes** (new/removed)
4. Analyze **category shifts**
5. Update **spending goals**
6. Review and optimize **rules**

**Time: ~1-2 hours**

## FAQ

### General

**Q: How long does transaction processing take?**
A: 1-2 minutes from file upload to dashboard visibility.

**Q: Can I edit past transactions?**
A: Yes, via API or by re-categorizing in the review interface.

**Q: Are my transactions stored locally?**
A: Yes, all data in your homelab PostgreSQL database.

**Q: Can multiple people use the system?**
A: Currently single-user. Multi-user support requires JWT authentication setup.

### Categorization

**Q: Why is confidence low on some transactions?**
A: Unknown vendors, ambiguous descriptors, or unusual patterns.

**Q: Can I change the category taxonomy?**
A: Yes, edit the taxonomy in `api/app/categorize.py` and update AI prompts.

**Q: How accurate is AI categorization?**
A: ~90-95% for common vendors, 70-80% for unknown merchants.

**Q: What happens if I disagree with AI?**
A: Manually finalize with your category. System learns from your choices over time (future feature).

### Technical

**Q: How do I add a new source account?**
A: Just use a new identifier in `source_account` field (e.g., "discover_card").

**Q: Can I import historical data?**
A: Yes, upload old statements - deduplication prevents duplicates.

**Q: How do I reset the database?**
A: `make down`, delete `postgres_data` volume, `make up`, `make migrate`, `make seed`.

**Q: Is there a mobile app?**
A: Not yet. Dashboard is responsive and works on mobile browsers.

### Errors

**Q: Transaction didn't appear after upload**
A: Check API logs: `make logs-api` for errors.

**Q: Duplicate transaction detected**
A: Same hash_id exists. Either a duplicate upload or legitimate duplicate charge.

**Q: OpenAI API error**
A: Check API key, quota, and network connectivity to OpenAI.

**Q: Receipt not linking**
A: Ensure receipt date/amount within ±3 days and ±10% of transaction.

---

**Need help?** Check logs with `make logs` or review [Troubleshooting](DEPLOYMENT.md#troubleshooting) section.

**Suggestions?** This is a personal project - feel free to customize and extend!
