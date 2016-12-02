module App.Layout exposing (..)

import App
import Html exposing (..)
import Html.Attributes exposing (..)
import TaskclusterLogin
import Utils


viewDropdown title pages =
    [ div [ class "dropdown" ]
        [ a
            [ class "nav-link dropdown-toggle"
            , id ("dropdown" ++ title)
            , href "#"
            , attribute "data-toggle" "dropdown"
            , attribute "aria-haspopup" "true"
            , attribute "aria-expanded" "false"
            ]
            [ text title ]
        , div
            [ class "dropdown-menu dropdown-menu-right"
            , attribute "aria-labelledby" "dropdownServices"
            ]
            pages
        ]
    ]


viewUser model =
    case model.user of
        Just user ->
            viewDropdown user.clientId
                [ a
                    [ class "dropdown-item"
                    , href "https://tools.taskcluster.net/credentials"
                    , target "_blank"
                    ]
                    [ text "Manage credentials" ]
                , a
                    [ Utils.onClick (App.NavigateTo App.LogoutRoute)
                    , href "#"
                    , class "dropdown-item"
                    ]
                    [ text "Logout" ]
                ]

        Nothing ->
            let
                loginTarget =
                    Just
                        ( "/login"
                        , "Release Engineering services"
                        )

                loginUrl =
                    { url = "https://login.taskcluster.net"
                    , target = loginTarget
                    , targetName = "target"
                    }

                loginMsg =
                    App.TaskclusterLoginMsg <| TaskclusterLogin.Login loginUrl
            in
                [ a
                    [ Utils.onClick loginMsg
                    , href "#"
                    , class "nav-link"
                    ]
                    [ text "Login" ]
                ]


viewNavBar model =
    [ button
        [ class "navbar-toggler hidden-md-up"
        , type' "button"
        , attribute "data-toggle" "collapse"
        , attribute "data-target" ".navbar-collapse"
        , attribute "aria-controls" "navbar-header"
        ]
        [ text "&#9776;" ]
    , a
        [ Utils.onClick (App.NavigateTo App.HomeRoute)
        , href "#"
        , class "navbar-brand"
        ]
        [ text "Release Engineering" ]
    , div [ class "collapse navbar-toggleable-sm navbar-collapse" ]
        [ ul [ class "nav navbar-nav" ]
            [ li [ class "nav-item" ] (viewUser model)
            ]
        ]
    ]


viewFooter model =
    [ hr [] []
    , ul []
        [ li []
            [ a [ href model.docsUrl ]
                [ text "Documentation" ]
            ]
        , li []
            [ a [ href "https://github.com/mozilla-releng/services/blob/master/CONTRIBUTING.rst" ]
                [ text "Contribute" ]
            ]
        , li []
            [ a [ href "https://github.com/mozilla-releng/services/issues/new" ]
                [ text "Contact" ]
            ]
        ]
    , div []
        [ text "version: "
        , a [ href ("https://github.com/mozilla-releng/services/releases/tag/" ++ model.version) ]
            [ text model.version ]
        ]
    ]


viewNotFound : App.Model -> Html.Html App.Msg
viewNotFound model =
    div [ class "hero-unit" ]
        [ h1 [] [ text "Page Not Found" ] ]


view : (App.Model -> Html.Html App.Msg) -> App.Model -> Html.Html App.Msg
view viewRoute model =
    div []
        [ nav
            [ id "navbar"
            , class "navbar navbar-full navbar-light"
            ]
            [ div [ class "container" ] (viewNavBar model) ]
        , div [ id "content" ]
            [ div [ class "container" ] [ viewRoute model ] ]
        , footer [ class "container" ] (viewFooter model)
        ]
