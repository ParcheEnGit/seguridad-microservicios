#!/usr/bin/env sh
# Despliega LabSentinel en Kubernetes (k3s): crea los Secrets a partir de .env
# y del certificado TLS, las ConfigMaps a partir de infra/ y aplica los
# manifiestos en el orden que compose.yaml expresa con depends_on.
#
# Uso, desde la raíz del repositorio y después de k8s/import-images.sh:
#   sudo sh k8s/deploy.sh /etc/letsencrypt/live/<dominio>/fullchain.pem /etc/letsencrypt/live/<dominio>/privkey.pem
set -eu

CERT="${1:?Uso: sh k8s/deploy.sh <certificado.pem> <clave.pem>}"
KEY="${2:?Uso: sh k8s/deploy.sh <certificado.pem> <clave.pem>}"
ENV_FILE="${ENV_FILE:-.env}"
NS=labsentinel

# Crea o actualiza un objeto generado por kubectl create.
apply_generated() {
  kubectl -n "$NS" create "$@" --dry-run=client -o yaml | kubectl apply -f -
}

kubectl apply -f k8s/namespace.yaml
apply_generated secret generic labsentinel-env --from-env-file="$ENV_FILE"
apply_generated secret tls labsentinel-tls --cert="$CERT" --key="$KEY"
apply_generated configmap gateway-config --from-file=default.conf=infra/nginx/default.conf
apply_generated configmap postgres-init --from-file=infra/postgres/init/
apply_generated configmap postgres-migrations --from-file=infra/postgres/migrations/
apply_generated configmap keycloak-realm --from-file=infra/keycloak/realm-labsentinel.json
apply_generated configmap keycloak-client-script --from-file=infra/keycloak/configure-client.py

kubectl apply -f k8s/network-policies.yaml -f k8s/storage.yaml -f k8s/postgres.yaml
kubectl -n "$NS" rollout status statefulset/postgres --timeout=300s

# Un Job terminado no se puede modificar; se recrea en cada despliegue.
kubectl -n "$NS" delete job database-migrations keycloak-client-config --ignore-not-found
kubectl apply -f k8s/database-migrations.yaml
kubectl -n "$NS" wait --for=condition=complete job/database-migrations --timeout=300s

kubectl apply -f k8s/keycloak.yaml
kubectl -n "$NS" rollout status deployment/keycloak --timeout=600s
kubectl -n "$NS" wait --for=condition=complete job/keycloak-client-config --timeout=300s

for manifest in auth-service device-service telemetry-service alert-ticket-service report-service simulator-device frontend gateway; do
  kubectl apply -f "k8s/$manifest.yaml"
done
for deployment in auth-service device-service telemetry-service alert-ticket-service report-service simulator-device frontend gateway; do
  kubectl -n "$NS" rollout status "deployment/$deployment" --timeout=300s
done

kubectl -n "$NS" get pods,services
