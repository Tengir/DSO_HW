# Hardening summary (P12)

- Dockerfile: non-root user, pinned base image tag, healthcheck enabled.
- IaC (docker-compose): added `read_only`, `cap_drop: [ALL]`, and `no-new-privileges`.
- Plan: review Trivy high/critical findings and update base image/deps if needed.
