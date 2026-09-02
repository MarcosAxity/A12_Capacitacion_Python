# Evidencia de auditoría de dependencias

**Herramienta:** [`pip-audit`](https://pypi.org/project/pip-audit/) 2.7.3 (usa las bases de datos OSV y PyPA Advisory).
**Fecha de ejecución:** 2026-08-26
**Comando:** `pip-audit -r requirements.txt -f json`
**Resultado:** `No known vulnerabilities found` (ver `pip-audit-report.json` para el JSON crudo).

## Historial de esta auditoría (evidencia de proceso, no solo del resultado final)

Durante la primera corrida se detectaron vulnerabilidades conocidas (CVEs) en 3 paquetes
de `requirements.txt`. Se investigó cada una y se corrigió fijando una versión más nueva
que resuelve el CVE, validando después que la suite de pruebas (77 tests) seguía pasando:

| Paquete | Versión insegura | CVEs relevantes | Versión corregida |
|---|---|---|---|
| `pyjwt` | 2.10.1 | CVE-2026-32597 (no valida el header `crit` de RFC 7515), CVE-2026-48526, CVE-2026-... | **2.13.0** |
| `python-multipart` | 0.0.20 | Varias vulnerabilidades de parsing de multipart/form-data | **0.0.31** |
| `starlette` (dependencia transitiva de FastAPI) | 0.41.3 → 0.47.2 → 0.49.1 | Varias, incluida denegación de servicio en parsing de formularios | **1.3.1** (requirió subir `fastapi` a `0.141.1` para mantener compatibilidad de versiones) |

Reproducir la auditoría localmente:

```bash
pip install -r requirements-dev.txt
pip-audit -r requirements.txt
```

## Cómo se integra en el pipeline CI/CD

El job `dependency-audit` del pipeline (`.github/workflows/ci.yml`) ejecuta `pip-audit`
en cada push/PR contra `main`. Si aparece una vulnerabilidad conocida sin corregir, el
build falla, evitando que se despliegue una versión con dependencias inseguras
(shift-left security).
