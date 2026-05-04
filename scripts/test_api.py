#!/usr/bin/env python3
"""
Validates the AAP API calls that back the Power BI queries.
Mirrors the logic in powerbi/fn_GetHosts.m and powerbi/fn_GetHostFacts.m.

Usage:
    export CONTROLLER_HOST=https://aap.example.com
    export CONTROLLER_USERNAME=admin
    export CONTROLLER_PASSWORD=secret
    python3 scripts/test_api.py --inventory 1

Or pass values directly:
    python3 scripts/test_api.py --url https://aap.example.com \
        --username admin --password secret --inventory 1
"""

import json
import os
import sys
import argparse
import requests
from requests.auth import HTTPBasicAuth


def get_hosts(base_url, inventory_id, auth, verify):
    hosts = []
    url = f"{base_url}/api/controller/v2/hosts/?inventory={inventory_id}&page_size=200"
    while url:
        resp = requests.get(url, auth=auth, verify=verify)
        resp.raise_for_status()
        data = resp.json()
        hosts.extend(data["results"])
        url = data.get("next")
    return hosts


def get_host_facts(base_url, host_id, auth, verify):
    url = f"{base_url}/api/controller/v2/hosts/{host_id}/ansible_facts/"
    resp = requests.get(url, auth=auth, verify=verify)
    resp.raise_for_status()
    return resp.json()


def flatten(host, facts):
    mem_mb       = facts.get("ansible_memtotal_mb")
    mem_free_mb  = facts.get("ansible_memfree_mb")
    uptime_s     = facts.get("ansible_uptime_seconds")
    pf_total_mb  = facts.get("ansible_pagefiletotal_mb")
    pf_free_mb   = facts.get("ansible_pagefilefree_mb")
    date_time    = facts.get("ansible_date_time") or {}

    # IPv4 only — skip any address containing ":"
    ip_addresses = facts.get("ansible_ip_addresses") or []
    ipv4_only    = [ip for ip in ip_addresses if ":" not in ip]

    # ansible_processor is a flat list: [index, vendor, name, index, vendor, name, ...]
    proc_list    = facts.get("ansible_processor") or []
    proc_names   = list(dict.fromkeys(proc_list[i] for i in range(2, len(proc_list), 3)))

    return {
        # Identity
        "id":                    host["id"],
        "name":                  host["name"],
        "inventory":             host.get("summary_fields", {}).get("inventory", {}).get("name"),
        # OS
        "OS":                    facts.get("ansible_distribution"),
        "OS_Name":               facts.get("ansible_os_name"),
        "OS_Family":             facts.get("ansible_os_family"),
        "OS_Version":            facts.get("ansible_distribution_version"),
        "OS_Major_Version":      facts.get("ansible_distribution_major_version"),
        "OS_Install_Type":       facts.get("ansible_os_installation_type"),
        "OS_Product_Type":       facts.get("ansible_os_product_type"),
        "OS_Install_Date":       facts.get("ansible_os_install_date"),
        # System
        "System":                facts.get("ansible_system"),
        "System_Description":    facts.get("ansible_system_description"),
        "System_Vendor":         facts.get("ansible_system_vendor"),
        "Product_Name":          facts.get("ansible_product_name"),
        "Product_Serial":        facts.get("ansible_product_serial"),
        "Product_UUID":          facts.get("ansible_product_uuid"),
        "Machine_ID":            facts.get("ansible_machine_id"),
        "BIOS_Version":          facts.get("ansible_bios_version"),
        "BIOS_Date":             facts.get("ansible_bios_date"),
        "Virt_Type":             facts.get("ansible_virtualization_type"),
        "Virt_Role":             facts.get("ansible_virtualization_role"),
        # Network
        "FQDN":                  facts.get("ansible_fqdn"),
        "Hostname":              facts.get("ansible_hostname"),
        "NetBIOS_Name":          facts.get("ansible_netbios_name"),
        "Node_Name":             facts.get("ansible_nodename"),
        "Domain":                facts.get("ansible_domain"),
        "Windows_Domain":        facts.get("ansible_windows_domain"),
        "Domain_Member":         facts.get("ansible_windows_domain_member"),
        "Domain_Role":           facts.get("ansible_windows_domain_role"),
        "IP_Addresses":          ", ".join(ipv4_only),
        # CPU
        "Architecture":          facts.get("ansible_architecture"),
        "Architecture2":         facts.get("ansible_architecture2"),
        "vCPUs":                 facts.get("ansible_processor_vcpus"),
        "Processor_Cores":       facts.get("ansible_processor_cores"),
        "Processor_Count":       facts.get("ansible_processor_count"),
        "Threads_Per_Core":      facts.get("ansible_processor_threads_per_core"),
        "Processor_Name":        proc_names[0] if proc_names else None,
        # Memory
        "Memory_MB":             mem_mb,
        "Memory_GB":             round(mem_mb / 1024, 1) if mem_mb else None,
        "Memory_Free_MB":        mem_free_mb,
        "Memory_Free_GB":        round(mem_free_mb / 1024, 1) if mem_free_mb else None,
        "Swap_Total_MB":         facts.get("ansible_swaptotal_mb"),
        "Pagefile_Total_MB":     pf_total_mb,
        "Pagefile_Free_MB":      pf_free_mb,
        "Pagefile_Total_GB":     round(pf_total_mb / 1024, 1) if pf_total_mb else None,
        # Time
        "Last_Boot":             facts.get("ansible_lastboot"),
        "Facts_Collected_UTC":   date_time.get("iso8601"),
        "Uptime_Seconds":        uptime_s,
        "Uptime_Days":           round(uptime_s / 86400, 1) if uptime_s else None,
        "Reboot_Pending":        facts.get("ansible_reboot_pending"),
        # User
        "User_ID":               facts.get("ansible_user_id"),
        "User_Dir":              facts.get("ansible_user_dir"),
        "User_SID":              facts.get("ansible_user_sid"),
        "User_GECOS":            facts.get("ansible_user_gecos"),
        # Windows-specific
        "PowerShell_Version":    facts.get("ansible_powershell_version"),
        "WinRM_Cert_Expires":    facts.get("ansible_win_rm_certificate_expires"),
        "WinRM_Cert_Thumbprint": facts.get("ansible_win_rm_certificate_thumbprint"),
        "Owner_Name":            facts.get("ansible_owner_name"),
        "Owner_Contact":         facts.get("ansible_owner_contact"),
    }


def print_table(rows):
    if not rows:
        print("No rows returned.")
        return
    try:
        from tabulate import tabulate
        print(tabulate(rows, headers="keys", tablefmt="simple"))
    except ImportError:
        keys = list(rows[0].keys())
        widths = {k: max(len(k), max(len(str(r.get(k) or "")) for r in rows)) for k in keys}
        sep = "  "
        print(sep.join(k.ljust(widths[k]) for k in keys))
        print(sep.join("-" * widths[k] for k in keys))
        for row in rows:
            print(sep.join(str(row.get(k) or "").ljust(widths[k]) for k in keys))


def main():
    parser = argparse.ArgumentParser(
        description="Test AAP API connectivity and validate Power BI data model."
    )
    parser.add_argument("--url",      default=os.environ.get("CONTROLLER_HOST"),
                        help="AAP base URL  (or set CONTROLLER_HOST)")
    parser.add_argument("--username", default=os.environ.get("CONTROLLER_USERNAME"),
                        help="AAP username  (or set CONTROLLER_USERNAME)")
    parser.add_argument("--password", default=os.environ.get("CONTROLLER_PASSWORD"),
                        help="AAP password  (or set CONTROLLER_PASSWORD)")
    parser.add_argument("--inventory", type=int, required=True,
                        help="Inventory ID to query (visible in the AAP URL)")
    parser.add_argument("--no-verify-certs", action="store_true",
                        help="Disable TLS certificate verification")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="Dump raw JSON instead of a table")
    args = parser.parse_args()

    missing = [label for label, val in [
        ("--url / CONTROLLER_HOST",          args.url),
        ("--username / CONTROLLER_USERNAME", args.username),
        ("--password / CONTROLLER_PASSWORD", args.password),
    ] if not val]
    if missing:
        print(f"error: missing required values: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    auth   = HTTPBasicAuth(args.username, args.password)
    verify = not args.no_verify_certs

    print(f"Fetching hosts for inventory {args.inventory} ...", file=sys.stderr)
    hosts = get_hosts(args.url, args.inventory, auth, verify)
    print(f"Found {len(hosts)} host(s). Fetching facts ...", file=sys.stderr)

    rows = []
    for host in hosts:
        facts = get_host_facts(args.url, host["id"], auth, verify)
        if not facts:
            print(f"  {host['name']}: no facts cached (skipped)", file=sys.stderr)
            continue
        rows.append(flatten(host, facts))

    print(f"Done — {len(rows)} host(s) with facts.\n", file=sys.stderr)

    if args.as_json:
        print(json.dumps(rows, indent=2))
    else:
        print_table(rows)


if __name__ == "__main__":
    main()
