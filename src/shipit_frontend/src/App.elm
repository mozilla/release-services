port module App exposing (..)

import Dict exposing ( Dict )
import Html exposing ( Html, div, nav, button, text, a, ul, li, footer, hr, span, strong )
import Html.App
import Html.Attributes exposing ( attribute, id, class, type', href, target )
import Html.Events as Events
import Json.Decode as JsonDecode exposing ( (:=) )
import Navigation exposing ( Location )
import RouteUrl exposing ( UrlChange )
import RouteUrl.Builder as Builder exposing ( Builder, builder, replacePath )
import Result exposing ( Result(Ok, Err))
import RemoteData as RemoteData exposing ( RemoteData(Loading, Success, NotAsked, Failure) )

import App.Home as Home 
import App.User as User
import App.Hawk as Hawk
import App.ReleaseDashboard as ReleaseDashboard
import App.Utils exposing ( eventLink )



-- TODO:
--   - add NotFound page and redirect to it when route not found
--


type Page
    = Home
    | ReleaseDashboard


type alias Model = {
  release_dashboard : ReleaseDashboard.Model,
  current_page : Page,
  current_user : Maybe User.Model,
  backend_dashboard_url: String
}

type Msg
    = ShowPage Page
    | UserMsg User.Msg
    | HawkMsg Hawk.Msg
    | ReleaseDashboardMsg ReleaseDashboard.Msg
    | SelectAnalysis ReleaseDashboard.Analysis

type alias Flags = {
    backend_dashboard_url : String
}

pageLink page attributes =
    eventLink (ShowPage page) attributes

analysisLink analysis attributes =
    eventLink (SelectAnalysis analysis) attributes


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
    let
        (dashboard, newCmd) = ReleaseDashboard.init flags.backend_dashboard_url
    in
    (
      {
         release_dashboard = dashboard,
         current_page = Home,
         current_user = Nothing,
         backend_dashboard_url = flags.backend_dashboard_url
      },
      Cmd.batch [
        -- Follow through with release dashboard init
        Cmd.map ReleaseDashboardMsg newCmd,

        -- Try to load local user
        User.localstorage_load True
      ]
    )


update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        ShowPage page ->
            ( { model | current_page = page }, Cmd.none )

        SelectAnalysis analysis ->
            let
                (newModel, newCmd) = ReleaseDashboard.update (ReleaseDashboard.SelectAnalysis analysis) model.release_dashboard
            in
                (
                  { model | release_dashboard = newModel, current_page = ReleaseDashboard },
                  Cmd.map ReleaseDashboardMsg newCmd
                )

        ReleaseDashboardMsg msg' ->
            let
                (newModel, newCmd) = ReleaseDashboard.update msg' model.release_dashboard
            in
                ( { model | release_dashboard = newModel }, Cmd.map ReleaseDashboardMsg newCmd )

        UserMsg usermsg -> 
            let
                (newUser, userCmd) = User.update usermsg model.current_user

                -- Send new user to dashboard
                -- TODO: use a message ?
                (newDashboard, dashboardCmd) = ReleaseDashboard.update (ReleaseDashboard.UserUpdate newUser) model.release_dashboard
            in
                (
                  { model | current_user = newUser, release_dashboard = newDashboard },
                  Cmd.batch [
                    Cmd.map UserMsg userCmd,
                    Cmd.map ReleaseDashboardMsg dashboardCmd
                  ]
                )

        HawkMsg hawkMsg ->
            -- Send msg to Hawk module
            let
                l = Debug.log "hawk MSG" hawkMsg
                hawkCmd = Hawk.update hawkMsg
            in
                (model, Cmd.map HawkMsg hawkCmd)


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
    , div [ class "collapse navbar-toggleable-sm navbar-collapse navbar-right" ]
          [ ul [ class "nav navbar-nav" ]
              (List.concat [
                  (viewNavDashboard model.release_dashboard),
                  [li [ class "nav-item" ] ( viewUser model )]
              ])
          ]
    ]

viewNavDashboard: ReleaseDashboard.Model -> List (Html Msg)
viewNavDashboard dashboard = 

  case dashboard.all_analysis of
    NotAsked -> [
      li [class "nav-item text-info"] [text "Initialising ..."]
    ]

    Loading -> [
      li [class "nav-item text-info"] [text "Loading ..."]
    ]

    Failure err -> [
      li [class "nav-item text-danger"] [text ("Error: " ++ toString err)]
    ]

    Success allAnalysis -> 
      (List.map viewNavAnalysis allAnalysis)

viewNavAnalysis: ReleaseDashboard.Analysis -> Html Msg
viewNavAnalysis analysis =
    li [class "nav-item"] [
      analysisLink analysis [class "btn btn-secondary"] [
        span [] [text (analysis.name ++ " ")],
        span [class "label label-primary"] [text (toString analysis.count)]
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
  div [] [
    nav [ id "navbar", class "navbar navbar-full navbar-light" ] [
      div [ class "container" ] ( viewNavBar model )
    ],
    div [ id "content" ] [
      case model.current_user of
        Just user ->
          div [class "container-fluid" ] [ viewPage model ]
        Nothing ->
          div [class "container"] [
            div [class "alert alert-warning"] [
              text "Please login first."
            ]
          ]
    ]
    , footer [ class "container" ] viewFooter
  ]


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch [ 
      Sub.map UserMsg (User.localstorage_get (User.LoggedIn)),
      Sub.map HawkMsg (Hawk.hawk_get (Hawk.BuiltHeader)) 
    ]
