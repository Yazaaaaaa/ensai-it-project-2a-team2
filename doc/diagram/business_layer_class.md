classDiagram
class User {
        <<abstract>>
        +int id
        +string email
        +string password_hash
    }
    class Admin {
    }
    class ClassicMember {
    }
    class Connection {
        +int id
        +int user_id
        +datetime timestamp
    }
    class NEO {
        +int id
        +string name
        +bool is_potentially_hazardous
        +bool is_user_created
    }
    class Fav {
        +int id
        +int user_id
        +int neo_id
    }
    class Alert {
        +int id
        +int user_id
        +int neo_id
        +evaluate(neo_data) bool
    }

    User <|-- Admin
    User <|-- ClassicMember
    User "1" --> "*" Connection : genere
    User "1" --> "*" Fav : possede
    User "1" --> "*" Alert : definit
    Fav "*" --> "1" NEO : concerne
    Alert "*" --> "0..1" NEO : cible
```