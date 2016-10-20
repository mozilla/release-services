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
  header_backend : Maybe String,
  header_target : Maybe String,
  task : Maybe (Task Http.RawError Http.Response),
  requestType : HawkRequestType
}

type alias UrlMethod = {
  url : String,
  method: String
}

type alias HawkParameters = {
  -- Simple structure to store parameters
  -- before building an hawk request
  backend : UrlMethod, -- Build an hawk header for backend auth
  target : Maybe UrlMethod, -- Build an optional hawk header for a sub target hit from backend (TC)
  body : Maybe String,
  requestType : HawkRequestType
}

type alias HawkRequest = {
  -- Simple data for port communication
  workflowId : Int,
  id : String,
  key : String,
  certificate : Maybe Certificate,
  backend : UrlMethod,
  target : Maybe UrlMethod,
  body : Maybe String
}

type alias HawkResponse = {
  -- Simple data for port communication
  workflowId : Int,
  header_backend : String,
  header_target : Maybe String
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

type alias BugzillaCredentials = {
  url: String, -- Bugzilla server
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
  bugzilla : Maybe BugzillaCredentials,
  bugzilla_url : String,
  bugzilla_check : WebData Bool
}

type alias LocalStorage = {
  user : Maybe User,
  bugzilla : Maybe BugzillaCredentials
}

type HawkRequestType = Empty
  | AllAnalysis
  | Analysis
  | GetBugzillaAuth
  | UpdateBugzillaAuth
  | BugUpdate

fromJust : Maybe a -> a
fromJust x = case x of
    Just y -> y
    Nothing -> Debug.crash "error: fromJust Nothing"

type Msg
  = Login LoginUrl
  | LoggingIn User
  | LoggedIn (Maybe LocalStorage)
  | LocalUser
  | Logout 
  | ProcessWorkflow Hawk
  | InitHawkRequest HawkParameters
  | BuiltHawkHeader (Maybe HawkResponse)
  | CheckedBugzillaCreds Bool (WebData Bool) 

init : String -> String -> (Model, Cmd Msg)
init backend_dashboard_url bugzilla_url =
  -- Init empty model
  let
    model = {
      backend_dashboard_url = backend_dashboard_url, 
      user = Nothing,
      bugzilla = Nothing,
      bugzilla_url = bugzilla_url, 
      bugzilla_check = NotAsked,
      workflows = Dict.empty,
      workflow_id = 0,
      skipped_requests = []
    }
  in
    -- Load user from local storage
    ( model, localstorage_load True )

runRequest: HawkParameters -> (Model, List Hawk, Cmd Msg) -> (Model, List Hawk, Cmd Msg)
runRequest params (model, hawk, cmd) =
  let
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
          user = Just user,
          bugzilla = model.bugzilla
        }
      )

    LoggedIn storage ->
      -- Check bugzilla auth
      -- when a new user logs in
      -- Also save new user !
      case storage of
        Just storage' ->
          (
            { model | user = storage'.user, bugzilla = storage'.bugzilla },
            [],
            checkBugzillaAuth storage'.bugzilla False
          )

        Nothing ->
          (model, [], Cmd.none)

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
          --GetBugzillaAuth ->
          --  processBugzillaAuth workflow
          _ ->
            Cmd.none
      in
        (model, [], cmd)

    CheckedBugzillaCreds save check ->
      (
        { model | bugzilla_check = check },
        [],

        -- Save credentials stored in model when valid
        case check of
          Success check' ->
            if check' && save then
              storeCredentials model.user model.bugzilla
            else
              Cmd.none
          _ ->
            Cmd.none
      )

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

checkBugzillaAuth : Maybe BugzillaCredentials -> Bool -> Cmd Msg
checkBugzillaAuth creds save =
  -- Check bugzilla auth is still valid
  case creds of
    Just bugzilla ->
      let
        task = buildBugzillaTask bugzilla {
          method = "GET",
          url = Http.url "/valid_login" [
            ("login", bugzilla.login)
          ]
        } Nothing -- no body
      in
        (Http.fromJson JsonDecode.bool task)
        |> RemoteData.asCmd
        |> Cmd.map (CheckedBugzillaCreds save)

    Nothing ->
      Cmd.none

storeCredentials : Maybe User -> Maybe BugzillaCredentials -> Cmd msg
storeCredentials user creds =
  -- Helper to store credentials structure
  localstorage_set {
      user = user,
      bugzilla = creds
    }

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
          backend = params.backend,
          target = params.target,
          body = params.body
        }

        -- Init hawk workflow
        workflow = {
          request = request,
          requestType = params.requestType,
          header_backend = Nothing,
          header_target = Nothing,
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
            header_backend = Just response.header_backend,
            header_target = response.header_target,
            task = Just (buildTCTask workflow.request response.header_backend response.header_target)
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

buildTCTask: HawkRequest -> String -> Maybe String -> Task Http.RawError Http.Response
buildTCTask request header_backend header_target =
  -- Build Taskcluster Http request task
  let
    body = case request.body of
      Just body' -> Http.string body'
      Nothing -> Http.empty

    headers = [
      -- Always use backend Hawk header
      ( "Authorization", header_backend ),
      ( "Accept", "application/json" ),
      ( "Content-Type", "application/json" )
    ] ++ case header_target of
      -- Only use extra target header when available
      Just h -> [ ("X-Authorization-Target", h) ]
      Nothing -> []
  in
    -- Always send to backend
    Http.send Http.defaultSettings {
      url = request.backend.url,
      verb = request.backend.method,
      headers = headers,
      body = body
    }

buildBugzillaTask: BugzillaCredentials -> UrlMethod -> Maybe String -> Task Http.RawError Http.Response
buildBugzillaTask creds url_method body =
  let
    body' = case body of
      Just b -> Http.string b
      Nothing -> Http.empty

    headers = [
      -- Use bugzilla token
      ( "x-bugzilla-api-key", creds.token ),
      ( "Accept", "application/json" ),
      ( "Content-Type", "application/json" )
    ]
  in
    -- Always send to Mozilla Bugzilla
    Http.send Http.defaultSettings {
      url = creds.url ++ "/rest" ++ url_method.url,
      verb = url_method.method,
      headers = headers,
      body = body'
    }

-- PORTS

-- XXX: until https://github.com/elm-lang/local-storage is ready

port localstorage_get : (Maybe LocalStorage -> msg) -> Sub msg
port localstorage_load : Bool -> Cmd msg
port localstorage_remove : Bool -> Cmd msg
port localstorage_set : LocalStorage -> Cmd msg

-- XXX: we need to find elm implementation for redirect

port redirect : LoginUrl -> Cmd msg

-- Hawk ports
port hawk_get : (Maybe HawkResponse -> msg) -> Sub msg
port hawk_build : HawkRequest -> Cmd msg
