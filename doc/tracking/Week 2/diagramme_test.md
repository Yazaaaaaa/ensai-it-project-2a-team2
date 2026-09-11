classDiagram
    class BaseDAO{
        <<abstract>>
        +getById(id) T
        +list(filters) List
        +save(entity) T
        +delete(id)
    }
    class BaseService{
        <<abstract>>
        +get(id) T
        +create(data) T
        +remove(id)
    }
    class BaseController{
        <<abstract>>
        +handleGet(id)
        +handleCreate(data)
        +handleDelete(id)
    }

    BaseController--> BaseService: appelle
    BaseService--> BaseDAO: utilise

    class UserDAO {
        +getByEmail(email) User
    }
    class UserService {
        +connexion(email, password)
        +create_account(email, password)
        +deconnexion()
    }
    class AdminService {
        +ban(user)
        +synchro_NASA()
        +deconnexion()
    }
    class UserController {
        +register(data)
        +login(credentials)
    }

    BaseDAO<|-- UserDAO
    BaseService<|-- UserService
    BaseService<|-- AdminService
    BaseController<|-- UserController

    class NeoDAO {
        +findUserCreated() List~NEO~
    }
    class NeoService {
        +searchNeos(criteria) List~NEO~
        +sorting_Neo_by(criteria)
        +export(list)
    }
    class NeoController {
        +search(criteria)
        +createUserNeo(data)
    }

    BaseDAO<|-- NeoDAO
    BaseService<|-- NeoService
    BaseController<|-- NeoController

    class FavDAO {
        +findByUser(user_id) List~Fav~
    }
    class FavService {
    }
    class FavController {
        +toggle(user_id, neo_id)
        +exportHistory(fav_id)
    }

    BaseDAO<|-- FavDAO
    BaseService<|-- FavService
    BaseController<|-- FavController

    class AlertDAO {
        +findActiveAlerts() List~Alert~
    }
    class AlertService {
        +send_notification()
    }
    class AlertController {
        +create(user_id, criteria)
    }

    BaseDAO<|-- AlertDAO
    BaseService<|-- AlertService
    BaseController<|-- AlertController

    class Connection_historyService{
    }

    BaseService<|-- Connection_historyService

    class User {
        <<abstract>>
        +int id
        +string email
        +string password_hash
    }
    class Admin {
        +triggerNasaSync()
    }
    class ClassicMember {
        +proposeNeo(data)
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

    UserDAO ..> User : crée
    NeoDAO ..> NEO : crée
    FavDAO ..> Fav : crée
    AlertDAO ..> Alert : crée

    %% --- Styles ---
    classDef controller fill:#d0e1fd,stroke:#2b579a,color:#0f2b5c;
    classDef service fill:#d1e7dd,stroke:#198754,color:#0f5132;
    classDef dao fill:#ffe5d9,stroke:#d9480f,color:#7c2d12;
    classDef business fill:#f3d5ff,stroke:#8e44ad,color:#4a154b;

    %% --- Affectation des classes CSS ---
    cssClass "BaseController,UserController,NeoController,FavController,AlertController" controller;
    cssClass "BaseService,UserService,AdminService,NeoService,FavService,AlertService,Connection_historyService" service;
    cssClass "BaseDAO,UserDAO,NeoDAO,FavDAO,AlertDAO" dao;
    cssClass "User,Admin,ClassicMember,Connection,NEO,Fav,Alert" business;