-- PAGE DISPLAY/VIEW CODE HERE
module App.NotificationIdentity.View exposing (..)

import App.NotificationIdentity.Types exposing (..)
import App.Utils
import Html exposing (..)
import Html.Attributes exposing (class, placeholder, id)
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

-- Map notification urgency level to badge colour class
urgencyLevel : String -> String
urgencyLevel urgency =
    case urgency of
        "LOW" -> "success"
        "NORMAL" -> "warning"
        "HIGH" -> "danger"
        _ -> "default"

-- Display a single notification preference
viewPreferenceItem : App.NotificationIdentity.Types.Preference -> Html App.NotificationIdentity.Types.Msg
viewPreferenceItem preference =
    div [ class "list-group-item justify-content-between" ]
    [ h5 [ class "list-group-item-heading" ]
        [ channelIcon preference.channel preference.target
        , text (preference.target)
        , span [class ("float-xs-right badge badge-" ++ (urgencyLevel preference.urgency))] [ text preference.urgency ]
        ]

    ]


-- Method to use for sorting preferences
preferenceSort : App.NotificationIdentity.Types.Preference -> Int
preferenceSort preference =
    case preference.urgency of
        "LOW" -> 1
        "NORMAL" -> 2
        "HIGH" -> 3
        "DO_YESTERDAY" -> 4
        _ -> -1


-- Display view for preferences
viewPreferences : App.NotificationIdentity.Types.Model -> Html App.NotificationIdentity.Types.Msg
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
                        |> List.map (viewPreferenceItem)
                        |> div [ class "list-group" ]

                display_name =
                    case model.retrieved_identity of
                        Just val ->
                            val

                        Nothing ->
                            ""

            in
                div [ class "container" ]
                    [ h3 [ class "lead" ] [ text display_name ]
                    , pref_display
                    ]


viewStatusMessage : App.NotificationIdentity.Types.Model -> Html App.NotificationIdentity.Types.Msg
viewStatusMessage model =
    case model.is_service_processing of
        True ->
            App.Utils.loading

        False ->
            case model.status_message of
                Nothing -> text ""
                Just message -> text message
