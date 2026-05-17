# ============================================================================
# LexGuard GCP bootstrap (Windows PowerShell port of setup.sh).
# Idempotent: re-running is safe.
#
# Usage:
#   $env:PROJECT_ID = "my-proj"; $env:REGION = "asia-south1"
#   .\setup.ps1
# ============================================================================
$ErrorActionPreference = "Stop"

if (-not $env:PROJECT_ID) { throw "PROJECT_ID env var required" }
$ProjectId     = $env:PROJECT_ID
$Region        = if ($env:REGION)        { $env:REGION }        else { "asia-south1" }
$VertexRegion  = if ($env:VERTEX_REGION) { $env:VERTEX_REGION } else { "us-central1" }
$SaName        = "lexguard-runner"
$SaEmail       = "$SaName@$ProjectId.iam.gserviceaccount.com"
$RepoName      = "lexguard"
$UploadBucket  = "$ProjectId-lexguard-uploads"
$ReportsBucket = "$ProjectId-lexguard-reports"

Write-Host "==> Project: $ProjectId  region: $Region  vertex: $VertexRegion"
gcloud config set project $ProjectId | Out-Null

Write-Host "==> Enabling required APIs"
$apis = @(
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "documentai.googleapis.com",
    "dlp.googleapis.com",
    "firestore.googleapis.com",
    "iamcredentials.googleapis.com",
    "identitytoolkit.googleapis.com",
    "logging.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "texttospeech.googleapis.com"
)
gcloud services enable @apis

Write-Host "==> Creating runtime service account (idempotent)"
$saCheck = gcloud iam service-accounts describe $SaEmail 2>$null
if (-not $saCheck) {
    gcloud iam service-accounts create $SaName --display-name="LexGuard Cloud Run runtime"
}

Write-Host "==> Granting least-privilege roles"
$roles = @(
    "roles/aiplatform.user",
    "roles/datastore.user",
    "roles/storage.objectAdmin",
    "roles/documentai.apiUser",
    "roles/dlp.user",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent"
)
foreach ($role in $roles) {
    gcloud projects add-iam-policy-binding $ProjectId `
        --member="serviceAccount:$SaEmail" `
        --role=$role `
        --condition=None | Out-Null
}

Write-Host "==> Creating Artifact Registry repo"
$repoCheck = gcloud artifacts repositories describe $RepoName --location=$Region 2>$null
if (-not $repoCheck) {
    gcloud artifacts repositories create $RepoName `
        --repository-format=docker `
        --location=$Region `
        --description="LexGuard container images"
}

Write-Host "==> Creating GCS buckets"
foreach ($bucket in @($UploadBucket, $ReportsBucket)) {
    $bucketCheck = gcloud storage buckets describe "gs://$bucket" 2>$null
    if (-not $bucketCheck) {
        gcloud storage buckets create "gs://$bucket" `
            --location=$Region `
            --uniform-bucket-level-access `
            --public-access-prevention
    }
}

Write-Host "==> Creating Firestore (Native) in $Region"
$fsCheck = gcloud firestore databases describe --database="(default)" 2>$null
if (-not $fsCheck) {
    gcloud firestore databases create --location=$Region --type=firestore-native
}

Write-Host @"

==============================================================================
GCP bootstrap complete.

  Project:           $ProjectId
  Region:            $Region
  Vertex region:     $VertexRegion
  Service account:   $SaEmail
  Artifact Registry: $Region-docker.pkg.dev/$ProjectId/$RepoName
  Upload bucket:     gs://$UploadBucket
  Reports bucket:    gs://$ReportsBucket

Next steps (manual):
  1. Create a Document AI 'Form Parser' processor in $VertexRegion; copy the
     processor ID into .env.
  2. Enable Firebase Auth (Google provider) in the Firebase console.
  3. Set GitHub Actions secrets: GCP_PROJECT_ID, GCP_WORKLOAD_IDENTITY_PROVIDER,
     GCP_SERVICE_ACCOUNT (=$SaEmail).
==============================================================================
"@
