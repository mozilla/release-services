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
import Json.Decode exposing (..)
import Hawk
import Http
import Navigation
--import Title
import UrlParser
import UrlParser exposing ((</>))
import Utils
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
    , identity_name = Nothing
    , preferences = NotAsked
    , api_problem = NotAsked
    , status_message = Nothing
    --, selected_preference = Just (App.NotificationIdentity.Types.Preference "" "" "" "LOW")  -- Set for testing "delete urgency"
    , selected_preference = Nothing
    , is_service_processing = False
    , retrieved_identity = Nothing
    , new_identity =
        Just { name = "testid"
        , preferences =
            [{channel = "EMAIL", name = "testid", target = "testid@moz.com", urgency = "LOW"}]
        }
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
                        Nothing
                    else
                        Just name
            in
                ({model | identity_name = newName}, Cmd.none, Nothing)

        App.NotificationIdentity.Types.PreferencesRequest ->
            case model.identity_name of
                Just val ->
                    ({model
                        | status_message = Nothing
                        , is_service_processing = True
                        , retrieved_identity = model.identity_name}, App.NotificationIdentity.Api.getPreferences model, Nothing)

                Nothing ->
                    ({model
                        | status_message = Just "Please enter an identity name."}, Cmd.none, Nothing)

        App.NotificationIdentity.Types.PreferencesResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}

                identity =
                    case model.identity_name of
                        Just val ->
                            val
                        Nothing ->
                            ""
            in
                if RemoteData.isFailure response then
                    ({resp_model
                        | status_message = Just ("Could not get preferences for " ++ identity)
                        , preferences = response
                        },
                        Cmd.none, Nothing)

                else
                    ({resp_model |
                        preferences = response}, Cmd.none, Nothing)

        App.NotificationIdentity.Types.IdentityDeleteRequest ->
            ({model
                | status_message = Nothing
                , is_service_processing = True}, App.NotificationIdentity.Api.deleteIdentity model, Nothing)

        App.NotificationIdentity.Types.IdentityDeleteResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}
            in
                case response of
                    Success resp ->  -- Means the body was null/no body
                        ({resp_model
                            | api_problem = NotAsked
                            , status_message = Just "Id deleted."}, Cmd.none, Nothing)
                    Failure err ->
                        case err of
                            Http.BadStatus err ->
                                ({resp_model
                                    --| api_problem = response
                                    | api_problem = NotAsked
                                    , status_message = Just (toString err)},
                                Utils.performMsg (App.NotificationIdentity.Types.HandleProblemJson err), Nothing)
                            _ ->
                                (resp_model, Cmd.none, Nothing)
                    _ ->
                        ({resp_model
                            --| api_problem = response}, Cmd.none, Nothing)
                            | api_problem = NotAsked}, Cmd.none, Nothing)


        App.NotificationIdentity.Types.UrgencyDeleteRequest ->
            ({model
                | status_message = Nothing
                , is_service_processing = True}, App.NotificationIdentity.Api.deletePreferenceByUrgency model, Nothing)

        App.NotificationIdentity.Types.UrgencyDeleteResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}

            in
                case response of
                    Success resp ->
                        ({resp_model
                            | api_problem = response
                            , status_message = Just "Preference deleted."}, Cmd.none, Nothing)

                    Failure err ->
                        ({resp_model
                            | api_problem = response
                            , status_message = Just (toString err)}, Cmd.none, Nothing)

                    _ ->
                        ({resp_model
                            | api_problem = response}, Cmd.none, Nothing)

        App.NotificationIdentity.Types.NewIdentityRequest ->
            ({model
                | status_message = Nothing
                , is_service_processing = False}, App.NotificationIdentity.Api.newIdentity model, Nothing)

        App.NotificationIdentity.Types.NewIdentityResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}

                success_message =
                    case model.new_identity of
                        Just new_identity ->
                            new_identity.name ++ " created."
                        Nothing -> ""
            in
                case response of
                    Success resp ->
                        ({resp_model
                            | api_problem = response
                            , status_message = Just success_message}, Cmd.none, Nothing)

                    Failure err ->
                        --(resp_model, Utils.performMsg (App.NotificationIdentity.Types.HandleProblemJson err), Nothing)
                        ({resp_model
                            | api_problem = response
                            , status_message = Just success_message}, Cmd.none, Nothing)
                    _ ->
                        ({resp_model
                            | api_problem = response}, Cmd.none, Nothing)

        App.NotificationIdentity.Types.OperationFail reason ->
            ({model
                | is_service_processing = False
                , status_message = Just reason}, Cmd.none, Nothing)

        App.NotificationIdentity.Types.HandleProblemJson err ->
            let
                problem_json =
                    err.body
                    |> Json.Decode.decodeString App.NotificationIdentity.Api.problem_decoder

                err_return =
                    ({model
                        | status_message = Just "Problem decoding ProblemJSON."}, Cmd.none, Nothing)

            in
                case problem_json of
                    Ok problem ->
                        case problem.detail of
                            Just detail ->
                                ({model |
                                    status_message = Just detail}, Cmd.none, Nothing)
                            Nothing ->
                                err_return
                    _ ->
                        err_return


view :
    App.NotificationIdentity.Types.Route
    -> List String
    -> App.NotificationIdentity.Types.Model
    -> Html App.NotificationIdentity.Types.Msg
view route scopes model =
    div [ class "container" ]
        [ h1 [] [ text "RelEng Notification Identity Preferences" ]
        , p [ class "lead" ] [ text "Manage preferred notification preferences for RelEng events" ]
        , div [ class "container" ]
            [ p [ class "lead" ] [ App.NotificationIdentity.View.viewStatusMessage model ]
            , div [ class "container" ]
                [ input [ placeholder "Enter identity name", onInput App.NotificationIdentity.Types.ChangeName ] []
                , button [ onClick App.NotificationIdentity.Types.PreferencesRequest ] [ text "Get preferences"  ]
                , button [ onClick App.NotificationIdentity.Types.IdentityDeleteRequest ] [ text "Delete identity" ]
                , button [ onClick App.NotificationIdentity.Types.UrgencyDeleteRequest ] [ text "Delete LOW urgency" ]
                , button [ onClick App.NotificationIdentity.Types.NewIdentityRequest ] [ text "Test New Identity create" ]
                ]
            , p [ class "lead" ] [ App.NotificationIdentity.View.viewPreferences model ]
            ]
        ]
