# Despliegue en Kubernetes (k3s) sobre AWS EC2

Esta guía publica LabSentinel en un clúster Kubernetes de un nodo con [k3s](https://k3s.io), una distribución certificada y liviana, instalada en una VM de AWS EC2. Los manifiestos están en [k8s/](../k8s) y reutilizan las imágenes, la configuración de Nginx y los archivos de `infra/` del despliegue con Docker Compose.

Resultado: la aplicación queda en `https://<dominio>` y Keycloak en `https://<dominio>:8443`, con un certificado de Let's Encrypt.

## 1. Correspondencia con compose.yaml

| compose.yaml | Kubernetes ([k8s/](../k8s)) |
| --- | --- |
| Servicios `auth-service`, `device-service`, `telemetry-service`, `alert-ticket-service`, `report-service`, `simulator-device`, `frontend` | Un *Deployment* y un *Service* por microservicio, con los mismos nombres |
| `gateway` (Nginx, puerto publicado) | *Deployment* + *Service* `LoadBalancer` en el puerto 443 |
| `keycloak` | *Deployment* + *Service* interno (8080) + *Service* `LoadBalancer` (8443) |
| `postgres` y volumen `postgres_data` | *StatefulSet* + *PersistentVolumeClaim* |
| `database-migrations`, `keycloak-client-config` | *Jobs* |
| `.env` | *Secret* `labsentinel-env` |
| Volumen `tls_certificates` | *Secret* TLS `labsentinel-tls` |
| `infra/nginx`, `infra/postgres`, `infra/keycloak` | *ConfigMaps* |
| `healthcheck` | *readinessProbe* y *livenessProbe* |
| Red `backend` con `internal: true` | *NetworkPolicies*: solo el gateway y Keycloak reciben tráfico externo, PostgreSQL acepta solo a sus clientes y los servicios sin necesidad de Internet no tienen salida |
| `depends_on` | Orden de aplicación en [k8s/deploy.sh](../k8s/deploy.sh) |

## 2. Máquina virtual

| Elemento | Valor |
| --- | --- |
| Instancia | AWS EC2 `m7i-flex.large` (2 vCPU, 8 GB), Ubuntu Server 24.04 LTS |
| Disco | 30 GiB gp3 |
| Security group (entrada) | 22 (SSH), 80 (validación de Let's Encrypt), 443 (aplicación), 8443 (Keycloak) |
| IP | *Elastic IP* asociada a la instancia |
| Dominio | Subdominio de [DuckDNS](https://www.duckdns.org) apuntando a la Elastic IP |

Conexión desde Windows:

```powershell
$key = "$HOME\.ssh\labsentinel-key.pem"
icacls $key /inheritance:r /grant:r "$($env:USERNAME):R"
ssh -i $key ubuntu@<dominio>
```

## 3. Preparar el servidor

```bash
sudo apt update && sudo apt install -y git certbot
curl -fsSL https://get.docker.com | sudo sh
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.31.4+k3s1 sh -s - --disable traefik --write-kubeconfig-mode 644
kubectl get nodes
```

Docker solo se usa para construir las imágenes. Se desactiva Traefik porque el gateway Nginx del proyecto ocupa el puerto 443.

```bash
git clone https://github.com/ParcheEnGit/seguridad-microservicios.git
cd seguridad-microservicios
git checkout feature/despliegue
```

## 4. Certificado HTTPS

```bash
sudo certbot certonly --standalone -d <dominio> -m <correo> --agree-tos --no-eff-email
```

## 5. Variables de entorno

```bash
cp .env.example .env
openssl rand -hex 32   # JWT_SECRET
openssl rand -hex 24   # SIMULATOR_API_KEY
nano .env
```

| Variable | Valor |
| --- | --- |
| `APP_ENV` | `production` |
| `POSTGRES_PASSWORD`, `KEYCLOAK_DB_PASSWORD` | Contraseña nueva y larga (la misma en ambas) |
| `KEYCLOAK_ADMIN_PASSWORD` | Contraseña nueva y larga |
| `JWT_SECRET`, `SIMULATOR_API_KEY` | Valores generados con `openssl` |
| `CORS_ORIGINS` | `https://<dominio>` |
| `COOKIE_SECURE` | `true` |
| `KEYCLOAK_ENABLED`, `VITE_KEYCLOAK_ENABLED` | `true` |
| `VITE_KEYCLOAK_URL`, `KEYCLOAK_URL_PUBLIC` | `https://<dominio>:8443` |
| `KEYCLOAK_REDIRECT_URI` | `https://<dominio>/api/auth/keycloak/callback` |
| `KEYCLOAK_FRONTEND_URL` | `https://<dominio>/` |
| `LOCAL_PASSWORD_LOGIN_ENABLED` | `false` |

`GOOGLE_CLIENT_ID` debe existir aunque no se use el acceso con Google. Las contraseñas del servidor no deben coincidir con las de desarrollo ni compartirse por chat.

## 6. Construir las imágenes y desplegar

```bash
sudo sh k8s/import-images.sh
sudo sh k8s/deploy.sh /etc/letsencrypt/live/<dominio>/fullchain.pem /etc/letsencrypt/live/<dominio>/privkey.pem
```

El primer comando construye las imágenes con Docker y las importa en k3s. El segundo crea los Secrets y ConfigMaps y aplica los manifiestos en orden: PostgreSQL, migraciones, Keycloak y su configuración, microservicios, frontend y gateway. Keycloak tarda entre 1 y 2 minutos en iniciar la primera vez; los reintentos de `keycloak-client-config` mientras tanto son normales.

## 7. Usuarios de Keycloak

1. Abrir `https://<dominio>:8443` e ingresar con `KEYCLOAK_ADMIN` y `KEYCLOAK_ADMIN_PASSWORD`.
2. Cambiar al realm **labsentinel** y crear los usuarios con su rol (`admin` o `lector`), como en el [manual técnico](manual-tecnico.md#usuarios-de-keycloak).
3. Abrir `https://<dominio>`, presionar «Ingresar con Keycloak» y registrar los dispositivos desde la interfaz.

## 8. Verificación

| Comprobación | Resultado esperado |
| --- | --- |
| `kubectl -n labsentinel get pods` | Todos `Running` y `1/1`; los Jobs en `Completed` |
| `https://<dominio>` | Pantalla de inicio de sesión con candado válido |
| `https://<dominio>/api/auth/health` | `{"status":"ok", ...}` |
| `curl -i https://<dominio>/api/devices/devices` | `401 Unauthorized` |
| `kubectl -n labsentinel logs deploy/simulator-device --tail 5` | Lecturas enviadas cada 15 s |

## 9. Operación

| Acción | Comando |
| --- | --- |
| Ver el estado | `kubectl -n labsentinel get pods,services` |
| Ver logs | `kubectl -n labsentinel logs -f deploy/<servicio>` |
| Escalar un microservicio | `kubectl -n labsentinel scale deploy/telemetry-service --replicas=2` |
| Actualizar a la última versión | `git pull`, `sudo sh k8s/import-images.sh`, `sudo sh k8s/deploy.sh <cert> <clave>` y `kubectl -n labsentinel rollout restart deployment` |
| Detener la aplicación (conserva los datos) | `kubectl -n labsentinel scale deploy --all --replicas=0` y `kubectl -n labsentinel scale statefulset/postgres --replicas=0` |
| Renovar el certificado (vence cada 90 días) | `sudo certbot renew` y volver a ejecutar `deploy.sh`, luego `kubectl -n labsentinel rollout restart deployment gateway keycloak` |
| Eliminar todo, incluidos los datos | `kubectl delete namespace labsentinel` |

Si un pod no inicia, `kubectl -n labsentinel describe pod <pod>` muestra el motivo (por ejemplo, una variable que falta en `.env`).

## 10. Consideraciones

- Solo los puertos 443 y 8443 quedan expuestos; PostgreSQL y los microservicios usan Services internos del clúster.
- El clúster tiene un nodo: Kubernetes reinicia los pods que fallan y permite escalar réplicas, pero no hay alta disponibilidad ante la caída de la VM.
- Keycloak se ejecuta en modo `start-dev`, como en el despliegue con Compose.
- Detener la instancia EC2 cuando no se use y eliminarla al terminar la evaluación para no consumir crédito.
