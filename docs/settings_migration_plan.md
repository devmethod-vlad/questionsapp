# Settings migration plan

## Scope split

### Settings layer (env/runtime-derived)
- `app/core/config.py::Settings` (`BaseSettings`) for FastAPI runtime options.
- Legacy runtime classes `Config`, `DevConfig`, `ProdConfig` for compatibility while migration is in progress.
- All env-derived values and runtime wiring stay in `app/core/config.py` at this stage.

### Domain constants (business/static dictionaries)
- Moved to `app/core/constants.py`:
  - `BASE_ROLE`
  - `QUESTION_STATUS`
  - `NULLSPACE`
  - `NULLROLE`
  - `SHOW_ALL_SPACES_ITEM`
  - `DEFAULT_RENDER_STATUSES`
  - `EXT_DICT`

These values are static domain defaults and should not be coupled to env loading logic.

## Later cleanup (out of this step)
- Remove class-based legacy config usage from runtime code after all reads are migrated to settings-layer accessors.
- Delete `Config` / `DevConfig` / `ProdConfig` from `app/core/config.py`.
- Keep a single settings entry point for runtime configuration and separate module(s) for domain constants.
