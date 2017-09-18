port module TaskclusterLogin exposing (..)

import Dict exposing (Dict)
import Json.Decode as JsonDecode
import Maybe
import Redirect
import String
import Utils
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


type alias Model ={
       
    credentials : Maybe Credentials
    , domain : String
    , client_id : String
}


type Msg
    = Login Redirect.Model
    | Logging Credentials
    | Logged (Maybe Credentials)
    | Logout
    | CheckCertificate Time


init : String -> String -> Maybe Credentials -> ( Model, Cmd Msg )
init domain client_id credentials =
  let
    model = {
        credentials = credentials,
        domain = domain,
        client_id = client_id
        }
  in
    (model , Task.perform CheckCertificate Time.now )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Login url ->
            ( model, Redirect.redirect url )

        Logging credentials ->
            ( model, taskclusterlogin_set credentials )

        Logged credentials ->
            ( { model | credentials = credentials}, Cmd.none )

        Logout ->
            ( model, taskclusterlogin_remove True )

        CheckCertificate time ->
            if isCertificateExpired time model.credentials then
                ( {model | credentials = Nothing }, taskclusterlogin_remove True )
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


isCertificateExpired : Float -> Maybe Credentials -> Bool
isCertificateExpired time credentials =
    case credentials of
        Just credentials_ ->
            case credentials_.certificate of
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

buildLoginMsg : Model -> Msg
buildLoginMsg user =
  let 
    url = Utils.buildUrl (user.domain ++ "/authorize") [
        ( "audience", "login.taskcluster.net")
        , ( "scope", "full-user-credentials openid")
        , ( "response_type", "code")
        , ( "client_id", user.client_id)
        -- TODO: redirect to backend ?
        , ( "redirect_uri", "https://localhost:8010/login")
        -- TODO: add state for CSRF protection ?
    ]
  in
    Login {
        url = url,
        target = Nothing,
        targetName = ""
    }


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
