-- PAGE DISPLAY/VIEW CODE HERE
module App.Notifications.View exposing (..)

import App.Notifications.Types exposing (..)
import App.Notifications.Form exposing (..)
import App.Notifications.Utils exposing (preferenceSort, urgencyLevel)
import App.Utils
import Html exposing (..)
import Html.Attributes exposing (class, placeholder, id)
import Html.Events exposing (onClick, onInput)
import RemoteData exposing (..)


channelIcon : String -> String -> Html Msg
channelIcon channel target =
    case channel of
        "EMAIL" ->
            i [ class "fa fa-envelope" ] []

        "IRC" ->
            if String.startsWith "#" target then
                i [ class "fa fa-comments" ] []
            else
                i [ class "fa fa-comment" ] []

        _ ->
            i [] []


-- Display a single notification preference
viewPreferenceItem : App.Notifications.Types.Model -> App.Notifications.Types.Preference -> Html App.Notifications.Types.Msg
viewPreferenceItem model preference =
    let
        urgency =
            case model.selected_preference of
                Just pref ->
                    pref.urgency
                Nothing ->
                    ""

        is_selected =
            urgency == preference.urgency

        item_content =
            [ channelIcon preference.channel preference.target
            , text (" " ++ preference.target)
            , span [ class ("float-xs-right badge badge-" ++ (urgencyLevel preference.urgency)) ] [ text preference.urgency ]
            , (if is_selected == True
                    then App.Notifications.Form.viewEditPreference model
                    else text "")
            ]

        div_attributes =
            [ class "list-group-item justify-content-between" ]
                |> List.append (if is_selected == False
                                then [ onClick (App.Notifications.Types.SelectPreference preference) ]
                                else [])


    in
        div div_attributes
        [ h5 [ class "list-group-item-heading list-group-item-action" ] item_content
        ]


viewPolicies : App.Notifications.Types.Model -> Html App.Notifications.Types.Msg
viewPolicies model =
    div [ class "container" ]
        [ input [ placeholder "Enter a message UID", onInput App.Notifications.Types.UpdateUID ] []
        , button [ onClick App.Notifications.Types.GetPendingMessagesRequest ] [ text "test '/message' command" ]
        , button [ onClick App.Notifications.Types.GetMessageRequest ] [ text "test GetMessageRequest command"]
        , button [ onClick App.Notifications.Types.DeleteMessageRequest ] [ text "test DeleteMessageRequest command" ]
        , button [ onClick App.Notifications.Types.NewMessageRequest ] [ text "test new message request" ]
        , button [ onClick App.Notifications.Types.TickTockRequest ] [ text "test manual TickTock trigger"]
        , button [ onClick App.Notifications.Types.GetActivePoliciesRequest ] [ text "test get active policies" ]
        ]


-- Display view for preferences
viewPreferences : App.Notifications.Types.Model -> Html App.Notifications.Types.Msg
viewPreferences model =
    case model.preferences of
        NotAsked -> text ""

        Loading -> App.Utils.loading

        Failure err -> text ""

        Success prefs ->
            let
                pref_display =
                    prefs
                        |> List.sortBy preferenceSort
                        |> List.map (viewPreferenceItem model)
                        |> div [ class "list-group" ]

                display_name =
                    case model.retrieved_identity of
                        Just val ->
                            val

                        Nothing ->
                            ""

            in
                div [ class "container" ]
                    [    hr [] []
                    ,    div [ class "container justify-content-between" ]
                            [ text display_name
                            , button [ onClick App.Notifications.Types.IdentityDeleteRequest ]
                                [ i [ class "fa fa-trash" ] []
                                , text " Delete identity"
                                ]
                            ]
                    , pref_display
                    ]


viewStatusMessage : App.Notifications.Types.Model -> Html App.Notifications.Types.Msg
viewStatusMessage model =
    case model.is_service_processing of
        True ->
            App.Utils.loading

        False ->
            case model.status_message of
                Nothing -> text ""
                Just message -> text message
