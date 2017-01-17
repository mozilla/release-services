module App.Utils exposing (..)

import App.Types
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events as Events
import Http
import Json.Decode as JsonDecode exposing ((:=))
import Utils
import VirtualDom


dropdown :
    (String -> a)
    -> List { b | name : String }
    -> Maybe String
    -> Html a
dropdown event items selected =
    div [ class "btn-group btn-dropdown" ]
        [ span
            [ type' "button"
            , class "btn btn-secondary dropdown-toggle"
            , attribute "data-toggle" "dropdown"
            , attribute "aria-haspopup" "true"
            , attribute "aria-expanded" "false"
            ]
            [ text <| Maybe.withDefault "Select a value..." selected
            ]
        , span
            [ type' "button"
            , class "btn btn-secondary dropdown-toggle"
            , attribute "data-toggle" "dropdown"
            , attribute "aria-haspopup" "true"
            , attribute "aria-expanded" "false"
            ]
            [ span [ class "sr-only" ] [ text "Toggle Dropdown" ]
            ]
        , div [ class "dropdown-menu" ]
            (List.map
                (\x ->
                    a
                        [ Utils.onClick (event x.name)
                        , class "dropdown-item"
                        ]
                        [ text x.name ]
                )
                items
            )
        ]


loading : VirtualDom.Node a
loading =
    div [ class "progress-wrapper" ]
        [ progress
            [ class "progress progress-striped progress-animated"
            , attribute "value" "100"
            , attribute "max" "100"
            ]
            [ text "Loading ..." ]
        , span [] [ text "Loading ..." ]
        ]


error : a -> String -> Html a
error event message =
    div
        [ class "alert alert-danger"
        , attribute "role" "alert"
        ]
        [ strong [] [ text "Error: " ]
        , span [] [ text message ]
        , a
            [ Utils.onClick event
            , class "alert-link"
            ]
            [ text " Click to retry." ]
        ]


handleResponse response =
    let
        decoderError =
            JsonDecode.object4 App.Types.ResponseError
                ("type" := JsonDecode.string)
                ("detail" := JsonDecode.string)
                ("status" := JsonDecode.int)
                ("title" := JsonDecode.string)
    in
        if 200 <= response.status && response.status < 300 then
            case response.value of
                Http.Text text ->
                    []

                _ ->
                    [ App.Types.Alert
                        App.Types.AlertDanger
                        "Error!"
                        "Response body is a blob, expecting a string."
                    ]
        else
            [ App.Types.Alert
                App.Types.AlertDanger
                "Error!"
                (case response.value of
                    Http.Text text ->
                        case JsonDecode.decodeString decoderError text of
                            Ok obj ->
                                obj.detail

                            Err error ->
                                text

                    r ->
                        response.statusText
                )
            ]


viewAlerts :
    List App.Types.Alert
    -> Html a
viewAlerts alerts =
    let
        getAlertTypeAsString alert =
            case alert.type_ of
                App.Types.AlertSuccess ->
                    "success"

                App.Types.AlertInfo ->
                    "info"

                App.Types.AlertWarning ->
                    "warning"

                App.Types.AlertDanger ->
                    "danger"

        createAlert alert =
            div [ class ("alert alert-" ++ (getAlertTypeAsString alert)) ]
                [ strong [] [ text alert.title ]
                , text alert.text
                ]
    in
        alerts
            |> List.map createAlert
            |> div []
