# Kubernetes Configuration Guidelines

## Commands
- Apply: `kubectl apply -f <file> --namespace=<namespace>`
- Validate: `kubectl apply -f <file> --dry-run=client`
- Test resource: `kubectl get <resource-type> <name> -n <namespace>` or `kubectl describe <resource-type> <name> -n <namespace>`
- View logs: `kubectl logs <pod-name> -n <namespace>`
- Generate secrets: `cd secrets && ./generate-secrets.sh <namespace>`
- Check Ingress: `kubectl get svc -n ingress-nginx` (LoadBalancer with external IP)
- Apply Postgres:
  - Production: `kubectl apply -f k8s/postgres/cloudnative-pg-{auth,tasks}.yaml`
  - Testing: `kubectl apply -f k8s/overlays/testing/cloudnative-pg.yaml` (requires namespace + secrets first)
- Common testing error: Forgetting to create namespace or secrets before deploying Postgres clusters

## Code Style
- **Indentation**: Use 2 spaces (no tabs)
- **Naming**: Use kebab-case for all resource names (e.g., `auth-service`, `postgres-auth`)
- **Labels**: Always include `app: <service-name>` label; add `environment: <env>` for overlays
- **Multi-resource files**: Separate resources with `---` (Deployment + Service in same file is standard)
- **Resource management**: Always specify `requests` and `limits` for CPU/memory
- **Health checks**: Include `livenessProbe` and `readinessProbe` for all deployments
- **High availability**: Use `podAntiAffinity` with `requiredDuringSchedulingIgnoredDuringExecution` for production deployments (2+ replicas)
- **Ingress**: Ingress Controller uses 2 replicas with anti-affinity + LoadBalancer service (Yandex Cloud automatically provisions external IP)
- **Secrets**: Reference via `secretKeyRef` or `secretRef` - NEVER hardcode sensitive values
- **Image policy**: Use `imagePullPolicy: IfNotPresent` and specific image tags (avoid `latest` in production)
- **Volumes**: Mount secrets as `readOnly: true`
- **Namespace**: Explicitly specify `namespace` in overlays, omit in base manifests.
- **Ingress resources**:
  - Ingress Controller manifests live in `ingress-nginx` namespace.
  - Application ingresses live in their target namespaces:
    - `prod` → host `tasky.f0x1d.com`, secret `tasky-f0x1d-com-tls`.
    - `testing` → host `test.tasky.f0x1d.com`, secret `test-tasky-f0x1d-com-tls`.
- **CloudNativePG**:
  - Cluster names: `postgres-auth`, `postgres-tasks` in `prod` and `testing`.
  - Databases: `auth` and `tasks` (no `authdb`/`tasksdb`).
  - Storage: Uses `yc-network-hdd` StorageClass (Yandex Cloud).
  - Superuser secrets: `postgres-auth-superuser`, `postgres-tasks-superuser`; `generate-secrets.sh` must stay in sync with cluster specs.
  - App `DATABASE_URL` values must use `*-rw` services (e.g. `postgres-auth-rw`, `postgres-tasks-rw`).
- **NetworkPolicies**: When adding new services or ports, update `k8s/networkpolicies-prod.yaml` and `k8s/networkpolicies-testing.yaml` so traffic remains explicitly allowed.

DO **NOT** KEEP BACKWARDS COMPATIBILITY OR FALLBACKS, unless user explicitly asks it
