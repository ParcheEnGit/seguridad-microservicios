<#
.SYNOPSIS
Instala la CA local generada por Docker en el almacén de confianza del usuario
actual. No requiere privilegios de administrador.

.DESCRIPTION
Ejecutar después de `docker compose up -d`. Permite que Chrome, Edge y otros
navegadores de Windows confíen en https://localhost:8080 y :8081 sin advertencia.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$certificatePath = Join-Path $env:TEMP "labsentinel-local-ca.crt"
docker compose run --rm --no-deps --entrypoint /bin/sh tls-init -c "cat /certs/labsentinel-local-ca.crt" |
    Set-Content -Path $certificatePath -Encoding ascii -NoNewline
Import-Certificate -FilePath $certificatePath -CertStoreLocation "Cert:\CurrentUser\Root" | Out-Null
Remove-Item -LiteralPath $certificatePath -Force
Write-Host "La CA local de LabSentinel fue confiada para el usuario actual." -ForegroundColor Green
