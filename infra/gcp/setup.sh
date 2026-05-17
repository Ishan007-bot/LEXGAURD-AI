#!/usr/bin/env bash
# ============================================================================
# LexGuard GCP bootstrap.
# Idempotent: re-running is safe.
#
# Usage:
#   PROJECT_ID=my-proj REGION=asia-south1 ./setup.sh
# ============================================================================
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?PROJECT_ID env var required}"
REGION="${REGION:-asia-south1}"
VERTEX_REGION="${VERTEX_REGION:-us-central1}"
SA_NAME="lexguard-runner"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REPO_NAME="lexguard"
UPLOAD_BUCKET="${PROJECT_ID}-lexguard-uploads"
REPORTS_BUCKET="${PROJECT_ID}-lexguard-reports"

echo "==> Project: ${PROJECT_ID}  region: ${REGION}  vertex: ${VERTEX_REGION}"
gcloud config set project "${PROJECT_ID}" >/dev/null

echo "==> Enabling required APIs"
gcloud services enable \
    aiplatform.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    cloudresourcemanager.googleapis.com \
    documentai.googleapis.com \
    dlp.googleapis.com \
    firestore.googleapis.com \
    iamcredentials.googleapis.com \
    identitytoolkit.googleapis.com \
    logging.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    storage.googleapis.com \
    texttospeech.googleapis.com

echo "==> Creating runtime service account (idempotent)"
if ! gcloud iam service-accounts describe "${SA_EMAIL}" >/dev/null 2>&1; then
    gcloud iam service-accounts create "${SA_NAME}" \
        --display-name="LexGuard Cloud Run runtime"
fi

echo "==> Granting least-privilege roles"
for ROLE in \
    roles/aiplatform.user \
    roles/datastore.user \
    roles/storage.objectAdmin \
    roles/documentai.apiUser \
    roles/dlp.user \
    roles/secretmanager.secretAccessor \
    roles/logging.logWriter \
    roles/monitoring.metricWriter \
    roles/cloudtrace.agent
do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="${ROLE}" \
        --condition=None >/dev/null
done

echo "==> Creating Artifact Registry repo"
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" >/dev/null 2>&1; then
    gcloud artifacts repositories create "${REPO_NAME}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="LexGuard container images"
fi

echo "==> Creating GCS buckets"
for BUCKET in "${UPLOAD_BUCKET}" "${REPORTS_BUCKET}"; do
    if ! gcloud storage buckets describe "gs://${BUCKET}" >/dev/null 2>&1; then
        gcloud storage buckets create "gs://${BUCKET}" \
            --location="${REGION}" \
            --uniform-bucket-level-access \
            --public-access-prevention
    fi
done

echo "==> Creating Firestore (Native) in ${REGION}"
if ! gcloud firestore databases describe --database="(default)" >/dev/null 2>&1; then
    gcloud firestore databases create --location="${REGION}" --type=firestore-native
fi

cat <<EOF

==============================================================================
GCP bootstrap complete.

  Project:           ${PROJECT_ID}
  Region:            ${REGION}
  Vertex region:     ${VERTEX_REGION}
  Service account:   ${SA_EMAIL}
  Artifact Registry: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}
  Upload bucket:     gs://${UPLOAD_BUCKET}
  Reports bucket:    gs://${REPORTS_BUCKET}

Next steps (manual):
  1. Create a Document AI 'Form Parser' processor in ${VERTEX_REGION}; copy the
     processor ID into .env.
  2. Enable Firebase Auth (Google provider) in the Firebase console.
  3. Set GitHub Actions secrets: GCP_PROJECT_ID, GCP_WORKLOAD_IDENTITY_PROVIDER,
     GCP_SERVICE_ACCOUNT (=${SA_EMAIL}).
==============================================================================
EOF
