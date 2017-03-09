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
            case JsonDecode.decodeString requestDecoder text of
                Ok request ->
                    ( Just request.id, Cmd.none, sendRequest request )

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
        hawk_add_header ( requestJson, credentials )



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
    let
        -- We can't access the internal type of the body
        -- so we are forced to send its representation
        body =
            if (toString request.body) == "EmptyBody" then
                JsonEncode.null
            else
                JsonEncode.string (toString request.body)
    in
        JsonEncode.encode 0 <|
            JsonEncode.object
                [ ( "id", JsonEncode.string request.id )
                , ( "method", JsonEncode.string request.method )
                , ( "url", JsonEncode.string request.url )
                , ( "headers", JsonEncode.list (List.map requestHeadersEncoder request.headers) )
                , ( "body", body )
                ]


requestHeadersEncoder : Http.Header -> JsonEncode.Value
requestHeadersEncoder header =
    -- Can not access header internals !
    JsonEncode.string (toString header)


requestDecoder : JsonDecode.Decoder Request
requestDecoder =
    JsonDecode.map5 Request
        (JsonDecode.field "id" JsonDecode.string)
        (JsonDecode.field "method" JsonDecode.string)
        (JsonDecode.field "url" JsonDecode.string)
        -- (JsonDecode.succeed [])
        (JsonDecode.field "headers"
            (JsonDecode.list requestHeaderDecoder)
        )
        (JsonDecode.field "body" requestBodyDecoder)


requestHeaderDecoder : JsonDecode.Decoder Http.Header
requestHeaderDecoder =
    JsonDecode.map2 Http.header
        (JsonDecode.index 0 JsonDecode.string)
        (JsonDecode.index 1 JsonDecode.string)


requestBodyDecoder : JsonDecode.Decoder Http.Body
requestBodyDecoder =
    JsonDecode.oneOf
        [ -- From string to BodyString
          JsonDecode.map (Http.stringBody "application/json") JsonDecode.string
        , -- From null to Empty
          JsonDecode.null Http.emptyBody
        ]



-- SUBSCRIPTIONS


subscriptions : (Msg -> a) -> Sub a
subscriptions outMsg =
    hawk_send_request SendRequest
        |> Sub.map outMsg



-- PORTS


port hawk_send_request : (String -> msg) -> Sub msg


port hawk_add_header : ( String, User.Credentials ) -> Cmd msg
