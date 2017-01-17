module Main exposing (..)

import App
import App.Home
import App.Layout
import App.TreeStatus
import App.TreeStatus.Api
import App.TreeStatus.Types
import App.TryChooser
import App.Types
import App.UserScopes
import Hawk
import Hop
import Hop.Types
import Html exposing (..)
import Html.App
import Html.Attributes exposing (..)
import Http
import Navigation
import String
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
      , userScopes = App.UserScopes.init
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
                    if String.startsWith "TreeStatus" route then
                        route
                            |> String.dropLeft (String.length "TreeStatus")
                            |> App.TreeStatus.Api.hawkResponse response
                            |> Cmd.map App.TreeStatusMsg
                    else if String.startsWith "UserScopes" route then
                        route
                            |> String.dropLeft (String.length "UserScopes")
                            |> App.UserScopes.hawkResponse response
                            |> Cmd.map App.UserScopesMsg
                    else
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
                    Hop.outputFromPath App.Types.hopConfig (App.reverse route)
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

                fetchUserScopes =
                    App.UserScopesMsg App.UserScopes.FetchScopes
            in
                case route of
                    App.NotFoundRoute ->
                        ( model, newCmd )

                    App.HomeRoute ->
                        { model
                            | trychooser = App.TryChooser.init
                            , treestatus =
                                App.TreeStatus.init model.treestatus.baseUrl
                        }
                            ! [ newCmd ]
                            |> Utils.andThen update fetchUserScopes

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

                    App.TryChooserRoute ->
                        update (App.TryChooserMsg App.TryChooser.Load) model
                            |> Utils.andThen update fetchUserScopes

                    App.TreeStatusRoute route ->
                        update (App.TreeStatusMsg (App.TreeStatus.Types.NavigateTo route)) model
                            |> Utils.andThen update fetchUserScopes

        App.UserScopesMsg msg2 ->
            let
                ( newModel, newCmd, hawkCmd ) =
                    App.UserScopes.update msg2 model.userScopes
            in
                ( { model | userScopes = newModel }
                , hawkCmd
                    |> Maybe.map (\x -> [ hawkSend model.user "UserScopes" x.route x.request ])
                    |> Maybe.withDefault []
                    |> List.append [ Cmd.map App.UserScopesMsg newCmd ]
                    |> Cmd.batch
                )

        App.TryChooserMsg msg2 ->
            let
                ( newModel, newCmd ) =
                    App.TryChooser.update msg2 model.trychooser
            in
                ( { model | trychooser = newModel }
                , Cmd.map App.TryChooserMsg newCmd
                )

        App.TreeStatusMsg msg2 ->
            let
                route =
                    case model.route of
                        App.TreeStatusRoute x ->
                            x

                        _ ->
                            App.TreeStatus.Types.TreesRoute

                ( newModel, newCmd, hawkCmd ) =
                    App.TreeStatus.update route msg2 model.treestatus
            in
                ( { model | treestatus = newModel }
                , hawkCmd
                    |> Maybe.map (\x -> [ hawkSend model.user "TreeStatus" x.route x.request ])
                    |> Maybe.withDefault []
                    |> List.append [ Cmd.map App.TreeStatusMsg newCmd ]
                    |> Cmd.batch
                )


hawkSend :
    TaskclusterLogin.Model
    -> String
    -> String
    -> Http.Request
    -> Cmd App.Msg
hawkSend user page route request =
    case user of
        Just user2 ->
            Hawk.send (page ++ route) request user2
                |> Cmd.map App.HawkMsg

        Nothing ->
            Cmd.none


viewRoute : App.Model -> Html App.Msg
viewRoute model =
    case model.route of
        App.NotFoundRoute ->
            App.Layout.viewNotFound model

        App.HomeRoute ->
            App.Home.view model

        App.LoginRoute ->
            -- TODO: this should be already a view on TaskclusterLogin
            text "Logging you in ..."

        App.LogoutRoute ->
            -- TODO: this should be already a view on TaskclusterLogin
            text "Logging you out ..."

        App.TryChooserRoute ->
            Html.App.map App.TryChooserMsg (App.TryChooser.view model.trychooser)

        App.TreeStatusRoute route ->
            App.TreeStatus.view
                route
                model.userScopes.scopes
                model.treestatus
                |> Html.App.map App.TreeStatusMsg


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
