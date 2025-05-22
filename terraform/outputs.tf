output "project_id" {
  description = "The GCP project ID where the GKE cluster is deployed."
  value       = google_container_cluster.primary.project
}

output "cluster_name" {
  description = "The name of the GKE cluster."
  value       = google_container_cluster.primary.name
}

output "cluster_location" {
  description = "The location (zone or region) of the GKE cluster."
  value       = google_container_cluster.primary.location
}

# output "ssh_instructions" {
#   description = <<-EOT
#     To SSH into a GKE node (instance) using OS Login (recommended):

#     1.  Ensure OS Login is enabled in your GCP project or specifically for these nodes (this Terraform config attempts to enable it on nodes).
#         You can check project-level OS Login status in the GCP Console (IAM & Admin > Settings, or Compute Engine > Metadata).

#     2.  Ensure your Google Cloud user account has the necessary IAM permissions:
#         - 'Compute OS Login' role (roles/compute.osLogin) OR
#         - 'Compute OS Admin Login' role (roles/compute.osAdminLogin) for sudo access.
#         - 'Service Account User' role (roles/iam.serviceAccountUser) on the GKE node's service account (if applicable, usually not needed for OS Login by user).

#     3.  Find an instance name and its zone. You can list instances:
#         gcloud compute instances list --project "${var.project_id}" --filter="name~'${google_container_node_pool.primary_nodes.name}'"

#     4.  Connect using gcloud:
#         gcloud compute ssh [YOUR_USERNAME_OR_OSLOGIN_USERNAME]@INSTANCE_NAME --project "${var.project_id}" --zone INSTANCE_ZONE

#         Example: If your OS Login username is 'user_example_com' and instance is 'gke-...-pool-xyz-1234' in 'us-central1-a':
#         gcloud compute ssh user_example_com@gke-${var.project_id}-gke-node-pool-xyz-1234 --project "${var.project_id}" --zone us-central1-a

#         Note: The username for OS Login is typically derived from your Google account email (e.g., 'user_domain_com' for 'user@domain.com').
#         `gcloud` often figures out the username automatically. You can also try:
#         gcloud compute ssh INSTANCE_NAME --project "${var.project_id}" --zone INSTANCE_ZONE

#     5. If `gcloud compute ssh` uses IAP (Identity-Aware Proxy) tunneling (often default), you won't need external IPs on nodes or direct SSH firewall rules from the internet.
#        Ensure the "IAP-Secured Tunnel User" role (`roles/iap.tunnelResourceAccessor`) is granted to users who need to SSH via IAP, on the project or on the specific instances.
#   EOT
#   value = "See description for SSH instructions."
# }