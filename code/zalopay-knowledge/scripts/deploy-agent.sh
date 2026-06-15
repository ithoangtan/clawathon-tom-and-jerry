#!/usr/bin/env bash
# deploy-agent.sh — Build, push, and deploy zalopay-knowledge to AgentBase Runtime.
#
# Usage:
#   bash scripts/deploy-agent.sh                  # build + push + update runtime
#   bash scripts/deploy-agent.sh --push-only      # skip build, push existing local image + update runtime
#   bash scripts/deploy-agent.sh --tag <tag>      # use specific tag
#   bash scripts/deploy-agent.sh --dry-run        # preview only, no changes
#   bash scripts/deploy-agent.sh --clean          # prune old local images + build from scratch (--no-cache)
#
# First-time setup:
#   1. Copy .env.example → .env and fill secrets (see variable comments in .env.example).
#   2. Ensure IAM credentials are set (GREENNODE_CLIENT_ID + GREENNODE_CLIENT_SECRET in env,
#      or .greennode.json in project root).
#   3. Ensure Docker is running.

set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────────────────

RUNTIME_NAME="zalopay-knowledge"
RUNTIME_DESCRIPTION="ZaloPay Knowledge Agent"
FLAVOR_ID="runtime-s2-general-4x8"  # 2 CPU, 8 GB
ENV_FILE=".env"
PLATFORM="linux/amd64"

# Path to the agentbase scripts (sibling repo — adjust if moved)
AGENTBASE_SCRIPTS="$(cd "$(dirname "$0")/../.." && pwd)/greennode-agentbase-skills/.claude/skills/agentbase/scripts"

# ── Parse flags ────────────────────────────────────────────────────────────────

TAG="v$(date +%Y%m%d%H%M%S)"
DRY_RUN=false
SKIP_BUILD=false
CLEAN_BUILD=false
NO_CACHE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)        TAG="$2"; shift 2 ;;
    --env-file)   ENV_FILE="$2"; shift 2 ;;
    --flavor)     FLAVOR_ID="$2"; shift 2 ;;
    --push-only)  SKIP_BUILD=true; shift ;;
    --dry-run)    DRY_RUN=true; shift ;;
    --clean)      CLEAN_BUILD=true; NO_CACHE="--no-cache"; shift ;;
    --help|-h)
      sed -n '2,14p' "$0" | sed 's/^# *//'
      exit 0 ;;
    *) echo "ERROR: Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ── Validation ─────────────────────────────────────────────────────────────────

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "==> Checking prerequisites..."

if [ ! -f "Dockerfile" ]; then
  echo "ERROR: Dockerfile not found in project root ($PROJECT_ROOT)" >&2
  exit 1
fi

if [ ! -d "$AGENTBASE_SCRIPTS" ]; then
  echo "ERROR: AgentBase scripts not found at: $AGENTBASE_SCRIPTS" >&2
  echo "       Clone greennode-agentbase-skills as a sibling of this repo." >&2
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: Env file not found: $ENV_FILE" >&2
  echo "       Copy .env.example to .env and fill in the required values." >&2
  exit 1
fi

# Check IAM credentials
bash "$AGENTBASE_SCRIPTS/check_credentials.sh" iam
echo ""

# ── Container Registry info ────────────────────────────────────────────────────

echo "==> Fetching Container Registry info..."
CR_REPO_JSON=$(bash "$AGENTBASE_SCRIPTS/cr.sh" repo get)
REGISTRY_URL=$(echo "$CR_REPO_JSON" | jq -r '.registryUrl // empty')
REPO_NAME=$(echo "$CR_REPO_JSON" | jq -r '.name // empty')

if [ -z "$REGISTRY_URL" ] || [ -z "$REPO_NAME" ]; then
  echo "ERROR: Could not read registryUrl or name from CR API." >&2
  echo "$CR_REPO_JSON" >&2
  exit 1
fi

IMAGE_PATH="${REGISTRY_URL}/${REPO_NAME}/${RUNTIME_NAME}"
IMAGE_FULL="${IMAGE_PATH}:${TAG}"

echo "  Registry : $REGISTRY_URL"
echo "  Image    : $IMAGE_FULL"
echo "  Env file : $ENV_FILE"
echo "  Flavor   : $FLAVOR_ID"
echo "  Platform : $PLATFORM"
echo ""

if [ "$DRY_RUN" = true ]; then
  echo "[dry-run] Would $([ "$SKIP_BUILD" = true ] && echo "push" || echo "build + push") → create/update runtime. Exiting."
  exit 0
fi

# ── Step 1: Clean (optional) ───────────────────────────────────────────────────

if [ "$CLEAN_BUILD" = true ] && [ "$SKIP_BUILD" = false ]; then
  echo "==> Cleaning old local images for '$RUNTIME_NAME'..."
  OLD_IMAGES=$(docker images --filter "reference=*/${RUNTIME_NAME}:*" --filter "reference=${RUNTIME_NAME}:*" -q 2>/dev/null || true)
  if [ -n "$OLD_IMAGES" ]; then
    # shellcheck disable=SC2086
    docker rmi -f $OLD_IMAGES 2>/dev/null || true
    echo "  Removed old images."
  else
    echo "  No old images found."
  fi
  echo "==> Pruning dangling images and stopped containers..."
  docker container prune -f --filter "label=app=zalopay-knowledge" 2>/dev/null || true
  docker image prune -f 2>/dev/null || true
  echo ""
fi

# ── Step 2: Build (skippable) ──────────────────────────────────────────────────

if [ "$SKIP_BUILD" = true ]; then
  echo "==> Skipping build (--push-only), using local image $IMAGE_FULL"
  echo ""
else
  echo "==> Building Docker image ($PLATFORM)${NO_CACHE:+ [no-cache]}..."
  # shellcheck disable=SC2086
  docker build --platform "$PLATFORM" $NO_CACHE -t "$IMAGE_FULL" .
  echo ""
fi

# ── Step 3: Login & Push ───────────────────────────────────────────────────────

echo "==> Logging in to AgentBase Container Registry..."
bash "$AGENTBASE_SCRIPTS/cr.sh" credentials docker-login
echo ""

echo "==> Pushing image..."
docker push "$IMAGE_FULL"
echo ""

# ── Step 4: Create or Update Runtime ──────────────────────────────────────────

echo "==> Checking for existing runtime '$RUNTIME_NAME'..."
RUNTIME_LIST=$(bash "$AGENTBASE_SCRIPTS/runtime.sh" list)
RUNTIME_ID=$(echo "$RUNTIME_LIST" | jq -r --arg name "$RUNTIME_NAME" \
  '.listData[]? | select(.name == $name) | .id // empty' | head -1)

COMMON_ARGS=(
  --image     "$IMAGE_FULL"
  --flavor    "$FLAVOR_ID"
  --env-file  "$ENV_FILE"
  --from-cr
  --min-replicas 1
  --max-replicas 1
  --cpu-scale    50
  --mem-scale    50
)

if [ -z "$RUNTIME_ID" ]; then
  echo "==> Creating new runtime '$RUNTIME_NAME'..."
  bash "$AGENTBASE_SCRIPTS/runtime.sh" create \
    --name        "$RUNTIME_NAME" \
    --description "$RUNTIME_DESCRIPTION" \
    "${COMMON_ARGS[@]}"
else
  echo "==> Updating existing runtime (id: $RUNTIME_ID)..."
  bash "$AGENTBASE_SCRIPTS/runtime.sh" update "$RUNTIME_ID" \
    "${COMMON_ARGS[@]}"
fi

echo ""
echo "==> Deploy complete!"
echo "    Image : $IMAGE_FULL"
echo "    View  : https://aiplatform.console.vngcloud.vn/agent-runtime?tab=runtime"
