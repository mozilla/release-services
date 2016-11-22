port module TaskclusterLogin exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Dict exposing (Dict)
import Utils exposing (eventLink)
import Json.Decode as JsonDecode exposing ((:=))
import Redirect
import Maybe


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
    { credentials : Maybe Credentials
    }


type Msg
    = Login Redirect.Model
    | Logging Credentials
    | Logged (Maybe Credentials)
    | Logout


init : ( Model, Cmd Msg )
init =
    ( { credentials = Nothing
      }
    , -- Initial credentials loading
      taskclusterlogin_load True
    )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Login url ->
            ( model, Redirect.redirect url )

        Logging creds ->
            ( model, taskclusterlogin_set creds )

        Logged creds ->
            ( { model | credentials = creds }
            , Cmd.none
            )

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


fromJust : Maybe a -> a
fromJust x =
    case x of
        Just y ->
            y

        Nothing ->
            Debug.crash "error: fromJust Nothing"


convertUrlQueryToUser : Dict String String -> Credentials
convertUrlQueryToUser query =
    -- TODO: handle more nicely clientId/Token
    { clientId = fromJust (Dict.get "clientId" query)
    , accessToken = fromJust (Dict.get "accessToken" query)
    , certificate =
        case Dict.get "certificate" query of
            Just certificate ->
                Result.toMaybe <| decodeCertificate certificate

            Nothing ->
                Nothing
    }



-- Views


redirectToLogin outMsg returnRoute description =
    { url = "https://login.taskcluster.net"
    , target = Just ( returnRoute, description )
    , targetName = "target"
    }
        |> Login
        |> outMsg



-- Ports


port taskclusterlogin_get : (Maybe Credentials -> msg) -> Sub msg


port taskclusterlogin_load : Bool -> Cmd msg


port taskclusterlogin_remove : Bool -> Cmd msg


port taskclusterlogin_set : Credentials -> Cmd msg



-- Add this subscription in main App
-- subscriptions = [
--    Sub.map TaskclusterLoginMsg (TaskclusterLogin.taskclusterlogin_get (TaskclusterLogin.Logged))
--   ]
