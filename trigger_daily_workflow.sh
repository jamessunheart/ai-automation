#!/bin/bash

# Trigger daily workflow for AI Marketing Engine

CAMPAIGN_ID="${1:-campaign_1}"
SCRIPTS_DIR="/Users/jamessunheart/Development/docs/coordination/scripts"

echo "🚀 Triggering Daily Workflow for Campaign: $CAMPAIGN_ID"
echo ""

# Send trigger message to orchestrator
"$SCRIPTS_DIR/session-send-message.sh" \
    marketing-orchestrator \
    "RUN_DAILY_WORKFLOW $CAMPAIGN_ID"

echo "✅ Workflow triggered for $CAMPAIGN_ID"
echo ""
echo "Monitor progress:"
echo "  $SCRIPTS_DIR/session-check-messages.sh marketing-orchestrator"
echo ""
echo "View all session status:"
echo "  $SCRIPTS_DIR/session-status.sh | grep marketing"
