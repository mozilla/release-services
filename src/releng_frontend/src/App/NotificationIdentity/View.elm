-- PAGE DISPLAY/VIEW CODE HERE
module App.NotificationIdentity.View exposing (..)

import App.NotificationIdentity.Types exposing (..)
import Html exposing (..)
import Html.Attributes exposing (class, placeholder)
import Html.Events exposing (onClick, onInput)
import RemoteData exposing (..)


channelIcon : String -> String -> Html Msg
channelIcon channel target =
    case channel of
        "EMAIL" ->
            i [ class "fa fa-envelope" ] []

        "IRC" ->
            if String.startsWith "#" target then
                --i [ class "fa fa-comments" ] []
                i [class "fa fa-circle-o-notch"] []
            else
                i [ class "fa fa-comment" ] []

        _ ->
            i [] []


urgencyLevel : String -> String
urgencyLevel urgency =
    case urgency of
        "LOW" ->
            "success"

        "NORMAL" ->
            "warning"

        "HIGH" ->
            "danger"

        _ ->
            "default"


viewPreferenceItem : App.NotificationIdentity.Types.Preference -> Html App.NotificationIdentity.Types.Msg
viewPreferenceItem preference =
    div [ class "list-group-item justify-content-between" ]
    [ h5 [ class "list-group-item-heading" ]
        [ channelIcon preference.channel preference.target
        , text (preference.target)
        , span [class ("float-xs-right badge badge-" ++ (urgencyLevel preference.urgency))]
            [ text preference.urgency
            ]
        ]

    ]



viewPreferences : App.NotificationIdentity.Types.Model -> Html App.NotificationIdentity.Types.Msg
viewPreferences model =
    case model.preferences of
        NotAsked -> text ""

        Loading -> text "Loading..."

        Failure err -> text ""

        Success prefs ->
            prefs
                |> List.sortBy .urgency
                |> List.map (viewPreferenceItem)
                |> div [ class "list-group" ]
