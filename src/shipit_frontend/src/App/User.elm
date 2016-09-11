port module App.User exposing (..)

import Dict exposing ( Dict )
import Json.Decode as JsonDecode exposing (Decoder, (:=) )
import Json.Encode as JsonEncode
import App.Utils exposing ( eventLink )
import Task exposing (Task)
import Http

type alias LoginUrl =
    { url : String
    , target : Maybe (String, String)
    }

type alias Hawk = {
  request : Maybe HawkRequest,
  header : Maybe String,
  response : Maybe Http.Response,
  task : Maybe (Task Http.RawError Http.Response),
  requestType : HawkRequestType
}

type alias HawkRequest = {
  -- Simple data for port communication
  id : String,
  key : String,
  certificate : Maybe Certificate,
  url : String,
  method : String
}

type alias Certificate =
    { version : Int
    , scopes : List String
    , start : Int
    , expiry : Int
    , seed : String
    , signature : String
    , issuer : String
    }

type alias User = {
  clientId : String,
  accessToken : String,
  certificate : Maybe Certificate
}

type alias Model = {
  backend_dashboard_url : String,
  user : Maybe User,
  hawk : Hawk
}

type HawkRequestType = Empty
  | AllAnalysis
  | Analysis
  | GetBugzillaAuth
  | UpdateBugzillaAuth


fromJust : Maybe a -> a
fromJust x = case x of
    Just y -> y
    Nothing -> Debug.crash "error: fromJust Nothing"

type Msg
  = Login LoginUrl
  | LoggingIn User
  | LoggedIn (Maybe User)
  | LocalUser
  | Logout 
  | InitHawkRequest String String HawkRequestType
  | BuiltHawkHeader String


init : String -> (Model, Cmd Msg)
init backend_dashboard_url =
  -- Init empty model
  let
    model = {
      backend_dashboard_url = backend_dashboard_url, 
      user = Nothing,
      hawk = {
        request = Nothing,
        header = Nothing,
        response = Nothing,
        task = Nothing,
        requestType = Empty
      }
    }
  in
    -- Load user from local storage
    ( model, localstorage_load True )

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of
    Login url ->
      ( model, redirect url )

    LoggingIn user ->
      ( model, localstorage_set { name = "shipit-credentials"
                                , value = Just user
                                }
      )
    LoggedIn user ->
      -- Check bugzilla auth
      -- when a new user logs in
      -- Also save new user !
      let
        model' = { model | user = user }
        url = "/bugzilla/auth"
      in
        ( model' , Cmd.none )
        -- buildHawkRequest model' "GET" url GetBugzillaAuth

    LocalUser ->
      -- Fetch local user from localstorage
      ( model, localstorage_load True )

    Logout ->
      ( model, localstorage_remove True )

    InitHawkRequest method url requestType ->
      -- Start a new request
      buildHawkRequest model method url requestType 

    BuiltHawkHeader header ->
      saveHawkHeader model header

decodeCertificate : String -> Result String Certificate
decodeCertificate text =
    JsonDecode.decodeString
        (JsonDecode.object7 Certificate
            ( "version"     := JsonDecode.int )
            ( "scopes"      := JsonDecode.list JsonDecode.string )
            ( "start"       := JsonDecode.int )
            ( "expiry"      := JsonDecode.int )
            ( "seed"        := JsonDecode.string )
            ( "signature"   := JsonDecode.string )
            ( "issuer"      := JsonDecode.string )
        ) text


convertUrlQueryToUser : Dict String String -> User
convertUrlQueryToUser query =
    -- TODO: handle more nicely clientId/Token
    { clientId = fromJust (Dict.get "clientId" query)
    , accessToken = fromJust (Dict.get "accessToken" query)
    , certificate =
             case Dict.get "certificate" query of
                 Just certificate ->
                     Result.toMaybe <| decodeCertificate certificate
                 Nothing -> Nothing
    }

buildHawkRequest: Model -> String -> String -> HawkRequestType -> (Model, Cmd Msg)
buildHawkRequest model method url requestType =
  -- Build a new hawk request towards a backend
  case model.user of
    Just user ->
      let
        request = {
          id = user.clientId,
          key = user.accessToken,
          certificate = user.certificate,
          url = url,
          method = method
        }

        -- Reset hawk
        hawk = {
          request = Just request,
          requestType = requestType,
          header = Nothing,
          response = Nothing,
          task = Nothing
        }
      in
        -- Use port to build the header
        (
          { model | hawk = hawk },
          hawk_build request
        )

    Nothing ->
      ( model, Cmd.none )

saveHawkHeader: Model -> String -> (Model, Cmd Msg)
saveHawkHeader model header =
  -- Save the newly received hawk header
  case model.user of
    Just user ->
      case model.hawk.request of
        -- Store header and build Task to send request later on
        Just request ->
          let
            hawk = model.hawk
            hawk' = { hawk | header = Just header, task = Just (buildHttpTask request header) }
          in
            ( { model | hawk = hawk' }, Cmd.none )

        Nothing ->
            ( model, Cmd.none )

    Nothing ->
      ( model, Cmd.none )

buildHttpTask: HawkRequest -> String -> Task Http.RawError Http.Response
buildHttpTask request header =
  -- Build Http request task
  Http.send Http.defaultSettings {
    url = request.url,
    verb = request.method,
    headers = [
      ( "Authorization", header ),
      ( "Accept", "application/json" )
    ],
    body = Http.empty
  }



--processBugzillaAuth: (Maybe Model) -> ((Maybe Model), Cmd Msg)
--processBugzillaAuth model =
--  -- Decode and save all analysis
--  case model.hawk.task of
--    Just task ->
--      (
--        model,
--        (Http.fromJson decodeAllAnalysis task)
--        |> RemoteData.asCmd
--        |> Cmd.map FetchedAllAnalysis
--      )
--    Nothing ->
--        ( model, Cmd.none )
--
-- PORTS

-- XXX: until https://github.com/elm-lang/local-storage is ready

type alias LocalStorage =
    { name : String
    , value : Maybe User
    }

port localstorage_get : (Maybe User -> msg) -> Sub msg
port localstorage_load : Bool -> Cmd msg
port localstorage_remove : Bool -> Cmd msg
port localstorage_set : LocalStorage -> Cmd msg

-- XXX: we need to find elm implementation for redirect

port redirect : LoginUrl -> Cmd msg

-- Hawk ports
port hawk_get : (String -> msg) -> Sub msg
port hawk_build : HawkRequest -> Cmd msg
