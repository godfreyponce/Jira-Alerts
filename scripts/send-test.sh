#!/bin/zsh
# Sends a fake alert payload to your Teams webhook so you can verify the
# Power Automate flow end-to-end without waiting for a real Jira event.
cd "$(dirname "$0:A")/.." || exit 1
set -a; source .env; set +a
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$TEAMS_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket": "TEST-0000",
    "summary": "Webhook test (safe to ignore)",
    "headline": "Test alert",
    "subline": "Sent by scripts/send-test.sh",
    "snippet": "If you can read this in Teams, your flow works.",
    "url": "https://example.com"
  }')
echo "Webhook returned HTTP $code (expect 202)"
