#!/usr/bin/env sh
set -eu

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE DATABASE "$KEYCLOAK_DB" OWNER "$POSTGRES_USER";
EOSQL
