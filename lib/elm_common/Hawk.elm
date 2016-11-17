port module Hawk exposing (..)

import Http
import Task exposing (Task)
import TaskclusterLogin
import Json.Encode as JsonEncode
import Json.Decode as JsonDecode


type Msg error success
    = AddHeader Http.Request TaskclusterLogin.Model
    | SendRequest String
    | Failure error
    | Success success


init =
  {}

subscriptions =
  [
    (hawk_send_request (SendRequest))
  ]

-- update : Msg -> model -> (model, Cmd Msg)
update msg model = 
    case msg of
        AddHeader request user ->
          let
            requestJson = requestEncoder request
          in
            ( model, hawk_add_header (requestJson, user) )

        SendRequest requestJson ->
            ( model, sendRequest requestJson )

        _ -> (model, Cmd.none)


requestEncoder : Http.Request -> String
requestEncoder request =
  JsonEncode.encode 0 <|
    JsonEncode.object [
      ("verb", JsonEncode.string request.verb),
      ("headers", JsonEncode.list (List.map requestHeadersEncoder request.headers)),
      ("url", JsonEncode.string request.url)
      --("body", JsonEncode.string request.body)
    ]

requestHeadersEncoder : (String, String) -> JsonEncode.Value
requestHeadersEncoder (key, value) =
  JsonEncode.list [
    JsonEncode.string key, 
    JsonEncode.string value
  ]


-- sendRequest : Http.Request -> Cmd msg
sendRequest requestJson =
  let
    -- TODO: use request decoder
    request = Http.Request "GET" [] "https://hijacked.net" Http.empty
  in
    Http.send Http.defaultSettings request 
    |> Task.perform Failure Success

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
    

port hawk_send_request:  (String -> msg) -> Sub msg
port hawk_add_header: (String, TaskclusterLogin.Model) -> Cmd msg
