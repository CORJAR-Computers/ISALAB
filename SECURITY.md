# Política de Seguridad — IsaLab

## Reporte de vulnerabilidades

Si descubres una vulnerabilidad de seguridad en IsaLab, **NO la reportes
públicamente** como un issue de GitHub. En su lugar, escribe a
**dev@corjar.com** con:

1. Descripción del problema y impacto potencial.
2. Pasos para reproducirlo (PoC si es posible).
3. Versión afectada y sistema operativo.

Te responderemos en un máximo de 72 horas hábiles.

## Alcance

Esta política aplica al código del repositorio
[CORJAR-Computers/ISALAB](https://github.com/CORJAR-Computers/ISALAB) en su
rama `main`. No aplica a forks ni a despliegues personalizados.

## Estado actual de seguridad

IsaLab está en fase de endurecimiento. Las siguientes áreas tienen issues
conocidos documentados (ver roadmap interno):

- **RBAC:** actualmente solo `UsuarioService` valida roles. Los demás
  servicios exponen CRUD sin autenticación de rol (issue CRITICAL C1 de
  servicios, pendiente en Fase 3).
- **Generación de PDFs:** algunos caminos no activan Jinja2 autoescape
  (issue CRITICAL C3 de servicios, pendiente en Fase 3).
- **Manejo de secretos:** el archivo `data/lab_config.json` se escribe en
  texto plano sin hardening de permisos (issue MEDIUM, pendiente en Fase 5).

## Prácticas recomendadas para desarrolladores

- **NUNCA** commitear `data/isalab.db`, `logs/*.log`, `data/pdfs/*.pdf`
  ni archivos `.env`. El `.gitignore` los excluye, pero verificable con
  `git ls-files | grep -E '(\\.db|\\.log|\\.env|pdfs/)'`.
- **NUNCA** imprimir hashes de contraseñas, tokens ni PII en logs. El
  logger debe redactar (pendiente: Fase 5).
- Usar `bcrypt` para cualquier almacenamiento de contraseñas. No inventar
  esquemas de hashing propios.
- Validar toda entrada del usuario con `utils/validators.py` antes de
  pasarla a servicios.
- En reportes PDF, SIEMPRE usar `reports/base.py` (que activa autoescape).
  No instanciar `jinja2.Environment` directamente.
