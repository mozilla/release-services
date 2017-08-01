port module TaskclusterLogin exposing (..)

import Dict exposing (Dict)
import Json.Decode as JsonDecode
import Maybe
import Redirect
import String
import Task
import Time exposing (Time)


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


type Msg
    = Login Redirect.Model
    | Logging Credentials
    | Logged Model
    | Logout
    | CheckCertificate Time


init : Maybe Credentials -> ( Model, Cmd Msg )
init credentials =
    ( credentials, Task.perform CheckCertificate Time.now )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Login url ->
            ( model, Redirect.redirect url )

        Logging credentials ->
            ( model, taskclusterlogin_set credentials )

        Logged model ->
            ( model, Cmd.none )

        Logout ->
            ( model, taskclusterlogin_remove True )

        CheckCertificate time ->
            if isCertificateExpired time model then
                ( Nothing, taskclusterlogin_remove True )
            else
                ( model, Cmd.none )


decodeCertificate : String -> Result String Certificate
decodeCertificate text =
    JsonDecode.decodeString
        (JsonDecode.map7 Certificate
            (JsonDecode.field "version" JsonDecode.int)
            (JsonDecode.field "scopes" (JsonDecode.list JsonDecode.string))
            (JsonDecode.field "start" JsonDecode.int)
            (JsonDecode.field "expiry" JsonDecode.int)
            (JsonDecode.field "seed" JsonDecode.string)
            (JsonDecode.field "signature" JsonDecode.string)
            (JsonDecode.field "issuer" JsonDecode.string)
        )
        text


isCertificateExpired : Float -> Model -> Bool
isCertificateExpired time user_ =
    case user_ of
        Just user ->
            case user.certificate of
                Just certificate ->
                    if time > toFloat certificate.expiry then
                        True
                    else
                        False

                Nothing ->
                    False

        Nothing ->
            False


convertUrlQueryToUser : Dict String String -> Maybe Credentials
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
