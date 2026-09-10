```mermaid
---
config:
  theme: redux
---
flowchart LR
    Visitor["Visitor"]
    User["User"]
    Admin["Administrator"]

    subgraph subgroup["NEO-watch application"]
        login([Login])
        signup([Signup])
        logout([Logout])
        search([Search NEOs])
        searchname([Search by name])
        searchfilter([Search by filters])
        download([Download the results])
        favlist([View the list of favorites NEOs])
        editlist([Edit the list])
        alerts([View alerts])
        editalerts([Edit alerts])
        add([Add NEO])
        update([Update the data])
        manage([Manage accounts])
        accounts([View accounts])
        deleteaccount([Delete an account])
        
    end

    Visitor --> signup
    Visitor --> login
    User --> search
    User --> favlist
    User --> add
    User --> alerts
    User --> logout
    Admin --> manage
    Admin --> update
    Admin --> User

    alerts -. "include" .-> editalerts
    manage -. "include" .-> accounts
    search -. "extend" .-> searchname
    search -. "extend" .-> searchfilter
    searchname -. "extend" .-> download
    searchfilter -. "extend" .-> download
    favlist -. "extend" .-> editlist
    manage -. "extend" .-> deleteaccount
```
