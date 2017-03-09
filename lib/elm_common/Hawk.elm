port module Hawk exposing (..)

import Http
import TaskclusterLogin as User
import Json.Encode as JsonEncode
import Json.Decode as JsonDecode
import RemoteData exposing (WebData)


type alias RequestID =
    String


type Msg
    = SendRequest String


type alias Request =
    { id : RequestID
    , method : String
    , url : String
    , headers : List Http.Header
    , body : Http.Body
    }


update :
    Msg
    -> ( Maybe RequestID, Cmd Msg, Cmd (WebData String) )
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


send : Request -> User.Credentials -> Cmd Msg
send request credentials =
    let
        requestJson =
            requestEncoder request
    in
        hawk_add_header ( request.id, requestJson, credentials )



-- Transform hawk request in a remote data Cmd
-- It must be ran from the app update cycle


sendRequest : Request -> Cmd (WebData String)
sendRequest request =
    let
        httpRequest =
            Http.request
                { method = request.method
                , headers = request.headers
                , url = request.url
                , body = request.body
                , expect =
                    Http.expectString
                    -- Always receive a string to be later decoded
                , timeout = Nothing
                , withCredentials = False
                }
    in
        RemoteData.sendRequest httpRequest



-- Json Encoders & Decoders


requestEncoder : Request -> String
requestEncoder request =
    JsonEncode.encode 0 <|
        JsonEncode.object
            [ ( "id", JsonEncode.string request.method )
            , ( "method", JsonEncode.string request.method )
            , ( "url", JsonEncode.string request.url )
            , ( "headers", JsonEncode.list (List.map requestHeadersEncoder request.headers) )
              -- We can't access the internal type of the body
              -- so we are forced to send its representation
            , ( "body", JsonEncode.string (toString request.body) )
            ]


requestHeadersEncoder : Http.Header -> JsonEncode.Value
requestHeadersEncoder header =
    -- Can not access header internals !
    JsonEncode.string (toString header)



--  JsonEncode.list
--      [ JsonEncode.string key
--      , JsonEncode.string value
--      ]


requestDecoder : JsonDecode.Decoder Request
requestDecoder =
    JsonDecode.map5 Request
        (JsonDecode.field "id" JsonDecode.string)
        (JsonDecode.field "method" JsonDecode.string)
        (JsonDecode.field "url" JsonDecode.string)
        (JsonDecode.field "headers"
            (JsonDecode.list
                (JsonDecode.map2 Http.header JsonDecode.string JsonDecode.string)
            )
        )
        (JsonDecode.field "body" requestBodyDecoder)


requestBodyDecoder : JsonDecode.Decoder Http.Body
requestBodyDecoder =
    JsonDecode.oneOf
        [ -- From string to BodyString
          JsonDecode.map (Http.stringBody "application/json") JsonDecode.string
        , -- From null to Empty
          JsonDecode.null Http.emptyBody
        ]


portDecoder : JsonDecode.Decoder ( RequestID, Request )
portDecoder =
    JsonDecode.map2 (,) JsonDecode.string requestDecoder



-- SUBSCRIPTIONS


subscriptions : (Msg -> a) -> Sub a
subscriptions outMsg =
    hawk_send_request SendRequest
        |> Sub.map outMsg



-- PORTS


port hawk_send_request : (String -> msg) -> Sub msg


port hawk_add_header : ( RequestID, String, User.Credentials ) -> Cmd msg
