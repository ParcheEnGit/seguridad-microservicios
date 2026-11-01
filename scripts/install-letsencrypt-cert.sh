#!/usr/bin/env sh
# Copia el certificado de Let's Encrypt de un dominio al volumen TLS que usan
# Nginx y Keycloak, con los nombres que esperan (localhost.crt y localhost.key).
#
# Uso, en el servidor y después de obtener el certificado con certbot:
#   sudo sh scripts/install-letsencrypt-cert.sh <dominio>
set -eu

DOMAIN="${1:?Uso: sudo sh scripts/install-letsencrypt-cert.sh <dominio>}"
VOLUME="${COMPOSE_PROJECT_NAME:-labsentinel}_tls_certificates"

if [ ! -s "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
  echo "No existe el certificado de $DOMAIN; ejecute primero certbot." >&2
  exit 1
fi

docker volume create "$VOLUME" >/dev/null
docker run --rm -v "$VOLUME:/certs" -v /etc/letsencrypt:/le:ro alpine:3.20 sh -ec "
  cp -L /le/live/$DOMAIN/fullchain.pem /certs/localhost.crt
  cp -L /le/live/$DOMAIN/privkey.pem /certs/localhost.key
  # tls-init regenera la CA local si falta alguno de sus archivos; se deja la
  # cadena pública en su lugar para que no reemplace el certificado.
  cp -L /le/live/$DOMAIN/chain.pem /certs/labsentinel-local-ca.crt
  chown 1000:0 /certs/localhost.key /certs/localhost.crt
  chmod 640 /certs/localhost.key
  chmod 644 /certs/localhost.crt /certs/labsentinel-local-ca.crt
"
echo "Certificado de $DOMAIN instalado en el volumen $VOLUME."
