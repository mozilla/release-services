port module App exposing (..)

import Dict exposing ( Dict )
import Html exposing ( Html, div, nav, button, text, a, ul, li, footer, hr )
import Html.App
import Html.Attributes exposing ( attribute, id, class, type', href, target )
import Html.Events as Events
import Json.Decode as JsonDecode exposing ( (:=) )
import Navigation exposing ( Location )
import RouteUrl exposing ( UrlChange )
import RouteUrl.Builder as Builder exposing ( Builder, builder, replacePath )
import Result exposing ( Result(Ok, Err))

import App.Home as Home 
import App.User as User
import App.ReleaseDashboard as ReleaseDashboard
import App.Utils exposing ( eventLink )



-- TODO:
--   - add NotFound page and redirect to it when route not found
--


type Page
    = Home
    | ReleaseDashboard


type alias Model =
    { release_dashboard : ReleaseDashboard.Model
    , current_page : Page
    , current_user : Maybe User.Model
    , backend_url : String
    }

type Msg
    = ShowPage Page
    | UserMsg User.Msg
    | ReleaseDashboardMsg ReleaseDashboard.Msg

type alias Flags = {
    user : Maybe User.Model,
    backendUrl : String
}



pageLink page attributes =
    eventLink (ShowPage page) attributes


delta2url' : Model -> Model -> Maybe Builder
delta2url' previous current =
    case current.current_page of
        ReleaseDashboard ->
            Maybe.map
                (Builder.prependToPath ["release-dashboard"])
                (Just builder)
        _ ->
            Maybe.map
                (Builder.prependToPath [])
                (Just builder)

delta2url : Model -> Model -> Maybe UrlChange
delta2url previous current =
    Maybe.map Builder.toUrlChange <| delta2url' previous current


pages =
    [ { page = ReleaseDashboard
      , title = "Release Dashboard"
      }
    ]

location2messages' : Builder -> List Msg
location2messages' builder =
    case Builder.path builder of
        first :: rest ->
            let
                builder' = Builder.replacePath rest builder
            in
                case first of
                    "login" ->
                        [ 
                          Builder.query builder
                              |> User.convertUrlQueryToModel
                              |> User.LoggingIn
                              |> UserMsg
                        , ShowPage Home
                        ]
                    "release-dashboard" ->
                        [ ShowPage ReleaseDashboard ]

                    -- TODO: This should redirect to NotFound
                    _ ->
                        [ ShowPage Home ]
        _ ->
            [ ShowPage Home ]

location2messages : Location -> List Msg
location2messages location =
    location2messages'
        <| Builder.fromUrl location.href


init : Flags -> (Model, Cmd Msg)
init flags =
    ( {
         release_dashboard = fst (ReleaseDashboard.init flags.user),
         current_page = Home,
         current_user = flags.user,
         backend_url = flags.backendUrl
      }
    , Cmd.none
    )


update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        ShowPage page ->
            case page of
                ReleaseDashboard ->
                    let 
                        (dashboard, newCmd) = ReleaseDashboard.init model.current_user
                    in
                        (
                            { model | current_page = page, release_dashboard = dashboard },
                            Cmd.map ReleaseDashboardMsg newCmd
                        )
                _ ->
                    ( { model | current_page = page }, Cmd.none )

        ReleaseDashboardMsg msg' ->
            let
                (newModel, newCmd) = ReleaseDashboard.update msg' model.release_dashboard
            in
                ( { model | release_dashboard = newModel }, Cmd.map ReleaseDashboardMsg newCmd )

        UserMsg msg' -> 
            let
                log' = Debug.log "UserMSG" msg'
                (newModel, newCmd) = User.update msg' model.current_user
            in
                ( { model | current_user = newModel }
                , Cmd.map UserMsg newCmd
                )



viewPage model =
    case model.current_page of
        Home ->
            Home.view model
        ReleaseDashboard ->
            Html.App.map ReleaseDashboardMsg (ReleaseDashboard.view model.release_dashboard)


viewDropdown title pages =
    [ div [ class "dropdown" ]
          [ a [ class "nav-link dropdown-toggle"
              , id ("dropdown" ++ title)
              , href "#"
              , attribute "data-toggle" "dropdown"
              , attribute "aria-haspopup" "true"
              , attribute "aria-expanded" "false"
              ]
              [ text title ]
          , div [ class "dropdown-menu dropdown-menu-right"
                , attribute "aria-labelledby" "dropdownServices"
                ] pages
          ]
    ]


viewUser model =
    case model.current_user of
        Just user ->
            viewDropdown (Maybe.withDefault "UNKNOWN" user.clientId )
                    [ a [ class "dropdown-item"
                        , href "https://tools.taskcluster.net/credentials"
                        , target "_blank"
                        ]
                        [ text "Manage credentials" ]
                    , eventLink (UserMsg User.Logout)
                                [ class "dropdown-item" ]
                                [ text "Logout" ]
                    ]
        Nothing ->
            let
                loginTarget =
                    Just ( "/login"
                         , "RelengAPI is a collection of Release Engineering services"
                         )
                loginUrl =
                    { url = "https://login.taskcluster.net"
                    , target = loginTarget
                    }
                loginMsg = UserMsg <| User.Login loginUrl
            in
                [ eventLink loginMsg [ class "nav-link" ] [ text "Login" ]
                ]


viewNavBar model =
    [ button [ class "navbar-toggler hidden-md-up"
             , type' "button"
             , attribute "data-toggle" "collapse"
             , attribute "data-target" ".navbar-collapse"
             , attribute "aria-controls" "navbar-header"
             ]
             [ text "&#9776;" ]
    , pageLink Home [ class "navbar-brand" ]
                    [ text "RelengAPI" ]
    , div [ class "collapse navbar-toggleable-sm navbar-collapse pull-right" ]
          [ ul [ class "nav navbar-nav" ]
               [ li [ class "nav-item" ]
                    ( viewDropdown "Pages" ( List.map (\x -> pageLink x.page [ class "dropdown-item" ]
                                                                                [ text x.title ]) pages ))
               , li [ class "nav-item" ] ( viewUser model )
               ]
          ]
    ]

viewFooter =
    [ hr [] []
    , ul [] 
         [ li [] [ a [ href "#" ] [ text "Github" ]]
         , li [] [ a [ href "#" ] [ text "Contribute" ]]
         , li [] [ a [ href "#" ] [ text "Contact" ]]
         -- TODO: add version / revision
         ]

    ]

view : Model -> Html Msg
view model =
    let
        log = Debug.log "LOCATION" (builder)
    in
    div []
        [ nav [ id "navbar", class "navbar navbar-full navbar-light" ]
              [ div [ class "container" ] ( viewNavBar model ) ]
        , div [ id "content" ]
              [ div [ class "container" ] [ viewPage model ] ]
        , footer [ class "container" ] viewFooter
        ]


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
    [ 
      Sub.map UserMsg (User.localstorage_get (User.LoggedIn))
    ]
