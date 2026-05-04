# Power BI Setup — AAP Pulse

Connects Power BI Desktop directly to the AAP REST API using Basic auth.
No Ansible playbook or intermediate file needed.

## Prerequisites

- Power BI Desktop installed (Windows)
- AAP instance reachable from that machine
- AAP account with at least **Read** on the target inventory
- At least one job template with **Use Fact Cache** enabled that has run against target hosts

## Step 1 — Verify API access

Run this from a terminal before touching Power BI. Substitute your values.

```
curl -u <username>:<password> \
  https://<aap-hostname>/api/controller/v2/hosts/?inventory=<id>&page_size=1
```

You should get a JSON response with `count` and `results`. If you get a 401, check credentials. If you get a certificate error, ensure your AAP cert is trusted or import the CA.

## Step 2 — Create parameters in Power BI Desktop

1. Open Power BI Desktop → **Home → Transform data → Transform data** (opens Power Query Editor)
2. **Home → Manage Parameters → New Parameter**
3. Create two parameters:

| Name | Type | Current Value |
|---|---|---|
| `AAP_URL` | Text | `https://your-aap-hostname` (no trailing slash) |
| `Inventory_ID` | Whole Number | The inventory ID from the AAP URL |

## Step 3 — Load the functions

For each of `fn_GetHosts.m` and `fn_GetHostFacts.m`:

1. In Power Query Editor: **Home → New Source → Blank Query**
2. **Home → Advanced Editor**
3. Replace all content with the contents of the `.m` file
4. Rename the query to match the filename without extension (`fn_GetHosts`, `fn_GetHostFacts`)
5. Click **Done**

Power Query will show the query as a function (a small `fx` icon).

## Step 4 — Load the main query

1. **Home → New Source → Blank Query**
2. **Home → Advanced Editor**
3. Replace all content with the contents of `AAP_HostFacts.m`
4. Rename the query to `AAP_HostFacts`
5. Click **Done** then **Close & Apply**

## Step 5 — Set credentials

When Power BI prompts for credentials for your AAP hostname:

- Authentication kind: **Basic**
- Username / Password: your AAP account credentials

To update credentials later: **File → Options → Data source settings**

## Step 6 — Validate

The `AAP_HostFacts` table should contain one row per host with these columns:

| Column | Source |
|---|---|
| `id` | AAP host ID |
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

Hosts with no cached facts will appear in the table with null values for all fact columns.

## Adding more fact fields

To expose additional ansible facts, edit `AAP_HostFacts.m` in Advanced Editor and add the field names to both lists in the `Table.ExpandRecordColumn` call. The field names match the ansible fact variable names exactly (e.g. `ansible_bios_version`, `ansible_selinux`).

## Scheduled refresh (Power BI Service)

Publishing to Power BI Service requires an **on-premises data gateway** if your AAP instance is not publicly reachable. Configure the gateway data source with the same Basic auth credentials used in Desktop.
