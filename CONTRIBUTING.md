# Cómo trabajamos — TaxiTech Solutions / Backend Squad

Este documento fija cómo se coordina el equipo en este proyecto: flujo de
trabajo, ramas, commits, revisión y definición de "hecho" por fase. El
objetivo es que cualquier persona que se incorpore al Backend Squad pueda
ponerse a trabajar sin depender de una explicación oral.

## Tablero y ceremonias

- El trabajo se gestiona en **GitHub Projects**, con una columna por fase
  del roadmap (`Backlog`, `Fase 1`, `Fase 2`, `Fase 3`, `Fase 4`, `Done`)
  más `En revisión` para PRs abiertas.
- Cada historia de usuario del README es una tarjeta, etiquetada con su
  prioridad MoSCoW y su fase.
- **Planning** al inicio de cada fase: se descompone la fase en tareas
  técnicas y se reparten.
- **Daily** corta (async en el canal del equipo si no coincide el horario):
  qué se hizo, qué se hace hoy, qué bloquea.
- **Review/demo** al cerrar cada fase: se enseña el entregable funcionando
  antes de mover las tarjetas a `Done`.

## Ramas y commits

- `main` siempre desplegable. Trabajo en ramas `feature/US-0X-descripcion`
  o `fix/lo-que-sea`.
- Mensajes de commit en [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/)
  (`feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`). Facilita
  generar changelog y que el historial cuente lo que pasó sin abrir cada diff.

## Pull Requests

- Una PR por historia de usuario (o tarea técnica pequeña), nunca varias
  fases mezcladas.
- La plantilla de PR (`.github/PULL_REQUEST_TEMPLATE.md`) exige: qué
  cambia, qué historia cubre, checklist de calidad y cómo probarlo.
- `CODEOWNERS` asigna revisor automático en las zonas sensibles (API, auth, web).
- No se mergea sin: CI en verde (lint + tests) y al menos una aprobación.

## Definición de "hecho" por fase

Una fase no se marca `Done` en el tablero hasta que:

1. El código cumple los requisitos funcionales de esa fase (ver README).
2. Hay tests automatizados cubriendo la lógica nueva.
3. `make lint` y `make test` pasan en CI.
4. Hay una demo grabada o en vivo mostrando el flujo completo.
5. El README refleja el estado real (no lo que se planeaba hacer).

## Entorno de desarrollo

Ver [README.md](README.md#-puesta-en-marcha) para la puesta en marcha
completa (`make install`, `make precommit-install`, `make test`).
