-- ROUTING, UPDATE, VIEW GO HERE


module App.Notifications exposing (..)

import App.Notifications.Api
import App.Notifications.Form
import App.Notifications.Types
import App.Notifications.View
import App.Types
import App.UserScopes
import App.Utils
import Form
import Hawk
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onClick, onInput)
import Http
import Json.Decode exposing (..)
import Json.Encode
import Navigation
import RemoteData exposing (..)
import UrlParser exposing ((</>))
import Utils


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
        , UrlParser.map App.Notifications.Types.ShowMessageRoute (UrlParser.s "message" </> UrlParser.string)
        , UrlParser.map App.Notifications.Types.HelpRoute (UrlParser.s "help")
        ]


reverseRoute : App.Notifications.Types.Route -> String
reverseRoute route =
    case route of
        App.Notifications.Types.BaseRoute ->
            "/notifications"

        App.Notifications.Types.ShowPreferencesRoute identity ->
            "/notifications/identity/" ++ identity

        App.Notifications.Types.ShowMessageRoute message_uid ->
            "/notifications/message/" ++ message_uid

        App.Notifications.Types.NewIdentityRoute ->
            "/notifications/new"

        App.Notifications.Types.PolicyRoute ->
            "/notifications/policy"

        App.Notifications.Types.HelpRoute ->
            "/notifications/help"


page : (App.Notifications.Types.Route -> a) -> App.Types.Page a b
page outRoute =
    { title = "RelEng Notifications"
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
    , input_value = Nothing
    , preferences = NotAsked
    , api_problem = NotAsked
    , selected_preference = Nothing
    , is_service_processing = False
    , retrieved_identity = Nothing
    , edit_form = Form.initial [] App.Notifications.Form.preferenceValidation
    , new_identity = Form.initial [] App.Notifications.Form.newIdentityValidation
    , new_message = Just App.Notifications.View.messageJsonExample
    , uid = Nothing
    , status_html = Nothing
    , policies = NotAsked
    , retrieved_message = NotAsked
    }


handleApiRequestFailure :
    App.Notifications.Types.Model
    -> Http.Error
    -> App.Notifications.Types.Msg
    -> ( App.Notifications.Types.Model, Cmd App.Notifications.Types.Msg, Maybe Hawk.Request )
handleApiRequestFailure model err event =
    case err of
        Http.BadStatus error ->
            ( model, Utils.performMsg (App.Notifications.Types.HandleProblemJson event error), Nothing )

        Http.NetworkError ->
            ( { model
                | status_html = Just (App.Utils.error event "A network error occurred.")
              }
            , Cmd.none
            , Nothing
            )

        _ ->
            -- Theoretically this should never happen
            ( model, Cmd.none, Nothing )


update :
    App.Notifications.Types.Route
    -> App.Notifications.Types.Msg
    -> App.Notifications.Types.Model
    -> ( App.Notifications.Types.Model, Cmd App.Notifications.Types.Msg, Maybe Hawk.Request )
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
            ( { model | input_value = newName }, Cmd.none, Nothing )

        App.Notifications.Types.GetPreferencesRequest ->
            let
                identity =
                    case model.input_value of
                        Just name ->
                            name

                        Nothing ->
                            ""

                request =
                    Hawk.Request
                        "GetPreferences"
                        "GET"
                        (model.identityUrl ++ "/identity/" ++ identity)
                        [ Http.header "Accept" "application/json" ]
                        Http.emptyBody
            in
            case model.input_value of
                Just val ->
                    ( { model
                        | is_service_processing = True
                        , retrieved_identity = model.input_value
                        , selected_preference = Nothing
                        , preferences = Loading
                        , policies = Loading
                        , status_html = Nothing
                      }
                    , Cmd.none
                    , Just request
                    )

                Nothing ->
                    ( { model
                        | status_html = Just (App.Utils.error App.Notifications.Types.GetPreferencesRequest "Please enter an identity.")
                      }
                    , Cmd.none
                    , Nothing
                    )

        App.Notifications.Types.GetPreferencesResponse response ->
            let
                resp_model =
                    { model
                        | is_service_processing = False
                        , preferences = NotAsked
                    }

                navigation_change_command =
                    case model.retrieved_identity of
                        Just id_name ->
                            reverseRoute (App.Notifications.Types.ShowPreferencesRoute id_name)
                                |> Navigation.newUrl

                        Nothing ->
                            Cmd.none

                get_policies_command =
                    Utils.performMsg App.Notifications.Types.GetActivePoliciesRequest

                err_resp =
                    ( resp_model, Cmd.none, Nothing )
            in
            case response of
                Success resp ->
                    let
                        preferences =
                            case decodeString App.Notifications.Api.preferenceDecoder resp of
                                Ok prefs ->
                                    Success prefs

                                _ ->
                                    NotAsked
                    in
                    ( { resp_model
                        | api_problem = NotAsked
                        , preferences = preferences
                      }
                    , Cmd.batch [ navigation_change_command, get_policies_command ]
                    , Nothing
                    )

                Failure err ->
                    handleApiRequestFailure resp_model err App.Notifications.Types.GetPreferencesRequest

                _ ->
                    err_resp

        App.Notifications.Types.IdentityDeleteRequest ->
            let
                identity =
                    case model.retrieved_identity of
                        Just name ->
                            name

                        Nothing ->
                            ""

                request =
                    Hawk.Request
                        "IdentityDelete"
                        "DELETE"
                        (model.identityUrl ++ "/identity/" ++ identity)
                        [ Http.header "Accept" "application/json" ]
                        Http.emptyBody
            in
            ( { model
                | status_html = Nothing
                , is_service_processing = True
              }
            , Cmd.none
            , Just request
            )

        App.Notifications.Types.IdentityDeleteResponse response ->
            let
                resp_model =
                    { model | is_service_processing = False }
            in
            case response of
                Success resp ->
                    -- Means the body was null/body
                    ( { resp_model
                        | api_problem = NotAsked
                        , status_html = Just (App.Utils.success App.Notifications.Types.ClearStatusMessage "Identity successfully deleted")
                        , preferences = NotAsked
                      }
                    , Cmd.none
                    , Nothing
                    )

                Failure err ->
                    handleApiRequestFailure resp_model err App.Notifications.Types.IdentityDeleteRequest

                _ ->
                    ( { resp_model
                        | api_problem = NotAsked
                      }
                    , Cmd.none
                    , Nothing
                    )

        App.Notifications.Types.UrgencyDeleteRequest ->
            case model.selected_preference of
                Nothing ->
                    ( model, Utils.performMsg (App.Notifications.Types.OperationFail App.Notifications.Types.UrgencyDeleteRequest "Please select a preference to delete."), Nothing )

                Just preference ->
                    let
                        identity =
                            case model.retrieved_identity of
                                Just name ->
                                    name

                                Nothing ->
                                    ""

                        request =
                            Hawk.Request
                                "UrgencyDelete"
                                "DELETE"
                                (model.identityUrl ++ "/identity" ++ identity ++ "/" ++ preference.urgency)
                                [ Http.header "Accept" "application/json" ]
                                Http.emptyBody
                    in
                    ( { model
                        | status_html = Nothing
                        , is_service_processing = True
                      }
                    , Cmd.none
                    , Just request
                    )

        App.Notifications.Types.UrgencyDeleteResponse response ->
            let
                resp_model =
                    { model | is_service_processing = False }

                success_status =
                    App.Utils.success App.Notifications.Types.ClearStatusMessage "Preference deleted!"
            in
            case response of
                Success resp ->
                    ( { resp_model
                        | api_problem = NotAsked
                        , status_html = Just success_status
                      }
                    , Utils.performMsg App.Notifications.Types.GetPreferencesRequest
                    , Nothing
                    )

                Failure err ->
                    handleApiRequestFailure resp_model err App.Notifications.Types.UrgencyDeleteRequest

                _ ->
                    ( resp_model, Cmd.none, Nothing )

        App.Notifications.Types.NewIdentityFormDisplay ->
            let
                new_route_command =
                    reverseRoute App.Notifications.Types.NewIdentityRoute
                        |> Navigation.newUrl
            in
            ( { model
                | retrieved_identity = Nothing
                , preferences = NotAsked
                , selected_preference = Nothing
                , new_identity = App.Notifications.Form.initializeNewIdentityForm
                , status_html = Nothing
              }
            , new_route_command
            , Nothing
            )

        App.Notifications.Types.NewIdentityFormMsg formMsg ->
            let
                new_model =
                    { model
                        | new_identity = Form.update App.Notifications.Form.newIdentityValidation formMsg model.new_identity
                    }
            in
            case formMsg of
                Form.Submit ->
                    -- Submit new identity
                    ( new_model, Utils.performMsg App.Notifications.Types.NewIdentityRequest, Nothing )

                Form.Append pref ->
                    -- New preference for ID
                    ( new_model, Cmd.none, Nothing )

                _ ->
                    -- Catchall
                    ( new_model, Cmd.none, Nothing )

        App.Notifications.Types.NewIdentityRequest ->
            let
                new_id_output =
                    Form.getOutput model.new_identity
            in
            case new_id_output of
                Nothing ->
                    ( model
                    , Utils.performMsg (App.Notifications.Types.OperationFail App.Notifications.Types.NewIdentityRequest "No new identity data.")
                    , Nothing
                    )

                Just new_identity ->
                    let
                        encoded_pref_list =
                            Json.Encode.list (List.map App.Notifications.Api.encodePreference new_identity.preferences)

                        msg_body =
                            Json.Encode.object
                                [ ( "preferences", encoded_pref_list )
                                ]

                        request =
                            Hawk.Request
                                "NewIdentity"
                                "PUT"
                                (model.identityUrl ++ "/identity/" ++ new_identity.name)
                                [ Http.header "Accept" "application/json" ]
                                (Http.jsonBody msg_body)
                    in
                    ( { model
                        | status_html = Nothing
                        , is_service_processing = True
                      }
                    , Cmd.none
                    , Just request
                    )

        App.Notifications.Types.NewIdentityResponse response ->
            let
                resp_model =
                    { model | is_service_processing = False }

                name_field =
                    Form.getFieldAsString "name" model.new_identity

                name =
                    case name_field.value of
                        Just v ->
                            v

                        Nothing ->
                            ""

                success_message =
                    "Identity " ++ name ++ " successfully created!"

                success =
                    App.Utils.success App.Notifications.Types.ClearStatusMessage success_message
            in
            case response of
                Success resp ->
                    ( { resp_model
                        | api_problem = NotAsked
                        , status_html = Just success
                        , input_value = Just name
                      }
                    , Utils.performMsg App.Notifications.Types.GetPreferencesRequest
                    , Nothing
                    )

                Failure err ->
                    handleApiRequestFailure resp_model err App.Notifications.Types.NewIdentityRequest

                _ ->
                    ( { resp_model
                        | api_problem = NotAsked
                      }
                    , Cmd.none
                    , Nothing
                    )

        App.Notifications.Types.ModifyIdentityRequest ->
            let
                modified_preference =
                    Form.getOutput model.edit_form
            in
            case modified_preference of
                Nothing ->
                    ( model
                    , Utils.performMsg (App.Notifications.Types.OperationFail App.Notifications.Types.ModifyIdentityRequest "No preference selected.")
                    , Nothing
                    )

                Just preference ->
                    let
                        id_name =
                            case model.retrieved_identity of
                                Just identity ->
                                    identity

                                Nothing ->
                                    ""

                        encoded_preference_list =
                            Json.Encode.list (List.map App.Notifications.Api.encodePreference [ preference ])

                        msg_body =
                            Json.Encode.object
                                [ ( "preferences", encoded_preference_list )
                                ]

                        request =
                            Hawk.Request
                                "ModifyIdentity"
                                "POST"
                                (model.identityUrl ++ "/identity/" ++ id_name)
                                [ Http.header "Accept" "application/json" ]
                                (Http.jsonBody msg_body)
                    in
                    ( { model
                        | status_html = Nothing
                        , is_service_processing = True
                      }
                    , Cmd.none
                    , Just request
                    )

        App.Notifications.Types.ModifyIdentityResponse response ->
            let
                resp_model =
                    { model
                        | is_service_processing = False
                    }

                success_message =
                    App.Utils.success App.Notifications.Types.ClearStatusMessage "Identity modified."
            in
            case response of
                Success resp ->
                    ( { resp_model
                        | api_problem = NotAsked
                        , status_html = Just success_message
                      }
                    , Utils.performMsg App.Notifications.Types.GetPreferencesRequest
                    , Nothing
                    )

                Failure err ->
                    handleApiRequestFailure resp_model err App.Notifications.Types.ModifyIdentityRequest

                _ ->
                    ( { resp_model
                        | api_problem = NotAsked
                      }
                    , Cmd.none
                    , Nothing
                    )

        App.Notifications.Types.SelectPreference preference ->
            ( { model
                | selected_preference = Just preference
                , edit_form = App.Notifications.Form.initializeFormFromPreference preference
              }
            , Cmd.none
            , Nothing
            )

        App.Notifications.Types.EditPreferenceFormMsg formMsg ->
            let
                new_model =
                    { model
                        | edit_form = Form.update App.Notifications.Form.preferenceValidation formMsg model.edit_form
                    }

                command =
                    case formMsg of
                        Form.Submit ->
                            Utils.performMsg App.Notifications.Types.ModifyIdentityRequest

                        Form.RemoveItem _ _ ->
                            Utils.performMsg App.Notifications.Types.UrgencyDeleteRequest

                        _ ->
                            Cmd.none
            in
            ( new_model, command, Nothing )

        App.Notifications.Types.NewMessageDisplay ->
            let
                new_route_command =
                    reverseRoute App.Notifications.Types.PolicyRoute
                        |> Navigation.newUrl

                new_model =
                    { model
                        | uid = Nothing
                        , status_html = Nothing
                    }
            in
            ( new_model, new_route_command, Nothing )

        App.Notifications.Types.GetPendingMessagesRequest ->
            let
                request =
                    Hawk.Request
                        "GetPendingMessages"
                        "GET"
                        (model.policyUrl ++ "/message")
                        [ Http.header "Accept" "application/json" ]
                        Http.emptyBody
            in
            ( { model
                | is_service_processing = True
              }
            , Cmd.none
            , Just request
            )

        App.Notifications.Types.GetPendingMessagesResponse response ->
            let
                resp_model =
                    { model | is_service_processing = False }
            in
            case response of
                Success resp ->
                    ( resp_model, Cmd.none, Nothing )

                Failure err ->
                    handleApiRequestFailure resp_model err App.Notifications.Types.GetPendingMessagesRequest

                _ ->
                    ( { resp_model
                        | api_problem = NotAsked
                      }
                    , Cmd.none
                    , Nothing
                    )

        App.Notifications.Types.GetMessageRequest ->
            let
                resp_model =
                    { model
                        | is_service_processing = True
                        , status_html = Nothing
                    }

                uid =
                    case model.input_value of
                        Just a ->
                            a

                        Nothing ->
                            ""

                request =
                    Hawk.Request
                        "GetMessage"
                        "GET"
                        (model.policyUrl ++ "/message/" ++ uid)
                        [ Http.header "Accept" "application/json" ]
                        Http.emptyBody
            in
            ( resp_model, Cmd.none, Just request )

        App.Notifications.Types.GetMessageResponse response ->
            let
                resp_model =
                    { model
                        | is_service_processing = False
                        , preferences = NotAsked
                    }

                navigation_change_command =
                    case model.input_value of
                        Just value ->
                            reverseRoute (App.Notifications.Types.ShowMessageRoute value)
                                |> Navigation.newUrl

                        Nothing ->
                            Cmd.none
            in
            case response of
                Success resp ->
                    let
                        message =
                            case decodeString App.Notifications.Api.messageDecoder resp of
                                Ok msg ->
                                    Success msg

                                _ ->
                                    NotAsked
                    in
                    ( { resp_model
                        | retrieved_message = message
                      }
                    , navigation_change_command
                    , Nothing
                    )

                Failure err ->
                    handleApiRequestFailure resp_model err App.Notifications.Types.GetMessageRequest

                _ ->
                    ( { resp_model | api_problem = NotAsked }, Cmd.none, Nothing )

        App.Notifications.Types.DeleteMessageRequest ->
            let
                resp_model =
                    { model | is_service_processing = True }

                uid =
                    case model.uid of
                        Just a ->
                            a

                        Nothing ->
                            ""

                request =
                    Hawk.Request
                        "DeleteMessage"
                        "DELETE"
                        (model.policyUrl ++ "/message/" ++ uid)
                        [ Http.header "Accept" "application/json" ]
                        Http.emptyBody
            in
            ( resp_model, Cmd.none, Just request )

        App.Notifications.Types.DeleteMessageResponse response ->
            let
                resp_model =
                    { model | is_service_processing = False }
            in
            case response of
                Success resp ->
                    ( resp_model, Cmd.none, Nothing )

                Failure err ->
                    handleApiRequestFailure resp_model err App.Notifications.Types.DeleteMessageRequest

                _ ->
                    ( model, Cmd.none, Nothing )

        App.Notifications.Types.NewMessageRequest ->
            case ( model.new_message, model.uid ) of
                ( Just message, Just new_uid ) ->
                    let
                        resp_model =
                            { model
                                | is_service_processing = True
                                , status_html = Nothing
                            }

                        request =
                            Hawk.Request
                                "NewMessage"
                                "PUT"
                                (model.policyUrl ++ "/message/" ++ new_uid)
                                [ Http.header "Accept" "application/json" ]
                                (Http.stringBody "application/json" message)
                    in
                    ( resp_model, Cmd.none, Just request )

                _ ->
                    ( model, Cmd.none, Nothing )

        App.Notifications.Types.NewMessageResponse response ->
            let
                resp_model =
                    { model | is_service_processing = False }
            in
            case response of
                Success resp ->
                    ( { resp_model
                        | status_html = Just (App.Utils.success App.Notifications.Types.ClearStatusMessage "Message successfully created")
                      }
                    , Cmd.none
                    , Nothing
                    )

                Failure err ->
                    handleApiRequestFailure resp_model err App.Notifications.Types.NewMessageRequest

                _ ->
                    ( model, Cmd.none, Nothing )

        App.Notifications.Types.NewMessageUpdate new_json ->
            ( { model
                | new_message =
                    if String.isEmpty new_json then
                        Nothing
                    else
                        Just new_json
              }
            , Cmd.none
            , Nothing
            )

        App.Notifications.Types.NewMessageUIDUpdate new_uid ->
            ( { model
                | uid =
                    if String.isEmpty new_uid then
                        Nothing
                    else
                        Just new_uid
              }
            , Cmd.none
            , Nothing
            )

        App.Notifications.Types.TickTockRequest ->
            let
                resp_model =
                    { model | is_service_processing = True }

                request =
                    Hawk.Request
                        "TickTock"
                        "POST"
                        (model.policyUrl ++ "/ticktock")
                        [ Http.header "Accept" "application/json" ]
                        Http.emptyBody
            in
            ( resp_model, Cmd.none, Just request )

        App.Notifications.Types.TickTockResponse response ->
            let
                resp_model =
                    { model | is_service_processing = False }
            in
            case response of
                Success resp ->
                    ( { resp_model
                        | status_html = Just (App.Utils.success App.Notifications.Types.ClearStatusMessage "TickTock successfully triggered")
                      }
                    , Cmd.none
                    , Nothing
                    )

                Failure err ->
                    handleApiRequestFailure resp_model err App.Notifications.Types.TickTockRequest

                _ ->
                    ( model, Cmd.none, Nothing )

        App.Notifications.Types.GetActivePoliciesRequest ->
            let
                resp_model =
                    { model | is_service_processing = True }

                identity =
                    case model.input_value of
                        Just name ->
                            name

                        Nothing ->
                            ""

                request =
                    Hawk.Request
                        "GetActivePolicies"
                        "GET"
                        (model.policyUrl ++ "/policy/" ++ identity)
                        [ Http.header "Accept" "application/json" ]
                        Http.emptyBody
            in
            ( resp_model, Cmd.none, Just request )

        App.Notifications.Types.GetActivePoliciesResponse response ->
            let
                resp_model =
                    { model | is_service_processing = False }
            in
            case response of
                Success resp ->
                    let
                        decoded_policies =
                            case decodeString App.Notifications.Api.policiesDecoder resp of
                                Ok policies ->
                                    Success policies

                                _ ->
                                    NotAsked
                    in
                    ( { resp_model
                        | policies = decoded_policies
                      }
                    , Cmd.none
                    , Nothing
                    )

                Failure err ->
                    handleApiRequestFailure resp_model err App.Notifications.Types.GetActivePoliciesRequest

                _ ->
                    ( model, Cmd.none, Nothing )

        App.Notifications.Types.HelpDisplay ->
            let
                new_route_command =
                    reverseRoute App.Notifications.Types.HelpRoute
                        |> Navigation.newUrl

                new_model =
                    { model
                        | uid = Nothing
                        , status_html = Nothing
                    }
            in
            ( new_model, new_route_command, Nothing )

        App.Notifications.Types.OperationFail event reason ->
            let
                err =
                    App.Utils.error event reason
            in
            ( { model
                | is_service_processing = False
                , status_html = Just err
              }
            , Cmd.none
            , Nothing
            )

        App.Notifications.Types.ClearStatusMessage ->
            ( { model | status_html = Nothing }, Cmd.none, Nothing )

        App.Notifications.Types.HandleProblemJson event err ->
            let
                problem_json =
                    err.body
                        |> Json.Decode.decodeString App.Notifications.Api.problemDecoder

                problem_fail_err =
                    App.Utils.error event "Problem decoding ProblemJSON."

                err_return =
                    ( { model
                        | status_html = Just problem_fail_err
                      }
                    , Cmd.none
                    , Nothing
                    )
            in
            case problem_json of
                Ok problem ->
                    case problem.detail of
                        Just detail ->
                            let
                                api_err =
                                    App.Utils.error event detail
                            in
                            ( { model
                                | status_html = Just api_err
                              }
                            , Cmd.none
                            , Nothing
                            )

                        Nothing ->
                            err_return

                _ ->
                    err_return

        App.Notifications.Types.NavigateTo route ->
            case route of
                App.Notifications.Types.BaseRoute ->
                    ( model, Cmd.none, Nothing )

                App.Notifications.Types.NewIdentityRoute ->
                    update route App.Notifications.Types.NewIdentityFormDisplay model

                App.Notifications.Types.PolicyRoute ->
                    update route App.Notifications.Types.NewMessageDisplay model

                App.Notifications.Types.ShowMessageRoute message_uid ->
                    update route App.Notifications.Types.GetMessageRequest { model | input_value = Just message_uid }

                App.Notifications.Types.ShowPreferencesRoute identity ->
                    let
                        newModel =
                            { model | input_value = Just identity }
                    in
                    update route App.Notifications.Types.GetPreferencesRequest newModel

                App.Notifications.Types.HelpRoute ->
                    update route App.Notifications.Types.HelpDisplay model



--
-- VIEW
--


view :
    App.Notifications.Types.Route
    -> App.UserScopes.Model
    -> App.Notifications.Types.Model
    -> Html App.Notifications.Types.Msg
view route scopes model =
    let
        main_content_view =
            case route of
                App.Notifications.Types.BaseRoute ->
                    text ""

                App.Notifications.Types.ShowPreferencesRoute id_name ->
                    div [ class "lead" ] [ App.Notifications.View.viewPreferences model ]

                App.Notifications.Types.NewIdentityRoute ->
                    div [ class "lead" ] [ App.Notifications.Form.viewNewIdentity model ]

                App.Notifications.Types.PolicyRoute ->
                    div [ class "lead" ] [ App.Notifications.View.viewNewMessage model ]

                App.Notifications.Types.ShowMessageRoute message_uid ->
                    div [ class "lead" ] [ App.Notifications.View.viewMessage model ]

                App.Notifications.Types.HelpRoute ->
                    div [ class "lead" ] [ App.Notifications.View.viewHelp ]
    in
    div [ class "container" ]
        [ h1 [] [ text "RelEng NagBot" ]
        , p [ class "lead" ] [ text "Manage preferred notification preferences for RelEng events" ]
        , div []
            [ p [ class "lead" ] [ App.Notifications.View.viewStatusMessage model ]
            , div [ class "input-group" ]
                [ span [ class "input-group-addon" ] [ i [ class "fa fa-search" ] [] ]
                , input
                    [ placeholder "Identity or Message UID"
                    , onInput App.Notifications.Types.ChangeName
                    , class "form-control"
                    ]
                    []
                ]
            , div [ class "btn-toolbar mb-3" ]
                [ div [ class "btn-group btn-group-justified" ]
                    [ button [ type_ "button", onClick App.Notifications.Types.GetPreferencesRequest, class "btn btn-outline-primary" ]
                        [ i [ class "fa fa-address-book" ] []
                        , text " Search Identities"
                        ]
                    , button [ type_ "button", onClick App.Notifications.Types.GetMessageRequest, class "btn btn-outline-primary" ]
                        [ i [ class "fa fa-inbox" ] []
                        , text " Search Messages"
                        ]
                    , button [ type_ "button", onClick App.Notifications.Types.NewIdentityFormDisplay, class "btn btn-outline-primary" ]
                        [ i [ class "fa fa-user-plus" ] []
                        , text " New Identity"
                        ]
                    , button [ type_ "button", onClick App.Notifications.Types.NewMessageDisplay, class "btn btn-outline-primary" ]
                        [ i [ class "fa fa-envelope" ] []
                        , text " New Message"
                        ]
                    , button [ type_ "button", onClick App.Notifications.Types.TickTockRequest, class "btn btn-outline-primary" ]
                        [ i [ class "fa fa-clock-o" ] []
                        , text " Trigger TickTock"
                        ]
                    , button [ type_ "button", onClick App.Notifications.Types.HelpDisplay, class "btn btn-outline-primary" ]
                        [ i [ class "fa fa-info-circle" ] []
                        ]
                    ]
                ]
            , main_content_view
            ]
        ]
