module App exposing (..)

import App.TreeStatus
import App.TreeStatus.Form
import App.TreeStatus.Types
import App.TryChooser
import App.Types
import App.UserScopes
import Hawk
import Navigation
import TaskclusterLogin
import Time
import UrlParser
import UrlParser exposing ((</>), (<?>))


--
-- ROUTING
--
-- inspired by https://github.com/rofrol/elm-navigation-example
--


type Route
    = NotFoundRoute
    | HomeRoute
    | LoginRoute (Maybe String) (Maybe String) (Maybe String)
    | LogoutRoute
    | TryChooserRoute
    | TreeStatusRoute App.TreeStatus.Types.Route


pages : List (App.Types.Page Route b)
pages =
    [ App.TryChooser.page TryChooserRoute
    , App.TreeStatus.page TreeStatusRoute
    ]


routeParser : UrlParser.Parser (Route -> a) a
routeParser =
    pages
        |> List.map (\x -> x.matcher)
        |> List.append
            [ UrlParser.map HomeRoute UrlParser.top
            , UrlParser.map NotFoundRoute (UrlParser.s "404")
            , UrlParser.map LoginRoute
                (UrlParser.s "login"
                    <?> UrlParser.stringParam "clientId"
                    <?> UrlParser.stringParam "accessToken"
                    <?> UrlParser.stringParam "certificate"
                )
            , UrlParser.map LogoutRoute (UrlParser.s "logout")
            ]
        |> UrlParser.oneOf


reverseRoute : Route -> String
reverseRoute route =
    case route of
        NotFoundRoute ->
            "/404"

        HomeRoute ->
            "/"

        LoginRoute _ _ _ ->
            "/login"

        LogoutRoute ->
            "/logout"

        TryChooserRoute ->
            "/trychooser"

        TreeStatusRoute route ->
            App.TreeStatus.reverseRoute route


parseLocation : Navigation.Location -> Route
parseLocation location =
    location
        |> UrlParser.parsePath routeParser
        |> Maybe.withDefault NotFoundRoute


navigateTo : Route -> Cmd Msg
navigateTo route =
    route
        |> reverseRoute
        |> Navigation.newUrl



--
-- FLAGS
--


type alias Flags =
    { user : TaskclusterLogin.Model
    , treestatusUrl : String
    , docsUrl : String
    , version : String
    }



--
-- MODEL
--


type alias Model =
    { history : List Navigation.Location
    , route : Route
    , user : TaskclusterLogin.Model
    , userScopes : App.UserScopes.Model
    , trychooser : App.TryChooser.Model
    , treestatus : App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
    , docsUrl : String
    , version : String
    }



--
-- MESSAGES
--


type Msg
    = UrlChange Navigation.Location
    | NavigateTo Route
    | Tick Time.Time
    | TaskclusterLoginMsg TaskclusterLogin.Msg
    | HawkMsg Hawk.Msg
    | UserScopesMsg App.UserScopes.Msg
    | TryChooserMsg App.TryChooser.Msg
    | TreeStatusMsg App.TreeStatus.Types.Msg
