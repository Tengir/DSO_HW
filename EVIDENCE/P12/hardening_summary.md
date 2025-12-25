# Hardening summary (P12)

- Dockerfile: non-root user, pinned base image tag, healthcheck enabled.
- IaC (docker-compose): added `read_only`, `cap_drop: [ALL]`, and `no-new-privileges`.
- IaC (k8s): added `runAsNonRoot`, `allowPrivilegeEscalation=false`, `readOnlyRootFilesystem`, `capabilities: drop ALL`.
- Plan: review Trivy high/critical findings and update base image/deps if needed.
