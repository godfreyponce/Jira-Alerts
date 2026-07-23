"""Configuration, loaded from environment variables.

Nothing secret is hard-coded. At runtime these come from GitHub Actions
secrets / repo variables (or a local .env if you use one for testing).
"""

import os


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise SystemExit(
            f"Missing required environment variable: {name}. "
            "Set it as a GitHub Actions secret/variable (or in your local .env)."
        )
    return val


# --- Jira (Data Center) ---
JIRA_BASE_URL = _require("JIRA_BASE_URL").rstrip("/")   # e.g. https://jira.example.com
JIRA_PAT = _require("JIRA_PAT")                          # Personal Access Token (Bearer)
JIRA_USERNAME = _require("JIRA_USERNAME")               # e.g. your-jira-username
JIRA_USER_KEY = _require("JIRA_USER_KEY")               # e.g. JIRAUSER00000

# --- Teams ---
TEAMS_WEBHOOK_URL = _require("TEAMS_WEBHOOK_URL")       # the Workflows webhook URL

# --- Tuning (all optional, sensible defaults) ---
# How far back the JQL looks. Keep comfortably larger than the cron interval
# so overlapping windows never leave a gap; dedup prevents repeat alerts.
LOOKBACK_MINUTES = int(os.environ.get("LOOKBACK_MINUTES", "30"))

# Drop remembered comment IDs older than this so state.json stays small.
PRUNE_DAYS = int(os.environ.get("PRUNE_DAYS", "30"))

# Max comments to inspect per issue per cycle (most-recent first).
COMMENTS_PER_ISSUE = int(os.environ.get("COMMENTS_PER_ISSUE", "20"))

# Truncate the comment snippet shown in the card to this many characters.
SNIPPET_CHARS = int(os.environ.get("SNIPPET_CHARS", "280"))

# Flood valve: if one cycle wants to send more cards than this, collapse the
# burst into a single digest card so the Teams webhook is never throttled.
MAX_CARDS_PER_CYCLE = int(os.environ.get("MAX_CARDS_PER_CYCLE", "10"))

# Where dedup state lives (relative to repo root).
STATE_PATH = os.environ.get("STATE_PATH", "state.json")

# Mention markers we treat as "this comment @mentions me".
MENTION_TOKENS = [
    f"[~{JIRA_USERNAME}]",
    f"[~accountid:{JIRA_USER_KEY}]",
]
