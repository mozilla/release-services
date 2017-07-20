-- PAGE DISPLAY/VIEW CODE HERE
module App.Notifications.View exposing (..)

import App.Notifications.Types exposing (..)
import App.Notifications.Form exposing (..)
import App.Notifications.Utils exposing (preferenceSort, urgencyLevel)
import App.Utils
import Date
import Html exposing (..)
import Html.Attributes exposing (class, placeholder, id, rows, style, type_)
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

                policies_display =
                    case model.policies of
                        Success policyList ->
                            div []
                                [ hr [] []
                                , h4 [] [ text "Active Notification Policies" ]
                                , List.map viewNotificationPolicy policyList
                                    |> div [ class "list-group" ]
                                ]

                        _ -> text ""


            in
                div [ class "container" ]
                    [    hr [] []
                    ,    div [ class "container justify-content-between" ]
                            [ text display_name
                            , button [ onClick App.Notifications.Types.IdentityDeleteRequest, class "btn btn-outline-primary" ]
                                [ i [ class "fa fa-trash" ] []
                                , text " Delete identity"
                                ]
                            ]
                    , h4 [] [ text "Notification Preferences" ]
                    , pref_display
                    , policies_display
                    ]


viewStatusMessage : App.Notifications.Types.Model -> Html App.Notifications.Types.Msg
viewStatusMessage model =
    case model.is_service_processing of
        True ->
            App.Utils.loading

        False ->
            case model.status_html of
                Nothing -> text ""
                Just html -> html


viewNotificationPolicy : App.Notifications.Types.Policy -> Html App.Notifications.Types.Msg
viewNotificationPolicy policy =
    let
        start_date = Date.fromString policy.start_timestamp
        stop_date = Date.fromString policy.stop_timestamp

        start_time_text =
            case start_date of
                Ok date ->
                    let
                        start_month = toString (Date.month date)
                        start_day = toString (Date.day date)
                        start_year = toString (Date.year date)
                        start_time_formatted =
                            (toString (Date.hour date)) ++ ":" ++ (toString (Date.minute date))
                    in
                        start_month ++ " " ++ start_day ++ ", " ++ start_year ++ " at " ++ start_time_formatted
                _ -> ""


        stop_time_text =
            case stop_date of
                Ok date ->
                    let
                        stop_month = toString (Date.month date)
                        stop_day = toString (Date.day date)
                        stop_year = toString (Date.year date)
                        stop_time_formatted =
                            (toString (Date.hour date)) ++ ":" ++ (toString (Date.minute date))
                    in
                        stop_month ++ " " ++ stop_day ++ ", " ++ stop_year ++ " at " ++ stop_time_formatted
                _ -> ""

        frequency_string =
            " Alert every "
                ++ (toString policy.frequency.days) ++ " days, "
                ++ (toString policy.frequency.hours) ++ " hours and "
                ++ (toString policy.frequency.minutes) ++ " minutes."
    in
        div [ class "list-group-item", style [("display", "flex"), ("flex-direction", "column")] ]
            [ div [ class "justify-content-between", style [("display", "flex"), ("flex-direction", "row")] ]
                [ i [ class "fa fa-hourglass-start" ] []
                , h4 [] [ text (" " ++ start_time_text ++ " ") ]
                , i [ class "fa fa-long-arrow-right" ] []
                , text "  "
                , i [ class "fa fa-hourglass-end" ] []
                , h4 [] [ text (" " ++ stop_time_text ++ " ") ]
                , span [ class ("float-xs-right badge badge-" ++ (urgencyLevel policy.urgency)) ] [ text policy.urgency ]
                ]
            , div [ class "justify-content-between" ]
                [ i [ class "fa fa-clock-o" ] []
                , h4 [] [ text frequency_string ]
                ]
            ]


viewNewMessage : App.Notifications.Types.Model -> Html App.Notifications.Types.Msg
viewNewMessage model =
    div [ class "form-group" ]
        [ hr [] []
        , input
            [ onInput App.Notifications.Types.NewMessageUIDUpdate
            , placeholder "New Message UID"
            , type_ "text"
            , class "form-control" ] []
        , textarea
            [ onInput App.Notifications.Types.NewMessageUpdate
            , placeholder "Enter New Message JSON"
            , class "form-control"
            , rows 10] []
        , button [ class "btn btn-outline-primary", onClick App.Notifications.Types.NewMessageRequest ]
            [ i [ class "fa fa-check" ] []
            , text " Submit New Message"
            ]
        ]
