#!/bin/bash

# Start all AI Marketing Engine sessions

SCRIPTS_DIR="/Users/jamessunheart/Development/docs/coordination/scripts"

echo "🚀 Starting AI Marketing Engine Sessions..."
echo ""

# Session #1: Orchestrator
echo "Starting Session #1: Orchestrator..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-orchestrator \
    "Coordinating AI marketing engine workflow"

# Sessions #2-#3: Research
echo "Starting Session #2: Research Team 1..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-research-1 \
    "Finding and scoring prospects (batch 1)"

echo "Starting Session #3: Research Team 2..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-research-2 \
    "Finding and scoring prospects (batch 2)"

# Sessions #4-#6: Outreach
echo "Starting Session #4: Outreach Team 1..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-outreach-1 \
    "Personalizing and sending outreach (batch 1)"

echo "Starting Session #5: Outreach Team 2..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-outreach-2 \
    "Personalizing and sending outreach (batch 2)"

echo "Starting Session #6: Outreach Team 3..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-outreach-3 \
    "Afternoon outreach batch"

# Sessions #7-#9: Conversation
echo "Starting Session #7: Conversation Team 1..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-conversation-1 \
    "Handling replies and qualification"

echo "Starting Session #8: Conversation Team 2..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-conversation-2 \
    "Reply analysis and auto-response"

echo "Starting Session #9: Conversation Team 3..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-conversation-3 \
    "High-value reply management"

# Sessions #10-#12: Human Helpers
echo "Starting Session #10: Human Approver..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-human-approver \
    "Prospect approval interface"

echo "Starting Session #11: Sales Closer 1..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-sales-closer-1 \
    "Sales calls and deal closing"

echo "Starting Session #12: Sales Closer 2..."
"$SCRIPTS_DIR/session-start.sh" \
    marketing-sales-closer-2 \
    "Backup sales closer"

echo ""
echo "✅ All 12 marketing sessions started"
echo ""
echo "Monitor status:"
echo "  $SCRIPTS_DIR/session-status.sh | grep marketing"
echo ""
echo "View messages:"
echo "  $SCRIPTS_DIR/session-check-messages.sh marketing-orchestrator"
echo ""
echo "Next: Trigger daily workflow:"
echo "  ./trigger_daily_workflow.sh campaign_1"
