# INFRA-825 · P5 · rewrite de AdGuard para paseo.e-dani.com

Dónde: x86 (`ubuntu`), worktree de la rama `infra-825-paseo-rewrite`, Python 3.12, pytest 9.0.3.

## 1. Rojo primero: solo el test cambiado, manifiesto de `main`

`python3 -m pytest -q tests` → FAIL (lo esperado)

```
FAILED tests/test_canonical_rewrites.py::test_seed_contains_every_canonical_host_once_at_the_lan_vip
FAILED tests/test_canonical_rewrites.py::test_init_container_reconciles_the_same_canonical_host_set
FAILED tests/test_canonical_rewrites.py::test_init_container_removes_retired_rewrites_from_persistent_config
3 failed in 0.07s
```

## 2. Verde con el cambio

`python3 -m pytest -q tests` → PASS

```
...                                                                      [100%]
3 passed in 0.06s
```

## 3. Mutación: volver a sembrar `chamber.e-dani.com` en el seed

Con la entrada `chamber.e-dani.com` reinsertada en `adguard-seed-config`, `python3 -m pytest -q tests` → FAIL (lo esperado)

```
FAILED tests/test_canonical_rewrites.py::test_seed_contains_every_canonical_host_once_at_the_lan_vip
1 failed, 2 passed in 0.06s
```

## 4. Restos de OpenChamber

`git grep -n -i chamber -- k8s tests` → solo las órdenes de borrado y la lista de retirados:

```
k8s/adguard.yaml:383:              remove_panel_rewrite "chamber.e-dani.com"
k8s/adguard.yaml:384:              remove_panel_rewrite "multichamber.e-dani.com"
tests/test_canonical_rewrites.py:68:    "chamber.e-dani.com",
tests/test_canonical_rewrites.py:69:    "multichamber.e-dani.com",
```

## Criterios

- C10 PASS: rewrite en `k8s/adguard.yaml:86`, el test lo exige en `tests/test_canonical_rewrites.py:49`.
- C11 PASS: no queda ningún rewrite ni host canónico `chamber*` (sección 4); el test lo impide en `tests/test_canonical_rewrites.py:97`.
- C12 PASS en local (sección 2); el CI de la PR lo confirma.
