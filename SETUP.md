# Initial Setup Guide

Complete guide to deploy microservices on Kubernetes using Helm. This is a **one-time setup** - after this, everything is automated.

---

## Prerequisites

- **Kubernetes cluster** (Yandex Cloud Managed Kubernetes or any other)
- **kubectl** configured and working (`kubectl get nodes`)
- **Helm 3** installed ([helm.sh/docs/intro/install](https://helm.sh/docs/intro/install/))
- **GitHub account** for container registry and CI/CD
- **Domain name** (optional but recommended for production)

**Verify your setup:**
```bash
kubectl version --client
# Should show: Client Version: v1.x.x

helm version
# Should show: version.BuildInfo{Version:"v3.x.x"...}

kubectl get nodes
# Should show your cluster nodes
```

---

## Overview: What We'll Deploy

```
Infrastructure Layer:
├─ NGINX Ingress Controller (with LoadBalancer)
├─ cert-manager + Let's Encrypt ClusterIssuer
└─ CloudNativePG Operator (PostgreSQL HA)

Application Layer (per service):
├─ Microservice (FastAPI app)
├─ PostgreSQL Cluster (CloudNativePG)
├─ Prometheus (metrics collection)
├─ Grafana (dashboards)
├─ Ingress (HTTPS routing)
└─ NetworkPolicies (security)
```

**Deployment approach:** Helm charts with environment-specific values files.

---

## Step 1: Configure GitHub Container Registry

### 1.1 Create Personal Access Token

1. Go to GitHub: **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Name: `kubernetes-ghcr`
4. Select scopes: `read:packages`, `write:packages`, `delete:packages`
5. Click **Generate token**
6. **Copy the token** (e.g., `ghp_xxxxxxxxxxxx`)

### 1.2 Test Authentication

```bash
export GITHUB_TOKEN=ghp_your_token_here
export GITHUB_USERNAME=your_github_username

echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin
# Expected: Login Succeeded
```

---

## Step 2: Configure Your Repository

### 2.1 Update Helm Values Files

Update image repositories in all values files with **your GitHub username (lowercase)**:

```bash
# Files to update:
# - helm-charts/values/auth-service-prod.yaml
# - helm-charts/values/auth-service-testing.yaml
# - helm-charts/values/tasks-service-prod.yaml
# - helm-charts/values/tasks-service-testing.yaml

# Change this:
image:
  repository: ghcr.io/f0x1d/auth-service

# To this (use YOUR username):
image:
  repository: ghcr.io/YOUR_USERNAME/auth-service
```

**Quick update with sed:**
```bash
cd helm-charts/values/

# Replace f0x1d with your username (lowercase!)
sed -i '' 's/ghcr.io\/f0x1d/ghcr.io\/YOUR_USERNAME/g' *.yaml

# Verify
grep "repository:" *.yaml
```

### 2.2 Update Domain Names (Optional)

If you have your own domain, update these in values files:

```bash
# In each values file, change:
ingress:
  host: tasky.f0x1d.com          # Change to your domain
grafana:
  ingress:
    host: tasky.f0x1d.com         # Change to your domain
```

### 2.3 Commit Changes

```bash
git add helm-charts/values/*.yaml
git commit -m "Configure repository for deployment"
git push
```

---

## Step 3: Prepare Kubernetes Cluster

### 3.1 Create Namespaces

```bash
# Production namespace
kubectl create namespace prod

# Testing namespace
kubectl create namespace testing

# Verify
kubectl get namespaces
```

### 3.2 Create Image Pull Secret

This allows Kubernetes to pull images from GitHub Container Registry:

```bash
# For production
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=$GITHUB_USERNAME \
  --docker-password=$GITHUB_TOKEN \
  --docker-email=your-email@example.com \
  -n prod

# For testing
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=$GITHUB_USERNAME \
  --docker-password=$GITHUB_TOKEN \
  --docker-email=your-email@example.com \
  -n testing

# Verify
kubectl get secret ghcr-secret -n prod
kubectl get secret ghcr-secret -n testing
```

**Note:** If your images are public, this is optional but still recommended.

---

## Step 4: Install Operators

### 4.1 Install CloudNativePG Operator

CloudNativePG manages PostgreSQL clusters with automatic high availability:

```bash
# Install operator
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.27/releases/cnpg-1.27.1.yaml

# Wait for operator to be ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=cloudnative-pg \
  -n cnpg-system \
  --timeout=120s

# Verify
kubectl get pods -n cnpg-system
# Should show: cnpg-controller-manager-xxx Running
```

### 4.2 Install cert-manager

cert-manager automates TLS certificate management:

```bash
# Install cert-manager
kubectl apply -f \
  https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/instance=cert-manager \
  -n cert-manager \
  --timeout=120s

# Verify
kubectl get pods -n cert-manager
# Should show 3 pods running: cert-manager, cainjector, webhook
```

---

## Step 5: Deploy Infrastructure with Helm

### 5.1 Deploy NGINX Ingress Controller

```bash
# Create namespace
kubectl create namespace ingress-nginx

# Deploy with Helm
helm upgrade --install ingress-nginx helm-charts/ingress-nginx \
  --namespace ingress-nginx

# Wait for pods to be ready
kubectl wait --for=condition=ready pod \
  -l app=ingress-nginx \
  -n ingress-nginx \
  --timeout=180s

# Check deployment
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx

# Get LoadBalancer IP (save this for later!)
kubectl get svc ingress-nginx-controller -n ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

**Expected:** 2 ingress-nginx controller pods running, LoadBalancer service with external IP.

### 5.2 Deploy cert-manager ClusterIssuer

```bash
# Deploy Let's Encrypt ClusterIssuer with your email
helm upgrade --install cert-issuer helm-charts/cert-manager-config \
  --set email=your-email@example.com

# Verify
kubectl get clusterissuer
# Should show: letsencrypt-prod   True
```

**What this does:** Enables automatic TLS certificate creation for your ingresses.

---

## Step 6: Generate and Apply Secrets

The secrets generation script creates and applies all necessary secrets to your cluster:
- **RSA keys** for JWT authentication
- **Grafana admin password** for monitoring access

```bash
# Generate and apply secrets for production
./scripts/generate-secrets.sh prod

# Generate and apply secrets for testing
./scripts/generate-secrets.sh testing
```

**Important:** The script will output the Grafana admin password. Save it securely!

**To retrieve the Grafana password later:**
```bash
# For production
kubectl get secret grafana-secrets -n prod -o jsonpath='{.data.admin_password}' | base64 -d && echo

# For testing
kubectl get secret grafana-secrets -n testing -o jsonpath='{.data.admin_password}' | base64 -d && echo
```

---

## Step 7: Build and Publish First Release

### 7.1 Verify GitHub Actions

Ensure GitHub Actions has proper permissions:

1. Go to your GitHub repository
2. **Settings** → **Actions** → **General**
3. **Workflow permissions**: Select "Read and write permissions"
4. Click **Save**

### 7.2 Create First Release Tag

```bash
# Create and push tag
git tag v1.0.0 -m "Initial release"
git push origin v1.0.0
```

**What happens:**
1. GitHub Actions builds Docker images
2. Pushes to `ghcr.io/YOUR_USERNAME/auth-service:v1.0.0`
3. Pushes to `ghcr.io/YOUR_USERNAME/tasks-service:v1.0.0`

**Monitor progress:**
- Go to GitHub → **Actions** tab
- Wait for "Build and Deploy" workflow to complete (~3-5 minutes)

### 7.3 Make Images Public (Recommended)

After first build completes:

1. Go to GitHub → Your profile → **Packages**
2. Click on `auth-service` package
3. **Package settings** → **Change visibility** → **Public**
4. Repeat for `tasks-service`

**Why?** No authentication needed, unlimited downloads, simpler configuration.

---

## Step 8: Deploy Services with Helm

### 8.1 Deploy to Production

```bash
# Deploy auth-service
helm upgrade --install auth-service helm-charts/microservice \
  -f helm-charts/values/auth-service-prod.yaml \
  --namespace prod

# Deploy tasks-service  
helm upgrade --install tasks-service helm-charts/microservice \
  -f helm-charts/values/tasks-service-prod.yaml \
  --namespace prod

# Watch deployment progress
kubectl get pods -n prod -w
```

**What gets deployed per service:**
- Deployment (the FastAPI app)
- Service (ClusterIP)
- PostgreSQL Cluster (2 replicas in prod)
- Prometheus (monitoring)
- Grafana (dashboards)
- Ingress (HTTPS routing)
- NetworkPolicies (security)

**Total: ~24 resources per service**

### 8.2 Wait for Everything to be Ready

```bash
# Check Helm releases
helm list -n prod

# Check pods (may take 2-3 minutes for PostgreSQL to initialize)
kubectl get pods -n prod

# Check PostgreSQL clusters
kubectl get cluster -n prod

# All resources
kubectl get all -n prod
```

**Expected output:**
```
NAME                           READY   STATUS    RESTARTS   AGE
auth-service-xxx               1/1     Running   0          2m
auth-service-grafana-xxx       1/1     Running   0          2m
auth-service-prometheus-xxx    1/1     Running   0          2m
postgres-auth-1                1/1     Running   0          2m
postgres-auth-2                1/1     Running   0          1m
tasks-service-xxx              1/1     Running   0          2m
tasks-service-grafana-xxx      1/1     Running   0          2m
tasks-service-prometheus-xxx   1/1     Running   0          2m
postgres-tasks-1               1/1     Running   0          2m
postgres-tasks-2               1/1     Running   0          1m
```

### 8.3 Deploy to Testing (Optional)

```bash
helm upgrade --install auth-service helm-charts/microservice \
  -f helm-charts/values/auth-service-testing.yaml \
  --namespace testing

helm upgrade --install tasks-service helm-charts/microservice \
  -f helm-charts/values/tasks-service-testing.yaml \
  --namespace testing
```

---

## Step 9: Configure DNS

### 9.1 Get LoadBalancer IP

```bash
kubectl get svc ingress-nginx-controller -n ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Example output: 51.250.10.20
```

### 9.2 Create DNS Records

Add **A records** in your DNS provider pointing to the LoadBalancer IP:

```
Type  Name                    Content              TTL
A     tasky.f0x1d.com         <LOADBALANCER_IP>    Auto
A     tasky-testing.f0x1d.com <LOADBALANCER_IP>    Auto
```

**For Cloudflare:**
- Enable proxy (orange cloud) for DDoS protection + SSL
- Set SSL/TLS mode to "Full" or "Full (strict)"
- Enable "Always Use HTTPS"

**For other DNS providers:**
- Just add the A records
- TLS certificates will be handled by cert-manager automatically

### 9.3 Wait for DNS Propagation

```bash
# Test DNS (may take 1-5 minutes)
nslookup tasky.f0x1d.com

# Or use curl
curl -I http://<LOADBALANCER_IP>
```

---

## Step 10: Verify Deployment

### 10.1 Test Direct Access via IP

```bash
LOADBALANCER_IP=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test auth service
curl http://$LOADBALANCER_IP/api/auth/docs

# Test tasks service
curl http://$LOADBALANCER_IP/api/tasks/docs

# Should return HTML (OpenAPI docs)
```

### 10.2 Test via Domain

```bash
# Test auth service (production)
curl https://tasky.f0x1d.com/api/auth/docs

# Test tasks service (production)
curl https://tasky.f0x1d.com/api/tasks/docs

# Test auth service (testing/dev)
curl https://tasky-testing.f0x1d.com/dev/api/auth/docs

# Test tasks service (testing/dev)
curl https://tasky-testing.f0x1d.com/dev/api/tasks/docs

# Should return HTML
```

### 10.3 Test API Endpoints

```bash
# Register a user
curl -X POST https://tasky.f0x1d.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Login
curl -X POST https://tasky.f0x1d.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Save the access_token from response

# Create a task
curl -X POST https://tasky.f0x1d.com/api/tasks/tasks \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "First Task", "content": "Testing deployment"}'

# List tasks
curl https://tasky.f0x1d.com/api/tasks/tasks \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 10.4 Access Web Interfaces

Open in browser:

**Production:**
- **Auth Service API Docs:** https://tasky.f0x1d.com/api/auth/docs
- **Tasks Service API Docs:** https://tasky.f0x1d.com/api/tasks/docs
- **Grafana Dashboard:** https://tasky.f0x1d.com/grafana
  - Username: `admin`
  - Password: (from Step 6 output or retrieve using command below)

**Testing/Dev:**
- **Auth Service API Docs:** https://tasky-testing.f0x1d.com/dev/api/auth/docs
- **Tasks Service API Docs:** https://tasky-testing.f0x1d.com/dev/api/tasks/docs
- **Grafana Dashboard:** https://tasky-testing.f0x1d.com/grafana

**PR Previews:**
- Access via: https://tasky-testing.f0x1d.com/pr-X/api/auth and https://tasky-testing.f0x1d.com/pr-X/api/tasks
- Replace X with your PR number

```bash
# Get Grafana password
kubectl get secret grafana-secrets -n prod -o jsonpath='{.data.admin_password}' | base64 -d && echo
```

---

## 🎉 Setup Complete!

### What You Have Now

✅ **Infrastructure:**
- Kubernetes cluster with NGINX Ingress (HA with 2 replicas)
- Automatic TLS certificates via cert-manager
- CloudNativePG operator for PostgreSQL HA

✅ **Microservices:**
- auth-service (2 replicas in prod)
- tasks-service (2 replicas in prod)
- Each with dedicated PostgreSQL cluster (HA)
- Per-service Prometheus + Grafana monitoring
- HTTPS access via Ingress
- NetworkPolicies for security

✅ **CI/CD:**
- GitHub Actions for automated builds
- GitHub Container Registry for images
- Helm for deployment management

✅ **Monitoring:**
- Prometheus scraping service metrics
- Grafana dashboards with Prometheus datasource
- Accessible at `/grafana` path

---

## Daily Workflow

### Making Changes

```bash
# 1. Edit code
vim auth-service/app/main.py

# 2. Commit and tag
git add .
git commit -m "Add new feature"
git tag v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0

# 3. Wait for GitHub Actions to build (~3-5 min)

# 4. Update Helm values
vim helm-charts/values/auth-service-prod.yaml
# Change: image.tag: "1.1.0"

git add helm-charts/values/auth-service-prod.yaml
git commit -m "Update auth-service to v1.1.0"
git push

# 5. Deploy with Helm
helm upgrade auth-service helm-charts/microservice \
  -f helm-charts/values/auth-service-prod.yaml \
  -n prod

# 6. Monitor
kubectl get pods -n prod -w
```

### Useful Commands

```bash
# List all Helm releases
helm list -A

# Check release status
helm status auth-service -n prod

# View current values
helm get values auth-service -n prod

# Rollback to previous version
helm rollback auth-service -n prod

# Uninstall release
helm uninstall auth-service -n prod

# Check logs
kubectl logs -f -n prod -l app=auth-service

# Check PostgreSQL status
kubectl get cluster -n prod

# Port forward for local testing
kubectl port-forward -n prod svc/auth-service 8000:8000
```

---

## Troubleshooting

### Pods not starting?

```bash
kubectl describe pod <pod-name> -n prod
kubectl logs <pod-name> -n prod
kubectl get events -n prod --sort-by='.lastTimestamp'
```

### Image pull errors?

```bash
# Check if secret exists
kubectl get secret ghcr-secret -n prod

# Check if image is public
# Go to: https://github.com/YOUR_USERNAME?tab=packages

# Verify image in pod
kubectl get pod <pod-name> -n prod -o jsonpath='{.spec.containers[0].image}'
```

### PostgreSQL not ready?

```bash
# Check cluster status
kubectl get cluster -n prod
kubectl describe cluster postgres-auth -n prod

# Check operator logs
kubectl logs -n cnpg-system -l app.kubernetes.io/name=cloudnative-pg

# Check pod logs
kubectl logs -n prod postgres-auth-1
```

### Ingress not working?

```bash
# Check ingress
kubectl get ingress -n prod
kubectl describe ingress auth-service-ingress -n prod

# Check cert-manager
kubectl get certificate -n prod
kubectl describe certificate -n prod

# Check ingress controller
kubectl logs -n ingress-nginx -l app=ingress-nginx
```

### Helm deployment fails?

```bash
# Check what would be deployed
helm template auth-service helm-charts/microservice \
  -f helm-charts/values/auth-service-prod.yaml \
  -n prod | kubectl apply --dry-run=client -f -

# Debug with --debug
helm upgrade --install auth-service helm-charts/microservice \
  -f helm-charts/values/auth-service-prod.yaml \
  -n prod \
  --debug --dry-run

# Check Helm release status
helm status auth-service -n prod
helm history auth-service -n prod
```

---

## Next Steps

- See [README.md](README.md) for detailed operations guide
- Configure monitoring dashboards in Grafana
- Set up automated backups for PostgreSQL
- Configure alerts in Prometheus

---

## Quick Reference Card

```bash
# Deploy/Update service
helm upgrade --install SERVICE helm-charts/microservice \
  -f helm-charts/values/SERVICE-ENV.yaml -n NAMESPACE

# Check status
helm list -n NAMESPACE
kubectl get pods -n NAMESPACE

# Rollback
helm rollback SERVICE -n NAMESPACE

# Logs
kubectl logs -f -n NAMESPACE -l app=SERVICE

# Database
kubectl get cluster -n NAMESPACE
kubectl exec -it postgres-SERVICE-1 -n NAMESPACE -- psql -U postgres DBNAME

# Monitoring
# Grafana: https://YOUR-DOMAIN/grafana (admin / <password>)
```

**Setup completed! 🚀**
