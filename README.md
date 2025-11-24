# Kubernetes Microservices: Auth & Tasks

Production-ready microservices architecture with automated CI/CD and high availability.

## Architecture

### Services
- **auth-service** (port 8000): JWT authentication with RSA keys
- **tasks-service** (port 8001): Task management with pagination and JWT validation

### Infrastructure
- **PostgreSQL HA**: CloudNativePG with automatic failover (2 replicas in prod, 1 in testing)
- **Kubernetes**: Yandex Cloud Managed Kubernetes cluster
- **Storage**: Yandex Cloud network HDD (`yc-network-hdd`)
- **Ingress**: NGINX Ingress Controller with LoadBalancer (automatic external IP from Yandex Cloud) + cert-manager (Let's Encrypt)
- **NetworkPolicies**: Locked-down ingress and DB access in `prod` and `testing`
- **Container Registry**: GitHub Container Registry (GHCR) - free and unlimited
- **CI/CD**: GitHub Actions - automatic builds on git tags
- **Monitoring**: Prometheus + Grafana with persistent storage
- **DNS**: tasky.f0x1d.com (prod), tasky-testing.f0x1d.com (testing and PR previews)

### Tech Stack
- **Python 3.13** + **FastAPI** + **PostgreSQL 16**
- **CloudNativePG** (Production-grade PostgreSQL operator with HA) + **Kubernetes** (Yandex Cloud)
- **GitHub Actions** (CI/CD) + **GHCR** (Container Registry)
- **Helm** (Package Management)

---

## Project Structure

```
.
├── auth-service/
│   ├── app/                      # FastAPI application
│   ├── Dockerfile
│   └── pyproject.toml
├── tasks-service/
│   ├── app/                      # FastAPI application
│   ├── Dockerfile
│   └── pyproject.toml
├── helm-charts/
│   ├── microservice/             # Reusable microservice Helm chart
│   │   ├── templates/            # Kubernetes resource templates
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── ingress.yaml
│   │   │   ├── postgres.yaml
│   │   │   ├── networkpolicy.yaml
│   │   │   ├── prometheus/       # Per-service monitoring
│   │   │   └── grafana/          # Per-service dashboards
│   │   ├── Chart.yaml
│   │   └── values.yaml           # Default values
│   ├── cert-manager-config/      # Let's Encrypt configuration
│   ├── ingress-nginx/            # NGINX Ingress Controller
│   ├── values/                   # Environment-specific values
│   │   ├── auth-service-prod.yaml
│   │   ├── auth-service-testing.yaml
│   │   ├── tasks-service-prod.yaml
│   │   └── tasks-service-testing.yaml
│   └── README.md
├── scripts/
│   └── generate-secrets.sh       # Secret generation script
├── .github/
│   ├── actions/
│   │   └── setup-k8s/                   # Reusable composite action for K8s setup
│   │       └── action.yaml
│   └── workflows/
│       ├── build-and-deploy.yaml        # CI/CD pipeline for releases
│       ├── build-and-deploy-preview.yaml # PR preview builds and deployments
│       └── cleanup-preview.yaml         # PR preview cleanup
├── README.md                     # This file
└── SETUP.md                      # One-time setup guide
```

---

## How It Works

### Development → Production Flow

```
1. Code changes → Git push
   
2. Release to Testing:
   ├─ Push to dev branch → CI builds → Deploy to testing with Helm
   └─ Test changes in testing environment
   
3. Release to Production:
   ├─ git tag v1.0.0 && git push --tags
   ├─ CI builds prod image with version tag
   ├─ Update helm-charts/values/*.yaml files with new version
   └─ Deploy to prod using: helm upgrade --install
```

### Container Versioning

- **Environment-specific values** in Helm values files
- **Helm** manages deployments with templating and values
- **Semantic versioning**: v1.0.0, v1.2.3, v2.0.0
- **Automatic builds**: GitHub Actions builds on git tags
- **Immutable images**: Each version is stored permanently in GHCR

---

## Initial Setup

**See [SETUP.md](SETUP.md) for complete step-by-step instructions.**

Quick overview:
1. Configure GitHub Container Registry (GHCR)
2. Update Helm values files with your configuration
3. Create secrets in Kubernetes
4. Push first release tag
5. Deploy to Kubernetes using Helm

This is done **once**. After this, everything is automated.

---

## Daily Workflow

### Making Changes

```bash
# 1. Make code changes
vim auth-service/app/main.py

# 2. Commit and push
git add .
git commit -m "Add new feature"
git push
```

### Releasing New Version

```bash
# Create and push release tag
git tag v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0

# GitHub Actions automatically builds and publishes
# Check progress: https://github.com/YOUR_USERNAME/kubernetes/actions
```

### Deploying to Kubernetes

```bash
# Wait for GitHub Actions to complete, then:
# Ensure namespace exists
kubectl create namespace prod --dry-run=client -o yaml | kubectl apply -f -

# Install or upgrade auth-service
helm upgrade --install auth-service helm-charts/microservice \
  -f helm-charts/values/auth-service-prod.yaml \
  --namespace prod

# Install or upgrade tasks-service
helm upgrade --install tasks-service helm-charts/microservice \
  -f helm-charts/values/tasks-service-prod.yaml \
  --namespace prod

# Watch rolling update
kubectl get pods -n prod -w
```

### Checking Status

```bash
# View pods
kubectl get pods -n prod

# View services
kubectl get svc -n prod

# View logs
kubectl logs -f -n prod -l app=auth-service
kubectl logs -f -n prod -l app=tasks-service

# Check deployment status
kubectl rollout status deployment/auth-service -n prod
kubectl rollout status deployment/tasks-service -n prod
```

### Rolling Back

```bash
# Rollback to previous Helm release
helm rollback auth-service -n prod

# Or rollback Kubernetes deployment
kubectl rollout undo deployment/auth-service -n prod
```

---

## API Endpoints

Access services at: `https://tasky.f0x1d.com` (via LoadBalancer + Ingress)

### Auth Service
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - Login (returns JWT tokens)
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/docs` - OpenAPI documentation

### Tasks Service
- `POST /api/tasks/tasks` - Create task
- `GET /api/tasks/tasks` - List tasks (with pagination)
- `GET /api/tasks/tasks/{id}` - Get task by ID
- `PUT /api/tasks/tasks/{id}` - Update task
- `DELETE /api/tasks/tasks/{id}` - Delete task
- `GET /api/tasks/docs` - OpenAPI documentation

### Monitoring

**Production:**
- Auth Service Grafana: `https://tasky.f0x1d.com/auth-grafana`
- Tasks Service Grafana: `https://tasky.f0x1d.com/tasks-grafana`
  - Username: `admin`
  - Password: (from secrets generation output)

**Testing:**
- Auth Service Grafana: `https://tasky-testing.f0x1d.com/dev/auth-grafana`
- Tasks Service Grafana: `https://tasky-testing.f0x1d.com/dev/tasks-grafana`
  - Username: `admin`
  - Password: (from secrets generation output)

### Environments

**Production:**
- Auth Service: `https://tasky.f0x1d.com/api/auth`
- Tasks Service: `https://tasky.f0x1d.com/api/tasks`

**Testing (dev branch):**
- Auth Service: `https://tasky-testing.f0x1d.com/dev/api/auth`
- Tasks Service: `https://tasky-testing.f0x1d.com/dev/api/tasks`

**PR Previews:**
- Auth Service: `https://tasky-testing.f0x1d.com/pr-X/api/auth`
- Tasks Service: `https://tasky-testing.f0x1d.com/pr-X/api/tasks`
(Replace X with your PR number)

### Example Usage

```bash
# Register user
curl -X POST https://tasky.f0x1d.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Login
curl -X POST https://tasky.f0x1d.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Create task (use access_token from login)
curl -X POST https://tasky.f0x1d.com/api/tasks/tasks \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Task", "content": "Description"}'

# List tasks
curl https://tasky.f0x1d.com/api/tasks/tasks?page=1&page_size=10 \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## Operations

### Viewing Logs

```bash
# Auth service logs
kubectl logs -f -n prod -l app=auth-service

# Tasks service logs  
kubectl logs -f -n prod -l app=tasks-service

# PostgreSQL logs
kubectl logs -f -n prod postgres-auth-0
kubectl logs -f -n prod postgres-tasks-0

# Ingress logs
kubectl logs -f -n ingress-nginx -l app=ingress-nginx
```

### Scaling Services

```bash
# Scale auth-service to 3 replicas
kubectl scale deployment auth-service -n prod --replicas=3

# Scale tasks-service to 3 replicas
kubectl scale deployment tasks-service -n prod --replicas=3
```

### Database Operations

```bash
# Check cluster status
kubectl get cluster -n prod
kubectl describe cluster postgres-auth -n prod

# Get superuser password
kubectl get secret postgres-auth-superuser -n prod -o jsonpath='{.data.password}' | base64 -d
echo

# Connect to PostgreSQL (master)
kubectl exec -it postgres-auth-1 -n prod -- psql -U postgres auth

# Backup database
kubectl exec -it postgres-auth-1 -n prod -- pg_dump -U postgres auth > backup.sql

# Restore database
kubectl exec -i postgres-auth-1 -n prod -- psql -U postgres auth < backup.sql

# Manual switchover (if needed)
kubectl cnpg promote postgres-auth 2 -n prod
```

### Monitoring

```bash
# Check cluster health
kubectl get nodes
kubectl get pods -n prod
kubectl top nodes
kubectl top pods -n prod

# Check Ingress status and LoadBalancer IP
kubectl get svc -n ingress-nginx
kubectl get pods -n ingress-nginx -o wide

# Check PostgreSQL replication
kubectl exec -it -n prod postgres-auth-0 -- patronictl list

# Access Grafana
# Get password:
kubectl get secret grafana-secrets -n prod -o jsonpath='{.data.admin_password}' | base64 -d
# Open: https://tasky.f0x1d.com/grafana
```

### Troubleshooting

**Pods not starting?**
```bash
# Check pod status and events
kubectl describe pod <pod-name> -n prod
kubectl get events -n prod --sort-by='.lastTimestamp'
```

**Image pull errors?**
```bash
# Check if imagePullSecret exists
kubectl get secret ghcr-secret -n prod

# Verify image name in deployment
kubectl get deployment auth-service -n prod -o jsonpath='{.spec.template.spec.containers[0].image}'

# Check if package is public on GitHub
# Go to: https://github.com/YOUR_USERNAME?tab=packages
```

**Service not accessible?**
```bash
# Check service
kubectl get svc -n prod

# Check ingress
kubectl get ingress -n prod
kubectl describe ingress services-ingress -n prod

# Get LoadBalancer IP
kubectl get svc ingress-nginx-controller -n ingress-nginx

# Test directly via LoadBalancer IP
curl http://<LOADBALANCER_IP>/api/auth/docs
```

**PostgreSQL issues?**
```bash
# Check PostgreSQL pods
kubectl get pods -n prod -l cnpg.io/cluster=postgres-auth

# Check cluster status
kubectl get cluster postgres-auth -n prod
kubectl describe cluster postgres-auth -n prod

# Check logs
kubectl logs -n prod postgres-auth-1 | tail -50

# For testing namespace deployment errors:
# 1. Verify namespace exists: kubectl get namespace testing
# 2. Verify secrets exist: kubectl get secret -n testing | grep postgres
# 3. Verify CNPG operator: kubectl get pods -n cnpg-system
```

---

## High Availability Testing

### Test Ingress HA

```bash
# Verify Ingress Controllers on different nodes
kubectl get pods -n ingress-nginx -o wide
# Should show 2 pods on DIFFERENT nodes

# Get LoadBalancer IP
kubectl get svc ingress-nginx-controller -n ingress-nginx

# Test LoadBalancer
curl http://<LOADBALANCER_IP>/api/auth/docs

# Simulate node failure - delete one Ingress pod
kubectl delete pod -n ingress-nginx <pod-name>

# Service should still work via LoadBalancer
curl https://tasky.f0x1d.com/api/auth/docs
```

### Test PostgreSQL HA

```bash
# Check current primary
kubectl get cluster postgres-auth -n prod

# Simulate primary failure - delete primary pod
kubectl delete pod postgres-auth-1 -n prod

# CloudNativePG automatically promotes standby to primary (~30 seconds)
# Check new primary
kubectl get cluster postgres-auth -n prod

# Services should continue working
curl https://tasky.f0x1d.com/api/auth/health
```

---

## Configuration Management

### Updating Image Versions

```bash
# Update version in Helm values files
vim helm-charts/values/auth-service-prod.yaml
# Change image.tag to "1.2.0"

vim helm-charts/values/tasks-service-prod.yaml
# Change image.tag to "1.2.0"

# Commit changes
git add helm-charts/values/*.yaml
git commit -m "Update to version v1.2.0"
git push

# Deploy with Helm
helm upgrade auth-service helm-charts/microservice \
  -f helm-charts/values/auth-service-prod.yaml \
  --namespace prod

helm upgrade tasks-service helm-charts/microservice \
  -f helm-charts/values/tasks-service-prod.yaml \
  --namespace prod
```

### Managing Secrets

```bash
# Generate and apply secrets (only once during setup)
./scripts/generate-secrets.sh prod

# Regenerate secrets if needed
./scripts/generate-secrets.sh prod

# Restart pods to pick up new secrets
kubectl rollout restart deployment/auth-service -n prod
```

---

## Maintenance

### Updating Kubernetes Resources

```bash
# Update resource limits in values file
vim helm-charts/values/auth-service-prod.yaml
# Modify resources.requests/limits

# Apply changes with Helm
helm upgrade auth-service helm-charts/microservice \
  -f helm-charts/values/auth-service-prod.yaml \
  --namespace prod
```

### Cleaning Up

```bash
# Delete entire environment
kubectl delete namespace prod

# Delete PersistentVolumes (if needed)
kubectl get pv | grep prod | awk '{print $1}' | xargs kubectl delete pv

# Clean up old images from GHCR
# Go to: https://github.com/YOUR_USERNAME?tab=packages
# Select package → Package settings → Delete old versions
```

### Upgrading Components

**Upgrade NGINX Ingress:**
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.0/deploy/static/provider/cloud/deploy.yaml
```

**Upgrade PostgreSQL:**
CloudNativePG handles upgrades automatically. To change version:
```bash
kubectl edit cluster postgres-auth -n prod
# Change spec.imageName to desired version
# CloudNativePG will perform rolling upgrade
```

---

## Security Best Practices

1. **Secrets Management**
   - Never commit secrets to Git
   - Rotate secrets regularly
   - Use Kubernetes secrets for sensitive data

2. **Container Images**
   - Use specific version tags (not `latest`)
   - Scan images for vulnerabilities
   - Keep base images updated

3. **Network Security**
   - Use LoadBalancer for secure external access
   - Enable TLS/SSL at ingress level or via Cloudflare proxy
   - NetworkPolicies restrict internal pod-to-pod traffic
   - Only ingress-nginx can reach application services

4. **Access Control**
   - Use RBAC for Kubernetes access
   - Limit service account permissions
   - Enable audit logging

5. **Database Security**
   - Use strong passwords
   - Enable SSL for database connections
   - Regular backups

---

## CI/CD Pipeline Details

### GitHub Actions Workflows

**Build and Deploy** (`.github/workflows/build-and-deploy.yaml`)

Triggered by:
- Git tags: `v*.*.*` (production deployment)
- Push to `dev` branch (testing deployment)
- Manual dispatch via GitHub UI

Workflow steps:
1. **Build**: Builds Docker images for both services using matrix strategy
2. **Tag**: Tags images with version and `latest`
3. **Push**: Pushes to GHCR (ghcr.io/YOUR_USERNAME/SERVICE:VERSION)
4. **Deploy**: Deploys to Kubernetes using Helm with environment-specific values

**Build and Deploy Preview** (`.github/workflows/build-and-deploy-preview.yaml`)

Triggered by:
- PR labeled with `deploy` or synchronized after labeling

Builds Docker images and creates temporary preview environments at `tasky-testing.f0x1d.com/pr-X/*`

**Cleanup Preview** (`.github/workflows/cleanup-preview.yaml`)

Triggered by:
- PR closed

Deletes preview environment resources (Helm releases and namespace)

### Semantic Versioning

Use semantic versioning for releases:
- `v1.0.0` → `v1.0.1` - Patch: Bug fixes
- `v1.0.0` → `v1.1.0` - Minor: New features (backward compatible)
- `v1.0.0` → `v2.0.0` - Major: Breaking changes

### Release Process

```bash
# 1. Test changes locally/in testing environment
# 2. Update version based on changes (patch/minor/major)
# 3. Create and push tag
git tag v1.2.0 -m "Release version 1.2.0: Add task filtering"
git push origin v1.2.0

# 4. Monitor GitHub Actions
# Visit: https://github.com/YOUR_USERNAME/kubernetes/actions

# 5. After build completes, deploy with Helm
helm upgrade auth-service helm-charts/microservice \
  -f helm-charts/values/auth-service-prod.yaml \
  -n prod

helm upgrade tasks-service helm-charts/microservice \
  -f helm-charts/values/tasks-service-prod.yaml \
  -n prod

# 6. Verify deployment
kubectl rollout status deployment/auth-service -n prod
kubectl rollout status deployment/tasks-service -n prod
```

---

## Architecture Decisions

### Why GHCR instead of Docker Hub?
- ✅ Free unlimited bandwidth for public images
- ✅ Integrated with GitHub (no separate account)
- ✅ Better GitHub Actions integration
- ✅ 500MB free for private repositories

### Why Helm?
- ✅ Package management with versioning and rollbacks
- ✅ Powerful templating for complex configurations
- ✅ Reusable charts for microservices
- ✅ Easy upgrades with `helm upgrade`
- ✅ Values files for environment-specific configs
- ✅ Industry standard for Kubernetes deployments

### Why Yandex Cloud Managed Kubernetes?
- ✅ Fully managed control plane (no maintenance overhead)
- ✅ Automatic updates and security patches
- ✅ Integrated LoadBalancer support (no manual IP management)
- ✅ Network HDD storage class built-in
- ✅ Production-ready with SLA guarantees
- ✅ Easy scaling and node management

### Why CloudNativePG for PostgreSQL?
- ✅ Kubernetes-native operator (no manual Patroni setup)
- ✅ Automatic failover in ~30 seconds
- ✅ Built-in backup/restore with barman
- ✅ Rolling upgrades without downtime
- ✅ Production-ready, used by enterprises
- ✅ Active development and community support

---

## Support & Resources

### Documentation
- GitHub Container Registry: https://docs.github.com/en/packages
- Helm: https://helm.sh/docs/
- Yandex Cloud Managed Kubernetes: https://cloud.yandex.com/en/services/managed-kubernetes
- CloudNativePG: https://cloudnative-pg.io/

### Quick Commands Reference

```bash
# Helm operations
helm list -n prod                 # List installed releases
helm status auth-service -n prod  # Check release status
helm get values auth-service -n prod  # View current values
helm history auth-service -n prod # View release history
helm rollback auth-service -n prod   # Rollback to previous version

# Kubernetes operations
kubectl get all -n prod           # Check everything
kubectl get pods -n prod -w       # Watch pods
kubectl logs -f -n prod -l app=auth-service  # Logs
kubectl describe pod <pod-name> -n prod      # Debug pod
kubectl exec -it <pod-name> -n prod -- /bin/bash  # Get into pod
kubectl port-forward -n prod svc/auth-service 8000:8000  # Port forward

# Resource usage
kubectl top nodes
kubectl top pods -n prod

# Get all images currently running
kubectl get pods -n prod -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
```

---

## License

MIT
