#!/bin/bash
# Deploy AI Marketing Engine to Production with Vault Credentials

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

VAULT_SCRIPTS="/Users/jamessunheart/Development/docs/coordination/scripts"
SERVER="root@198.54.123.234"
REMOTE_PATH="/root/services/ai-automation"

echo -e "${GREEN}🚀 Deploying AI Marketing Engine with Vault Credentials${NC}"
echo ""

# Check FPAI_CREDENTIALS_KEY is set
if [ -z "$FPAI_CREDENTIALS_KEY" ]; then
    echo -e "${RED}❌ FPAI_CREDENTIALS_KEY not set${NC}"
    echo "Set it with: export FPAI_CREDENTIALS_KEY=your_key"
    exit 1
fi

# Retrieve credentials
echo -e "${YELLOW}📥 Retrieving credentials from vault...${NC}"
ANTHROPIC_KEY=$("$VAULT_SCRIPTS/session-get-credential.sh" anthropic_api_key)
echo "✅ ANTHROPIC_API_KEY retrieved"

# Check Brevo (preferred) or SendGrid (fallback)
if BREVO_KEY=$("$VAULT_SCRIPTS/session-get-credential.sh" brevo_api_key 2>/dev/null); then
    HAS_BREVO=true
    BREVO_SENDER=$("$VAULT_SCRIPTS/session-get-credential.sh" brevo_verified_sender 2>/dev/null || echo "james@fullpotential.com")
    echo "✅ BREVO_API_KEY retrieved"
    echo "✅ BREVO verified sender: $BREVO_SENDER"
elif SENDGRID_KEY=$("$VAULT_SCRIPTS/session-get-credential.sh" sendgrid_api_key 2>/dev/null); then
    HAS_SENDGRID=true
    echo "✅ SENDGRID_API_KEY retrieved"
else
    HAS_EMAIL=false
    echo "⚠️  No email service configured - will use simulation mode"
fi

# Apollo.io API (optional but recommended)
if APOLLO_KEY=$("$VAULT_SCRIPTS/session-get-credential.sh" apollo_api_key 2>/dev/null); then
    HAS_APOLLO=true
    echo "✅ APOLLO_API_KEY retrieved"
else
    echo "⚠️  No Apollo API key found (prospect data will be limited)"
fi

# Sync code to server
echo ""
echo -e "${YELLOW}📤 Syncing code to production server...${NC}"
rsync -avz --exclude='*.pyc' --exclude='__pycache__' --exclude='*.log' \
    /Users/jamessunheart/Development/SERVICES/ai-automation/ \
    "$SERVER:$REMOTE_PATH/"
echo "✅ Code synced"

# Stop old process
echo ""
echo -e "${YELLOW}🛑 Stopping old process...${NC}"
ssh "$SERVER" "ps aux | grep 'uvicorn.*8700' | grep -v grep | awk '{print \$2}' | xargs kill 2>/dev/null || echo 'No process running'"

# Start with environment variables
echo ""
echo -e "${YELLOW}🚀 Starting service with vault credentials...${NC}"

# Build environment variables
ENV_VARS="ANTHROPIC_API_KEY='$ANTHROPIC_KEY'"

if [ "$HAS_APOLLO" = true ]; then
    ENV_VARS="$ENV_VARS APOLLO_API_KEY='$APOLLO_KEY'"
fi

if [ "$HAS_BREVO" = true ]; then
    ENV_VARS="$ENV_VARS BREVO_API_KEY='$BREVO_KEY' BREVO_FROM_EMAIL='$BREVO_SENDER' BREVO_FROM_NAME='James from Full Potential AI' BREVO_DAILY_LIMIT='300'"
elif [ "$HAS_SENDGRID" = true ]; then
    ENV_VARS="$ENV_VARS SENDGRID_API_KEY='$SENDGRID_KEY' SENDGRID_FROM_EMAIL='james@fullpotential.com' SENDGRID_FROM_NAME='James from Full Potential AI'"
fi

# Deploy with all credentials
ssh "$SERVER" "cd $REMOTE_PATH && $ENV_VARS nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8700 > logs/app.log 2>&1 &"

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Test service
echo ""
echo -e "${YELLOW}🔍 Testing service...${NC}"
if ssh "$SERVER" "curl -s http://localhost:8700/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Service is running!${NC}"
    echo ""
    echo "Production URL: http://198.54.123.234:8700"
    echo "Health check: http://198.54.123.234:8700/health"
    echo ""
    echo -e "${GREEN}✅ AI agents are now using ANTHROPIC_API_KEY from vault${NC}"
    if [ "$HAS_BREVO" = true ]; then
        echo -e "${GREEN}✅ Email service: Brevo ($BREVO_SENDER) - 300 emails/day${NC}"
        echo -e "${GREEN}🚀 AI Marketing Engine: 100% OPERATIONAL${NC}"
    elif [ "$HAS_SENDGRID" = true ]; then
        echo -e "${GREEN}✅ Email service: SendGrid - 100 emails/day${NC}"
    else
        echo -e "${YELLOW}⚠️  Email sending in simulation mode (add brevo_api_key or sendgrid_api_key to vault)${NC}"
    fi
else
    echo -e "${RED}❌ Service failed to start${NC}"
    echo "Check logs with: ssh $SERVER 'tail -100 $REMOTE_PATH/logs/app.log'"
    exit 1
fi
