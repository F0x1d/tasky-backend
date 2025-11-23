# Initial Setup Guide

This guide walks you through the **one-time setup** process. After this, everything is automated via CI/CD.

---

## Prerequisites

- **Kubernetes cluster** (Yandex Cloud Managed Kubernetes)
- **kubectl** configured to access your cluster
- **GitHub account** (for Container Registry and Actions)
- **Domain name** with Cloudflare DNS (free plan)
- **OpenSSL** (for generating RSA keys)
- **StorageClass** `yc-network-hdd` available in your cluster (default in Yandex Cloud)

---

## Step 1: Configure GitHub Container Registry (GHCR)

### 1.1 Create Personal Access Token

1. Go to GitHub: **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Name: `k8s-container-registry`
4. Expiration: Select appropriate duration (90 days or longer)
5. Select scopes:
   - ✅ `read:packages`
   - ✅ `write:packages`
   - ✅ `delete:packages`
6. Click **Generate token**
7. **IMPORTANT:** Copy the token immediately (e.g., `ghp_xxxxxxxxxxxx`)

### 1.2 Test Authentication

```bash
# Save your credentials
export GITHUB_TOKEN=ghp_your_token_here
export GITHUB_USERNAME=your_github_username

# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# Expected output: "Login Succeeded"
```

---

## Step 2: Configure Repository

### 2.1 Update Kustomization Files

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username (**MUST BE LOWERCASE**) in the overlay kustomization files:

```bash
# Update prod overlay
vim k8s/overlays/prod/kustomization.yaml
# Change image names from ghcr.io/f0x1d to ghcr.io/YOUR_USERNAME

# Update testing overlay
vim k8s/overlays/testing/kustomization.yaml
# Change image names from ghcr.io/f0x1d to ghcr.io/YOUR_USERNAME

# Update preview overlay
vim k8s/overlays/preview/kustomization.yaml
# Change image names from ghcr.io/f0x1d to ghcr.io/YOUR_USERNAME
```

**IMPORTANT:** GHCR requires lowercase repository names. If your GitHub username has uppercase letters (like `F0x1d`), you **must** convert it to lowercase (`f0x1d`) in the image name.

**Verify changes:**
```bash
# Check prod overlay
cat k8s/overlays/prod/kustomization.yaml

# Should show (with lowercase username):
# images:
#   - name: auth-service
#     newName: ghcr.io/YOUR_USERNAME/auth-service
#     newTag: 1.0.1
```

### 2.2 Update ArgoCD Configuration (if using)

```bash
# Edit k8s/argocd/applications.yaml
# Replace YOUR_USERNAME with your GitHub username (actual case - Git URLs are case-sensitive)
vim k8s/argocd/applications.yaml

# Update the repoURL with your actual repository:
# repoURL: https://github.com/F0x1d/tasks-microservices.git
```

**Note:** Git repository URLs are case-sensitive and should match your actual GitHub repository name.

### 2.3 Commit Configuration

```bash
git add k8s/overlays/*/kustomization.yaml k8s/argocd/applications.yaml
git commit -m "Configure GHCR registry"
git push
```

---

## Step 3: Configure Kubernetes Cluster

### 3.1 Create Namespaces

```bash
kubectl apply -f k8s/namespaces/prod.yaml
kubectl apply -f k8s/namespaces/testing.yaml

# Verify
kubectl get namespaces
```

### 3.2 Create imagePullSecret

This allows Kubernetes to pull images from GHCR:

```bash
# For production namespace
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=$GITHUB_USERNAME \
  --docker-password=$GITHUB_TOKEN \
  --docker-email=your-email@example.com \
  -n prod

# For testing namespace
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

**Note:** If your images are public, this secret is optional but recommended.

### 3.3 NetworkPolicies

NetworkPolicies are now included in the overlays and will be applied automatically when you deploy the overlays. They restrict access to services and databases while keeping ingress-nginx, Prometheus and CloudNativePG internals working.

---

## Step 4: Generate and Apply Secrets

### 4.1 Generate Secrets

```bash
cd k8s/secrets

# Make script executable
chmod +x generate-secrets.sh

# Generate secrets for production
./generate-secrets.sh prod

# IMPORTANT: Save the output! It contains:
# - Database passwords
# - Grafana admin password
# - RSA keys location

# Generate secrets for testing
./generate-secrets.sh testing
```

### 4.2 Apply Secrets to Kubernetes

**For production:**
```bash
kubectl apply -f rsa-keys-secret.yaml -n prod
kubectl apply -f grafana-secrets.yaml -n prod
```

**For testing:**
```bash
kubectl apply -f rsa-keys-secret.yaml -n testing
kubectl apply -f grafana-secrets.yaml -n testing
```

**Verify secrets:**
```bash
kubectl get secrets -n prod
kubectl get secrets -n testing
```

---

## Step 5: Install CloudNativePG Operator

CloudNativePG is a Kubernetes operator that manages PostgreSQL clusters with automatic high availability.

### 5.1 Install the Operator

```bash
# Install CloudNativePG operator
kubectl apply --server-side --force-conflicts -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.27/releases/cnpg-1.27.1.yaml

# Wait for operator to be ready (30-60 seconds)
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=cloudnative-pg \
  -n cnpg-system \
  --timeout=120s

# Verify operator is running
kubectl get pods -n cnpg-system
# Should show: cnpg-controller-manager-... Running
```

### 5.2 Deploy PostgreSQL Clusters

PostgreSQL clusters are now managed through overlays and will be deployed with the environment:

**For testing (1 replica):**
```bash
# Prerequisites checklist (all must be done first):
# 1. ✅ Namespace 'testing' created (Step 3.1)
# 2. ✅ Secrets created in 'testing' namespace (Step 4.2)
# 3. ✅ CNPG operator installed (Step 5.1)
# 4. ✅ StorageClass 'yc-network-hdd' exists (default in Yandex Cloud)

# Deploy testing PostgreSQL clusters
kubectl apply -f k8s/overlays/testing/cloudnative-pg.yaml
```

**Troubleshooting deployment errors:**
```bash
# Error: "namespace testing not found"
→ kubectl apply -f k8s/namespaces/testing.yaml

# Error: "secret postgres-auth-superuser not found"
→ cd k8s/secrets && ./generate-secrets.sh testing && kubectl apply -f postgres-*.yaml -n testing

# Error: "no matches for kind Cluster in version postgresql.cnpg.io/v1"
→ Install CNPG operator (see Step 5.1)

# Error: "storageclass yc-network-hdd not found"
→ kubectl get storageclass  # Check available storage classes

# Error: Deployment hangs or fails with unclear error
→ See k8s/TROUBLESHOOTING.md for detailed diagnostics
→ Clean up and retry:
  kubectl delete cluster --all -n testing
  kubectl delete pvc --all -n testing
  # Wait 30 seconds, then retry
  kubectl apply -f k8s/overlays/testing/cloudnative-pg.yaml
```

**Wait for clusters to be ready:**
```bash
# Watch clusters initializing (takes 2-3 minutes)
kubectl get cluster -n prod -w

# Should show:
# NAME             AGE   INSTANCES   READY   STATUS
# postgres-auth    2m    2           2       Cluster in healthy state
# postgres-tasks   2m    2           2       Cluster in healthy state

# Check pods
kubectl get pods -n prod -l cnpg.io/cluster
# Should show: postgres-auth-1, postgres-auth-2 (both Running and Ready)
```

### 5.3 Get Database Credentials

CloudNativePG uses the superuser secrets you created in Step 4:

```bash
# Get superuser password for auth database
kubectl get secret postgres-auth-superuser -n prod -o jsonpath='{.data.password}' | base64 -d
echo

# Get superuser password for tasks database
kubectl get secret postgres-tasks-superuser -n prod -o jsonpath='{.data.password}' | base64 -d
echo

# Save these passwords - you'll need them!
```

### 5.4 Verify Database Connection

```bash
# Connect to auth database
kubectl exec -it postgres-auth-1 -n prod -- psql -U postgres auth

# Inside psql:
# \l                  # List databases
# \dt                 # List tables
# \q                  # Quit

# Connect to tasks database
kubectl exec -it postgres-tasks-1 -n prod -- psql -U postgres tasks
```

### 5.5 Deploy Monitoring (Optional)

Monitoring can be deployed separately or included in overlays:

**Option A: Deploy manually (recommended for initial setup):**
```bash
kubectl apply -f k8s/monitoring/prometheus.yaml -n prod
kubectl apply -f k8s/monitoring/grafana.yaml -n prod

# Wait for monitoring to be ready
kubectl wait --for=condition=ready pod -l app=prometheus -n prod --timeout=120s
kubectl wait --for=condition=ready pod -l app=grafana -n prod --timeout=120s
```

**Option B: Include in overlay (for automated deployments):**
Add to `k8s/overlays/prod/kustomization.yaml`:
```yaml
resources:
  - ../../monitoring/prometheus.yaml
  - ../../monitoring/grafana.yaml
```

---

## Step 6: Build and Publish First Release

### 6.1 Verify GitHub Actions Workflow

```bash
# Check that workflow file exists
cat .github/workflows/build-and-deploy.yaml

# Verify repository settings on GitHub:
# Settings → Actions → General → Workflow permissions
# Ensure "Read and write permissions" is selected
```

### 6.2 Create First Release

```bash
# Create and push first release tag
git tag v1.0.0 -m "Initial release"
git push origin v1.0.0

# GitHub Actions will automatically:
# 1. Build Docker images
# 2. Push to ghcr.io/YOUR_USERNAME/auth-service:v1.0.0
# 3. Update k8s/*/kustomization.yaml
# 4. Commit changes back to Git
```

### 6.3 Monitor Build Progress

1. Go to your GitHub repository
2. Click **Actions** tab
3. You should see "Build and Deploy" workflow running
4. Click on the workflow to see progress
5. Wait for it to complete (usually 3-5 minutes)

### 6.4 Make Images Public (Recommended)

After first build:

1. Go to your GitHub profile
2. Click **Packages** tab
3. Find `auth-service` package → Click it
4. Click **Package settings** (bottom right)
5. Scroll to **Danger Zone**
6. Click **Change visibility** → **Public**
7. Repeat for `tasks-service`

**Why public?**
- No authentication needed for pulling images
- Unlimited downloads
- Simpler Kubernetes configuration

---

## Step 7: Deploy Services

### 7.1 Deploy Services to Production

```bash
# Deploy complete production environment using overlay
kubectl apply -k k8s/overlays/prod

# Watch pods starting
kubectl get pods -n prod -w

# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=auth-service -n prod --timeout=120s
kubectl wait --for=condition=ready pod -l app=tasks-service -n prod --timeout=120s
```

**Verify deployments:**
```bash
kubectl get deployments -n prod
kubectl get pods -n prod
kubectl get svc -n prod

# Check which image version is running
kubectl get pods -n prod -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
# Should show ghcr.io/YOUR_USERNAME/auth-service:1.0.1
```

**Deploy Testing Environment (optional):**
```bash
kubectl apply -k k8s/overlays/testing
```

---

## Step 8: Configure Ingress

### 8.1 Install cert-manager

cert-manager automates TLS certificate management with Let's Encrypt:

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=120s

# Apply ClusterIssuer for Let's Encrypt production
kubectl apply -f k8s/ingress/cert-manager-clusterissuer.yaml
```

cert-manager will automatically create and renew TLS certificates:
- `tasky-f0x1d-com-tls` in `prod` namespace
- `test-tasky-f0x1d-com-tls` in `testing` namespace

### 8.2 Deploy NGINX Ingress Controller

```bash
# Deploy ingress-nginx controller (includes ConfigMaps, RBAC, Service, Deployment)
kubectl apply -f k8s/ingress/ingress.yaml

# Wait for Ingress Controller to be ready
kubectl wait --for=condition=ready pod -l app=ingress-nginx -n ingress-nginx --timeout=180s
```

**Note:** The ingress rules for each environment are deployed with the overlays in Step 7.

### 8.3 Verify Ingress and Get LoadBalancer IP

```bash
# Check that Ingress pods are on DIFFERENT nodes
kubectl get pods -n ingress-nginx -o wide

# Get LoadBalancer external IP (Yandex Cloud automatically provisions it)
kubectl get svc ingress-nginx-controller -n ingress-nginx

# Example output:
# NAME                       TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)
# ingress-nginx-controller   LoadBalancer   10.96.123.45    51.250.10.20    80:32080/TCP,443:32443/TCP

# Save the EXTERNAL-IP for DNS configuration
```

### 8.4 Test Direct Access via LoadBalancer

```bash
# Get LoadBalancer IP
LOADBALANCER_IP=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test HTTP access
curl http://$LOADBALANCER_IP/api/auth/docs
curl http://$LOADBALANCER_IP/api/tasks/docs

# Should return HTML (OpenAPI docs)
```

---

## Step 9: Configure Cloudflare DNS

### 9.1 Add DNS Records

1. Get LoadBalancer IP:
```bash
kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

2. Log in to your DNS provider (Cloudflare, etc.)
3. Add **A records** pointing to the LoadBalancer IP:

```
Type  Name                         Content              TTL
A     tasky.f0x1d.com              <LOADBALANCER_IP>    Auto
A     test.tasky.f0x1d.com         <LOADBALANCER_IP>    Auto
```

**For Cloudflare:**
- ✅ Enable **Cloudflare Proxy** (orange cloud icon) for SSL/TLS and DDoS protection
- ✅ Or disable proxy (grey cloud) and use TLS certificates directly in Kubernetes

**For other DNS providers:**
- Just point A records to the LoadBalancer IP
- Use TLS certificates in Kubernetes (cert-manager handles this automatically)

### 9.2 Configure SSL/TLS

1. In Cloudflare Dashboard, go to **SSL/TLS** section
2. Set SSL/TLS encryption mode to: **Full** (or **Full (strict)** if you have valid certs on your nodes)
3. Enable **Always Use HTTPS** under SSL/TLS → Edge Certificates

### 9.3 Test Domain Access

```bash
# Test your domain (may take 1-5 minutes for DNS to propagate)
curl https://tasky.f0x1d.com/api/auth/docs
curl https://tasky.f0x1d.com/api/tasks/docs

# Check SSL certificate
curl -I https://tasky.f0x1d.com
# Should show: HTTP/2 200
```

---

## Step 10: Verify Everything Works

### 10.1 Test API Endpoints

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
  -d '{"title": "Test Task", "content": "Testing API"}'

# List tasks
curl https://tasky.f0x1d.com/api/tasks/tasks \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 10.2 Access Web Interfaces

Open in browser:
- **Auth Service API**: https://tasky.f0x1d.com/api/auth/docs
- **Tasks Service API**: https://tasky.f0x1d.com/api/tasks/docs
- **Grafana**: https://tasky.f0x1d.com/grafana
  - Username: `admin`
  - Password: (from secrets generation output in Step 4)

### 10.3 Test High Availability

**Test Ingress HA:**
```bash
# Delete one Ingress pod
kubectl delete pod -n ingress-nginx <pod-name>

# Service should still work (LoadBalancer routes to remaining pod)
curl https://tasky.f0x1d.com/api/auth/health
# Should return: {"status":"healthy"}
```

**Test PostgreSQL HA:**
```bash
# Check current primary
kubectl get cluster postgres-auth -n prod

# Delete primary pod (pod-1 is usually primary)
kubectl delete pod postgres-auth-1 -n prod

# CloudNativePG automatically promotes standby (~30 seconds)
# Check new primary
kubectl get cluster postgres-auth -n prod

# Service should still work
curl -X POST https://tasky.f0x1d.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser2", "password": "testpass123"}'
```

---

## Step 11: (Optional) Set Up ArgoCD for GitOps

### 11.1 Install ArgoCD

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s
```

### 11.2 Access ArgoCD UI

```bash
# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo

# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open browser: https://localhost:8080
# Login: admin / <password from above>
```

### 11.3 Create Applications

```bash
# Apply ArgoCD applications (now pointing to overlays)
kubectl apply -f k8s/argocd/applications.yaml

# Verify in UI or CLI
kubectl get applications -n argocd

# You should see:
# - prod-env (k8s/overlays/prod)
# - testing-env (k8s/overlays/testing)
```

### 11.5 Configure Preview Environments (Optional)

To enable automatic PR Previews:

```bash
# Apply the ApplicationSet (Requires ArgoCD)
kubectl apply -f k8s/argocd/applicationset-preview.yaml
```

This will automatically deploy ephemeral environments for every open Pull Request.

---

## Troubleshooting Setup Issues

### GitHub Actions Fails

**Check repository permissions:**
```bash
# GitHub Repository → Settings → Actions → General
# Workflow permissions: "Read and write permissions"
```

**Check workflow logs:**
```
GitHub → Actions → Select failed workflow → View logs
```

### Image Pull Errors

**Check secret:**
```bash
kubectl get secret ghcr-secret -n prod
kubectl describe secret ghcr-secret -n prod
```

**Recreate secret:**
```bash
kubectl delete secret ghcr-secret -n prod
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=$GITHUB_USERNAME \
  --docker-password=$GITHUB_TOKEN \
  -n prod
```

**Check if package is public:**
```
GitHub → Your Profile → Packages → Select package → Package settings → Visibility
```

### Services Not Accessible

**Check services:**
```bash
kubectl get svc -n prod
kubectl describe svc auth-service -n prod
```

**Check ingress:**
```bash
kubectl get ingress -n prod
kubectl describe ingress services-ingress -n prod
```

**Check pods:**
```bash
kubectl get pods -n prod
kubectl describe pod <pod-name> -n prod
kubectl logs <pod-name> -n prod
```

### PostgreSQL Issues

**Check cluster status:**
```bash
kubectl get cluster -n prod
kubectl describe cluster postgres-auth -n prod
```

**Check logs:**
```bash
kubectl logs -n prod postgres-auth-1
```

**Check secrets:**
```bash
kubectl get secret postgres-auth-superuser -n prod -o yaml
```

---

## Setup Complete!

You now have:
- ✅ Yandex Cloud Managed Kubernetes cluster
- ✅ GitHub Container Registry configured
- ✅ CI/CD pipeline with GitHub Actions
- ✅ PostgreSQL with CloudNativePG (automatic HA and failover)
- ✅ Microservices deployed with security hardening
- ✅ NGINX Ingress with LoadBalancer and HA
- ✅ DNS pointing to LoadBalancer IP
- ✅ NetworkPolicies for security isolation
- ✅ Monitoring with Prometheus + Grafana (persistent storage)
- ✅ (Optional) GitOps with ArgoCD

## Next Steps

1. **Daily development**: See [README.md](README.md) for daily workflow
2. **Make changes**: Edit code, commit, create tag, let CI/CD handle the rest
3. **Monitor**: Use Grafana dashboard and kubectl commands
4. **Scale**: Increase replicas as needed with `kubectl scale`

## Quick Reference

```bash
# Create new release
git tag v1.1.0 -m "New features"
git push origin v1.1.0

# Deploy (after GitHub Actions completes)
kubectl apply -k k8s/overlays/prod

# Check status
kubectl get pods -n prod

# View logs
kubectl logs -f -n prod -l app=auth-service

# Check PostgreSQL cluster status
kubectl get cluster -n prod

# Rollback if needed
kubectl rollout undo deployment/auth-service -n prod
```

---

## CloudNativePG Quick Reference

```bash
# List all PostgreSQL clusters
kubectl get cluster -n prod

# Get cluster details
kubectl describe cluster postgres-auth -n prod

# Get credentials
kubectl get secret postgres-auth-superuser -n prod -o jsonpath='{.data.password}' | base64 -d

# Connect to database
kubectl exec -it postgres-auth-1 -n prod -- psql -U postgres auth

# Check replication status
kubectl get cluster postgres-auth -n prod -o wide

# Manual switchover
kubectl cnpg promote postgres-auth 2 -n prod

# Backup database (if configured)
kubectl cnpg backup postgres-auth -n prod
```

**Setup completed! 🎉**
