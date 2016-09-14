port module App.User exposing (..)

import Dict exposing ( Dict )
import Json.Decode as JsonDecode exposing (Decoder, (:=) )
import Json.Encode as JsonEncode
import RemoteData as RemoteData exposing ( WebData, RemoteData(Loading, Success, NotAsked, Failure) )
import App.Utils exposing ( eventLink )
import Task exposing (Task)
import Http

type alias LoginUrl =
    { url : String
    , target : Maybe (String, String)
    , targetName : String
    }

type alias Hawk = {
  request : HawkRequest,
  header : Maybe String,
  task : Maybe (Task Http.RawError Http.Response),
  requestType : HawkRequestType
}

type alias HawkParameters = {
  -- Simple structure to store parameters
  -- before building an hawk request
  url : String,
  method : String,
  body : Maybe String,
  requestType : HawkRequestType
}

type alias HawkRequest = {
  -- Simple data for port communication
  workflowId : Int,
  id : String,
  key : String,
  certificate : Maybe Certificate,
  url : String,
  method : String,
  body : Maybe String
}

type alias HawkResponse = {
  -- Simple data for port communication
  workflowId : Int,
  header : String
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

type alias BugzillaAuth = {
  authenticated : Bool,
  message : String
}

type alias BugzillaCredentials = {
  login: String,
  token: String
}

type alias Model = {
  backend_dashboard_url : String,
  user : Maybe User,

  -- Hawk workflows
  workflows : Dict Int Hawk,
  workflow_id : Int,
  skipped_requests : List HawkParameters,

  -- Bugzilla auth
  bugzilla_auth : WebData (BugzillaAuth)
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
  | ProcessWorkflow Hawk
  | InitHawkRequest HawkParameters
  | BuiltHawkHeader (Maybe HawkResponse)
  | FetchedBugzillaAuth (WebData BugzillaAuth)
  | ReceivedBugzillaCreds (Maybe BugzillaCredentials)

init : String -> (Model, Cmd Msg)
init backend_dashboard_url =
  -- Init empty model
  let
    model = {
      backend_dashboard_url = backend_dashboard_url, 
      user = Nothing,
      bugzilla_auth = NotAsked,
      workflows = Dict.empty,
      workflow_id = 0,
      skipped_requests = []
    }
  in
    -- Load user from local storage
    ( model, localstorage_load True )

test : HawkParameters -> (Model, List Hawk, Cmd Msg) -> (Model, List Hawk, Cmd Msg)
test params full =
  let
    (model, hawk, cmd) = full
    (model', hawk', cmd') = buildHawkRequest model params
  in
    ( model', hawk ++ hawk', Cmd.batch [ cmd, cmd'] )


update : Msg -> Model -> (Model, List Hawk, Cmd Msg)
update msg model =
  case msg of
    Login url ->
      ( model, [], redirect url )

    LoggingIn user ->
      (
        model, [], localstorage_set {
          name = "shipit-credentials",
          value = Just user
        }
      )

    LoggedIn user ->
      -- Check bugzilla auth
      -- when a new user logs in
      -- Also save new user !
      let
        model' = { model | user = user }
        params = {
          method = "GET",
          url = model.backend_dashboard_url ++ "/bugzilla/auth",
          body = Nothing,
          requestType = GetBugzillaAuth
        }
      in
        --buildHawkRequest model' params
        List.foldr test (model', [], Cmd.none) ( params :: model.skipped_requests )

    LocalUser ->
      -- Fetch local user from localstorage
      ( model, [], localstorage_load True )

    Logout ->
      ( model, [], localstorage_remove True )

    InitHawkRequest params ->
      -- Start a new request
      buildHawkRequest model params

    BuiltHawkHeader response ->
      case response of
        Just response' -> 
          saveHawkHeader model response'
        Nothing ->
          ( model, [], Cmd.none)

    ProcessWorkflow workflow ->
      -- Process task from workflow
      let
        cmd = case workflow.requestType of
          GetBugzillaAuth ->
            processBugzillaAuth workflow
          UpdateBugzillaAuth ->
            processBugzillaAuth workflow
          _ ->
            Cmd.none
      in
        (model, [], cmd)

    FetchedBugzillaAuth auth ->
      ( { model | bugzilla_auth = auth }, [], Cmd.none )

    ReceivedBugzillaCreds creds ->
      -- Do not store credentials, send them to backend
      case creds of
        Just creds' ->
          let
            credsJson = JsonEncode.encode 0 (JsonEncode.object [
              ("login", JsonEncode.string creds'.login),
              ("token", JsonEncode.string creds'.token)
            ])
            params = {
              method = "POST",
              url = model.backend_dashboard_url ++ "/bugzilla/auth",
              body = Just credsJson,    
              requestType = UpdateBugzillaAuth
            }
          in
            buildHawkRequest model params

        Nothing ->
          ( model, [], Cmd.none )

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

convertUrlQueryToBugzillaCreds : Dict String String -> Maybe (BugzillaCredentials)
convertUrlQueryToBugzillaCreds query =
    let
      login = Dict.get "client_api_login" query
      token = Dict.get "client_api_token" query
    in
      
      login `Maybe.andThen` (\login' -> case token of
        Just token' -> Just {
          login = login',
          token = token'
        }
        Nothing -> Nothing)

buildHawkRequest: Model -> HawkParameters -> (Model, List Hawk, Cmd Msg)
buildHawkRequest model params =
  -- Build a new hawk request towards a backend
  case model.user of
    Just user ->
      let
        -- Build an id to match port & hawk requests
        wid = model.workflow_id + 1

        -- Build hawk request for port
        request = {
          id = user.clientId,
          workflowId = wid,
          key = user.accessToken,
          certificate = user.certificate,
          url = params.url,
          method = params.method,
          body = params.body
        }

        -- Init hawk workflow
        workflow = {
          request = request,
          requestType = params.requestType,
          header = Nothing,
          task = Nothing
        }

        -- Add the new request in dict
        workflows = Dict.insert wid workflow model.workflows
      in
        (
          { model | workflows = workflows, workflow_id = wid },
          [ workflow ],
          hawk_build workflow.request
        )

    Nothing ->
      -- Store skipped requests for later use
      let
        l = Debug.log "Skipping request" params
      in        
        ( { model | skipped_requests = params :: model.skipped_requests }, [], Cmd.none )

saveHawkHeader: Model -> HawkResponse -> (Model, List Hawk, Cmd Msg)
saveHawkHeader model response =
  -- Find matching worfkow for response
  let
    wid = response.workflowId
  in
    case Dict.get wid model.workflows of
      Just workflow ->
        let 
          -- Use the newly received hawk header
          -- to build the http task
          workflow' = { workflow |
            header = Just response.header,
            task = Just (buildHttpTask workflow.request response.header)
          }

          -- Update existing workflow
          workflows = Dict.insert wid workflow' model.workflows
        in
          (
            { model | workflows = workflows },
            [ workflow' ],
             Cmd.none
          )

      Nothing ->
          ( model, [], Cmd.none )

buildHttpTask: HawkRequest -> String -> Task Http.RawError Http.Response
buildHttpTask request header =
  -- Build Http request task
  let
    body = case request.body of
      Just body' -> Http.string body'
      Nothing -> Http.empty
  in
    Http.send Http.defaultSettings {
      url = request.url,
      verb = request.method,
      headers = [
        ( "Authorization", header ),
        ( "Accept", "application/json" )
      ],
      body = body
    }


processBugzillaAuth: Hawk -> Cmd Msg
processBugzillaAuth workflow =
  -- Decode and save all analysis
  case workflow.task of
    Just task ->
      (Http.fromJson decodeBugzillaAuth task)
      |> RemoteData.asCmd
      |> Cmd.map FetchedBugzillaAuth

    Nothing ->
        Cmd.none

decodeBugzillaAuth : Decoder BugzillaAuth
decodeBugzillaAuth =
  JsonDecode.object2 BugzillaAuth
    ("authenticated" := JsonDecode.bool)
    ("message" := JsonDecode.string)

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
port hawk_get : (Maybe HawkResponse -> msg) -> Sub msg
port hawk_build : HawkRequest -> Cmd msg
