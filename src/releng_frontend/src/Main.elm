module Main exposing (..)

import App
import App.Home
import App.Layout
import App.TreeStatus
import Hawk
import Html
import Html.App
import Navigation
import RouteUrl
import RouteUrl.Builder
import TaskclusterLogin


delta2url : App.Model -> App.Model -> Maybe RouteUrl.UrlChange
delta2url previous current =
    let
        url =
            case current.route of
                App.HomeRoute ->
                    Maybe.map
                        (RouteUrl.Builder.prependToPath [])
                        (Just RouteUrl.Builder.builder)

                App.TreeStatusRoute ->
                    Maybe.map
                        (RouteUrl.Builder.prependToPath [ "treestatus" ])
                        (Just RouteUrl.Builder.builder)

                App.NotFoundRoute ->
                    Maybe.map
                        (RouteUrl.Builder.prependToPath [ "404" ])
                        (Just RouteUrl.Builder.builder)
    in
        Maybe.map RouteUrl.Builder.toUrlChange url


location2messages : Navigation.Location -> List App.Msg
location2messages location =
    let
        builder =
            RouteUrl.Builder.fromUrl location.href
    in
        case RouteUrl.Builder.path RouteUrl.Builder.builder of
            first :: rest ->
                -- Extensions integration
                case Debug.log "URL" first of
                    "login" ->
                        [ RouteUrl.Builder.query RouteUrl.Builder.builder
                            |> TaskclusterLogin.convertUrlQueryToUser
                            |> TaskclusterLogin.Logging
                            |> App.TaskclusterLoginMsg
                        ]

                    "treestatus" ->
                        [ App.NavigateTo App.TreeStatusRoute ]

                    _ ->
                        [ App.NavigateTo App.NotFoundRoute ]

            _ ->
                [ App.NavigateTo App.HomeRoute ]


init : App.Flags -> ( App.Model, Cmd App.Msg )
init flags =
    ( { user = flags.user
      , route = App.HomeRoute
      , treestatus = App.TreeStatus.init flags.treestatusUrl
      , docsUrl = flags.docsUrl
      , version = flags.version
      }
    , Cmd.none
    )


update : App.Msg -> App.Model -> ( App.Model, Cmd App.Msg )
update msg model =
    case msg of
        App.TaskclusterLoginMsg userMsg ->
            let
                ( newUser, userCmd ) =
                    TaskclusterLogin.update userMsg model.user
            in
                ( { model | user = newUser }
                , Cmd.map App.TaskclusterLoginMsg userCmd
                )

        App.HawkMsg hawkMsg ->
            let
                ( requestId, cmd, response ) =
                    Hawk.update hawkMsg

                routeHawkMsg route =
                    case route of
                        --TOD:
                        --"LoadScopes" ->
                        --    Cmd.map SetScopes response
                        _ ->
                            Cmd.none

                appCmd =
                    requestId
                        |> Maybe.map routeHawkMsg
                        |> Maybe.withDefault Cmd.none
            in
                ( model
                , Cmd.batch
                    [ Cmd.map App.HawkMsg cmd
                    , appCmd
                    ]
                )

        App.NavigateTo route ->
            case route of
                App.HomeRoute ->
                    ( { model
                        | route = route
                        , treestatus = App.TreeStatus.init model.treestatus.baseUrl
                      }
                    , Cmd.none
                    )

                App.TreeStatusRoute ->
                    let
                        treestatus =
                            App.TreeStatus.load model.treestatus
                    in
                        ( { model
                            | route = route
                            , treestatus = fst treestatus
                          }
                        , Cmd.map App.TreeStatusMsg <| snd treestatus
                        )

                _ ->
                    ( { model | route = route }
                    , Cmd.none
                    )

        App.TreeStatusMsg treestatusMsg ->
            let
                ( newModel, newCmd ) =
                    App.TreeStatus.update treestatusMsg model.treestatus
            in
                ( { model | treestatus = newModel }
                , Cmd.map App.TreeStatusMsg newCmd
                )


viewRoute : App.Model -> Html.Html App.Msg
viewRoute model =
    case model.route of
        App.NotFoundRoute ->
            App.Layout.viewNotFound model

        App.HomeRoute ->
            App.Home.view model

        App.TreeStatusRoute ->
            Html.App.map App.TreeStatusMsg (App.TreeStatus.view model.treestatus)


subscriptions : App.Model -> Sub App.Msg
subscriptions model =
    Sub.batch
        [ Sub.map App.TaskclusterLoginMsg <|
            TaskclusterLogin.taskclusterlogin_get TaskclusterLogin.Logged
        , Sub.map App.HawkMsg <|
            Hawk.hawk_send_request Hawk.SendRequest
        ]


main : Program App.Flags
main =
    RouteUrl.programWithFlags
        { delta2url = delta2url
        , location2messages = location2messages
        , init = init
        , update = update
        , view = App.Layout.view viewRoute
        , subscriptions = subscriptions
        }
