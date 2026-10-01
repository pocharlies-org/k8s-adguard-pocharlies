# ARCHITECTURE.md — k8s-adguard-pocharlies

> Repositorio de manifiestos (sin código de aplicación): AdGuard Home como DNS de la LAN con *rewrites*
> `*.lan.e-dani.com` → `192.168.50.240` (traefik-lan). Escrito por `architect` (SC-1426, hija de SC-1421).

## 1. Clientes y versiones

Un solo «cliente»: los equipos de la LAN/tailnet que usan `adguard-dns` (UDP/TCP 53) y la UI web.

| cliente | repositorio / ruta | versión desplegada | cómo se despliega |
|---|---|---|---|
| DNS + UI AdGuard Home | este repo, `k8s/adguard.yaml` | imagen `adguard/adguardhome:v0.107.76` (fijada por tag en el manifiesto) | ArgoCD app `adguard` |

## 2. Dependencias, en ambos sentidos

- **Depende de** — nodo `ubuntu` (el Deployment lleva `nodeSelector kubernetes.io/hostname: ubuntu` y monta
  `hostPath /var/lib/adguard/{conf,work}`); metallb (IP LAN del Service `adguard-dns`, `192.168.50.241`);
  `traefik-lan` (destino de los rewrites, `192.168.50.240`, repo `k8s-infra-pocharlies`).
- **Dependen de él** — todo cliente de la LAN resuelve `*.lan.e-dani.com` y los hosts canónicos (lista en
  `tests/test_canonical_rewrites.py`) a través de él; cada IngressRoute nueva con host `*.e-dani.com` interno
  exige añadir el rewrite aquí. **Application ArgoCD `adguard`**: repo `pocharlies-org/k8s-adguard-pocharlies`,
  path `k8s`, tronco **`main`**, sync automático (`prune: false`, `selfHeal: true`, `ServerSideApply`),
  namespace `adguard`. Se registra en `k8s-gitops-pocharlies` (`deploy/prod`, app-of-apps `root`).
- No tiene `CONTRACTS.yaml`; la lista de hosts canónicos de los tests actúa de contrato de facto.

## 3. Stack

| pieza | versión | para qué | no se usa en su lugar |
|---|---|---|---|
| AdGuard Home | v0.107.76 | DNS con rewrites y filtros | CoreDNS/dnsmasq a mano |
| Kustomize (directorio `k8s/`, YAML plano) | — | un único `adguard.yaml` (Namespace, PVC, ConfigMap seed, Deployment, Services) | Helm: no hay valores que parametrizar |
| pytest + PyYAML | pytest 9 (local) | test del manifiesto | — |

El initContainer `config-seed` (busybox) siembra `AdGuardHome.yaml` desde el ConfigMap `adguard-seed-config`.

## 4. Componentes compartidos

| concepto | pieza canónica | ruta | quién la usa |
|---|---|---|---|
| Rewrites DNS de la LAN | ConfigMap `adguard-seed-config` | `k8s/adguard.yaml` | toda la LAN |
| Lista de hosts canónicos | `CANONICAL_HOSTS` | `tests/test_canonical_rewrites.py` | CI de este repo |
| CI estándar | `reusable-ci.yml@main` | `pocharlies-org/k8s-gitops-pocharlies/.github/workflows/` | `ci.yml` |

## 5. Cómo se construye aquí

Todo en un solo manifiesto (`k8s/adguard.yaml`). Un host nuevo = una línea de rewrite en el ConfigMap + su
entrada en `CANONICAL_HOSTS` en el mismo PR. Sin imágenes propias.

## 6. Tests y validaciones

```sh
python -m pytest tests/test_canonical_rewrites.py   # el manifiesto contiene todos los hosts canónicos
kustomize build k8s >/dev/null                      # lo que hace el reusable-ci (kustomize_paths: ". k8s")
```

Nº de tests: **pendiente de medir** (un fichero de test).

## 7. CI/CD y despliegue

- `ci.yml` → `reusable-ci.yml@main` (runner `arc-k8s`, `run_node/run_docker_build: false`, kustomize `. k8s`).
- `pr-review.yml` (revisión de PR de la org), `release.yml` (Release Production, `workflow_dispatch`/tags),
  `update-versions.yml` (lunes 07:00 UTC, `arc-k8s`: vigila versión de AdGuard Home).
- Despliegue: merge a `main` → ArgoCD `adguard` sincroniza solo. **Validación en producción** (Synced ≠
  funcionando): `dig @192.168.50.241 argocd.e-dani.com` debe devolver `192.168.50.240` y la UI responder en
  `adguard.e-dani.com`. Pendiente de verificar desde aquí (sin kubectl).

## 8. Decisiones y trampas

- El README dice «k3s v1.32.5» y ArgoCD en `k8s-gitops-pocharlies`: el cluster real es k3s v1.36 — README
  desactualizado (pendiente de corregir).
- `hostPath` + `nodeSelector ubuntu`: el DNS no se reprograma en otro nodo; si `ubuntu` cae, cae el DNS LAN.
- `prune: false`: borrar un recurso del manifiesto no lo borra del cluster.

Última verificación contra el código: 2026-10-01 · c3cbe0d (clon local; Application medida en `apps-argocd.json`, sync `3f702c1e`)
