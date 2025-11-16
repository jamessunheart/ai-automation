# Brevo Email Integration - Quick Setup

**Status**: Ready to activate
**Provider**: Brevo (formerly SendinBlue)
**Purpose**: Email sending for AI Marketing Engine

---

## ✅ What's Ready

1. **Brevo Email Service** - `/marketing_engine/services/email_service_brevo.py`
   - Full Brevo API integration
   - Rate limiting (300/day free tier, 20K/day paid)
   - Email validation
   - Template personalization
   - Tracking (opens/clicks)
   - Bulk sending with delays

2. **Backward Compatible** - Works alongside existing SendGrid service
   - Environment variable based switching
   - Same interface as SendGrid service
   - Drop-in replacement

---

## 🚀 Quick Activation (When Brevo is Ready)

### Step 1: Get Brevo API Key

**From your Brevo account:**
1. Log in to https://app.brevo.com
2. Go to Settings → SMTP & API
3. Click "Create a new API key"
4. Copy the API key (starts with `xkeysib-...`)

### Step 2: Add to Credential Vault

```bash
cd /Users/jamessunheart/Development/docs/coordination/scripts

# Add Brevo API key to vault
export FPAI_CREDENTIALS_KEY="0090050b4ac419b69bfd0b7763d861fd11619255f672b4122c34b97abe12d63f"
./session-set-credential.sh brevo_api_key "xkeysib-YOUR-KEY-HERE" api_key brevo

# Also set sender email (if different from default)
./session-set-credential.sh brevo_from_email "james@fullpotential.com" email brevo
```

### Step 3: Update AI Marketing Engine to Use Brevo

**Option A: Environment Variables (Quick)**
```bash
cd /Users/jamessunheart/Development/SERVICES/ai-automation

# Update start script
cat > start-with-brevo.sh << 'EOF'
#!/bin/bash
export FPAI_CREDENTIALS_KEY="0090050b4ac419b69bfd0b7763d861fd11619255f672b4122c34b97abe12d63f"

# Get credentials from vault
BREVO_KEY=$(../docs/coordination/scripts/session-get-credential.sh brevo_api_key)
BREVO_EMAIL=$(../docs/coordination/scripts/session-get-credential.sh brevo_from_email)

# Export for service
export BREVO_API_KEY="$BREVO_KEY"
export BREVO_FROM_EMAIL="${BREVO_EMAIL:-james@fullpotential.com}"
export BREVO_FROM_NAME="James from Full Potential AI"
export BREVO_DAILY_LIMIT="300"  # Free tier limit

# Start service
python3 -m uvicorn main:app --host 0.0.0.0 --port 8700
EOF

chmod +x start-with-brevo.sh
```

**Option B: Update Existing Service (Production)**

Update `marketing_engine/services/__init__.py`:
```python
# Change from:
from .email_service import EmailService, get_email_service

# To:
from .email_service_brevo import BrevoEmailService as EmailService, get_brevo_service as get_email_service
```

### Step 4: Test Email Sending

```bash
# Start service with Brevo
./start-with-brevo.sh

# In another terminal, test sending
curl -X POST http://localhost:8700/api/marketing/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Brevo Test Campaign",
    "icp": {
      "industries": ["Technology"],
      "company_sizes": ["1-10"],
      "job_titles": ["Founder"]
    }
  }'
```

### Step 5: Deploy to Production

```bash
cd /Users/jamessunheart/Development/SERVICES/ai-automation
export FPAI_CREDENTIALS_KEY="0090050b4ac419b69bfd0b7763d861fd11619255f672b4122c34b97abe12d63f"
./deploy-with-credentials.sh
```

The deploy script will automatically:
- Pull Brevo credentials from vault
- Update environment variables on server
- Restart service with Brevo enabled

---

## 📊 Brevo vs SendGrid

| Feature | SendGrid | Brevo |
|---------|----------|-------|
| **Free Tier** | 100/day | **300/day** ✅ |
| **Paid Tier** | $15/mo (40K emails) | **$25/mo (20K emails)** |
| **Deliverability** | Excellent | Excellent |
| **API** | REST API | REST API |
| **Tracking** | Opens, Clicks | Opens, Clicks |
| **SMTP Relay** | Yes | Yes |
| **Your Issue** | ❌ Won't let you send | ✅ Working |

**Brevo Advantages**:
- 3x more emails on free tier (300 vs 100/day)
- Currently working for you ✅
- Similar API, easy migration
- Better support for EU users

---

## 🔧 Configuration Options

### Environment Variables

```bash
# Required
BREVO_API_KEY="xkeysib-..."

# Optional (with defaults)
BREVO_FROM_EMAIL="james@fullpotential.com"
BREVO_FROM_NAME="James from Full Potential AI"
BREVO_DAILY_LIMIT="300"  # Free tier
```

### Rate Limits

**Free Tier**: 300 emails/day
**Lite Plan** ($25/mo): 20,000 emails/month (667/day)
**Premium Plans**: Up to millions/month

For AI Marketing Engine ($120K MRR target), we'd need:
- 100 prospects/day = 300 emails/day (outreach + follow-ups)
- Free tier: Good for MVP/testing
- Paid tier: Needed for scale (Month 2+)

---

## 🎯 Next Steps

1. **Right Now**: Testing Brevo manually ✅
2. **When Ready**: Add API key to vault (Step 2 above)
3. **Activation**: Run deploy script (Step 5 above)
4. **Result**: AI Marketing Engine 100% operational 🚀

---

## 💡 Migration Path

**Phase 1** (Now): Brevo for outbound marketing
**Phase 2** (Future): Could add SendGrid for transactional emails
**Result**: Best of both worlds - Brevo for campaigns, SendGrid for receipts/notifications

---

## ✅ Checklist

- [ ] Brevo account created
- [ ] Brevo email verified
- [ ] Brevo API key generated
- [ ] API key added to vault
- [ ] Service updated to use Brevo
- [ ] Test email sent successfully
- [ ] Deployed to production
- [ ] AI Marketing Engine 100% operational

---

**Ready to activate as soon as you provide the Brevo API key!**

**Current Status**: Brevo email service coded and ready, waiting for API key from your testing.
