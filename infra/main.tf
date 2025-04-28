terraform {
  required_version = ">= 1.0" # Specify your required Terraform version

  # Configure Terraform Cloud backend
  cloud {
    organization = "NovaSounds" # Updated TFC organization name

    workspaces {
      # We can use tags or name prefixes to manage dev/prod workspaces later
      name = "nip-infra-dev" # Example initial workspace name
    }
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0" # Specify compatible Google provider version
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  # Credentials configured via Terraform Cloud workspace variables or gcloud auth
  credentials = var.gcp_credentials_json
}

# Add initial resource definitions here later
# Example: Google Project Services, BigQuery Dataset, GCS Bucket

# ---- Enable Necessary GCP APIs ----

locals {
  # List of required APIs for the project
  required_gcp_apis = [
    "storage.googleapis.com",        # Cloud Storage
    "bigquery.googleapis.com",       # BigQuery
    "run.googleapis.com",          # Cloud Run
    "cloudfunctions.googleapis.com", # Cloud Functions
    "cloudbuild.googleapis.com",     # Cloud Build
    "iam.googleapis.com",          # IAM
    "artifactregistry.googleapis.com", # Artifact Registry (for Docker images)
    "aiplatform.googleapis.com",     # Vertex AI
    # Add other APIs as needed, e.g., pubsub.googleapis.com if using Pub/Sub
  ]
}

resource "google_project_service" "apis" {
  for_each = toset(local.required_gcp_apis)

  project                    = var.gcp_project_id
  service                    = each.value
  disable_dependent_services = false # Usually keep this false
  disable_on_destroy         = false # Set to true if you want APIs disabled on destroy
}

# ---- Core Data Platform Resources ----

resource "google_storage_bucket" "staging_bucket" {
  name          = "${var.gcp_project_id}-nip-staging-bucket" # Unique bucket name
  location      = var.gcp_region
  storage_class = "STANDARD" # Or choose another class like REGIONAL, NEARLINE, etc.

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30 # Example: Delete objects older than 30 days
    }
  }

  # Optional: Configure CORS if needed for web access
}

resource "google_bigquery_dataset" "nip_dw" {
  dataset_id                 = "nova_insights_platform"
  friendly_name              = "Nova Insights Platform DW"
  description                = "Main Data Warehouse for the Nova Insights Platform"
  location                   = var.gcp_region # Keep DW in the same region
  project                    = var.gcp_project_id
  delete_contents_on_destroy = false # Set to true for dev/test if needed
}

# ---- Service Accounts ----

resource "google_service_account" "etl_sa" {
  account_id   = "nip-etl-sa"
  display_name = "NIP ETL Service Account"
  description  = "Service account for Nova Insights Platform ETL Cloud Run jobs"
  project      = var.gcp_project_id
}

resource "google_service_account" "api_sa" {
  account_id   = "nip-api-sa"
  display_name = "NIP API Service Account"
  description  = "Service account for Nova Insights Platform Cloud Functions (Pitch Score, Alerts)"
  project      = var.gcp_project_id
}

# ---- Artifact Registry ----

resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.gcp_region
  repository_id = "nip-docker-repo"
  description   = "Docker repository for Nova Insights Platform images"
  format        = "DOCKER"
  project       = var.gcp_project_id
}

# ---- Outputs ----

output "gcp_project_id" {
  description = "The GCP project ID being used."
  value       = var.gcp_project_id
}

output "staging_bucket_name" {
  description = "Name of the GCS bucket used for staging data."
  value       = google_storage_bucket.staging_bucket.name
}

output "bigquery_dataset_id" {
  description = "ID of the main BigQuery dataset."
  value       = google_bigquery_dataset.nip_dw.dataset_id
}

output "etl_service_account_email" {
  description = "Email address of the ETL service account."
  value       = google_service_account.etl_sa.email
}

output "api_service_account_email" {
  description = "Email address of the API service account."
  value       = google_service_account.api_sa.email
}

output "docker_repository_name" {
  description = "Name of the Artifact Registry Docker repository."
  value       = google_artifact_registry_repository.docker_repo.name
}
