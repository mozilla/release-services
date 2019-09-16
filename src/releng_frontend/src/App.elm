module App exposing (..)

import App.Tokens
import App.ToolTool
import App.TreeStatus
import App.TreeStatus.Form
import App.TreeStatus.Types
import App.Types
import App.UserScopes
import Hawk
import Navigation
import TaskclusterLogin
import UrlParser exposing ((</>), (<?>))


--
-- ROUTING
--
-- inspired by https://github.com/rofrol/elm-navigation-example
--


type Route
    = NotFoundRoute
    | HomeRoute
    | LoginRoute (Maybe String) (Maybe String)
    | LogoutRoute
    | TokensRoute
    | ToolToolRoute
    | TreeStatusRoute App.TreeStatus.Types.Route


pages : List (App.Types.Page Route b)
pages =
    [ App.Tokens.page TokensRoute
    , App.ToolTool.page ToolToolRoute
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
                    <?> UrlParser.stringParam "code"
                    <?> UrlParser.stringParam "state"
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

        LoginRoute _ _ ->
            "/login"

        LogoutRoute ->
            "/logout"

        TokensRoute ->
            "/tokens"

        ToolToolRoute ->
            "/tooltool"

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
    { auth0 : Maybe TaskclusterLogin.Tokens
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
    , tokens : App.Tokens.Model
    , tooltool : App.ToolTool.Model
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
    | TaskclusterLoginMsg TaskclusterLogin.Msg
    | HawkMsg Hawk.Msg
    | UserScopesMsg App.UserScopes.Msg
    | TokensMsg App.Tokens.Msg
    | ToolToolMsg App.ToolTool.Msg
    | TreeStatusMsg App.TreeStatus.Types.Msg
