#!/usr/bin/env bash
# =============================================================================
# Kisan Agent — Cloud Run Deploy Script
# =============================================================================
# This script handles the full deployment pipeline in one command.
# It ensures all post-deploy configurations are always applied correctly.
#
# Usage:
#   ./deploy.sh
#
# Prerequisites:
#   - gcloud CLI authenticated and configured
#   - agents-cli installed (uv tool install google-agents-cli)
#   - Secrets already created in Secret Manager:
#       - DATA_GOV_IN_API_KEY
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration (edit these as needed)
# ---------------------------------------------------------------------------
PROJECT_ID="kisan-agent-500311"
REGION="us-central1"
SERVICE_NAME="kisan-agent"
MAX_INSTANCES=2
MIN_INSTANCES=0

# Secrets mapping: ENV_VAR_NAME=SECRET_NAME
SECRETS="DATA_GOV_IN_API_KEY=DATA_GOV_IN_API_KEY"

# Environment variables
ENV_VARS="GOOGLE_CLOUD_LOCATION=global"

# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------
echo "🚀 Step 1/3: Deploying ${SERVICE_NAME} to Cloud Run (${REGION})..."
agents-cli deploy \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --secrets "${SECRETS}" \
  --update-env-vars "${ENV_VARS}" \
  --no-confirm-project

echo ""

# ---------------------------------------------------------------------------
# Post-deploy: Fix instance scaling (agents-cli resets to its defaults)
# ---------------------------------------------------------------------------
echo "⚙️  Step 2/3: Setting instance limits (min=${MIN_INSTANCES}, max=${MAX_INSTANCES})..."
gcloud run services update "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --max-instances="${MAX_INSTANCES}" \
  --min-instances="${MIN_INSTANCES}" \
  --quiet

echo ""

# ---------------------------------------------------------------------------
# Post-deploy: Ensure public access (agents-cli uses --no-allow-unauthenticated)
# ---------------------------------------------------------------------------
echo "🌐 Step 3/3: Granting public access (allUsers → roles/run.invoker)..."
gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --quiet

echo ""

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")

echo "============================================="
echo "✅ Deployment complete!"
echo "🔗 Service URL: ${SERVICE_URL}"
echo "🛡️  Max instances: ${MAX_INSTANCES}"
echo "🌐 Public access: enabled"
echo "============================================="
