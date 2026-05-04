# aap.pulse

Ansible playbooks and Power BI queries for surfacing Ansible Automation Platform data — host facts, job history, and inventory metrics — into external reporting tools.

## Architecture

### Option A — Playbook to JSON file

```
AAP fact cache → get_host_facts.yml → output/facts-<host>.json
```

Good for one-off CLI use or feeding a file-based data source.

### Option B — Power BI direct to AAP API (primary approach)

```
Power BI Desktop
  └── AAP_URL + Inventory_ID parameters
        └── fn_GetHosts  → GET /api/controller/v2/hosts/?inventory=<id>
              └── fn_GetHostFacts  → GET /api/controller/v2/hosts/<id>/ansible_facts/
                    └── AAP_HostFacts table (one row per host, fact columns expanded)
```

Power BI authenticates to the AAP REST API using Basic auth — no intermediate file or token management needed. The `AAP_HostFacts` query returns a flat table with OS, kernel, memory, IP, uptime, and architecture per host.

## Playbooks

| Playbook | Purpose |
|---|---|
| `playbooks/get_host_facts.yml` | Retrieve cached ansible facts for a specific host from AAP and write them to a JSON file |

### Requirements

- Ansible Automation Platform 2.4+
- Collection: `ansible.platform`
- Environment variables: `CONTROLLER_HOST`, `CONTROLLER_USERNAME`, `CONTROLLER_PASSWORD`

### Usage

```bash
export CONTROLLER_HOST=https://<your-aap-url>
export CONTROLLER_USERNAME=admin
export CONTROLLER_PASSWORD=<password>

ansible-playbook -i inventories/sample/ playbooks/get_host_facts.yml \
  --extra-vars target_host=<hostname>
```

Facts are written to `output/facts-<hostname>.json`.

## Power BI

Power Query M source files are in `powerbi/`. See [`powerbi/setup.md`](powerbi/setup.md) for step-by-step setup instructions.

| File | Purpose |
|---|---|
| `fn_GetHosts.m` | Paginated host list for a given inventory |
| `fn_GetHostFacts.m` | Fact cache fetch for a single host ID |
| `AAP_HostFacts.m` | Main query — joins functions into a flat reporting table |
| `setup.md` | Power BI Desktop setup and credential instructions |

### Prerequisites for testing

| Requirement | Notes |
|---|---|
| Power BI Desktop | Free, Windows only |
| AAP instance reachable from that machine | |
| AAP read-only account | Recommend a dedicated service account |
| Fact cache populated | At least one job with **Use Fact Cache** enabled must have run against target hosts |
| Inventory ID | Integer ID visible in the AAP URL when browsing an inventory |

### Columns returned

| Column | Ansible Fact |
|---|---|
| `name` | Hostname as registered in AAP |
| `inventory_name` | Inventory the host belongs to |
| `OS` / `OS_Version` | `ansible_distribution` / `_version` |
| `Kernel` | `ansible_kernel` |
| `Architecture` | `ansible_architecture` |
| `vCPUs` | `ansible_processor_vcpus` |
| `Memory_MB` / `Memory_GB` | `ansible_memtotal_mb` |
| `FQDN` | `ansible_fqdn` |
| `IP_Address` | `ansible_default_ipv4.address` |
| `Uptime_Seconds` / `Uptime_Days` | `ansible_uptime_seconds` |

## Testing on Linux

`scripts/test_api.py` mirrors the Power Query M logic and runs on Fedora without Power BI Desktop.

```bash
# Install dependency (if needed)
pip install requests          # or: sudo dnf install python3-requests

# Run with env vars
export CONTROLLER_HOST=https://aap.example.com
export CONTROLLER_USERNAME=admin
export CONTROLLER_PASSWORD=secret

python3 scripts/test_api.py --inventory 1

# Or pass everything inline
python3 scripts/test_api.py \
  --url https://aap.example.com \
  --username admin --password secret \
  --inventory 1

# Output raw JSON instead of a table
python3 scripts/test_api.py --inventory 1 --json

# Self-signed cert
python3 scripts/test_api.py --inventory 1 --no-verify-certs
```

Install `tabulate` for a cleaner table output (`pip install tabulate`), otherwise the script falls back to plain-text alignment.

## License

MIT — see [LICENSE](LICENSE).
