module Main exposing (..)

import App
import App.Home
import App.Layout
import App.TreeStatus
import App.TryChooser
import Hawk
import Hop
import Hop.Types
import Html
import Html
import Html.App
import Navigation
import Task
import TaskclusterLogin
import Utils


init : App.Flags -> ( App.Route, Hop.Types.Address ) -> ( App.Model, Cmd App.Msg )
init flags ( route, address ) =
    ( { route = route
      , address = address
      , docsUrl = flags.docsUrl
      , version = flags.version
      , user = flags.user
      , trychooser = App.TryChooser.init
      , treestatus = App.TreeStatus.init flags.treestatusUrl
      }
      -- XXX: weird way to trigger a Msg from init, there must be a nicer way
      -- triggering (App.NavigateTo route) ensures that .load function is called
    , Utils.performMsg (App.NavigateTo route)
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
                        --TODO:
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
            let
                newCmd =
                    Hop.outputFromPath App.hopConfig (App.pathFromRoute route)
                        |> Navigation.newUrl

                goHome =
                    App.NavigateTo App.HomeRoute

                login =
                    model.address.query
                        |> TaskclusterLogin.convertUrlQueryToUser
                        |> Maybe.map
                            (\x ->
                                x
                                    |> TaskclusterLogin.Logging
                                    |> App.TaskclusterLoginMsg
                            )
                        |> Maybe.withDefault goHome

                logout =
                    App.TaskclusterLoginMsg TaskclusterLogin.Logout
            in
                case route of
                    App.NotFoundRoute ->
                        ( model, newCmd )

                    App.HomeRoute ->
                        ( { model
                            | trychooser = App.TryChooser.init
                            , treestatus =
                                App.TreeStatus.init model.treestatus.baseUrl
                          }
                        , newCmd
                        )

                    App.LoginRoute ->
                        model
                            ! []
                            |> Utils.andThen update login
                            |> Utils.andThen update goHome

                    App.LogoutRoute ->
                        model
                            ! []
                            |> Utils.andThen update logout
                            |> Utils.andThen update goHome

                    App.TreeStatusRoute ->
                        App.TreeStatus.load App.TreeStatusMsg newCmd model

                    App.TryChooserRoute ->
                        App.TryChooser.load App.TryChooserMsg newCmd model

        App.TreeStatusMsg msg2 ->
            App.TreeStatus.update App.TreeStatusMsg msg2 model

        App.TryChooserMsg msg2 ->
            App.TryChooser.update App.TryChooserMsg msg2 model



--viewRoute : App.Model -> Html.Html App.Msg


viewRoute model =
    case model.route of
        App.NotFoundRoute ->
            App.Layout.viewNotFound model

        App.HomeRoute ->
            App.Home.view model

        App.LoginRoute ->
            -- TODO: this should be already a view on TaskclusterLogin
            Html.text "Logging you in ..."

        App.LogoutRoute ->
            -- TODO: this should be already a view on TaskclusterLogin
            Html.text "Logging you out ..."

        App.TryChooserRoute ->
            Html.App.map App.TryChooserMsg (App.TryChooser.view model.trychooser)

        App.TreeStatusRoute ->
            Html.App.map App.TreeStatusMsg (App.TreeStatus.view model.treestatus)


subscriptions : App.Model -> Sub App.Msg
subscriptions model =
    Sub.batch
        [ TaskclusterLogin.subscriptions App.TaskclusterLoginMsg
        , Hawk.subscriptions App.HawkMsg
        ]


main : Program App.Flags
main =
    Navigation.programWithFlags App.urlParser
        { init = init
        , view = App.Layout.view viewRoute
        , update = update
        , urlUpdate = App.urlUpdate
        , subscriptions = subscriptions
        }
