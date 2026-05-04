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

60 columns, one row per host. Hosts with no cached facts appear with null values for all fact columns.

**Identity**

| Column | Source |
|---|---|
| `id` | AAP host ID |
| `name` | Hostname as registered in AAP |
| `inventory` | Inventory name |

**OS**

| Column | Ansible Fact |
|---|---|
| `OS` | `ansible_distribution` |
| `OS_Name` | `ansible_os_name` |
| `OS_Family` | `ansible_os_family` |
| `OS_Version` | `ansible_distribution_version` |
| `OS_Major_Version` | `ansible_distribution_major_version` |
| `OS_Install_Type` | `ansible_os_installation_type` |
| `OS_Product_Type` | `ansible_os_product_type` |
| `OS_Install_Date` | `ansible_os_install_date` |

**System**

| Column | Ansible Fact |
|---|---|
| `System` | `ansible_system` |
| `System_Description` | `ansible_system_description` |
| `System_Vendor` | `ansible_system_vendor` |
| `Product_Name` | `ansible_product_name` |
| `Product_Serial` | `ansible_product_serial` |
| `Product_UUID` | `ansible_product_uuid` |
| `Machine_ID` | `ansible_machine_id` |
| `BIOS_Version` | `ansible_bios_version` |
| `BIOS_Date` | `ansible_bios_date` |
| `Virt_Type` | `ansible_virtualization_type` |
| `Virt_Role` | `ansible_virtualization_role` |

**Network**

| Column | Ansible Fact |
|---|---|
| `FQDN` | `ansible_fqdn` |
| `Hostname` | `ansible_hostname` |
| `NetBIOS_Name` | `ansible_netbios_name` |
| `Node_Name` | `ansible_nodename` |
| `Domain` | `ansible_domain` |
| `Windows_Domain` | `ansible_windows_domain` |
| `Domain_Member` | `ansible_windows_domain_member` |
| `Domain_Role` | `ansible_windows_domain_role` |
| `IP_Addresses` | `ansible_ip_addresses` (IPv4 only, comma-separated) |

**CPU**

| Column | Ansible Fact |
|---|---|
| `Architecture` | `ansible_architecture` |
| `Architecture2` | `ansible_architecture2` |
| `vCPUs` | `ansible_processor_vcpus` |
| `Processor_Cores` | `ansible_processor_cores` |
| `Processor_Count` | `ansible_processor_count` |
| `Threads_Per_Core` | `ansible_processor_threads_per_core` |
| `Processor_Name` | `ansible_processor` (first unique CPU name extracted) |

**Memory**

| Column | Ansible Fact |
|---|---|
| `Memory_MB` | `ansible_memtotal_mb` |
| `Memory_GB` | Derived from `ansible_memtotal_mb` |
| `Memory_Free_MB` | `ansible_memfree_mb` |
| `Memory_Free_GB` | Derived from `ansible_memfree_mb` |
| `Swap_Total_MB` | `ansible_swaptotal_mb` |
| `Pagefile_Total_MB` | `ansible_pagefiletotal_mb` |
| `Pagefile_Free_MB` | `ansible_pagefilefree_mb` |
| `Pagefile_Total_GB` | Derived from `ansible_pagefiletotal_mb` |

**Time**

| Column | Ansible Fact |
|---|---|
| `Last_Boot` | `ansible_lastboot` |
| `Facts_Collected_UTC` | `ansible_date_time.iso8601` |
| `Uptime_Seconds` | `ansible_uptime_seconds` |
| `Uptime_Days` | Derived from `ansible_uptime_seconds` |
| `Reboot_Pending` | `ansible_reboot_pending` |

**User**

| Column | Ansible Fact |
|---|---|
| `User_ID` | `ansible_user_id` |
| `User_Dir` | `ansible_user_dir` |
| `User_SID` | `ansible_user_sid` |
| `User_GECOS` | `ansible_user_gecos` |

**Windows**

| Column | Ansible Fact |
|---|---|
| `PowerShell_Version` | `ansible_powershell_version` |
| `WinRM_Cert_Expires` | `ansible_win_rm_certificate_expires` |
| `WinRM_Cert_Thumbprint` | `ansible_win_rm_certificate_thumbprint` |
| `Owner_Name` | `ansible_owner_name` |
| `Owner_Contact` | `ansible_owner_contact` |

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
