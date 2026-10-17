# Lab deployment on GCP for the complaint-routing classifier: Artifact Registry, Cloud Run
# (1 vCPU, 1 GiB, scale to zero), a dedicated service account with no roles, and an
# optional billing budget. Models are baked into the image: no secrets needed.
# Two-step apply: first with deploy_app=false, push the image, then deploy_app=true.
# Destroy at the end of every lab: `make tf-gcp-destroy`.

data "google_project" "this" {}

resource "google_project_service" "apis" {
  for_each           = toset(["run.googleapis.com", "artifactregistry.googleapis.com", "billingbudgets.googleapis.com"])
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = var.app_name
  format        = "DOCKER"
  description   = "FDE series images"
  depends_on    = [google_project_service.apis]
}

resource "google_service_account" "run" {
  account_id   = "${var.app_name}-run"
  display_name = "Cloud Run runtime for ${var.app_name}"
}

resource "google_cloud_run_v2_service" "app" {
  count               = var.deploy_app ? 1 : 0
  name                = var.app_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.run.email
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}/${var.app_name}:${var.image_tag}"
      ports {
        container_port = 8000
      }
      resources {
        limits   = { cpu = "1", memory = "1Gi" }
        cpu_idle = true
      }
      env {
        name  = "ENVIRONMENT"
        value = "gcp"
      }
      env {
        name  = "SERVE_MODEL"
        value = var.serve_model
      }
      startup_probe {
        http_get {
          path = "/health/live"
        }
      }
      liveness_probe {
        http_get {
          path = "/health/live"
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.deploy_app && var.allow_public ? 1 : 0
  name     = google_cloud_run_v2_service.app[0].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_billing_budget" "lab" {
  count           = var.billing_account == "" ? 0 : 1
  billing_account = var.billing_account
  display_name    = "${var.app_name}-monthly"

  budget_filter {
    projects = ["projects/${data.google_project.this.number}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget_usd)
    }
  }

  dynamic "threshold_rules" {
    for_each = [0.5, 0.8, 1.0]
    content {
      threshold_percent = threshold_rules.value
    }
  }

  depends_on = [google_project_service.apis]
}
