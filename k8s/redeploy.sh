#!/usr/bin/env sh
# Actualiza el servidor a la última versión de la rama y vuelve a desplegar.
# Lo ejecuta el workflow de CD por SSH; también se puede ejecutar a mano:
#   sh k8s/redeploy.sh <dominio>
set -eu

DOMAIN="${1:?Uso: sh k8s/redeploy.sh <dominio>}"
BRANCH="${BRANCH:-feature/despliegue}"
NS=labsentinel

cd "$(dirname "$0")/.."
git fetch --quiet origin "$BRANCH"
# .env no está versionado, así que no se modifica.
git reset --quiet --hard "origin/$BRANCH"
echo "Desplegando $(git log -1 --format='%h %s')"

sudo sh k8s/import-images.sh
sudo sh k8s/deploy.sh "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "/etc/letsencrypt/live/$DOMAIN/privkey.pem"
# Las imágenes usan la etiqueta latest; el reinicio carga las recién importadas.
kubectl -n "$NS" rollout restart deployment
for deployment in $(kubectl -n "$NS" get deployment -o name); do
  kubectl -n "$NS" rollout status "$deployment" --timeout=600s
done
