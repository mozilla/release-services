port module App exposing (..)

import Dict exposing ( Dict )
import Html exposing ( Html, div, nav, button, text, a, ul, li, footer, hr, span, strong, p )
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
  current_user : User.Model,
  backend_dashboard_url: String
}

type Msg
    = ShowPage Page
    | UserMsg User.Msg -- triggers fetch all analysis
    | HawkMsg User.Msg -- update current hawk header
    | ReleaseDashboardMsg ReleaseDashboard.Msg
    | FetchAnalysis ReleaseDashboard.Analysis

type alias Flags = {
    backend_dashboard_url : String
}

pageLink page attributes =
    eventLink (ShowPage page) attributes

analysisLink analysis attributes =
    eventLink (FetchAnalysis analysis) attributes


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
                              |> User.convertUrlQueryToUser
                              |> User.LoggingIn
                              |> UserMsg
                        , ShowPage Home
                        ]
                    "bugzilla" ->
                        [ 
                          Builder.query builder
                              |> User.convertUrlQueryToBugzillaCreds
                              |> User.ReceivedBugzillaCreds
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
        (user, userCmd) = User.init flags.backend_dashboard_url
    in
    (
      {
         release_dashboard = dashboard,
         current_page = Home,
         current_user = user,
         backend_dashboard_url = flags.backend_dashboard_url
      },
      -- Follow through with sub parts init
      Cmd.batch [
        Cmd.map ReleaseDashboardMsg newCmd,
        Cmd.map UserMsg userCmd
      ]
    )


update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        ShowPage page ->
            ( { model | current_page = page }, Cmd.none )

        FetchAnalysis analysis ->
            let
                (newModel, newUser, newCmd) = ReleaseDashboard.update (ReleaseDashboard.FetchAnalysis analysis) model.release_dashboard model.current_user
            in
                (
                  { model | release_dashboard = newModel, current_page = ReleaseDashboard, current_user = newUser },
                  Cmd.map ReleaseDashboardMsg newCmd
                )

        ReleaseDashboardMsg msg' ->
            let
                (newModel, newUser, newCmd) = ReleaseDashboard.update msg' model.release_dashboard model.current_user
            in
                (
                  { model | release_dashboard = newModel, current_user = newUser },
                  Cmd.map ReleaseDashboardMsg newCmd
                )

        UserMsg usermsg -> 
          case usermsg of
            User.LoggedIn _ -> 
              let
                -- Update current user
                (newUser, _, userCmd) = User.update usermsg model.current_user

                -- Reload all analysis on an user update
                (newDashboard, newUser', newCmd) = ReleaseDashboard.update ReleaseDashboard.FetchAllAnalysis model.release_dashboard newUser
              in
                (
                  { model | current_user = newUser', release_dashboard = newDashboard },
                  Cmd.batch [
                    Cmd.map UserMsg userCmd,
                    Cmd.map ReleaseDashboardMsg newCmd
                  ]
                )

            _ ->
              let
                -- Just Update current user
                (newUser, _, userCmd) = User.update usermsg model.current_user
              in
                (
                  { model | current_user = newUser },
                  Cmd.map UserMsg userCmd
                )

        HawkMsg usermsg -> 
            let
              -- Update current user
              (newUser, workflows, userCmd) = User.update usermsg model.current_user
            in
              List.foldr test ({model | current_user = newUser}, Cmd.map UserMsg userCmd) workflows

test : User.Hawk -> (Model, Cmd Msg) -> (Model, Cmd Msg)
test workflow full =
  let
    (model, cmd) = full
    -- Send message to sub parts to process requests
    (dashboard, newUser, dashboardCmd) = ReleaseDashboard.update (ReleaseDashboard.ProcessWorkflow workflow) model.release_dashboard model.current_user
    (newUser', _, userCmd) = User.update (User.ProcessWorkflow workflow) newUser
  in
    (
      { model | current_user = newUser', release_dashboard = dashboard },
      Cmd.batch [
        cmd,
        Cmd.map UserMsg userCmd,
        Cmd.map ReleaseDashboardMsg dashboardCmd
      ]
    )
    

viewPage model =
    case model.current_page of
        Home ->
            Home.view model
        ReleaseDashboard ->
            Html.App.map ReleaseDashboardMsg (ReleaseDashboard.view model.release_dashboard)


viewDropdown title pages =
    [ div [ class "dropdown" ]
          [ a [ class "nav-link dropdown-toggle btn btn-primary"
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

viewLogin =
  let
      loginTarget =
          Just ( "/login"
               , "RelengAPI is a collection of Release Engineering services"
               )
      loginUrl =
          { url = "https://login.taskcluster.net"
          , target = loginTarget
          , targetName = "target"
          }
      loginMsg = UserMsg <| User.Login loginUrl
  in
      [ eventLink loginMsg [ class "nav-link" ] [ text "Login TaskCluster" ]
      ]

viewLoginBugzilla =
  let
      loginTarget =
          Just ( "/bugzilla"
               , "RelengAPI is a collection of Release Engineering services"
               )
      loginUrl =
          { url = "https://bugzilla.mozilla.org/auth.cgi"
          , target = loginTarget
          , targetName = "callback"
          }
      loginMsg = UserMsg <| User.Login loginUrl
  in
      [ eventLink loginMsg [ class "nav-link" ] [ text "Login Bugzilla" ]
      ]

viewUser model =
  case model.current_user.user of
    Just user ->
      viewDropdown user.clientId [
        -- Link to TC manager
        a [ class "dropdown-item",
            href "https://tools.taskcluster.net/credentials",
            target "_blank"
        ] [ text "Manage credentials" ],

        -- Display bugzilla status
        viewBugzillaAuth model.current_user,

        -- Logout from TC
        div [class "dropdown-divider"] [],
        eventLink (UserMsg User.Logout) [ class "dropdown-item" ] [ text "Logout" ]
      ]

    Nothing -> viewLogin


viewNavBar model =
    [ button [ class "navbar-toggler hidden-md-up"
             , type' "button"
             , attribute "data-toggle" "collapse"
             , attribute "data-target" ".navbar-collapse"
             , attribute "aria-controls" "navbar-header"
             ]
             [ text "Menu" ]
    , pageLink Home [ class "navbar-brand" ]
                    [ text "RelengAPI" ]
    , div [ class "collapse navbar-toggleable-sm navbar-collapse navbar-right" ]
          [ ul [ class "nav navbar-nav" ]
              (List.concat [
                  (viewNavDashboard model.release_dashboard),
                  [li [ class "nav-item pull-xs-right" ] ( viewUser model )]
              ])
          ]
    ]

viewNavDashboard: ReleaseDashboard.Model -> List (Html Msg)
viewNavDashboard dashboard = 

  case dashboard.all_analysis of
    NotAsked -> []

    Loading -> [
      li [class "nav-item text-info"] [text "Loading Bugs analysis..."] 
    ]

    Failure err -> [
      li [class "nav-item text-danger"] [text ("Error: " ++ toString err)]
    ]

    Success allAnalysis -> 
      (List.map viewNavAnalysis allAnalysis)

viewNavAnalysis: ReleaseDashboard.Analysis -> Html Msg
viewNavAnalysis analysis =
    li [class "nav-item"] [
      analysisLink analysis [class "nav-link"] [
        span [] [text (analysis.name ++ " ")],
        if analysis.count > 0 then
          span [class "label label-primary"] [text (toString analysis.count)]
        else
          span [class "label label-success"] [text (toString analysis.count)]
      ]
    ]

viewBugzillaAuth: User.Model -> Html Msg
viewBugzillaAuth user = 

  case user.bugzilla_auth of
    NotAsked ->
      a [class "dropdown-item text-info disabled"] [text "Init. Bugzilla auth"]

    Loading ->
      a [class "dropdown-item text-info disabled"] [text "Loading Bugzilla auth."]

    Failure err ->
      a [class "dropdown-item text-danger"] [
        span [] [text ("Error while loading bugzilla auth: " ++ toString err)],
        span []  viewLoginBugzilla
      ]  

    Success auth -> 
      if auth.authenticated then
        a [class "dropdown-item text-success disabled"] [text ("Bugzilla: " ++ auth.message)]

      else
        a [class "dropdown-item text-danger"] [
          span [] [text ("Error with your bugzilla auth: " ++ auth.message)],
          span [] viewLoginBugzilla
        ] 

viewFooter =
  footer [] [
    ul [] [
      li [] [ a [ href "https://github.com/mozilla-releng/services" ] [ text "Github" ]],
      li [] [ a [ href "#" ] [ text "Contribute" ]],
      li [] [ a [ href "#" ] [ text "Contact" ]]
      -- TODO: add version / revision
    ]
  ]

view : Model -> Html Msg
view model =
  div [] [
    nav [ id "navbar", class "navbar navbar-full navbar-dark bg-inverse" ] [
      div [ class "container-fluid" ] ( viewNavBar model )
    ],
    div [ id "content" ] [
      case model.current_user.user of
        Just user ->
          div [class "container-fluid" ] [ viewPage model ]
        Nothing ->
          div [class "container"] [
            div [class "alert alert-warning"] [
              text "Please login first."
            ]
          ]
    ],
    viewFooter
  ]


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch [ 
      Sub.map UserMsg (User.localstorage_get (User.LoggedIn)),
      Sub.map HawkMsg (User.hawk_get (User.BuiltHawkHeader)) 
    ]
