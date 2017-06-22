-- ROUTING, UPDATE, VIEW GO HERE
module App.NotificationIdentity exposing (..)

import App.NotificationIdentity.Api
--import App.NotificationIdentity.Form
import App.NotificationIdentity.Types
import App.NotificationIdentity.View
import App.Types
--import App.Utils
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onClick, onInput)
--import Json.Decode exposing (..)
import Hawk
--import Http exposing (..)
import Navigation
--import Title
import UrlParser
import UrlParser exposing ((</>))
--import Utils
import RemoteData exposing (..)


--
-- ROUTING
--

routeParser : UrlParser.Parser (App.NotificationIdentity.Types.Route -> a) a
routeParser =
    UrlParser.oneOf
        [ UrlParser.map App.NotificationIdentity.Types.BaseRoute UrlParser.top
        ]


reverseRoute : App.NotificationIdentity.Types.Route -> String
reverseRoute route =
    case route of
        App.NotificationIdentity.Types.BaseRoute ->
            "/notificationidentity"

page : (App.NotificationIdentity.Types.Route -> a) -> App.Types.Page a b
page outRoute =
    { title = "Notification Identity"
    , description = "Manage RelEng notification preferences for individuals and groups."
    , matcher = UrlParser.map outRoute (UrlParser.s "notificationidentity" </> routeParser)
    }


--
-- UPDATE
--

init : String -> App.NotificationIdentity.Types.Model
init url =
    { baseUrl = url
    , identity_name = "an identity."
    , preferences = NotAsked
    , api_problem = NotAsked
    , status_message = ""
    }


update :
    App.NotificationIdentity.Types.Route
    -> App.NotificationIdentity.Types.Msg
    -> App.NotificationIdentity.Types.Model
    -> (App.NotificationIdentity.Types.Model, Cmd App.NotificationIdentity.Types.Msg, Maybe Hawk.Request)
update currentRoute msg model =
    case msg of
        App.NotificationIdentity.Types.NavigateTo route ->
            (model, (reverseRoute route) |> Navigation.newUrl, Nothing)

        App.NotificationIdentity.Types.ChangeName name ->
            let
                newName =
                    if String.isEmpty name then
                        "an identity."
                    else
                        name
            in
                ({model | identity_name = newName}, Cmd.none, Nothing)

        App.NotificationIdentity.Types.PreferencesRequest ->
            ({model
                | status_message = ""}, App.NotificationIdentity.Api.getPreferences model, Nothing)

        App.NotificationIdentity.Types.PreferencesResponse response ->
            if RemoteData.isFailure response then
                ({model
                    | status_message = "Could not get preferences for " ++ model.identity_name
                    , preferences = response},
                    Cmd.none, Nothing)

            else
                ({model |
                    preferences = response}, Cmd.none, Nothing)

        App.NotificationIdentity.Types.IdentityDeleteRequest ->
            ({model
                | status_message = ""}, App.NotificationIdentity.Api.deleteIdentity model, Nothing)

        App.NotificationIdentity.Types.IdentityDeleteResponse response ->
            case response of
                Success resp->
                    ({model
                        | api_problem = response
                        , status_message = "Id deleted."}, Cmd.none, Nothing)
                Failure err->
                    ({model
                        | api_problem = response
                        , status_message = toString err}, Cmd.none, Nothing)
                _ ->
                    ({model
                        | api_problem = response}, Cmd.none, Nothing)



view :
    App.NotificationIdentity.Types.Route
    -> List String
    -> App.NotificationIdentity.Types.Model
    -> Html App.NotificationIdentity.Types.Msg
view route scopes model =
    div [ class "container" ] [
        h1 [] [ text "RelEng Notification Identity Preferences" ],
        p [ class "lead" ] [ text "Manage preferred notification preferences for RelEng events" ],
        div [ class "container" ] [
            p [ class "lead" ] [text model.status_message ],
            div [ class "container" ] [
                input [ placeholder "Enter identity name", onInput App.NotificationIdentity.Types.ChangeName] [],
                button [ onClick App.NotificationIdentity.Types.PreferencesRequest ] [ text "Get preferences"  ],
                button [ onClick App.NotificationIdentity.Types.IdentityDeleteRequest ] [ text "Delete identity" ]
            ],
            p [ class "lead" ] [ App.NotificationIdentity.View.viewPreferences model ]
        ]
    ]
