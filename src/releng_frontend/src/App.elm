module App exposing (..)

import App.TreeStatus
import App.TryChooser
import App.Types
import Hawk
import Hop
import Hop.Types
import Navigation
import TaskclusterLogin
import UrlParser
import UrlParser exposing ((</>))
import Utils


type Route
    = NotFoundRoute
    | HomeRoute
    | LoginRoute
    | LogoutRoute
    | TryChooserRoute
    | TreeStatusRoute App.TreeStatus.Route


pages : List (App.Types.Page Route b)
pages =
    [ App.TryChooser.page TryChooserRoute
    , App.TreeStatus.page TreeStatusRoute
    ]


routes : UrlParser.Parser (Route -> a) a
routes =
    pages
        |> List.map (\x -> x.matcher)
        |> List.append
            [ UrlParser.format HomeRoute (UrlParser.s "")
            , UrlParser.format NotFoundRoute (UrlParser.s "404")
            , UrlParser.format LoginRoute (UrlParser.s "login")
            , UrlParser.format LogoutRoute (UrlParser.s "logout")
            ]
        |> UrlParser.oneOf


reverse : Route -> String
reverse route =
    case route of
        NotFoundRoute ->
            "/404"

        HomeRoute ->
            "/"

        LoginRoute ->
            "/login"

        LogoutRoute ->
            "/logout"

        TryChooserRoute ->
            "/trychooser"

        TreeStatusRoute route ->
            App.TreeStatus.reverse route


urlParser : Navigation.Parser ( Route, Hop.Types.Address )
urlParser =
    let
        parse address =
            address
                |> UrlParser.parse identity routes
                |> Result.withDefault NotFoundRoute

        resolver =
            Hop.makeResolver App.Types.hopConfig parse
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
