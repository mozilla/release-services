port module TaskclusterLogin exposing (..)

import Dict exposing (Dict)
import Json.Decode as JsonDecode exposing (Decoder)
import Json.Encode as JsonEncode
import Maybe
import Redirect
import Http
import String
import Task
import Date
import Time exposing (Time)


-- Auth0 code to exchange against token


type alias Code =
    { code : String
    , state : String
    }



-- Auth0 tokens


type alias Tokens =
    { expires : Int
    , access_token : String
    , id_token : String
    }



-- Taskcluster credentials


type alias Credentials =
    { clientId : String
    , accessToken : String
    , certificate : Maybe String
    , expires : Float
    }


type alias Model =
    { code : Maybe Code
    , tokens : Maybe Tokens
    , credentials : Maybe Credentials
    , backend_url : String
    }


type Msg
    = Login
    | LoginRedirect (Result Http.Error String)
    | Logging Code
    | ExchangedTokens (Result Http.Error Tokens)
    | Logged (Maybe Tokens)
    | Logout
    | CheckTaskclusterCredentials Time
    | LoadedTaskclusterCredentials (Result Http.Error Credentials)


init : String -> Maybe Tokens -> ( Model, Cmd Msg )
init backend_url tokens =
    let
        model =
            { code = Nothing
            , tokens = tokens
            , credentials = Nothing
            , -- TODO : switch to tokens ?
              backend_url = backend_url
            }
    in
        ( model
        , Cmd.batch
            [ loadTaskclusterCredentials model
            , Task.perform CheckTaskclusterCredentials Time.now
            ]
        )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Login ->
            -- Request new login url
            let
                request =
                    Http.get (model.backend_url ++ "/auth0/login") JsonDecode.string
            in
                ( model, Http.send LoginRedirect request )

        LoginRedirect response ->
            -- Redirect user to login url
            case response of
                Ok url ->
                    let
                        redirection =
                            { url = url
                            , target = Nothing
                            , targetName = ""
                            }
                    in
                        ( model, Redirect.redirect redirection )

                Err error ->
                    -- TODO: display error ?
                    ( model, Cmd.none )

        Logging code ->
            let
                payload =
                    JsonEncode.object
                        [ ( "code", JsonEncode.string code.code )
                        , ( "state", JsonEncode.string code.state )
                        ]

                request =
                    Http.request
                        { method = "POST"
                        , headers = []
                        , url = (model.backend_url ++ "/auth0/check")
                        , body = Http.jsonBody payload
                        , expect = Http.expectJson decodeTokens
                        , timeout = Nothing
                        , withCredentials = False
                        }
            in
                -- Exchange code for tokens through backend
                ( model, Http.send ExchangedTokens request )

        ExchangedTokens response ->
            -- Received tokens from backend
            -- Store in localstorage
            case response of
                Ok tokens ->
                    let
                        x =
                            Debug.log "tokens" tokens
                    in
                        ( { model | tokens = Just tokens }, auth_set tokens )

                Err error ->
                    -- TODO: display error ?
                    ( model, Cmd.none )

        Logged tokens ->
            let
                model_ =
                    { model | tokens = tokens }
            in
                ( model_, loadTaskclusterCredentials model_ )

        Logout ->
            ( model, auth_remove True )

        CheckTaskclusterCredentials time ->
            -- Renew automatically certificate
            if isCertificateExpired time model.credentials then
                ( model, loadTaskclusterCredentials model )
            else
                ( model, Cmd.none )

        LoadedTaskclusterCredentials response ->
            case response of
                Ok credentials ->
                    ( { model | credentials = Just credentials }, Cmd.none )

                Err error ->
                    ( { model | credentials = Nothing }, Cmd.none )


loadTaskclusterCredentials : Model -> Cmd Msg
loadTaskclusterCredentials model =
    case model.tokens of
        Just tokens ->
            let
                url =
                    "https://login.taskcluster.net/v1/oidc-credentials/mozilla-auth0"

                request =
                    Http.request
                        { method = "GET"
                        , headers =
                            [ Http.header "Authorization" ("Bearer " ++ tokens.access_token)
                            ]
                        , url = url
                        , body = Http.emptyBody
                        , expect = Http.expectJson decodeTaskclusterCredentials
                        , timeout = Nothing
                        , withCredentials = False
                        }
            in
                Http.send LoadedTaskclusterCredentials request

        Nothing ->
            Cmd.none


decodeTokens : Decoder Tokens
decodeTokens =
    JsonDecode.map3 Tokens
        (JsonDecode.field "expires" JsonDecode.int)
        (JsonDecode.field "access_token" JsonDecode.string)
        (JsonDecode.field "id_token" JsonDecode.string)


decodeTaskclusterCredentials : Decoder Credentials
decodeTaskclusterCredentials =
    JsonDecode.map4 Credentials
        (JsonDecode.at [ "credentials", "clientId" ] JsonDecode.string)
        (JsonDecode.at [ "credentials", "accessToken" ] JsonDecode.string)
        (JsonDecode.at [ "credentials", "certificate" ] (JsonDecode.maybe JsonDecode.string))
        (JsonDecode.field "expires" decodeDate)


decodeDate : Decoder Float
decodeDate =
    -- Convert a date string to a timestamp
    JsonDecode.map
        (\date ->
            case Date.fromString date of
                Ok d ->
                    Time.inSeconds <| Date.toTime d

                Err e ->
                    0
        )
        JsonDecode.string


isCertificateExpired : Float -> Maybe Credentials -> Bool
isCertificateExpired time credentials =
    case credentials of
        Just credentials_ ->
            if time > credentials_.expires then
                True
            else
                False

        Nothing ->
            False


convertUrlQueryToCode : Dict String String -> Maybe Code
convertUrlQueryToCode query =
    convertUrlParametersToCode
        (Dict.get "code" query)
        (Dict.get "state" query)


convertUrlParametersToCode : Maybe String -> Maybe String -> Maybe Code
convertUrlParametersToCode code state =
    case ( code, state ) of
        ( Just value1, Just value2 ) ->
            Just
                { code = value1
                , state = value2
                }

        _ ->
            Nothing



-- UTILS


shortUsername : String -> String
shortUsername username =
    let
        parts =
            String.split "/" username
    in
        if List.length parts == 2 then
            parts
                |> List.reverse
                |> List.head
                |> Maybe.withDefault username
        else
            username



-- SUBSCRIPTIONS


subscriptions : (Msg -> a) -> Sub a
subscriptions outMsg =
    Sub.batch
        [ auth_get Logged
        , Time.every (50 * Time.second) CheckTaskclusterCredentials
        ]
        |> Sub.map outMsg



-- PORTS


port auth_get : (Maybe Tokens -> msg) -> Sub msg


port auth_load : Bool -> Cmd msg


port auth_remove : Bool -> Cmd msg


port auth_set : Tokens -> Cmd msg
