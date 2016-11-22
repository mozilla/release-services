port module Hawk exposing (..)

import Http
import Task exposing (Task)
import TaskclusterLogin as User
import Json.Encode as JsonEncode
import Json.Decode as JsonDecode exposing ((:=))
import RemoteData as RemoteData exposing (WebData, RemoteData(Loading, Success, NotAsked, Failure))


type Msg
    = AddHeader Http.Request User.Credentials
    | SendRequest String


update : Msg -> ( Cmd Msg, Cmd (RemoteData Http.RawError Http.Response) )
update msg =
    case msg of
        AddHeader request credentials ->
            ( send request credentials, Cmd.none )

        SendRequest requestJson ->
            case requestDecoder requestJson of
                Ok request ->
                    ( Cmd.none, sendRequest request )

                Err error ->
                    let
                        l =
                            Debug.log "Request decoding error" error
                    in
                        ( Cmd.none, Cmd.none )



-- Encode Http request in json to pass it through ports


send : Http.Request -> User.Credentials -> Cmd Msg
send request credentials =
    let
        requestJson =
            requestEncoder request
    in
        hawk_add_header ( requestJson, credentials )



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
            , ( "body", JsonEncode.null )
              -- TODO: support text body
            ]


requestHeadersEncoder : ( String, String ) -> JsonEncode.Value
requestHeadersEncoder ( key, value ) =
    JsonEncode.list
        [ JsonEncode.string key
        , JsonEncode.string value
        ]


requestDecoder : String -> Result String Http.Request
requestDecoder text =
    JsonDecode.decodeString
        (JsonDecode.object4 Http.Request
            ("verb" := JsonDecode.string)
            ("headers"
                := JsonDecode.list
                    (JsonDecode.tuple2 (,) JsonDecode.string JsonDecode.string)
            )
            ("url" := JsonDecode.string)
            ("body" := JsonDecode.succeed Http.empty)
         -- TODO
        )
        text



-- Used by apps to apply multiple Json decoders


applyDecoders : model -> List (model -> String -> model) -> Http.Response -> model
applyDecoders initialModel decoders response =
    -- Apply every decoders in list on response+model
    -- Folding to an only final model instance
    if 200 <= response.status && response.status < 300 then
        case response.value of
            Http.Text responseText ->
                List.foldl
                    (\decoder m -> decoder m responseText)
                    initialModel
                    decoders

            _ ->
                initialModel
    else
        initialModel



--requestBodyToValue: Http.Body -> JsonEncode.Value
--requestBodyToValue body =
--  case body of
--    Empty -> JsonEncode.object [
--      ("type", JsonEncode.string "Empty"),
--      ("value", JsonEncode.null)
--    ]
--    BodyString x -> JsonEncode.object [
--      ("type", JsonEncode.string "BodyString"),
--      ("value", JsonEncode.string x)
--    ]
--    ArrayBuffer -> JsonEncode.object [
--      ("type", JsonEncode.string "ArrayBuffer"),
--      ("value", JsonEncode.null)
--    ]
--    BodyFormData -> JsonEncode.object [
--      ("type", JsonEncode.string "BodyFormData"),
--      ("value", JsonEncode.null)
--    ]
--    BodyBlob -> JsonEncode.object [
--      ("type", JsonEncode.string "BodyBlob"),
--      ("value", JsonEncode.null)
--    ]


port hawk_send_request : (String -> msg) -> Sub msg


port hawk_add_header : ( String, User.Credentials ) -> Cmd msg



-- Add this subscription in main App
-- subscriptions = [
--    Sub.map HawkRequest (Hawk.hawk_send_request (Hawk.SendRequest))
--   ]
