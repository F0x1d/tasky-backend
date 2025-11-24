#!/bin/bash

# Script to generate and apply secrets for Kubernetes deployment
# Usage: ./generate-secrets.sh <namespace>
# Example: ./generate-secrets.sh prod
#          ./generate-secrets.sh testing

set -e

NAMESPACE=${1:-prod}

echo "========================================"
echo "Generating secrets for namespace: $NAMESPACE"
echo "========================================"
echo ""

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "❌ Error: Namespace '$NAMESPACE' does not exist"
    echo "Create it first with: kubectl create namespace $NAMESPACE"
    exit 1
fi

# Generate RSA keys for JWT
echo "📝 Generating RSA key pair for JWT authentication..."
openssl genrsa -out private_key.pem 2048 2>/dev/null
openssl rsa -in private_key.pem -pubout -out public_key.pem 2>/dev/null
echo "✅ RSA keys generated"

# Create RSA keys secret
echo "🔐 Creating RSA keys secret in namespace '$NAMESPACE'..."
kubectl create secret generic rsa-keys \
  --from-file=private_key.pem=private_key.pem \
  --from-file=public_key.pem=public_key.pem \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Generate random password for Grafana
GRAFANA_PASSWORD=$(openssl rand -base64 16)

# Create Grafana secrets
echo "🔐 Creating Grafana secrets in namespace '$NAMESPACE'..."
kubectl create secret generic grafana-secrets \
  --from-literal=admin_password=$GRAFANA_PASSWORD \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Clean up temporary files
rm -f private_key.pem public_key.pem

echo ""
echo "========================================"
echo "✅ Secrets created successfully!"
echo "========================================"
echo ""
echo "📊 Grafana admin credentials:"
echo "   Username: admin"
echo "   Password: $GRAFANA_PASSWORD"
echo ""
echo "⚠️  IMPORTANT: Save the Grafana password securely!"
echo ""
echo "📋 To retrieve the password later:"
echo "   kubectl get secret grafana-secrets -n $NAMESPACE -o jsonpath='{.data.admin_password}' | base64 -d && echo"
echo ""
echo "🔍 Verify secrets were created:"
echo "   kubectl get secrets -n $NAMESPACE | grep -E 'rsa-keys|grafana-secrets'"
echo ""
