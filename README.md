# GitHub Forest (InsideForest style) 🌲

Este repo genera un **bosque animado** basado en tus contribuciones de GitHub (grid 53×7) y lo actualiza **cada semana** con GitHub Actions.

- **Sprites (árboles)**: `assets/trees/A1.png ... A8.png`
- **Salida**: `dist/forest.gif` y `dist/forest.png`

## Cómo usarlo

1) Crea un repo nuevo en GitHub (o usa tu repo de perfil `USERNAME/USERNAME`).
2) Sube el contenido de este zip.
3) (Opcional recomendado) en **Settings → Secrets and variables → Actions** agrega:
   - `GH_PROFILE_USER` (tu usuario de GitHub, p.ej. `jcval94`)
   - Si el workflow no puede leer contribuciones con `GITHUB_TOKEN`, crea un PAT y guárdalo como:
     - `GH_TOKEN` con scopes: `read:user` (y `repo` solo si el repo es privado)

El workflow corre cada semana y también puedes ejecutarlo manualmente.

## Mostrar el GIF en tu README

```md
![forest](dist/forest.gif)
```

## Ajustes rápidos

- Cambia el mapping de actividad → tamaño en `src/render.py`:
  - `pick_sprite_bucket(count)` decide qué PNG usar.
  - `height_from_count(count)` define qué tan alto se dibuja.

---

Hecho para que sea **determinístico** (sin parpadeos) y con fallback a datos dummy si falla la API.
