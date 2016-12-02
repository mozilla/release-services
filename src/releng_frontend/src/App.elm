module App exposing (..)

import App.TreeStatus
import App.TryChooser
import Hawk
import Hop
import Hop.Types
import Navigation
import TaskclusterLogin
import UrlParser
import Utils


type Route
    = NotFoundRoute
    | HomeRoute
    | TryChooserRoute
    | LoginRoute
    | LogoutRoute
    | TreeStatusRoute


hopConfig : Hop.Types.Config
hopConfig =
    { hash = False
    , basePath = ""
    }


type alias Page =
    { title : String
    , description : String
    , route : Route
    , path : String
    }


pages : List Page
pages =
    [ { title = "TryChooser"
      , description =
            "Generate parts of try syntax and restrict tests to certain directories."
      , route = TryChooserRoute
      , path = "trychooser"
      }
    , { title = "TreeStatus"
      , description = "??? TODO ???"
      , route = TreeStatusRoute
      , path = "treestatus"
      }
    ]



--routes : List { route : Route, path : String }


routes =
    pages
        |> List.map
            (\x ->
                { route = x.route
                , path = x.path
                }
            )
        |> List.append
            [ { route = HomeRoute
              , path = ""
              }
            , { route = NotFoundRoute
              , path = "404"
              }
            , { route = LoginRoute
              , path = "login"
              }
            , { route = LogoutRoute
              , path = "logout"
              }
            ]


pathFromRoute : Route -> String
pathFromRoute route =
    routes
        |> List.filter (\x -> x.route == route)
        |> List.map (\x -> x.path)
        |> List.head
        |> Maybe.withDefault "404"


urlParser : Navigation.Parser ( Route, Hop.Types.Address )
urlParser =
    let
        routes2 =
            routes
                |> List.map (\x -> UrlParser.format x.route (UrlParser.s x.path))
                |> UrlParser.oneOf

        parse address =
            address
                |> UrlParser.parse identity routes2
                |> Result.withDefault NotFoundRoute

        resolver =
            Hop.makeResolver hopConfig parse
    in
        Navigation.makeParser (.href >> resolver)


urlUpdate : ( Route, Hop.Types.Address ) -> Model -> ( Model, Cmd Msg )
urlUpdate ( route, address ) model =
    ( { model
        | route = route
        , address = address
      }
    , Cmd.none
    )


type alias Model =
    { route : Route
    , address : Hop.Types.Address
    , user : TaskclusterLogin.Model
    , trychooser : App.TryChooser.Model
    , treestatus : App.TreeStatus.Model
    , docsUrl : String
    , version : String
    }


type Msg
    = TaskclusterLoginMsg TaskclusterLogin.Msg
    | HawkMsg Hawk.Msg
    | NavigateTo Route
    | TryChooserMsg App.TryChooser.Msg
    | TreeStatusMsg App.TreeStatus.Msg


type alias Flags =
    { user : TaskclusterLogin.Model
    , treestatusUrl : String
    , docsUrl : String
    , version : String
    }
