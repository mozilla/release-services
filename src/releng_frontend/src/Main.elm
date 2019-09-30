module Main exposing (..)

import App
import App.Home
import App.Layout
import App.Tokens
import App.ToolTool
import App.TreeStatus
import App.TreeStatus.Api
import App.TreeStatus.Types
import App.UserScopes
import Hawk
import Html exposing (..)
import Navigation
import String
import TaskclusterLogin
import Utils


main : Program App.Flags App.Model App.Msg
main =
    Navigation.programWithFlags App.UrlChange
        { init = init
        , view = App.Layout.view viewRoute
        , update = update
        , subscriptions = subscriptions
        }


init : App.Flags -> Navigation.Location -> ( App.Model, Cmd App.Msg )
init flags location =
    let
        route =
            App.parseLocation location

        ( user, userCmd ) =
            TaskclusterLogin.init flags.treestatusUrl flags.auth0

        model =
            { history = [ location ]
            , route = route
            , docsUrl = flags.docsUrl
            , version = flags.version
            , user = user
            , userScopes = App.UserScopes.init
            , tokens = App.Tokens.init
            , tooltool = App.ToolTool.init
            , treestatus = App.TreeStatus.init flags.treestatusUrl
            }

        ( model_, appCmd ) =
            initRoute model route
    in
    ( model_
    , Cmd.batch
        [ appCmd
        , Cmd.map App.TaskclusterLoginMsg userCmd
        ]
    )


initRoute : App.Model -> App.Route -> ( App.Model, Cmd App.Msg )
initRoute model route =
    case route of
        App.NotFoundRoute ->
            model ! []

        App.HomeRoute ->
            { model
                | tokens = App.Tokens.init
                , tooltool = App.ToolTool.init
                , treestatus =
                    App.TreeStatus.init model.treestatus.baseUrl
            }
                ! [ Utils.performMsg (App.UserScopesMsg App.UserScopes.FetchScopes) ]

        App.LoginRoute code state ->
            let
                loginCmd =
                    case TaskclusterLogin.convertUrlParametersToCode code state of
                        Just code_ ->
                            TaskclusterLogin.Logging code_
                                |> App.TaskclusterLoginMsg
                                |> Utils.performMsg

                        Nothing ->
                            Cmd.none
            in
            model
                ! [ loginCmd
                  , App.navigateTo App.HomeRoute
                  ]

        App.LogoutRoute ->
            model
                ! [ Utils.performMsg (App.TaskclusterLoginMsg TaskclusterLogin.Logout)

                  -- TODO: we should be redirecting to the url that we were loging in from
                  , Utils.performMsg (App.NavigateTo App.HomeRoute)
                  ]

        App.TokensRoute ->
            model ! []

        App.ToolToolRoute ->
            model ! []

        App.TreeStatusRoute route ->
            model
                ! [ Utils.performMsg (App.TreeStatusMsg (App.TreeStatus.Types.NavigateTo route))
                  , Utils.performMsg (App.UserScopesMsg App.UserScopes.FetchScopes)
                  ]


update : App.Msg -> App.Model -> ( App.Model, Cmd App.Msg )
update msg model =
    case msg of
        --
        -- ROUTING
        --
        App.UrlChange location ->
            { model
                | history = location :: model.history
                , route = App.parseLocation location
            }
                ! []

        App.NavigateTo route ->
            let
                ( newModel, newCmd ) =
                    initRoute model route
            in
            ( newModel
            , Cmd.batch
                [ App.navigateTo route
                , newCmd
                ]
            )

        --
        -- LOGIN / LOGOUT
        --
        App.TaskclusterLoginMsg userMsg ->
            let
                ( newUser, userCmd ) =
                    TaskclusterLogin.update userMsg model.user

                fetchScopes =
                    case userMsg of
                        TaskclusterLogin.LoadedTaskclusterCredentials response ->
                            [ Utils.performMsg (App.UserScopesMsg App.UserScopes.FetchScopes) ]

                        _ ->
                            []
            in
            ( { model | user = newUser }
            , [ Cmd.map App.TaskclusterLoginMsg userCmd ]
                |> List.append fetchScopes
                |> Cmd.batch
            )

        --
        -- HAWK REQUESTS
        --
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

        App.UserScopesMsg msg_ ->
            let
                ( newModel, newCmd, hawkCmd ) =
                    App.UserScopes.update msg_ model.userScopes
            in
            ( { model | userScopes = newModel }
            , hawkCmd
                |> Maybe.map (\req -> [ hawkSend model.user "UserScopes" req ])
                |> Maybe.withDefault []
                |> List.append [ Cmd.map App.UserScopesMsg newCmd ]
                |> Cmd.batch
            )

        App.TokensMsg msg_ ->
            let
                ( newModel, newCmd ) =
                    App.Tokens.update msg_ model.tokens
            in
            ( { model | tokens = newModel }
            , Cmd.map App.TokensMsg newCmd
            )

        App.ToolToolMsg msg_ ->
            let
                ( newModel, newCmd ) =
                    App.ToolTool.update msg_ model.tooltool
            in
            ( { model | tooltool = newModel }
            , Cmd.map App.ToolToolMsg newCmd
            )

        App.TreeStatusMsg msg_ ->
            let
                route =
                    case model.route of
                        App.TreeStatusRoute x ->
                            x

                        _ ->
                            App.TreeStatus.Types.ShowTreesRoute

                ( newModel, newCmd, hawkCmd ) =
                    App.TreeStatus.update route msg_ model.treestatus
            in
            ( { model | treestatus = newModel }
            , hawkCmd
                |> Maybe.map (\req -> [ hawkSend model.user "TreeStatus" req ])
                |> Maybe.withDefault []
                |> List.append [ Cmd.map App.TreeStatusMsg newCmd ]
                |> Cmd.batch
            )


hawkSend :
    TaskclusterLogin.Model
    -> String
    -> Hawk.Request
    -> Cmd App.Msg
hawkSend user page request =
    let
        pagedRequest =
            { request | id = page ++ request.id }
    in
    case user.credentials of
        Just credentials ->
            Hawk.send pagedRequest credentials
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

        App.LoginRoute _ _ ->
            -- TODO: this should be already a view on TaskclusterLogin
            text "Logging you in ..."

        App.LogoutRoute ->
            -- TODO: this should be already a view on TaskclusterLogin
            text "Logging you out ..."

        App.TokensRoute ->
            Html.map App.TokensMsg (App.Tokens.view model.tokens)

        App.ToolToolRoute ->
            Html.map App.ToolToolMsg (App.ToolTool.view model.tooltool)

        App.TreeStatusRoute route ->
            App.TreeStatus.view
                route
                model.user
                model.userScopes
                model.treestatus
                |> Html.map App.TreeStatusMsg


subscriptions : App.Model -> Sub App.Msg
subscriptions model =
    Sub.batch
        [ TaskclusterLogin.subscriptions App.TaskclusterLoginMsg
        , Hawk.subscriptions App.HawkMsg
        ]
