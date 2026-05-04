# Changelog

## [Unreleased]

### Added
- `playbooks/get_host_facts.yml` — retrieve and report ansible facts for a host from the AAP fact cache; uses `ansible.platform.token` for auth and writes full facts to `output/` as JSON
- `powerbi/fn_GetHosts.m` — Power Query M function; paginated host list from AAP inventory via REST API
- `powerbi/fn_GetHostFacts.m` — Power Query M function; fetches ansible fact cache for a single host ID
- `powerbi/AAP_HostFacts.m` — main Power Query; joins host list and per-host facts into a flat reporting table (OS, kernel, memory, IP, uptime, architecture)
- `powerbi/setup.md` — step-by-step instructions for loading queries into Power BI Desktop and configuring Basic auth credentials
- `LICENSE` — MIT license

### Changed
- `inventories/sample/group_vars/all.yml` — `aap_validate_certs` default changed to `true`
- `playbooks/get_host_facts.yml` — `controller_validate_certs` default changed to `true`; `target_host` default cleared and added to assert so callers must supply it via `--extra-vars`
- `.gitignore` — added defensive entries for vault password files, `.env`, and secrets files
- `scripts/test_api.py` — Python script that mirrors the Power Query M logic; validates AAP API connectivity and data model on Linux without Power BI Desktop
