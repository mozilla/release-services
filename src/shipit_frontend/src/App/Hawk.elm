port module App.Hawk exposing (..)
import Task exposing (Task)
import App.User as User
import Json.Decode as Json exposing (Decoder)
import List exposing ((::))
import Http

type RequestType = Empty
  | AllAnalysis
  | Analysis

type alias Model = {
  request : Maybe PortRequest,
  header : Maybe String,
  response : Maybe Http.Response,
  task : Maybe (Task Http.RawError Http.Response),
  requestType : RequestType
}

type alias PortRequest = {
  -- Simple data for port communication
  id : String,
  key : String,
  certificate : Maybe User.Certificate,
  url : String,
  method : String
}

type Msg
  = InitRequest User.Model String String RequestType
  | BuiltHeader String
  | FetchFailure Http.RawError
  | FetchSuccess Http.Response

fromJust : Maybe a -> a
fromJust x = case x of
    Just y -> y
    Nothing -> Debug.crash "error: fromJust Nothing"

init: (Model, Cmd Msg)
init =
  -- Empty model at first
  ( {
    request = Nothing,
    header = Nothing,
    task = Nothing,
    response = Nothing,
    requestType = Empty
  }, Cmd.none)


update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of

    InitRequest user method url requestType ->
      -- Start a new request
      let
        request = {
          id = fromJust user.clientId,
          key = fromJust user.accessToken,
          certificate = user.certificate,
          url = url,
          method = method
        }
      in
        -- Use port to build the header
        (
          { model | request = Just request, requestType = requestType },
          hawk_build request
        )

    BuiltHeader header ->
      case model.request of
        -- Store header and send request
        Just request ->
          (
            { model | header = Just header, task = Just (buildTask request header) },
            Cmd.none
            -- sendRequest request header
          )

        Nothing ->
          ( model, Cmd.none )

    FetchFailure err ->
      let
        l = Debug.log "Fetch failure" err
      in
        ( model, Cmd.none )

    FetchSuccess response ->
      -- Store response
        ( { model | response = Just response }, Cmd.none )

sendRequest: PortRequest -> String -> Cmd Msg
sendRequest request header =
  -- Send HTTP request with Hawk header
  Http.send Http.defaultSettings {
    url = request.url,
    verb = request.method,
    headers = [
      ( "Authorization", header ),
      ( "Accept", "application/json" )
    ],
    body = Http.empty
  }
  |> Task.perform FetchFailure FetchSuccess
  


buildTask: PortRequest -> String -> Task Http.RawError Http.Response
buildTask request header =
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
  


--workflow: Maybe User.Model -> String -> String -> Decoder obj -> Task Http.Error obj
--workflow maybeUser method url decoder = 
--  case maybeUser of
--    Just user ->
--      let
--        request = {
--        }
--      in
--        -- Build Auth header
--        buildHeader request
--
--        -- Send HTTP request to backend
--        `Task.andThen` \header -> (sendRequest request header) |> (Http.fromJson decoder)
--
--    Nothing ->
--      -- No credentials
--      Task.fail Http.NetworkError

-- PORTS
port hawk_get : (String -> msg) -> Sub msg
port hawk_build : PortRequest -> Cmd msg
