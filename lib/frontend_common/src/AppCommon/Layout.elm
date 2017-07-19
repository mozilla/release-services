module AppCommon.Layout exposing ( Layout
                                 , init
                                 , isLoading
                                 , withVersion
                                 , withLogo
                                 , withContent
                                 , withHeaderContent
                                 , toView
                                 )


import Html exposing (..)
import Html.Attributes exposing (..)
import AppCommon.Taskcluster


type alias Layout a =
    { loading : Bool
    , version : Maybe String
    , logo : Maybe (Html a)
    , headerContent : Maybe (List (Html a))
    , content : Maybe (Html a)
    , session : Maybe AppCommon.Taskcluster.Credentials
    }


init : Maybe AppCommon.Taskcluster.Credentials -> Layout a
init session =
    { loading = False
    , version = Nothing
    , logo = Nothing
    , headerContent = Nothing
    , content = Nothing
    , session = session
    }


isLoading : Layout a -> Layout a
isLoading layout =
    { layout | loading = True }


withLogo : Html a -> Layout a -> Layout a
withLogo logo layout =
    { layout | logo = Just logo }


withVersion : String -> Layout a -> Layout a
withVersion version layout =
    { layout | version = Just version }


withContent : Html a -> Layout a -> Layout a
withContent content layout =
    { layout | content = Just content }


withHeaderContent : List (Html a) -> Layout a -> Layout a
withHeaderContent content layout =
    { layout | headerContent = Just content }


toView : Layout a -> Html a
toView layout =
    div
        []
        [ header
            [ id "header"]
            [ nav
                [ id "navbar"
                , class "navbar navbar-toggleable-sm"
                ]
                [ div
                    [ class "container" ]
                    ([ button
                           [ class "navbar-toggler navbar-toggler-left"
                           , type_ "button"
                           , attribute "data-toggle" "collapse"
                           , attribute "data-target" "#navbar-content"
                           , attribute "aria-controls" "navbar-content"
                           , attribute "aria-expanded" "false"
                           , attribute "aria-label" "Toggle navigation"
                           ]
                           [ span [ class "navbar-toggler-icon" ] []
                           ]
                        ] |> List.append (layout.logo |> Maybe.map (\x -> [ a [ class "navbar-brand", href "#" ] [ x ] ])
                                                      |> Maybe.withDefault [])
                          |> List.append
                              [ button
                                    [ class "navbar-toggler navbar-toggler-left"
                                    , type_ "button"
                                    , attribute "data-toggle" "collapse"
                                    , attribute "data-target" "#navbar-content"
                                    , attribute "aria-controls" "navbar-content"
                                    , attribute "aria-expanded" "false"
                                    , attribute "aria-label" "Toggle navigation"
                                    ]
                                    [ span [ class "navbar-toggler-icon" ] [] ]
                              , div [ class "collapse navbar-collapse"
                                    , id "navbar-content"
                                    ]
                                    (Maybe.withDefault [] layout.headerContent)
                              ]
                          |> List.reverse
                    )
                ]
            ]
        , section
            [ id "content" ]
            [ div 
                [ class "container" ]
                [ text "content" ]
            ]
        , footer
            [ id "footer" ]
            [ div 
                [ class "container" ]
                [ ul
                    [ class "footer-links" ]
                    [ li [] [ text "Documentation" ]
                    , li [] [ text "Contribute" ]
                    , li [] [ text "Contact" ]
                    ]
                , ul
                    []
                    [ li [] [ text "Version: v21" ]
                    ]
                ]
            ]
        ]
