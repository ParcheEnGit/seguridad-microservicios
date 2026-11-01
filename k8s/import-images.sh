#!/usr/bin/env sh
# Construye las imágenes de LabSentinel con Docker (incluido el frontend
# compilado de compose.prod.yaml) y las importa en el runtime de k3s.
#
# Uso, desde la raíz del repositorio y con .env completo:
#   sudo sh k8s/import-images.sh
set -eu

PROJECT="${COMPOSE_PROJECT_NAME:-labsentinel}"
IMPORT="${IMPORT:-k3s ctr images import -}"
SERVICES="auth-service device-service telemetry-service alert-ticket-service report-service simulator-device frontend"

docker compose -f compose.yaml -f compose.prod.yaml build $SERVICES
for service in $SERVICES; do
  echo "Importando $PROJECT-$service en k3s..."
  docker save "$PROJECT-$service:latest" | $IMPORT
done
