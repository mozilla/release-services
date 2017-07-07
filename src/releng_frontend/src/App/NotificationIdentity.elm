-- ROUTING, UPDATE, VIEW GO HERE
module App.NotificationIdentity exposing (..)

import App.NotificationIdentity.Api
import App.NotificationIdentity.Form
import App.NotificationIdentity.Types
import App.NotificationIdentity.View
import App.Types
import Form
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onClick, onInput)
import Json.Decode exposing (..)
import Hawk
import Http
import Navigation
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
    , selected_preference = Nothing
    , is_service_processing = False
    , retrieved_identity = Nothing
    , is_creating_identity = False
    , edit_form = Form.initial [] App.NotificationIdentity.Form.editPreferenceValidation
    , new_identity = Form.initial [] App.NotificationIdentity.Form.newIdentityValidation
    }


handleApiRequestFailure :
    App.NotificationIdentity.Types.Model ->
    Http.Error ->
    (App.NotificationIdentity.Types.Model, Cmd App.NotificationIdentity.Types.Msg, Maybe Hawk.Request)
handleApiRequestFailure model err =
    case err of
        Http.BadStatus err ->
            (model, Utils.performMsg (App.NotificationIdentity.Types.HandleProblemJson err), Nothing)
        _ ->  -- Theoretically this should never happen
            (model, Cmd.none, Nothing)


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

        App.NotificationIdentity.Types.GetPreferencesRequest ->
            case model.identity_name of
                Just val ->
                    ({model
                        | is_service_processing = True
                        , retrieved_identity = model.identity_name
                        , selected_preference = Nothing
                        , preferences = Loading
                        , is_creating_identity = False}, App.NotificationIdentity.Api.getPreferences model, Nothing)

                Nothing ->
                    ({model
                        | status_message = Just "Please enter an identity name."}, Cmd.none, Nothing)

        App.NotificationIdentity.Types.GetPreferencesResponse response ->
            let
                resp_model =
                    {model
                        | is_service_processing = False
                        , preferences = NotAsked}

                err_resp =
                    (resp_model, Cmd.none, Nothing)
            in
                case response of
                    Success resp ->
                        ({resp_model
                            | api_problem = NotAsked
                            , preferences = response}, Cmd.none, Nothing)
                    Failure err ->
                        handleApiRequestFailure resp_model err
                    _ ->
                        err_resp


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
                            , status_message = Just "Id deleted."
                            , preferences = NotAsked }, Cmd.none, Nothing)
                    Failure err ->
                        handleApiRequestFailure resp_model err
                    _ ->
                        ({resp_model
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
                            | api_problem = NotAsked
                            , status_message = Just "Preference deleted."},

                        Utils.performMsg App.NotificationIdentity.Types.GetPreferencesRequest, Nothing)

                    Failure err ->
                        handleApiRequestFailure resp_model err

                    _ ->
                        (resp_model, Cmd.none, Nothing)


        App.NotificationIdentity.Types.NewIdentityFormDisplay ->
            ({model
                | is_creating_identity = True
                , retrieved_identity = Nothing
                , preferences = NotAsked
                , selected_preference = Nothing
                , new_identity = App.NotificationIdentity.Form.initializeNewIdentityForm}, Cmd.none, Nothing)


        App.NotificationIdentity.Types.NewIdentityFormMsg formMsg ->
            let
                new_model =
                    { model
                        | new_identity = Form.update App.NotificationIdentity.Form.newIdentityValidation formMsg model.new_identity }

            in
                case formMsg of
                    Form.Submit ->  -- Submit new identity
                        (new_model, Utils.performMsg App.NotificationIdentity.Types.NewIdentityRequest, Nothing)

                    Form.Append pref ->  -- New preference for ID
                        (new_model, Cmd.none, Nothing)

                    _ -> -- Catchall
                        (new_model, Cmd.none, Nothing)

        App.NotificationIdentity.Types.NewIdentityRequest ->
            ({model
                | status_message = Nothing
                , is_service_processing = True}, App.NotificationIdentity.Api.newIdentity model, Nothing)


        App.NotificationIdentity.Types.NewIdentityResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}

                name_field = Form.getFieldAsString "name" model.new_identity

                name =
                    case name_field.value of
                        Just v -> v
                        Nothing -> ""

                success_message =
                            "Identity " ++ name ++ " sucessfully created."
            in
                case response of
                    Success resp ->
                        ({resp_model
                            | api_problem = NotAsked
                            , status_message = Just success_message
                            , identity_name = Just name},
                        Utils.performMsg App.NotificationIdentity.Types.GetPreferencesRequest, Nothing)

                    Failure err ->
                       handleApiRequestFailure resp_model err

                    _ ->
                        ({resp_model
                            | api_problem = NotAsked}, Cmd.none, Nothing)

        App.NotificationIdentity.Types.ModifyIdentityRequest ->
            ({model
                | status_message = Nothing
                , is_service_processing = True}, App.NotificationIdentity.Api.modifyIdentity model, Nothing)


        App.NotificationIdentity.Types.ModifyIdentityResponse response ->
            let
                resp_model =
                    { model
                        | is_service_processing = False }

                success_message = "Identity modified."
            in
                case response of
                    Success resp ->
                        ({resp_model
                            | api_problem = NotAsked
                            , status_message = Just success_message}, Utils.performMsg App.NotificationIdentity.Types.GetPreferencesRequest, Nothing)

                    Failure err ->
                       handleApiRequestFailure resp_model err

                    _ ->
                        ({resp_model
                            | api_problem = NotAsked}, Cmd.none, Nothing)


        App.NotificationIdentity.Types.SelectPreference preference ->
            ({ model
                | selected_preference = Just preference
                , edit_form = App.NotificationIdentity.Form.initializeFormFromPreference preference},
            Cmd.none, Nothing)

        App.NotificationIdentity.Types.EditPreferenceFormMsg formMsg ->
            let
                new_model = { model
                    | edit_form = Form.update App.NotificationIdentity.Form.editPreferenceValidation formMsg model.edit_form }


                command =
                    case formMsg of
                        Form.Submit ->
                            Utils.performMsg App.NotificationIdentity.Types.ModifyIdentityRequest


                        Form.RemoveItem _ _ ->
                            Utils.performMsg App.NotificationIdentity.Types.UrgencyDeleteRequest

                        _ ->
                            Cmd.none
            in
                (new_model, command, Nothing)

        App.NotificationIdentity.Types.OperationFail reason ->
            ({model
                | is_service_processing = False
                , status_message = Just reason}, Cmd.none, Nothing)


        App.NotificationIdentity.Types.HandleProblemJson err ->
            let
                problem_json =
                    err.body
                    |> Json.Decode.decodeString App.NotificationIdentity.Api.problemDecoder

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


--
-- VIEW
--
view :
    App.NotificationIdentity.Types.Route
    -> List String
    -> App.NotificationIdentity.Types.Model
    -> Html App.NotificationIdentity.Types.Msg
view route scopes model =
    let
        new_identity_form =
            case model.is_creating_identity of
                True ->
                    p [ class "lead" ] [ App.NotificationIdentity.Form.viewNewIdentity model ]
                False ->
                    text ""

        preferences_view =
            case model.preferences of
                Success _ ->
                    p [ class "lead" ] [ App.NotificationIdentity.View.viewPreferences model ]
                _ ->
                    text ""
    in
        div [ class "container" ]
            [ h1 [] [ text "RelEng NagBot Preferences" ]
            , p [ class "lead" ] [ text "Manage preferred notification preferences for RelEng events" ]
            , div []
                [ p [ class "lead" ] [ App.NotificationIdentity.View.viewStatusMessage model ]
                , div [ class "container" ]
                    [ input [ placeholder "Enter identity name", onInput App.NotificationIdentity.Types.ChangeName ] []
                    , button [ onClick App.NotificationIdentity.Types.GetPreferencesRequest ]
                        [ i [ class "fa fa-search" ] []
                        , text " Search Identities"
                        ]
                    , button [ onClick App.NotificationIdentity.Types.NewIdentityFormDisplay ]
                        [ i [ class "fa fa-user-plus" ] []
                        , text " New Identity"
                        ]
                    ]
                , new_identity_form
                , preferences_view
                ]
            ]
