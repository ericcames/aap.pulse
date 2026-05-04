// AAP_HostFacts — main query
// Combines fn_GetHosts and fn_GetHostFacts into a flat table ready for reporting.
// Requires parameters AAP_URL (text) and Inventory_ID (number) to exist in the model.
let
    Hosts = fn_GetHosts(AAP_URL, Inventory_ID),

    // One API call per host — try/otherwise null guards against hosts with no cached facts
    WithFacts = Table.AddColumn(Hosts, "facts",
                    each try fn_GetHostFacts(AAP_URL, [id]) otherwise null,
                    type record),

    // Expand all scalar fact fields; nested fields (lists/records) extracted below
    Expanded = Table.ExpandRecordColumn(WithFacts, "facts", {
                   "ansible_distribution",
                   "ansible_os_name",
                   "ansible_os_family",
                   "ansible_distribution_version",
                   "ansible_distribution_major_version",
                   "ansible_os_installation_type",
                   "ansible_os_product_type",
                   "ansible_os_install_date",
                   "ansible_system",
                   "ansible_system_description",
                   "ansible_system_vendor",
                   "ansible_product_name",
                   "ansible_product_serial",
                   "ansible_product_uuid",
                   "ansible_machine_id",
                   "ansible_bios_version",
                   "ansible_bios_date",
                   "ansible_virtualization_type",
                   "ansible_virtualization_role",
                   "ansible_fqdn",
                   "ansible_hostname",
                   "ansible_netbios_name",
                   "ansible_nodename",
                   "ansible_domain",
                   "ansible_windows_domain",
                   "ansible_windows_domain_member",
                   "ansible_windows_domain_role",
                   "ansible_ip_addresses",
                   "ansible_architecture",
                   "ansible_architecture2",
                   "ansible_processor_vcpus",
                   "ansible_processor_cores",
                   "ansible_processor_count",
                   "ansible_processor_threads_per_core",
                   "ansible_processor",
                   "ansible_memtotal_mb",
                   "ansible_memfree_mb",
                   "ansible_swaptotal_mb",
                   "ansible_pagefiletotal_mb",
                   "ansible_pagefilefree_mb",
                   "ansible_lastboot",
                   "ansible_date_time",
                   "ansible_uptime_seconds",
                   "ansible_reboot_pending",
                   "ansible_user_id",
                   "ansible_user_dir",
                   "ansible_user_sid",
                   "ansible_user_gecos",
                   "ansible_powershell_version",
                   "ansible_win_rm_certificate_expires",
                   "ansible_win_rm_certificate_thumbprint",
                   "ansible_owner_name",
                   "ansible_owner_contact"
               }, {
                   "OS",
                   "OS_Name",
                   "OS_Family",
                   "OS_Version",
                   "OS_Major_Version",
                   "OS_Install_Type",
                   "OS_Product_Type",
                   "OS_Install_Date",
                   "System",
                   "System_Description",
                   "System_Vendor",
                   "Product_Name",
                   "Product_Serial",
                   "Product_UUID",
                   "Machine_ID",
                   "BIOS_Version",
                   "BIOS_Date",
                   "Virt_Type",
                   "Virt_Role",
                   "FQDN",
                   "Hostname",
                   "NetBIOS_Name",
                   "Node_Name",
                   "Domain",
                   "Windows_Domain",
                   "Domain_Member",
                   "Domain_Role",
                   "_ip_addresses_list",
                   "Architecture",
                   "Architecture2",
                   "vCPUs",
                   "Processor_Cores",
                   "Processor_Count",
                   "Threads_Per_Core",
                   "_processor_list",
                   "Memory_MB",
                   "Memory_Free_MB",
                   "Swap_Total_MB",
                   "Pagefile_Total_MB",
                   "Pagefile_Free_MB",
                   "Last_Boot",
                   "_date_time",
                   "Uptime_Seconds",
                   "Reboot_Pending",
                   "User_ID",
                   "User_Dir",
                   "User_SID",
                   "User_GECOS",
                   "PowerShell_Version",
                   "WinRM_Cert_Expires",
                   "WinRM_Cert_Thumbprint",
                   "Owner_Name",
                   "Owner_Contact"
               }),

    // Memory in GB
    WithMemGB = Table.AddColumn(Expanded, "Memory_GB",
                    each if [Memory_MB] is number
                         then Number.Round([Memory_MB] / 1024, 1) else null),

    WithMemFreeGB = Table.AddColumn(WithMemGB, "Memory_Free_GB",
                        each if [Memory_Free_MB] is number
                             then Number.Round([Memory_Free_MB] / 1024, 1) else null),

    // Pagefile in GB
    WithPfGB = Table.AddColumn(WithMemFreeGB, "Pagefile_Total_GB",
                   each if [Pagefile_Total_MB] is number
                        then Number.Round([Pagefile_Total_MB] / 1024, 1) else null),

    // Uptime in days
    WithUptimeDays = Table.AddColumn(WithPfGB, "Uptime_Days",
                         each if [Uptime_Seconds] is number
                              then Number.Round([Uptime_Seconds] / 86400, 1) else null),

    // ISO8601 timestamp from the ansible_date_time record
    WithFactsTime = Table.AddColumn(WithUptimeDays, "Facts_Collected_UTC",
                        each if [_date_time] is record
                             then Record.FieldOrDefault([_date_time], "iso8601", null)
                             else null),

    // IPv4 only from ansible_ip_addresses list (exclude anything with ":")
    WithIPs = Table.AddColumn(WithFactsTime, "IP_Addresses",
                  each if [_ip_addresses_list] is list
                       then Text.Combine(
                           List.Select([_ip_addresses_list], each not Text.Contains(_, ":")),
                           ", ")
                       else null),

    // Processor name — ansible_processor is [index, vendor, name, index, vendor, name, ...]
    WithCPU = Table.AddColumn(WithIPs, "Processor_Name",
                  each if [_processor_list] is list and List.Count([_processor_list]) >= 3
                       then List.Distinct(
                           List.Transform(
                               {0 .. Number.IntegerDivide(List.Count([_processor_list]) - 1, 3)},
                               each [_processor_list]{_ * 3 + 2}
                           )
                       ){0}
                       else null),

    Final = Table.RemoveColumns(WithCPU, {"_ip_addresses_list", "_processor_list", "_date_time"})
in
    Final
