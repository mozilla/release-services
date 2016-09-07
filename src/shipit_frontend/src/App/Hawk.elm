port module App.Hawk exposing (..)
import Task exposing (Task)
import App.User as User
import Json.Decode as Json exposing (Decoder)
import List exposing ((::))
import Http


type alias PortRequest = {
  -- Simple data for port communication
  id : String,
  key : String,
  certificate : Maybe User.Certificate,
  url : String,
  method : String
}

type Msg
    = BuiltHeader String

update : Msg -> (Cmd Msg)
update msg =
    case msg of
        BuiltHeader header ->
            let
                l = Debug.log "HEADER received" header
            in
                Cmd.none

sendRequest: PortRequest -> String -> Task Http.RawError Http.Response
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
  

fromJust : Maybe a -> a
fromJust x = case x of
    Just y -> y
    Nothing -> Debug.crash "error: fromJust Nothing"


buildHeader: PortRequest -> Task never String
buildHeader request = 
    let
      x = hawk_build request
      l = Debug.log "asked port to build HAWK" x
    in
      -- DUMMY
      (Task.succeed "Hawk DEMOHEADER")


workflow: Maybe User.Model -> String -> String -> Decoder obj -> Task Http.Error obj
workflow maybeUser method url decoder = 
  case maybeUser of
    Just user ->
      let
        request = {
          id = fromJust user.clientId,
          key = fromJust user.accessToken,
          certificate = user.certificate,
          url = url,
          method = method
        }
      in
        -- Build Auth header
        buildHeader request

        -- Send HTTP request to backend
        `Task.andThen` \header -> (sendRequest request header) |> (Http.fromJson decoder)

    Nothing ->
      -- No credentials
      Task.fail Http.NetworkError

-- PORTS
port hawk_get : (String -> msg) -> Sub msg
port hawk_build : PortRequest -> Cmd msg
