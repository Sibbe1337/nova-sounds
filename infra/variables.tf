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

# Add other variables here as needed
