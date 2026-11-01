# Despliegue en un servidor en la nube

Esta guía publica LabSentinel en una máquina virtual con IP pública, usando el mismo `compose.yaml` más los ajustes de [compose.prod.yaml](../compose.prod.yaml). Para desplegar en Kubernetes (k3s), ver [despliegue-kubernetes.md](despliegue-kubernetes.md).

Resultado: la aplicación queda en `https://<dominio>` y Keycloak en `https://<dominio>:8443`, con un certificado de Let's Encrypt reconocido por cualquier navegador.

## 1. Requisitos

| Elemento | Valor recomendado |
| --- | --- |
| Máquina virtual | Ubuntu 24.04 LTS, 2 vCPU y 4 GB de RAM (el sistema completo usa ~1,3 GB) |
| Disco | 30 GB |
| Proveedor | Azure for Students (crédito de 100 USD con el correo institucional, sin tarjeta) u Oracle Cloud Always Free (VM Ampere A1 ARM) |
| Dominio | Subdominio gratuito de [DuckDNS](https://www.duckdns.org) |

Todas las imágenes del proyecto están disponibles para `amd64` y `arm64`.

## 2. Crear la máquina virtual

1. En el portal del proveedor, crear una VM Ubuntu 24.04 con el tamaño indicado (en AWS EC2: *m7i-flex.large* o *c7i-flex.large*, elegibles en el plan gratuito; en Azure: *Standard B2s*).
2. Autenticación por **clave SSH** (descargar la clave privada y guardarla en un lugar seguro).
3. Abrir los puertos de entrada en el firewall del proveedor (en AWS: *Security group*; en Azure: *Network security group*; en Oracle: *Security List* de la VCN):

| Puerto | Uso |
| --- | --- |
| 22 | SSH (administración) |
| 80 | Validación de Let's Encrypt al emitir y renovar el certificado |
| 443 | Aplicación (gateway Nginx) |
| 8443 | Keycloak |

4. Anotar la **IP pública** de la VM. En AWS, asociar una *Elastic IP* para que la IP no cambie al detener y volver a iniciar la instancia.

## 3. Dominio gratuito

En Azure basta con la etiqueta DNS de la IP pública: en la VM, *Overview* → *DNS name* → *Not configured*, escribir una etiqueta (por ejemplo `labsentinel-g36`) y guardar. El dominio queda como `labsentinel-g36.<región>.cloudapp.azure.com`.

En otros proveedores, usar DuckDNS:

1. Ingresar a [duckdns.org](https://www.duckdns.org), crear un subdominio (por ejemplo `labsentinel-g36`) y asignarle la IP pública de la VM.
2. Verificar desde el equipo local que el dominio responde con esa IP:

   ```powershell
   nslookup labsentinel-g36.duckdns.org
   ```

En el resto de la guía, `<dominio>` es el dominio completo, por ejemplo `labsentinel-g36.duckdns.org`.

## 4. Preparar el servidor

Conectarse por SSH (`ssh -i <clave> <usuario>@<IP>`) y ejecutar:

```bash
sudo apt update && sudo apt install -y git certbot
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit
```

Volver a conectarse para que el grupo `docker` tenga efecto y clonar el repositorio:

```bash
git clone https://github.com/ParcheEnGit/seguridad-microservicios.git
cd seguridad-microservicios
git checkout dev
```

En Ubuntu de Oracle Cloud, abrir además los puertos en el firewall interno del sistema:

```bash
sudo iptables -I INPUT -p tcp -m multiport --dports 80,443,8443 -j ACCEPT
sudo netfilter-persistent save
```

## 5. Certificado HTTPS

```bash
sudo certbot certonly --standalone -d <dominio> -m <correo> --agree-tos --no-eff-email
sudo sh scripts/install-letsencrypt-cert.sh <dominio>
```

El primer comando obtiene el certificado (usa el puerto 80) y el segundo lo copia al volumen que usan Nginx y Keycloak.

## 6. Variables de entorno

```bash
cp .env.example .env
openssl rand -hex 32   # usar para JWT_SECRET
openssl rand -hex 24   # usar para SIMULATOR_API_KEY
nano .env
```

Cambiar, como mínimo:

| Variable | Valor |
| --- | --- |
| `APP_ENV` | `production` (desactiva el acceso local con contraseña) |
| `GATEWAY_PORT` | `443` |
| `KEYCLOAK_PORT` | `8443` |
| `POSTGRES_PASSWORD`, `KEYCLOAK_DB_PASSWORD` | Contraseña nueva y larga (la misma en ambas) |
| `KEYCLOAK_ADMIN_PASSWORD` | Contraseña nueva y larga (la consola de Keycloak es pública) |
| `JWT_SECRET`, `SIMULATOR_API_KEY` | Los valores generados con `openssl` |
| `CORS_ORIGINS` | `https://<dominio>` |
| `COOKIE_SECURE` | `true` |
| `KEYCLOAK_ENABLED`, `VITE_KEYCLOAK_ENABLED` | `true` |
| `VITE_KEYCLOAK_URL`, `KEYCLOAK_URL_PUBLIC` | `https://<dominio>:8443` |
| `KEYCLOAK_REDIRECT_URI` | `https://<dominio>/api/auth/keycloak/callback` |
| `KEYCLOAK_FRONTEND_URL` | `https://<dominio>/` |
| `LOCAL_PASSWORD_LOGIN_ENABLED` | `false` |

Las contraseñas del servidor no deben coincidir con las de los equipos de desarrollo ni compartirse por chat.

## 7. Iniciar LabSentinel

```bash
docker compose -f compose.yaml -f compose.prod.yaml up -d --build
docker compose -f compose.yaml -f compose.prod.yaml ps
```

El primer arranque construye las imágenes y puede tardar varios minutos. Si `keycloak-client-config` termina con error porque Keycloak aún no estaba listo, ejecutar el mismo `up -d` otra vez.

Para no repetir `-f compose.yaml -f compose.prod.yaml` en cada comando:

```bash
echo 'COMPOSE_FILE=compose.yaml:compose.prod.yaml' >> .env
```

## 8. Usuarios de Keycloak

1. Abrir `https://<dominio>:8443` e ingresar con `KEYCLOAK_ADMIN` y `KEYCLOAK_ADMIN_PASSWORD`.
2. Cambiar al realm **labsentinel** y crear los usuarios con su rol de realm (`admin` o `lector`), igual que en el [manual técnico](manual-tecnico.md#usuarios-de-keycloak).
3. Abrir `https://<dominio>` y presionar «Ingresar con Keycloak».

## 9. Verificación

| Comprobación | Resultado esperado |
| --- | --- |
| `https://<dominio>` en el navegador | Pantalla de inicio de sesión con candado válido |
| `https://<dominio>/api/auth/health` | `{"status":"ok", ...}` |
| `curl -i https://<dominio>/api/devices/devices` (sin sesión) | `401 Unauthorized` |
| `docker compose ps` | Microservicios en estado `healthy` |
| `docker compose logs --tail 20 simulator-device` | Lecturas enviadas cada 15 s |

## 10. Mantenimiento

| Acción | Comando |
| --- | --- |
| Actualizar a la última versión | `git pull` y `docker compose up -d --build`, luego `docker compose restart gateway` |
| Ver logs | `docker compose logs -f <servicio>` |
| Detener | `docker compose down` (conserva los datos) |
| Renovar el certificado (vence cada 90 días) | `sudo certbot renew` y luego `sudo sh scripts/install-letsencrypt-cert.sh <dominio> && docker compose restart gateway keycloak` |

Para que la renovación sea automática:

```bash
sudo certbot renew --dry-run
echo "0 4 * * 1 root certbot renew --quiet --deploy-hook 'sh $(pwd)/scripts/install-letsencrypt-cert.sh <dominio> && cd $(pwd) && docker compose restart gateway keycloak'" | sudo tee /etc/cron.d/labsentinel-cert
```

## 11. Consideraciones de seguridad

- PostgreSQL y los microservicios no se exponen a Internet; solo los puertos 443 y 8443.
- La consola de administración de Keycloak queda accesible en el puerto 8443: usar una contraseña robusta y no reutilizarla.
- Keycloak se ejecuta en modo `start-dev`, adecuado para la demostración académica. Para producción real se recomienda el modo `start` con su configuración de hostname y caché.
- Al terminar la evaluación, detener o eliminar la VM para no consumir crédito.
