port module Hawk exposing (..)

import Http
import Task exposing (Task)
import TaskclusterLogin as User
import Json.Encode as JsonEncode
import Json.Decode as JsonDecode exposing ((:=))
import RemoteData as RemoteData exposing (WebData, RemoteData(Loading, Success, NotAsked, Failure))


type alias RequestID =
    String


type Msg
    = SendRequest String


update :
    Msg
    -> ( Maybe RequestID, Cmd Msg, Cmd (RemoteData Http.RawError Http.Response) )
update msg =
    case msg of
        SendRequest text ->
            case JsonDecode.decodeString portDecoder text of
                Ok ( requestId, request ) ->
                    ( Just requestId, Cmd.none, sendRequest request )

                Err error ->
                    let
                        _ =
                            Debug.log "Request decoding error" error
                    in
                        ( Nothing, Cmd.none, Cmd.none )



-- Encode Http request in json to pass it through ports


send : RequestID -> Http.Request -> User.Credentials -> Cmd Msg
send requestId request credentials =
    let
        requestJson =
            requestEncoder request
    in
        hawk_add_header ( requestId, requestJson, credentials )



-- Transform http request in a remote data Cmd
-- It must be ran from the app update cycle


sendRequest : Http.Request -> Cmd (RemoteData Http.RawError Http.Response)
sendRequest request =
    Http.send Http.defaultSettings request
        |> RemoteData.asCmd



-- Json Encoders & Decoders


requestEncoder : Http.Request -> String
requestEncoder request =
    JsonEncode.encode 0 <|
        JsonEncode.object
            [ ( "verb", JsonEncode.string request.verb )
            , ( "headers", JsonEncode.list (List.map requestHeadersEncoder request.headers) )
            , ( "url", JsonEncode.string request.url )
              -- We can't access the internal type of the body
              -- so we are forced to send its representation
            , ( "body", JsonEncode.string (toString request.body) )
            ]


requestHeadersEncoder : ( String, String ) -> JsonEncode.Value
requestHeadersEncoder ( key, value ) =
    JsonEncode.list
        [ JsonEncode.string key
        , JsonEncode.string value
        ]


requestDecoder : JsonDecode.Decoder Http.Request
requestDecoder =
    JsonDecode.object4 Http.Request
        ("verb" := JsonDecode.string)
        ("headers"
            := JsonDecode.list
                (JsonDecode.tuple2 (,) JsonDecode.string JsonDecode.string)
        )
        ("url" := JsonDecode.string)
        ("body" := requestBodyDecoder)


requestBodyDecoder : JsonDecode.Decoder Http.Body
requestBodyDecoder =
    JsonDecode.oneOf
        [ -- From string to BodyString
          JsonDecode.map Http.string JsonDecode.string
        , -- From null to Empty
          JsonDecode.null Http.empty
        ]


portDecoder : JsonDecode.Decoder ( RequestID, Http.Request )
portDecoder =
    JsonDecode.tuple2 (,) JsonDecode.string requestDecoder


port hawk_send_request : (String -> msg) -> Sub msg


port hawk_add_header : ( RequestID, String, User.Credentials ) -> Cmd msg
