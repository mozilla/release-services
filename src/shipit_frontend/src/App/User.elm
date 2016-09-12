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
    }

type alias Hawk = {
  request : HawkRequest,
  header : Maybe String,
  task : Maybe (Task Http.RawError Http.Response),
  requestType : HawkRequestType
}

type alias HawkRequest = {
  -- Simple data for port communication
  workflowId : Int,
  id : String,
  key : String,
  certificate : Maybe Certificate,
  url : String,
  method : String
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

type alias Model = {
  backend_dashboard_url : String,
  user : Maybe User,

  -- Hawk workflows
  workflows : Dict Int Hawk,
  workflow_id : Int,

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
  | InitHawkRequest String String HawkRequestType
  | BuiltHawkHeader (Maybe HawkResponse)
  | FetchedBugzillaAuth (WebData BugzillaAuth)


init : String -> (Model, Cmd Msg)
init backend_dashboard_url =
  -- Init empty model
  let
    model = {
      backend_dashboard_url = backend_dashboard_url, 
      user = Nothing,
      bugzilla_auth = NotAsked,
      workflows = Dict.empty,
      workflow_id = 0
    }
  in
    -- Load user from local storage
    ( model, localstorage_load True )

update : Msg -> Model -> (Model, (Maybe Hawk), Cmd Msg)
update msg model =
  case msg of
    Login url ->
      ( model, Nothing, redirect url )

    LoggingIn user ->
      ( model, Nothing, localstorage_set { name = "shipit-credentials"
                                , value = Just user
                                }
      )
    LoggedIn user ->
      -- Check bugzilla auth
      -- when a new user logs in
      -- Also save new user !
      let
        model' = { model | user = user }
        url = model.backend_dashboard_url ++ "/bugzilla/auth"
        l = Debug.log "Check bugzilla" url
      in
        buildHawkRequest model' "GET" url GetBugzillaAuth

    LocalUser ->
      -- Fetch local user from localstorage
      ( model, Nothing, localstorage_load True )

    Logout ->
      ( model, Nothing, localstorage_remove True )

    InitHawkRequest method url requestType ->
      -- Start a new request
      buildHawkRequest model method url requestType 

    BuiltHawkHeader response ->
      case response of
        Just response' -> 
          saveHawkHeader model response'
        Nothing ->
          ( model, Nothing, Cmd.none)

    ProcessWorkflow workflow ->
      -- Process task from workflow
      let
        cmd = case workflow.requestType of
          GetBugzillaAuth ->
            processBugzillaAuth workflow
          _ ->
            Cmd.none
      in
        (model, Nothing, cmd)

    FetchedBugzillaAuth auth ->
      ( { model | bugzilla_auth = auth }, Nothing, Cmd.none )

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

buildHawkRequest: Model -> String -> String -> HawkRequestType -> (Model, (Maybe Hawk), Cmd Msg)
buildHawkRequest model method url requestType =
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
          url = url,
          method = method
        }

        -- Init hawk workflow
        workflow = {
          request = request,
          requestType = requestType,
          header = Nothing,
          task = Nothing
        }

        -- Add the new request in dict
        workflows = Dict.insert wid workflow model.workflows
      in
        (
          { model | workflows = workflows, workflow_id = wid },
          Just workflow,
          hawk_build workflow.request
        )

    Nothing ->
      ( model, Nothing, Cmd.none )

saveHawkHeader: Model -> HawkResponse -> (Model, (Maybe Hawk), Cmd Msg)
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
            Just workflow',
             Cmd.none
          )

      Nothing ->
          ( model, Nothing, Cmd.none )

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
