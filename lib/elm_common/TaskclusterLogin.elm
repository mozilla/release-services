port module TaskclusterLogin exposing (..)

import Dict exposing (Dict)
import Html exposing (..)
import Html.Attributes exposing (..)
import Json.Decode as JsonDecode exposing ((:=))
import Maybe
import Redirect
import String


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


init : Maybe Credentials -> ( Model, Cmd Msg )
init credentials =
    ( credentials, Cmd.none )


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


decodeCertificate : String -> Result String Certificate
decodeCertificate text =
    JsonDecode.decodeString
        (JsonDecode.object7 Certificate
            ("version" := JsonDecode.int)
            ("scopes" := JsonDecode.list JsonDecode.string)
            ("start" := JsonDecode.int)
            ("expiry" := JsonDecode.int)
            ("seed" := JsonDecode.string)
            ("signature" := JsonDecode.string)
            ("issuer" := JsonDecode.string)
        )
        text


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


redirectToLogin outMsg returnRoute description =
    { url = "https://login.taskcluster.net"
    , target = Just ( returnRoute, description )
    , targetName = "target"
    }
        |> Login
        |> outMsg



-- UTILS


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
    taskclusterlogin_get Logged
        |> Sub.map outMsg



-- PORTS


port taskclusterlogin_get : (Maybe Credentials -> msg) -> Sub msg


port taskclusterlogin_load : Bool -> Cmd msg


port taskclusterlogin_remove : Bool -> Cmd msg


port taskclusterlogin_set : Credentials -> Cmd msg
