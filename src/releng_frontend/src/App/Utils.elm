module App.Utils exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events as Events
import Json.Decode as JsonDecode
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
