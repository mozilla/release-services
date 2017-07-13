-- ROUTING, UPDATE, VIEW GO HERE
module App.Notifications exposing (..)

import App.Notifications.Api
import App.Notifications.Form
import App.Notifications.Types
import App.Notifications.View
import App.Types
import App.Utils
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
--
routeParser : UrlParser.Parser (App.Notifications.Types.Route -> a) a
routeParser =
    UrlParser.oneOf
        [ UrlParser.map App.Notifications.Types.BaseRoute UrlParser.top
        , UrlParser.map App.Notifications.Types.ShowPreferencesRoute (UrlParser.s "identity" </> UrlParser.string)
        , UrlParser.map App.Notifications.Types.NewIdentityRoute (UrlParser.s "new")
        , UrlParser.map App.Notifications.Types.PolicyRoute (UrlParser.s "policy")
        ]


reverseRoute : App.Notifications.Types.Route -> String
reverseRoute route =
    case route of
        App.Notifications.Types.BaseRoute ->
            "/notifications"

        App.Notifications.Types.ShowPreferencesRoute identity ->
            "/notifications/identity/" ++ identity

        App.Notifications.Types.NewIdentityRoute ->
            "/notifications/new"

        App.Notifications.Types.PolicyRoute ->
            "/notifications/policy"

page : (App.Notifications.Types.Route -> a) -> App.Types.Page a b
page outRoute =
    { title = "Notification Identity"
    , description = "Manage RelEng notification preferences for individuals and groups."
    , matcher = UrlParser.map outRoute (UrlParser.s "notifications" </> routeParser)
    }


--
-- UPDATE
--

init : String -> String -> App.Notifications.Types.Model
init identityUrl policyUrl =
    { identityUrl = identityUrl
    , policyUrl = policyUrl
    , identity_name = Nothing
    , preferences = NotAsked
    , api_problem = NotAsked
    --, status_message = Nothing
    , selected_preference = Nothing
    , is_service_processing = False
    , retrieved_identity = Nothing
    , edit_form = Form.initial [] App.Notifications.Form.editPreferenceValidation
    , new_identity = Form.initial [] App.Notifications.Form.newIdentityValidation
    , new_message = Form.initial [] App.Notifications.Form.newMessageValidation
    , uid = Nothing
    , status_html = Nothing
    }


handleApiRequestFailure :
    App.Notifications.Types.Model ->
    Http.Error ->
    App.Notifications.Types.Msg ->
    (App.Notifications.Types.Model, Cmd App.Notifications.Types.Msg, Maybe Hawk.Request)
handleApiRequestFailure model err event =
    case err of
        Http.BadStatus err ->
            (model, Utils.performMsg (App.Notifications.Types.HandleProblemJson event err), Nothing)
        _ ->  -- Theoretically this should never happen
            (model, Cmd.none, Nothing)


update :
    App.Notifications.Types.Route
    -> App.Notifications.Types.Msg
    -> App.Notifications.Types.Model
    -> (App.Notifications.Types.Model, Cmd App.Notifications.Types.Msg, Maybe Hawk.Request)
update currentRoute msg model =
    case msg of
        App.Notifications.Types.ChangeName name ->
            let
                newName =
                    if String.isEmpty name then
                        Nothing
                    else
                        Just name
            in
                ({model | identity_name = newName}, Cmd.none, Nothing)

        App.Notifications.Types.GetPreferencesRequest ->
            case model.identity_name of
                Just val ->
                    ({model
                        | is_service_processing = True
                        , retrieved_identity = model.identity_name
                        , selected_preference = Nothing
                        , preferences = Loading
                        }, App.Notifications.Api.getPreferences model, Nothing)

                Nothing ->
                    ({model
                        | status_html = Just (App.Utils.error App.Notifications.Types.GetPreferencesRequest "Please enter an identity.")}, Cmd.none, Nothing)

        App.Notifications.Types.GetPreferencesResponse response ->
            let
                resp_model =
                    {model
                        | is_service_processing = False
                        , preferences = NotAsked}

                navigation_change_command =
                    case model.retrieved_identity of
                        Just id_name ->
                            (reverseRoute (App.Notifications.Types.ShowPreferencesRoute id_name))
                                |> Navigation.newUrl

                        Nothing ->
                            Cmd.none

                err_resp =
                    (resp_model, Cmd.none, Nothing)
            in
                case response of
                    Success resp ->
                        ({resp_model
                            | api_problem = NotAsked
                            , preferences = response}, navigation_change_command, Nothing)
                    Failure err ->
                        handleApiRequestFailure resp_model err App.Notifications.Types.GetPreferencesRequest
                    _ ->
                        err_resp


        App.Notifications.Types.IdentityDeleteRequest ->
            ({model
                | status_html = Nothing
                , is_service_processing = True
                , status_html = Nothing}, App.Notifications.Api.deleteIdentity model, Nothing)

        App.Notifications.Types.IdentityDeleteResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}
            in
                case response of
                    Success resp ->  -- Means the body was null/no body
                        ({resp_model
                            | api_problem = NotAsked
                            , status_html = Just (App.Utils.success App.Notifications.Types.ClearStatusMessage "Identity successfully deleted")
                            , preferences = NotAsked }, Cmd.none, Nothing)
                    Failure err ->
                        handleApiRequestFailure resp_model err App.Notifications.Types.IdentityDeleteRequest
                    _ ->
                        ({resp_model
                            | api_problem = NotAsked}, Cmd.none, Nothing)


        App.Notifications.Types.UrgencyDeleteRequest ->
            ({model
                | status_html = Nothing
                , is_service_processing = True}, App.Notifications.Api.deletePreferenceByUrgency model, Nothing)


        App.Notifications.Types.UrgencyDeleteResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}

                success_status =
                    App.Utils.success App.Notifications.Types.ClearStatusMessage "Preference deleted!"

            in
                case response of
                    Success resp ->
                        ({resp_model
                            | api_problem = NotAsked
                            , status_html = Just success_status},

                        Utils.performMsg App.Notifications.Types.GetPreferencesRequest, Nothing)

                    Failure err ->
                        handleApiRequestFailure resp_model err App.Notifications.Types.UrgencyDeleteRequest

                    _ ->
                        (resp_model, Cmd.none, Nothing)


        App.Notifications.Types.NewIdentityFormDisplay ->
            let
                new_route_command =
                    (reverseRoute App.Notifications.Types.NewIdentityRoute
                        |> Navigation.newUrl)
            in
                ({model
                    | retrieved_identity = Nothing
                    , preferences = NotAsked
                    , selected_preference = Nothing
                    , new_identity = App.Notifications.Form.initializeNewIdentityForm}, new_route_command, Nothing)
                

        App.Notifications.Types.NewIdentityFormMsg formMsg ->
            let
                new_model =
                    { model
                        | new_identity = Form.update App.Notifications.Form.newIdentityValidation formMsg model.new_identity }

            in
                case formMsg of
                    Form.Submit ->  -- Submit new identity
                        (new_model, Utils.performMsg App.Notifications.Types.NewIdentityRequest, Nothing)

                    Form.Append pref ->  -- New preference for ID
                        (new_model, Cmd.none, Nothing)

                    _ -> -- Catchall
                        (new_model, Cmd.none, Nothing)


        App.Notifications.Types.NewIdentityRequest ->
            ({model
                | status_html = Nothing
                , is_service_processing = True}, App.Notifications.Api.newIdentity model, Nothing)


        App.Notifications.Types.NewIdentityResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}

                name_field = Form.getFieldAsString "name" model.new_identity

                name =
                    case name_field.value of
                        Just v -> v
                        Nothing -> ""

                success_message =
                            "Identity " ++ name ++ " successfully created!"

                success =
                    App.Utils.success App.Notifications.Types.ClearStatusMessage success_message
            in
                case response of
                    Success resp ->
                        ({resp_model
                            | api_problem = NotAsked
                            , status_html = Just success
                            , identity_name = Just name},
                        Utils.performMsg App.Notifications.Types.GetPreferencesRequest, Nothing)

                    Failure err ->
                       handleApiRequestFailure resp_model err App.Notifications.Types.NewIdentityRequest

                    _ ->
                        ({resp_model
                            | api_problem = NotAsked}, Cmd.none, Nothing)


        App.Notifications.Types.ModifyIdentityRequest ->
            ({model
                | status_html = Nothing
                , is_service_processing = True}, App.Notifications.Api.modifyIdentity model, Nothing)


        App.Notifications.Types.ModifyIdentityResponse response ->
            let
                resp_model =
                    { model
                        | is_service_processing = False }

                success_message =
                    App.Utils.success App.Notifications.Types.ClearStatusMessage "Identity modified."
            in
                case response of
                    Success resp ->
                        ({resp_model
                            | api_problem = NotAsked
                            , status_html = Just success_message}, Utils.performMsg App.Notifications.Types.GetPreferencesRequest, Nothing)

                    Failure err ->
                       handleApiRequestFailure resp_model err App.Notifications.Types.ModifyIdentityRequest

                    _ ->
                        ({resp_model
                            | api_problem = NotAsked}, Cmd.none, Nothing)


        App.Notifications.Types.SelectPreference preference ->
            ({ model
                | selected_preference = Just preference
                , edit_form = App.Notifications.Form.initializeFormFromPreference preference},
            Cmd.none, Nothing)


        App.Notifications.Types.EditPreferenceFormMsg formMsg ->
            let
                new_model = { model
                    | edit_form = Form.update App.Notifications.Form.editPreferenceValidation formMsg model.edit_form }

                command =
                    case formMsg of
                        Form.Submit ->
                            Utils.performMsg App.Notifications.Types.ModifyIdentityRequest


                        Form.RemoveItem _ _ ->
                            Utils.performMsg App.Notifications.Types.UrgencyDeleteRequest

                        _ ->
                            Cmd.none
            in
                (new_model, command, Nothing)


        App.Notifications.Types.PolicyDisplay ->
            let
                new_route_command =
                    (reverseRoute App.Notifications.Types.PolicyRoute)
                        |> Navigation.newUrl
            in
                (model, new_route_command, Nothing)


        App.Notifications.Types.UpdateUID newUid ->
            ({model | uid = Just newUid}, Cmd.none, Nothing)


        App.Notifications.Types.GetPendingMessagesRequest ->
            ({model
                | is_service_processing = True}, App.Notifications.Api.getPendingMessages model, Nothing)


        App.Notifications.Types.GetPendingMessagesResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}


            in
                case response of
                    Success resp ->
                        (resp_model, Cmd.none, Nothing)

                    Failure err ->
                       handleApiRequestFailure resp_model err App.Notifications.Types.GetPendingMessagesRequest

                    _ ->
                        ({resp_model
                            | api_problem = NotAsked}, Cmd.none, Nothing)


        App.Notifications.Types.GetMessageRequest ->
            let
                resp_model =
                    {model | is_service_processing = True}
            in
                (resp_model, App.Notifications.Api.getMessageByUid model, Nothing)


        App.Notifications.Types.GetMessageResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}
            in
                case response of
                    Success resp ->
                        (resp_model, Cmd.none, Nothing)

                    Failure err ->
                        handleApiRequestFailure resp_model err App.Notifications.Types.GetMessageRequest
                    _ ->
                        ({resp_model | api_problem = NotAsked}, Cmd.none, Nothing)



        App.Notifications.Types.DeleteMessageRequest ->
            let
                resp_model =
                    {model | is_service_processing = True}
            in
                (resp_model, App.Notifications.Api.deleteMessage model, Nothing)


        App.Notifications.Types.DeleteMessageResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}
            in
                case response of
                    Success resp ->
                        (resp_model, Cmd.none, Nothing)

                    Failure err ->
                        handleApiRequestFailure resp_model err App.Notifications.Types.DeleteMessageRequest

                    _ ->
                        (model, Cmd.none, Nothing)


        App.Notifications.Types.NewMessageRequest ->
            let
                resp_model =
                    {model | is_service_processing = True}
            in
                (resp_model, App.Notifications.Api.putNewMessage model, Nothing)


        App.Notifications.Types.NewMessageResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}
            in
                case response of
                    Success resp ->
                        (resp_model, Cmd.none, Nothing)
                    Failure err ->
                        handleApiRequestFailure resp_model err App.Notifications.Types.NewMessageRequest
                    _ ->
                        (model, Cmd.none, Nothing)


        App.Notifications.Types.TickTockRequest ->
            let
                resp_model =
                    {model | is_service_processing = True}
            in
                (resp_model, App.Notifications.Api.tickTock model, Nothing)


        App.Notifications.Types.TickTockResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}
            in
                case response of
                    Success resp ->
                        (resp_model, Cmd.none, Nothing)
                    Failure err ->
                        handleApiRequestFailure resp_model err App.Notifications.Types.TickTockRequest
                    _ ->
                        (model, Cmd.none, Nothing)


        App.Notifications.Types.GetActivePoliciesRequest ->
            let
                resp_model =
                    {model | is_service_processing = True}
            in
                (resp_model, App.Notifications.Api.getActivePolicies model, Nothing)


        App.Notifications.Types.GetActivePoliciesResponse response ->
            let
                resp_model =
                    {model | is_service_processing = False}
            in
                case response of
                    Success resp ->
                        (resp_model, Cmd.none, Nothing)

                    Failure err ->
                        handleApiRequestFailure resp_model err App.Notifications.Types.GetActivePoliciesRequest

                    _ ->
                        (model, Cmd.none, Nothing)


        App.Notifications.Types.OperationFail event reason ->
            let
                err =
                    App.Utils.error event reason
            in
                ({model
                    | is_service_processing = False
                    , status_html = Just err}, Cmd.none, Nothing)


        App.Notifications.Types.ClearStatusMessage ->
            ({model | status_html = Nothing}, Cmd.none, Nothing)


        App.Notifications.Types.HandleProblemJson event err ->
            let
                problem_json =
                    err.body
                    |> Json.Decode.decodeString App.Notifications.Api.problemDecoder

                problem_fail_err =
                    App.Utils.error event "Problem decoding ProblemJSON."

                err_return =
                    ({model
                        | status_html = Just problem_fail_err}, Cmd.none, Nothing)

            in
                case problem_json of
                    Ok problem ->
                        case problem.detail of
                            Just detail ->
                                let
                                    api_err =
                                        App.Utils.error event detail
                                in
                                    ({model |
                                        status_html = Just api_err}, Cmd.none, Nothing)
                            Nothing ->
                                err_return
                    _ ->
                        err_return


--
-- VIEW
--
view :
    App.Notifications.Types.Route
    -> List String
    -> App.Notifications.Types.Model
    -> Html App.Notifications.Types.Msg
view route scopes model =
    let
        errtst =
            case model.status_html of
                Just some_div -> some_div
                Nothing -> text ""

        main_content_view =
            case route of
                App.Notifications.Types.BaseRoute ->
                    text ""

                App.Notifications.Types.ShowPreferencesRoute id_name ->
                    p [ class "lead" ] [ App.Notifications.View.viewPreferences model ]

                App.Notifications.Types.NewIdentityRoute ->
                    p [ class "lead" ] [ App.Notifications.Form.viewNewIdentity model ]

                App.Notifications.Types.PolicyRoute ->
                    p [ class "lead" ] [ App.Notifications.View.viewPolicies model ]

    in
        div [ class "container" ]
            [ h1 [] [ text "RelEng NagBot Preferences" ]
            , p [ class "lead" ] [ text "Manage preferred notification preferences for RelEng events" ]
            , div []
                [ p [ class "lead" ] [ App.Notifications.View.viewStatusMessage model ]
                , div [ class "container" ]
                    [ input [ placeholder "Enter identity name", onInput App.Notifications.Types.ChangeName ] []
                    , button [ onClick App.Notifications.Types.GetPreferencesRequest ]
                        [ i [ class "fa fa-search" ] []
                        , text " Search Identities"
                        ]
                    , button [ onClick App.Notifications.Types.NewIdentityFormDisplay ]
                        [ i [ class "fa fa-user-plus" ] []
                        , text " New Identity"
                        ]
                    , button [ onClick App.Notifications.Types.PolicyDisplay ]
                        [ i [ class "fa fa-list-ol" ] []
                        , text " Policy"
                        ]
                    ]
                , main_content_view
                ]
            ]
