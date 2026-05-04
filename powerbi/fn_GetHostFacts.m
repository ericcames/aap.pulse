// fn_GetHostFacts
// Fetches the ansible fact cache for a single host from AAP.
// Returns the raw facts record; empty record {} if no facts are cached for the host.
// Parameters:
//   AAP_URL - base URL of your AAP instance, e.g. https://aap.example.com
//   host_id - integer host ID (from fn_GetHosts)
(AAP_URL as text, host_id as number) as record =>
let
    URL      = AAP_URL
                 & "/api/controller/v2/hosts/"
                 & Number.ToText(host_id)
                 & "/ansible_facts/",
    Response = Web.Contents(URL, [Headers = [Accept = "application/json"]]),
    Facts    = Json.Document(Response)
in
    Facts
