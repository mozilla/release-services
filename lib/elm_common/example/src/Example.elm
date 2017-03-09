port module Example exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Html.App
import Http
import Json.Encode as JsonEncode
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
    | SetSecret (RemoteData Http.RawError Http.Response)
    | WriteSecret



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


type alias Flags =
    { taskcluster : Maybe (User.Credentials)
    , bugzilla : Maybe (Bugzilla.Credentials)
    }


init : Flags -> ( Model, Cmd Msg )
init flags =
    let
        -- Extensions integration
        ( bz, bzCmd ) =
            Bugzilla.init "https://bugzilla-dev.allizom.org" flags.bugzilla

        ( user, userCmd ) =
            User.init flags.taskcluster
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

                        "WriteSecret" ->
                            Cmd.map SetSecret response

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

        SetSecret response ->
            let
                l =
                    Debug.log "Set secret !" response
            in
                ( model, Cmd.none )

        LoadScopes ->
            case model.user of
                Just user ->
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
                            (Hawk.send "LoadScopes" request user)
                        )

                Nothing ->
                    ( model, Cmd.none )

        LoadRoles ->
            case model.user of
                Just user ->
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
                            (Hawk.send "LoadRoles" request user)
                        )

                Nothing ->
                    ( model, Cmd.none )

        WriteSecret ->
            case model.user of
                Just user ->
                    let
                        -- Build Taskcluster http request
                        url =
                            "https://secrets.taskcluster.net/v1/secret/garbage/testElmCommon"

                        payload =
                            JsonEncode.encode 0
                                (JsonEncode.object
                                    [ ( "secret"
                                      , JsonEncode.object
                                            [ ( "secretKey", JsonEncode.string "secretValue" )
                                            , ( "test", JsonEncode.int 42 )
                                            ]
                                      )
                                    , ( "expires", JsonEncode.string "0" )
                                    ]
                                )

                        headers =
                            [ ( "Content-Type", "application/json" )
                            ]

                        request =
                            Http.Request "PUT" headers url (Http.string payload)
                    in
                        ( model
                        , -- Extensions integration
                          -- This is how we do a request using Hawk
                          Cmd.map HawkRequest
                            (Hawk.send "WriteSecret" request user)
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
        , viewLogin model
        , h1 [] [ text "Hawk" ]
        , viewHawk model
        , h1 [] [ text "Bugzilla" ]
        , Html.App.map BugzillaMsg (Bugzilla.view model.bugzilla)
        ]


viewLogin model =
    case model.user of
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
        [ case model.user of
            Just user ->
                p []
                    [ button [ onClick LoadScopes ] [ text "Request Taskcluster scopes" ]
                    , button [ onClick LoadRoles ] [ text "Request Taskcluster roles" ]
                    , button [ onClick WriteSecret ] [ text "Set Taskcluster secret garbage/testElmCommon" ]
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
