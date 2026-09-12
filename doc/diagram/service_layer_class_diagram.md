```mermaid
classDiagram
  class BaseService{
          <<abstract>>
          +get(id) T
          +create(data) T
          +remove(id)
  }
  class NeoService {
        +searchNeos(criteria) List~NEO~
        +sorting_Neo_by(criteria)
        +export(list)
  }
  BaseService<|-- NeoService

  class FavService {
  }
  BaseService<|-- FavService

  class AlertService {
        +send_notification()
  }
  BaseService<|-- AlertService

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
  BaseService<|-- UserService
  BaseService<|-- AdminService

  class Connection_historyService{
  }
  BaseService<|-- Connection_historyService
