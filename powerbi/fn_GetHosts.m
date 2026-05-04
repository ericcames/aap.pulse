// fn_GetHosts
// Returns a table of all hosts in the given inventory, handling pagination.
// Parameters:
//   AAP_URL      - base URL of your AAP instance, e.g. https://aap.example.com
//   Inventory_ID - integer ID shown in the AAP URL when browsing an inventory
(AAP_URL as text, Inventory_ID as number) as table =>
let
    FirstURL = AAP_URL
        & "/api/controller/v2/hosts/?inventory="
        & Number.ToText(Inventory_ID)
        & "&page_size=200",

    FetchPage = (url as text) as record =>
        Json.Document(
            Web.Contents(url, [Headers = [Accept = "application/json"]])
        ),

    // Walk pages until next is null
    PageResults = List.Generate(
        () => FetchPage(FirstURL),
        each List.Count(_[results]) > 0,
        each if _[next] <> null
             then FetchPage(_[next])
             else [results = {}, next = null],
        each _[results]
    ),

    AllHosts   = List.Combine(PageResults),
    AsTable    = Table.FromList(AllHosts, Splitter.SplitByNothing(), {"Record"}),
    Expanded   = Table.ExpandRecordColumn(AsTable, "Record",
                     {"id", "name", "summary_fields"},
                     {"id", "name", "summary_fields"}),
    WithInv    = Table.AddColumn(Expanded, "inventory_name",
                     each try _[summary_fields][inventory][name] otherwise null),
    Result     = Table.RemoveColumns(WithInv, {"summary_fields"})
in
    Result
