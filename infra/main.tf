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
    "cloudresourcemanager.googleapis.com", # Needed to enable other APIs
    "storage.googleapis.com",        # Cloud Storage
    "bigquery.googleapis.com",       # BigQuery
    "run.googleapis.com",          # Cloud Run
    "cloudfunctions.googleapis.com", # Cloud Functions
    "cloudbuild.googleapis.com",     # Cloud Build
    "iam.googleapis.com",          # IAM
    "artifactregistry.googleapis.com", # Artifact Registry (for Docker images)
    "aiplatform.googleapis.com",     # Vertex AI
    "container.googleapis.com",      # Kubernetes Engine (for GKE)
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

# ---- IAM Bindings ----

# ETL Service Account Permissions
resource "google_storage_bucket_iam_member" "etl_sa_gcs_writer" {
  bucket = google_storage_bucket.staging_bucket.name
  role   = "roles/storage.objectAdmin" # Allows creating/deleting objects
  member = google_service_account.etl_sa.member
}

resource "google_bigquery_dataset_iam_member" "etl_sa_bq_editor" {
  dataset_id = google_bigquery_dataset.nip_dw.dataset_id
  project    = var.gcp_project_id
  role       = "roles/bigquery.dataEditor" # Allows creating tables, writing data
  member     = google_service_account.etl_sa.member
}

# API Service Account Permissions
resource "google_bigquery_dataset_iam_member" "api_sa_bq_viewer" {
  dataset_id = google_bigquery_dataset.nip_dw.dataset_id
  project    = var.gcp_project_id
  role       = "roles/bigquery.dataViewer" # Allows reading data
  member     = google_service_account.api_sa.member
}

resource "google_project_iam_member" "api_sa_functions_invoker" {
  project = var.gcp_project_id
  role    = "roles/cloudfunctions.invoker" # Allows invoking functions
  member  = google_service_account.api_sa.member
}

# ---- Cloud Run Job (ETL) ----

resource "google_cloud_run_v2_job" "etl_job" {
  name     = "nip-etl-job" # Name for the Cloud Run Job resource itself
  location = var.gcp_region
  project  = var.gcp_project_id
  deletion_protection = false # Temporarily disable to allow replacement if tainted

  template {
    template {
      service_account = google_service_account.etl_sa.email

      containers {
        # Define the container that runs the ETL process
        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/nip-etl-runner:latest"
        name  = "etl-container"

        # Optional: Add command, args, env vars, resources (CPU/memory) as needed
        # command = ["python", "run_meltano.py"]
        # args    = ["--schedule", "spotify_schedule"]
        # env {
        #   name  = "TARGET_GCS_BUCKET"
        #   value = google_storage_bucket.staging_bucket.name
        # }
        # resources {
        #   limits = {
        #     cpu    = "1000m"
        #     memory = "512Mi"
        #   }
        # }
      }

      # Optional: Configure job execution settings (timeout, retries)
      # max_retries = 3
    }
  }
}

# ---- Cloud Functions ----

# Pitch Score API Function
resource "google_cloudfunctions2_function" "pitch_score_api" {
  name     = "nip-pitch-score-api"
  location = var.gcp_region
  project  = var.gcp_project_id

  build_config {
    runtime     = "python311" # Matches TPRD Dev Env Standard
    entry_point = "handle_request" # Assumed entry point, adjust if needed
    source {
      storage_source {
        bucket = google_storage_bucket.staging_bucket.name
        object = "functions-source/pitch-score-api.zip" # Placeholder source code location
      }
    }
  }

  service_config {
    max_instance_count = 3 # Example scaling
    min_instance_count = 0
    available_memory   = "256Mi"
    timeout_seconds    = 60
    service_account_email = google_service_account.api_sa.email
    ingress_settings    = "ALLOW_ALL" # Or "ALLOW_INTERNAL_ONLY" if needed
    all_traffic_on_latest_revision = true
  }
}

# Alert Threshold API Function
resource "google_cloudfunctions2_function" "alert_threshold_api" {
  name     = "nip-alert-threshold-api"
  location = var.gcp_region
  project  = var.gcp_project_id

  build_config {
    runtime     = "python311"
    entry_point = "handle_request" # Assumed entry point, adjust if needed
    source {
      storage_source {
        bucket = google_storage_bucket.staging_bucket.name
        object = "functions-source/alert-threshold-api.zip" # Placeholder source code location
      }
    }
  }

  service_config {
    max_instance_count = 2 # Example scaling
    min_instance_count = 0
    available_memory   = "256Mi"
    timeout_seconds    = 60
    service_account_email = google_service_account.api_sa.email
    ingress_settings    = "ALLOW_ALL"
    all_traffic_on_latest_revision = true
  }
}

# ---- Vertex AI ----

# Note: More specific Vertex AI resources (training jobs, endpoints, monitoring)
# will likely be added as the ML pipeline is developed.

resource "google_vertex_ai_dataset" "ml_dataset" {
  display_name = "NIP Pitch Score Features Dataset"
  metadata_schema_uri = "gs://google-cloud-aiplatform/schema/dataset/metadata/tabular_1.0.0.yaml" # Schema for tabular data
  region       = var.gcp_region
  project      = var.gcp_project_id

  # encryption_spec {
  #   kms_key_name = "your-kms-key-name" # Optional: Add CMEK if needed
  # }
}

# ---- GKE Cluster (Metabase) ----

resource "google_container_cluster" "metabase_cluster" {
  name     = "nip-metabase-cluster"
  location = var.gcp_region
  project  = var.gcp_project_id

  # Enable Autopilot
  enable_autopilot = true

  # Autopilot clusters manage their own node pools, networking (usually VPC-native),
  # and other configurations automatically.
  # We remove explicit node_pool, networking_mode, etc., configurations.

  # Minimal required configuration for Autopilot:
  initial_node_count = 1 # Required for Terraform provider, but Autopilot manages scaling.

  # Optional: Configure release channel, maintenance windows, etc.
  # release_channel {
  #   channel = "REGULAR"
  # }
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

output "cloud_run_etl_job_name" {
  description = "Name of the Cloud Run job for ETL."
  value       = google_cloud_run_v2_job.etl_job.name
}

output "pitch_score_api_uri" {
  description = "URI of the Pitch Score API Cloud Function."
  value       = google_cloudfunctions2_function.pitch_score_api.service_config[0].uri
}

output "alert_threshold_api_uri" {
  description = "URI of the Alert Threshold API Cloud Function."
  value       = google_cloudfunctions2_function.alert_threshold_api.service_config[0].uri
}

output "vertex_ai_dataset_name" {
  description = "Name of the Vertex AI Dataset for ML features."
  value       = google_vertex_ai_dataset.ml_dataset.name
}

output "metabase_gke_cluster_name" {
  description = "Name of the GKE Autopilot cluster for Metabase."
  value       = google_container_cluster.metabase_cluster.name
}

output "metabase_gke_cluster_endpoint" {
  description = "Endpoint IP for the GKE Autopilot cluster."
  value       = google_container_cluster.metabase_cluster.endpoint
  sensitive   = true # Endpoint might be considered sensitive
}
