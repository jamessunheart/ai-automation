#!/bin/bash
# AI Marketing Engine - Start with Centralized Vault Credentials
# Automatically retrieves credentials from centralized vault

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_SCRIPTS="/Users/jamessunheart/Development/docs/coordination/scripts"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔐 AI Marketing Engine - Starting with Vault Credentials${NC}"
echo ""

# Check FPAI_CREDENTIALS_KEY is set
if [ -z "$FPAI_CREDENTIALS_KEY" ]; then
    echo -e "${RED}❌ FPAI_CREDENTIALS_KEY not set${NC}"
    echo "Set it with: export FPAI_CREDENTIALS_KEY=your_key"
    exit 1
fi

# Retrieve credentials from vault
echo -e "${YELLOW}📥 Retrieving credentials from vault...${NC}"

export ANTHROPIC_API_KEY=$("$VAULT_SCRIPTS/session-get-credential.sh" anthropic_api_key)
echo "✅ ANTHROPIC_API_KEY retrieved"

# Check if SendGrid is available
if SENDGRID_KEY=$("$VAULT_SCRIPTS/session-get-credential.sh" sendgrid_api_key 2>/dev/null); then
    export SENDGRID_API_KEY="$SENDGRID_KEY"
    echo "✅ SENDGRID_API_KEY retrieved"
else
    echo "⚠️  SENDGRID_API_KEY not in vault - email will be simulated"
fi

if SENDGRID_EMAIL=$("$VAULT_SCRIPTS/session-get-credential.sh" sendgrid_from_email 2>/dev/null); then
    export SENDGRID_FROM_EMAIL="$SENDGRID_EMAIL"
    export SENDGRID_FROM_NAME="James from Full Potential AI"
    echo "✅ SENDGRID_FROM_EMAIL retrieved"
else
    export SENDGRID_FROM_EMAIL="james@fullpotential.com"
    export SENDGRID_FROM_NAME="James from Full Potential AI"
    echo "⚠️  SENDGRID_FROM_EMAIL not in vault - using default"
fi

echo ""
echo -e "${GREEN}🚀 Starting AI Marketing Engine on port 8700...${NC}"
echo ""

# Start the service
cd "$SCRIPT_DIR"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8700
