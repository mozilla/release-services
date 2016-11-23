port module Example exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Html.App
import Http
import Json.Decode as JsonDecode exposing ((:=))
import RouteUrl exposing (UrlChange)
import RouteUrl.Builder as Builder exposing (Builder, builder, replacePath)
import RemoteData exposing (WebData, RemoteData(..))
import Navigation exposing (Location)
import BugzillaLogin as Bugzilla
import TaskclusterLogin as User
import Hawk
import Utils


type
    Msg
    -- Extensions integration
    = BugzillaMsg Bugzilla.Msg
    | UserMsg User.Msg
    | HawkRequest Hawk.Msg
      -- App code
    | SetScopes (RemoteData Http.RawError Http.Response)
    | LoadScopes
    | SetRoles (RemoteData Http.RawError Http.Response)
    | LoadRoles



-- triggers HawkRequest


type alias Role =
    { roleId : String
    , scopes : List String
    }


type alias Model =
    { -- Extensions integration
      user : User.Model
    , bugzilla : Bugzilla.Model
    , -- App code
      scopes : List String
    , roles : List Role
    }


init : ( Model, Cmd Msg )
init =
    let
        -- Extensions integration
        ( bz, bzCmd ) =
            Bugzilla.init "https://bugzilla-dev.allizom.org"

        ( user, userCmd ) =
            User.init
    in
        ( { -- Extensions integration
            bugzilla = bz
          , user = user
          , -- App code
            scopes = []
          , roles = []
          }
        , -- Follow through with sub parts init
          Cmd.batch
            [ -- Extensions integration
              Cmd.map BugzillaMsg bzCmd
            , Cmd.map UserMsg userCmd
            ]
        )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        -- Extensions integration
        BugzillaMsg bzMsg ->
            let
                ( newBz, bzCmd ) =
                    Bugzilla.update bzMsg model.bugzilla
            in
                ( { model | bugzilla = newBz }
                , Cmd.map BugzillaMsg bzCmd
                )

        UserMsg userMsg ->
            let
                ( newUser, userCmd ) =
                    User.update userMsg model.user
            in
                ( { model | user = newUser }
                , Cmd.map UserMsg userCmd
                )

        HawkRequest hawkMsg ->
            let
                ( requestId, cmd, response ) =
                    Hawk.update hawkMsg

                routeHawkRequest route =
                    case route of
                        "LoadScopes" ->
                            Cmd.map SetScopes response

                        "LoadRoles" ->
                            Cmd.map SetRoles response

                        _ ->
                            Cmd.none

                appCmd =
                    requestId
                        |> Maybe.map routeHawkRequest
                        |> Maybe.withDefault Cmd.none
            in
                ( model
                , Cmd.batch
                    [ Cmd.map HawkRequest cmd
                    , appCmd
                    ]
                )

        -- App specific
        SetScopes response ->
            ( response
                |> RemoteData.map
                    (\r -> { model | scopes = Utils.decodeResponse scopesDecoder [] r })
                |> RemoteData.withDefault model
            , Cmd.none
            )

        SetRoles response ->
            ( response
                |> RemoteData.map
                    (\r -> { model | roles = Utils.decodeResponse rolesDecoder [] r })
                |> RemoteData.withDefault model
            , Cmd.none
            )

        LoadScopes ->
            case model.user.credentials of
                Just credentials ->
                    let
                        -- Build Taskcluster http request
                        url =
                            "https://auth.taskcluster.net/v1/scopes/current"

                        request =
                            Http.Request "GET" [] url Http.empty
                    in
                        ( model
                        , -- Extensions integration
                          -- This is how we do a request using Hawk
                          Cmd.map HawkRequest
                            (Hawk.send "LoadScopes" request credentials)
                        )

                Nothing ->
                    ( model, Cmd.none )

        -- App specific
        LoadRoles ->
            case model.user.credentials of
                Just credentials ->
                    let
                        -- Build Taskcluster http request
                        url =
                            "https://auth.taskcluster.net/v1/roles"

                        request =
                            Http.Request "GET" [] url Http.empty
                    in
                        ( model
                        , -- Extensions integration
                          -- This is how we do a request using Hawk
                          Cmd.map HawkRequest
                            (Hawk.send "LoadRoles" request credentials)
                        )

                Nothing ->
                    ( model, Cmd.none )


scopesDecoder =
    JsonDecode.at [ "scopes" ] (JsonDecode.list JsonDecode.string)


rolesDecoder =
    JsonDecode.list
        (JsonDecode.object2 Role
            ("roleId" := JsonDecode.string)
            ("scopes" := JsonDecode.list JsonDecode.string)
        )



-- Demo view


view model =
    div []
        [ h1 [] [ text "Taskcluster" ]
        , viewLogin model.user
        , h1 [] [ text "Hawk" ]
        , viewHawk model
        , h1 [] [ text "Bugzilla" ]
        , Html.App.map BugzillaMsg (Bugzilla.view model.bugzilla)
        ]


viewLogin model =
    case model.credentials of
        Just user ->
            div [] [ text ("Logged in as " ++ user.clientId) ]

        Nothing ->
            div []
                [ a
                    [ Utils.onClick
                        (User.redirectToLogin
                            UserMsg
                            "/login"
                            "Uplift dashboard helps Mozilla Release Management team in their workflow."
                        )
                    , href "#"
                    , class "nav-link"
                    ]
                    [ text "Login TaskCluster" ]
                ]


viewHawk model =
    div []
        [ case model.user.credentials of
            Just credentials ->
                p []
                    [ button [ onClick LoadScopes ] [ text "Request Taskcluster scopes" ]
                    , button [ onClick LoadRoles ] [ text "Request Taskcluster roles" ]
                    ]

            Nothing ->
                span [ class "text-warning" ] [ text "Login on Taskcluster first." ]
        , div []
            [ viewScopes model.scopes
            , div [] (List.map viewRole model.roles)
            ]
        ]


viewScopes scopes =
    ul [] (List.map (\s -> li [] [ text s ]) scopes)


viewRole role =
    div []
        [ h5 [] [ text ("Role: " ++ role.roleId) ]
        , viewScopes role.scopes
        ]



-- Empty Routing


location2messages : Location -> List Msg
location2messages location =
    let
        builder =
            Builder.fromUrl location.href
    in
        case Builder.path builder of
            first :: rest ->
                -- Extensions integration
                case first of
                    "login" ->
                        [ Builder.query builder
                            |> User.convertUrlQueryToUser
                            |> User.Logging
                            |> UserMsg
                        ]

                    _ ->
                        []

            _ ->
                []


delta2url : Model -> Model -> Maybe UrlChange
delta2url previous current =
    Nothing



-- Subscriptions


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ -- Extensions integration
          Sub.map BugzillaMsg (Bugzilla.bugzillalogin_get (Bugzilla.Logged))
        , Sub.map UserMsg (User.taskclusterlogin_get (User.Logged))
        , Sub.map HawkRequest (Hawk.hawk_send_request (Hawk.SendRequest))
        ]
