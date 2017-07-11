port module AppCommon.Taskcluster exposing (..)


import Dict
import Http
import Json.Decode
import Maybe
import Redirect
import RemoteData
import String
import Task
import Time



type alias Certificate =
    { version : Int
    , scopes : List String
    , start : Int
    , expiry : Int
    , seed : String
    , signature : String
    , issuer : String
    }


type alias Credentials =
    { clientId : String
    , accessToken : String
    , certificate : Maybe Certificate
    }


type alias Model =
    Maybe Credentials


type alias RequestId =
    String


type alias Request =
    { id : RequestId
    , method : String
    , url : String
    , headers : List Http.Header
    , body : Http.Body
    }


type Msg
    = Login Redirect.Model
    | Logging Credentials
    | Logged Model
    | Logout
    | CheckCertificate Time.Time
    | SendRequest String


init : Maybe Credentials -> ( Model, Cmd Msg )
init credentials =
    ( credentials, Task.perform CheckCertificate Time.now )


update : (Cmd (RemoteData.WebData String) -> Request -> Cmd a) -> Msg -> Model -> ( Model, Cmd Msg, Cmd a )
update routeHawkResponse msg model =
    case msg of
        Login url ->
            ( model, Redirect.redirect url, Cmd.none )

        Logging credentials ->
            ( model, taskclusterlogin_set credentials, Cmd.none )

        Logged model ->
            ( model, Cmd.none, Cmd.none )

        Logout ->
            ( model, taskclusterlogin_remove True, Cmd.none )

        CheckCertificate time ->
            if isCertificateExpired time model then
                ( Nothing, taskclusterlogin_remove True, Cmd.none )
            else
                ( model, Cmd.none, Cmd.none )

        SendRequest text ->
            case Json.Decode.decodeString requestDecoder text of
                Ok request ->
                    ( model
                    , Cmd.none
                    , Cmd.none --TODO: sendRequest routeHawkResponse request
                    )

                Err error ->
                    let
                        _ =
                            Debug.log "Request decoding error" error
                    in
                        ( model, Cmd.none, Cmd.none )


sendRequest : (Cmd (RemoteData.WebData String) -> Request -> Cmd a) -> Request -> Cmd a
sendRequest routeHawkResponse request =
    let
        httpRequest =
            Http.request
                { method = request.method
                , headers = request.headers
                , url = request.url
                , body = request.body
                -- Always receive a string to be later decoded
                , expect = Http.expectString
                , timeout = Nothing
                , withCredentials = False
                }
        httpCmd =
            RemoteData.sendRequest httpRequest
    in
        routeHawkResponse httpCmd request


requestDecoder : Json.Decode.Decoder Request
requestDecoder =
    Json.Decode.map5 Request
        (Json.Decode.field "id" Json.Decode.string)
        (Json.Decode.field "method" Json.Decode.string)
        (Json.Decode.field "url" Json.Decode.string)
        -- (Json.Decode.succeed [])
        (Json.Decode.field "headers"
            (Json.Decode.list requestHeaderDecoder)
        )
        (Json.Decode.field "body" requestBodyDecoder)


requestHeaderDecoder : Json.Decode.Decoder Http.Header
requestHeaderDecoder =
    Json.Decode.map2 Http.header
        (Json.Decode.index 0 Json.Decode.string)
        (Json.Decode.index 1 Json.Decode.string)


requestBodyDecoder : Json.Decode.Decoder Http.Body
requestBodyDecoder =
    Json.Decode.oneOf
        [ -- From string to BodyString
          Json.Decode.map (Http.stringBody "application/json") Json.Decode.string
        , -- From null to Empty
          Json.Decode.null Http.emptyBody
        ]


decodeCertificate : String -> Result String Certificate
decodeCertificate text =
    Json.Decode.decodeString
        (Json.Decode.map7 Certificate
            (Json.Decode.field "version" Json.Decode.int)
            (Json.Decode.field "scopes" (Json.Decode.list Json.Decode.string))
            (Json.Decode.field "start" Json.Decode.int)
            (Json.Decode.field "expiry" Json.Decode.int)
            (Json.Decode.field "seed" Json.Decode.string)
            (Json.Decode.field "signature" Json.Decode.string)
            (Json.Decode.field "issuer" Json.Decode.string)
        )
        text


isCertificateExpired : Float -> Model -> Bool
isCertificateExpired time user_ =
    case user_ of
        Just user ->
            case user.certificate of
                Just certificate ->
                    if time > (toFloat certificate.expiry) then
                        True
                    else
                        False

                Nothing ->
                    False

        Nothing ->
            False


convertUrlQueryToUser : Dict.Dict String String -> Maybe Credentials
convertUrlQueryToUser query =
    let
        clientId =
            Dict.get "clientId" query

        accessToken =
            Dict.get "accessToken" query

        certificate2 =
            Dict.get "certificate" query

        certificate =
            case certificate2 of
                Just text ->
                    Result.toMaybe (decodeCertificate text)

                Nothing ->
                    Nothing
    in
        case ( clientId, accessToken ) of
            ( Just value1, Just value2 ) ->
                Just
                    { clientId = value1
                    , accessToken = value2
                    , certificate = certificate
                    }

            _ ->
                Nothing


-- VIEWS


redirectToLogin : (Msg -> a) -> String -> String -> a
redirectToLogin outMsg returnRoute description =
    { url = "https://login.taskcluster.net"
    , target = Just ( returnRoute, description )
    , targetName = "target"
    }
        |> Login
        |> outMsg



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
        [ taskclusterlogin_get Logged
        , Time.every (50 * Time.second) CheckCertificate
        ]
        |> Sub.map outMsg



-- PORTS


port taskclusterlogin_get : (Maybe Credentials -> msg) -> Sub msg


port taskclusterlogin_load : Bool -> Cmd msg


port taskclusterlogin_remove : Bool -> Cmd msg


port taskclusterlogin_set : Credentials -> Cmd msg
