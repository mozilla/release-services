module App.Layout exposing (..)

import App
import Html exposing (..)
import Html.Attributes exposing (..)
import String
import TaskclusterLogin
import Utils


viewDropdown : String -> List (Html msg) -> List (Html msg)
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


viewUser : App.Model -> List (Html App.Msg)
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


viewNavBar : App.Model -> List (Html App.Msg)
viewNavBar model =
    [ button
        [ class "navbar-toggler navbar-toggler-right"
        , type_ "button"
        , attribute "data-toggle" "collapse"
        , attribute "data-target" "#navbarNavDropdown"
        , attribute "aria-controls" "navbarNavDropdown"
        , attribute "aria-expanded" "false"
        , attribute "aria-label" "Toggle navigation"
        ]
        [ span [ class "navbar-toggler-icon" ] [] ]
    , a
        [ Utils.onClick (App.NavigateTo App.HomeRoute)
        , href "#"
        , class "navbar-brand"
        ]
        [ text "Release Engineering" ]
    , div
        [ class "collapse navbar-collapse"
        , id "navbarNavDropdown"
        ]
        [ ul [ class "navbar-nav" ]
            [ li [ class "nav-item" ] (viewUser model)
            ]
        ]
    ]


viewFooter : App.Model -> List (Html App.Msg)
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
        , a [ href ("https://github.com/mozilla-releng/services/releases/tag/v" ++ model.version) ]
            [ text model.version ]
        ]
    ]


viewNotFound : App.Model -> Html.Html App.Msg
viewNotFound model =
    div [ class "hero-unit" ]
        [ h1 [] [ text "Page Not Found" ] ]


view : (App.Model -> Html.Html App.Msg) -> App.Model -> Html.Html App.Msg
view viewRoute model =
    let
        routeName =
            model.route
                |> toString
                |> String.toLower
                |> String.dropRight (String.length "Route")
    in
        div [ id ("page-" ++ routeName) ]
            [ nav
                [ id "navbar"
                , class "navbar navbar-toggleable-md bg-faded navbar-inverse"
                ]
                [ div [ class "container" ] (viewNavBar model) ]
            , div [ id "content" ]
                [ div [ class "container" ] [ viewRoute model ] ]
            , footer [ class "container" ] (viewFooter model)
            ]
