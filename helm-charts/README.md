# Helm Charts

This directory contains Helm charts for deploying all microservices with their own PostgreSQL, Prometheus, and Grafana instances.

## Structure

```
helm-charts/
├── microservice/          # Reusable chart for all microservices
├── values/                # Environment-specific values files
├── ingress-nginx/         # Ingress controller
└── cert-manager-config/   # TLS certificate management
```

## Quick Start

### Deployment

```bash
# 1. Deploy ingress-nginx
helm upgrade --install ingress-nginx ./helm-charts/ingress-nginx --create-namespace

# 2. Deploy cert-manager config
helm upgrade --install cert-manager-config ./helm-charts/cert-manager-config

# 3. Deploy auth-service to prod
helm upgrade --install auth-service ./helm-charts/microservice \
  -f ./helm-charts/values/auth-service-prod.yaml \
  --namespace prod --create-namespace

# 4. Deploy tasks-service to prod
helm upgrade --install tasks-service ./helm-charts/microservice \
  -f ./helm-charts/values/tasks-service-prod.yaml \
  --namespace prod

# 5. Deploy to testing environment
helm upgrade --install auth-service ./helm-charts/microservice \
  -f ./helm-charts/values/auth-service-testing.yaml \
  --namespace testing --create-namespace

helm upgrade --install tasks-service ./helm-charts/microservice \
  -f ./helm-charts/values/tasks-service-testing.yaml \
  --namespace testing
```

## Features

Each service gets:
- **Independent PostgreSQL database** (CloudNativePG with 2 replicas in prod, 1 in testing)
- **Dedicated Prometheus instance** for metrics collection
- **Dedicated Grafana instance** for visualization
- **Network policies** for security
- **Ingress with TLS** (Let's Encrypt)
- **Pod anti-affinity** for HA in prod

## Values Files

- `auth-service-prod.yaml` - Auth service production config (2 replicas, 2 postgres instances)
- `auth-service-testing.yaml` - Auth service testing config (1 replica, 1 postgres instance)
- `tasks-service-prod.yaml` - Tasks service production config
- `tasks-service-testing.yaml` - Tasks service testing config

## Monitoring Access

- **Grafana**: `https://tasky.f0x1d.com/grafana/` (prod) or `https://tasky-testing.f0x1d.com/grafana/` (testing)
- **Prometheus**: Not exposed externally (access via port-forward if needed)

```bash
# Access Prometheus
kubectl port-forward -n prod svc/auth-service-prometheus 9090:9090

# Access Grafana directly
kubectl port-forward -n prod svc/auth-service-grafana 3000:3000
```

## Customization

To add a new service:
1. Create a new values file in `helm-charts/values/`
2. Deploy using: `helm upgrade --install <name> ./helm-charts/microservice -f ./helm-charts/values/<your-values>.yaml`

## Updating Services

```bash
# Update image tag in values file, then:
helm upgrade auth-service ./helm-charts/microservice \
  -f ./helm-charts/values/auth-service-prod.yaml \
  --namespace prod
```
