variable "gcp_project_id" {
  description = "The Google Cloud project ID."
  type        = string
  # No default, should be provided via Terraform Cloud workspace variables
}

variable "gcp_region" {
  description = "The Google Cloud region for resources."
  type        = string
  default     = "europe-west1" # Example default, adjust as needed
}

variable "gcp_credentials_json" {
  description = "Content of the GCP service account key JSON file (set as sensitive variable in TFC)."
  type        = string
  sensitive   = true
  # No default, value must be provided via Terraform Cloud workspace variables
}

# Add other variables here as needed
