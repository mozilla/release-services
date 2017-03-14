port module Example exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Encode as JsonEncode
import Json.Decode as JsonDecode
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
    | SetScopes (WebData String)
    | LoadScopes
    | SetRoles (WebData String)
    | LoadRoles
    | SetSecret (WebData String)
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
      scopes : WebData (List String)
    , roles : WebData (List Role)
    }


type alias Flags =
    { taskcluster : Maybe User.Credentials
    , bugzilla : Maybe Bugzilla.Credentials
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
            scopes = NotAsked
          , roles = NotAsked
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
            ( { model | scopes = Utils.decodeJsonString scopesDecoder response }
            , Cmd.none
            )

        SetRoles response ->
            ( { model | roles = Utils.decodeJsonString rolesDecoder response }
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
                            Hawk.Request "LoadScopes" "GET" url [] Http.emptyBody
                    in
                        ( model
                        , -- Extensions integration
                          -- This is how we do a request using Hawk
                          Cmd.map HawkRequest
                            (Hawk.send request user)
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
                            Hawk.Request "LoadRoles" "GET" url [] Http.emptyBody
                    in
                        ( model
                        , -- Extensions integration
                          -- This is how we do a request using Hawk
                          Cmd.map HawkRequest
                            (Hawk.send request user)
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
                                    , ( "expires", JsonEncode.string "2020-01-01T00:00:00.000Z" )
                                    ]
                                )

                        request =
                            Hawk.Request "WriteSecret" "PUT" url [] (Http.stringBody "application/json" payload)
                    in
                        ( model
                        , -- Extensions integration
                          -- This is how we do a request using Hawk
                          Cmd.map HawkRequest
                            (Hawk.send request user)
                        )

                Nothing ->
                    ( model, Cmd.none )


scopesDecoder : JsonDecode.Decoder (List String)
scopesDecoder =
    JsonDecode.at [ "scopes" ] (JsonDecode.list JsonDecode.string)


rolesDecoder : JsonDecode.Decoder (List Role)
rolesDecoder =
    JsonDecode.list
        (JsonDecode.map2 Role
            (JsonDecode.field "roleId" JsonDecode.string)
            (JsonDecode.field "scopes" (JsonDecode.list JsonDecode.string))
        )



-- Demo view


view : Model -> Html Msg
view model =
    div []
        [ h1 [] [ text "Taskcluster" ]
        , viewLogin model
        , h1 [] [ text "Hawk" ]
        , viewHawk model
        , h1 [] [ text "Bugzilla" ]
        , Html.map BugzillaMsg (Bugzilla.view model.bugzilla)
        ]


viewLogin : Model -> Html Msg
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


viewHawk : Model -> Html Msg
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
            [ case model.scopes of
                Success scopes ->
                    viewScopes scopes

                Failure err ->
                    div [ class "alert alert-danger" ] [ text ("Error:" ++ (toString err)) ]

                Loading ->
                    div [ class "alert alert-info" ] [ text "Loading scopes" ]

                NotAsked ->
                    div [ class "alert alert-info" ] [ text "Scopes Not loaded" ]
            , case model.roles of
                Success roles ->
                    div [] (List.map viewRole roles)

                Failure err ->
                    div [ class "alert alert-danger" ] [ text ("Error:" ++ (toString err)) ]

                Loading ->
                    div [ class "alert alert-info" ] [ text "Loading roles" ]

                NotAsked ->
                    div [ class "alert alert-info" ] [ text "Roles Not loaded" ]
            ]
        ]


viewScopes : List String -> Html msg
viewScopes scopes =
    ul [] (List.map (\s -> li [] [ text s ]) scopes)


viewRole : Role -> Html msg
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
                            |> Maybe.map
                                (\x ->
                                    x
                                        |> User.Logging
                                        |> UserMsg
                                )
                            |> Maybe.withDefault (LoadScopes)
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
