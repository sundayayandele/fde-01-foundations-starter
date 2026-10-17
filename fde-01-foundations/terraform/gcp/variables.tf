variable "project_id" {
  description = "GCP project for the lab (use a sandbox project)."
  type        = string
}

variable "region" {
  description = "Region. europe-west1 (Belgium) or europe-west4 (Netherlands) keep data in the EU."
  type        = string
  default     = "europe-west4"
}

variable "app_name" {
  description = "Name used for every resource."
  type        = string
  default     = "fde-01-foundations"
}

variable "image_tag" {
  description = "Image tag pushed to the Artifact Registry repository created here."
  type        = string
  default     = "1.0.0"
}

variable "deploy_app" {
  description = "Create the Cloud Run service. Set false on the first apply, push the image, then set true."
  type        = bool
  default     = false
}

variable "allow_public" {
  description = "Allow unauthenticated calls (lab only)."
  type        = bool
  default     = true
}

variable "billing_account" {
  description = "Billing account ID for the budget (XXXXXX-XXXXXX-XXXXXX). Leave empty to skip the budget."
  type        = string
  default     = ""
}

variable "monthly_budget_usd" {
  description = "Monthly budget; alerts at 50, 80 and 100 percent go to billing admins."
  type        = number
  default     = 50
}

variable "serve_model" {
  description = "Model bundle the API serves by default, as <dataset>/<kind>."
  type        = string
  default     = "banking77/baseline"
}
