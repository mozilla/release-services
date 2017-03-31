module Main exposing (..)

import App
import App.Home
import App.Layout
import App.TreeStatus
import App.TreeStatus.Api
import App.TreeStatus.Types
import App.TryChooser
import App.UserScopes
import Hawk
import Html exposing (..)
import Navigation
import String
import TaskclusterLogin
import Time
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

        model =
            { history = [ location ]
            , route = route
            , docsUrl = flags.docsUrl
            , version = flags.version
            , user = flags.user
            , userScopes = App.UserScopes.init
            , trychooser = App.TryChooser.init
            , treestatus = App.TreeStatus.init flags.treestatusUrl
            }
    in
        initRoute model route


initRoute : App.Model -> App.Route -> ( App.Model, Cmd App.Msg )
initRoute model route =
    case route of
        App.NotFoundRoute ->
            model ! []

        App.HomeRoute ->
            { model
                | trychooser = App.TryChooser.init
                , treestatus =
                    App.TreeStatus.init model.treestatus.baseUrl
            }
                ! [ Utils.performMsg (App.UserScopesMsg App.UserScopes.FetchScopes) ]

        App.LoginRoute clientId accessToken certificate ->
            let
                -- TODO: parsing of the arguments should go into TaskclusterLogin.elm
                certificate_ =
                    case certificate of
                        Just text ->
                            TaskclusterLogin.decodeCertificate text
                                |> Result.toMaybe

                        Nothing ->
                            Nothing

                credentials =
                    case ( clientId, accessToken ) of
                        ( Just clientId_, Just accessToken_ ) ->
                            Just
                                (TaskclusterLogin.Credentials
                                    clientId_
                                    accessToken_
                                    certificate_
                                )

                        _ ->
                            Nothing

                loginCmd =
                    case credentials of
                        Just credentials_ ->
                            Utils.performMsg
                                (App.TaskclusterLoginMsg
                                    (TaskclusterLogin.Logging credentials_)
                                )

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

        App.TryChooserRoute ->
            model
                ! [ Utils.performMsg (App.TryChooserMsg App.TryChooser.Load)
                  , Utils.performMsg (App.UserScopesMsg App.UserScopes.FetchScopes)
                  ]

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
        App.Tick time ->
            if TaskclusterLogin.isCertificateExpired time model.user then
                update (App.TaskclusterLoginMsg TaskclusterLogin.Logout) model
            else
                ( model, Cmd.none )

        App.TaskclusterLoginMsg userMsg ->
            let
                ( newUser, userCmd ) =
                    TaskclusterLogin.update userMsg model.user
            in
                ( { model | user = newUser }
                , Cmd.map App.TaskclusterLoginMsg userCmd
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

        App.TryChooserMsg msg_ ->
            let
                ( newModel, newCmd ) =
                    App.TryChooser.update msg_ model.trychooser
            in
                ( { model | trychooser = newModel }
                , Cmd.map App.TryChooserMsg newCmd
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
            { request | id = (page ++ request.id) }
    in
        case user of
            Just user2 ->
                Hawk.send pagedRequest user2
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

        App.LoginRoute _ _ _ ->
            -- TODO: this should be already a view on TaskclusterLogin
            text "Logging you in ..."

        App.LogoutRoute ->
            -- TODO: this should be already a view on TaskclusterLogin
            text "Logging you out ..."

        App.TryChooserRoute ->
            Html.map App.TryChooserMsg (App.TryChooser.view model.trychooser)

        App.TreeStatusRoute route ->
            App.TreeStatus.view
                route
                model.userScopes.scopes
                model.treestatus
                |> Html.map App.TreeStatusMsg


subscriptions : App.Model -> Sub App.Msg
subscriptions model =
    Sub.batch
        [ TaskclusterLogin.subscriptions App.TaskclusterLoginMsg
        , Hawk.subscriptions App.HawkMsg
        , Time.every (50 * Time.second) App.Tick
        ]
