# Changelog

## 0.2.0 (unreleased)

- Requires Python 3.11 or newer.
- Uses Chatsnack 0.9.2 for generation and Snapclass for the YAML code cache,
  replacing the Plunkylib and datafiles dependencies.
- Sets dependency security floors: AnyIO 4.14.2, idna 3.15,
  python-dotenv 1.2.2, and ruamel.yaml 0.18.10.
- Retains `doom`, `doom.impending`, `doom.chosen`, and `consume`, along with
  existing function signatures and the cached YAML `signatures` format.
  Impending can generate/cache code without executing it; Chosen executes
  existing cached code without generating new code.

### Upgrading from 0.1.x

Use Python 3.11+ and keep `datafiles/cataclysm/code`, or the `code` directory
under the configured `CATACLYSM_BASE_DIR`. The existing YAML cache format does
not need conversion. Matching cached code is reused before fresh generation.

Choose how to handle configuration before running `cataclysm init`:

1. **Keep the legacy configuration for now.** Leave
   `CataclysmQuery.yml` absent from `CHATSNACK_BASE_DIR` (default:
   `./datafiles/chatsnack`). Keep the existing Plunkylib petition, params,
   prompt files, and `PLUNKYLIB_BASE_DIR` setting. The fallback uses the prompt
   and params selected by the petition, maps `engine` to `model`, and defaults
   to Chat Completions with tools disabled. Avoid rerunning init until choosing
   to migrate.
2. **Migrate custom settings to Chatsnack.** Run `cataclysm init` to create the
   primary file, then edit it before generating new code. Copy the `messages`
   from the prompt selected by the old petition and map the old `engine` value
   to `params.model`. For the closest plain-text behavior, set
   `params.runtime: chat_completions` and `params.tool_choice: none`; retain
   completion options supported by the chosen model. Keep `{arg1}` interpolation
   and require the generated executable body to assign `_exec_return_values`.
   Alternatively, deliberately adopt the packaged Responses/tool setup and
   choose model/options for that runtime.

**The primary Chatsnack file takes precedence over all legacy configuration.**
Init adds it even when old Plunkylib files exist. The old files stay on disk,
but changing them no longer controls generation once the primary file exists.
Init preserves an existing primary file. Explicit process environment settings
take precedence over working-directory `.env` settings.

Legacy configuration loading does not guarantee identical provider requests:
Chatsnack translates legacy `max_tokens` to `max_completion_tokens` at the SDK
boundary. Model availability, account access, and acceptance of the resulting
request still need a live check.

### Verification

Windows AMD64 Python 3.11, 3.12, and 3.13 passed offline regression and installed
package checks. Mocked SDK round trips cover the packaged Responses/tool flow
and legacy Chat Completions text flow. Live provider acceptance and live
notebook execution remain unverified. Linux/macOS, Python 3.14+, and every
allowed dependency-version combination have not been tested.
