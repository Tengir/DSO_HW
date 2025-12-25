# Hardening summary (P12)

- Dockerfile: non-root user, pinned base image tag, healthcheck enabled.
- IaC (docker-compose): added `read_only`, `cap_drop: [ALL]`, and `no-new-privileges`.
- IaC (k8s): added namespace, pod securityContext, resource limits/requests, and container hardening.
- Plan: review Trivy High/Critical findings and update base image/deps if needed; keep non-root execution.
