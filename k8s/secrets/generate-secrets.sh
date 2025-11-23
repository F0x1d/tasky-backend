#!/bin/bash

# Script to generate secrets for Kubernetes deployment
# Usage: ./generate-secrets.sh <namespace>

NAMESPACE=${1:-prod}

echo "Generating secrets for namespace: $NAMESPACE"

# Generate RSA keys for JWT
echo "Generating RSA key pair..."
openssl genrsa -out private_key.pem 2048
openssl rsa -in private_key.pem -pubout -out public_key.pem

# Create RSA keys secret
echo "Creating RSA keys secret..."
kubectl create secret generic rsa-keys \
  --from-file=private_key.pem=private_key.pem \
  --from-file=public_key.pem=public_key.pem \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml > rsa-keys-secret.yaml

# Generate random password only for Grafana
GRAFANA_PASSWORD=$(openssl rand -base64 16)

# Grafana secrets
echo "Creating Grafana secrets..."
kubectl create secret generic grafana-secrets \
  --from-literal=admin_password=$GRAFANA_PASSWORD \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml > grafana-secrets.yaml

echo ""
echo "========================================"
echo "Secrets generated successfully!"
echo "========================================"
echo "Grafana admin password: $GRAFANA_PASSWORD"
echo ""
echo "IMPORTANT: Save these passwords securely!"
echo ""
echo "To apply secrets to cluster, run:"
echo "kubectl apply -f rsa-keys-secret.yaml"
echo "kubectl apply -f grafana-secrets.yaml"
echo ""
echo "Clean up temporary files:"
echo "rm private_key.pem public_key.pem"
