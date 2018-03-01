module Utils exposing (..)

import Html
import Html.Events
import Http
import Json.Decode as JsonDecode
import RemoteData exposing (RemoteData(..), WebData)
import Task


performMsg : a -> Cmd a
performMsg msg =
    Task.perform
        (\x -> msg)
        (Task.succeed ())


onClick : msg -> Html.Attribute msg
onClick msg =
    Html.Events.onWithOptions
        "click"
        (Html.Events.Options False True)
        (JsonDecode.succeed msg)


andThen :
    (msg -> model -> ( model, Cmd msg ))
    -> msg
    -> ( model, Cmd msg )
    -> ( model, Cmd msg )
andThen update msg ( model, cmd ) =
    let
        ( model_, cmd_ ) =
            update msg model
    in
    ( model_, Cmd.batch [ cmd, cmd_ ] )


onChange : (String -> msg) -> Html.Attribute msg
onChange handler =
    JsonDecode.at [ "target", "value" ] JsonDecode.string
        |> JsonDecode.map handler
        |> Html.Events.on "change"


decodeJsonString : JsonDecode.Decoder a -> WebData String -> WebData a
decodeJsonString decoder response =
    case response of
        Success text ->
            case JsonDecode.decodeString decoder text of
                Ok obj ->
                    Success obj

                Err error ->
                    -- Should be BadPayload here but we don't have
                    -- acces to Http.Response from here :/
                    Failure Http.NetworkError

        Failure x ->
            Failure x

        Loading ->
            Loading

        NotAsked ->
            NotAsked



--


{-| Create a properly encoded URL with a [query string][qs]. The first argument is
the portion of the URL before the query string, which is assumed to be
properly encoded already. The second argument is a list of all the
key/value pairs needed for the query string. Both the keys and values
will be appropriately encoded, so they can contain spaces, ampersands, etc.
[qs]: <http://en.wikipedia.org/wiki/Query_string>
url "<http://example.com/users"> [ ("name", "john doe"), ("age", "30") ]
-- <http://example.com/users?name=john+doe&age=30>
From: <https://github.com/evancz/elm-http/blob/3.0.1/src/Http.elm#L56-L73>
as it got removed from http library in Elm 0.18
-}
buildUrl : String -> List ( String, String ) -> String
buildUrl baseUrl args =
    case args of
        [] ->
            baseUrl

        _ ->
            baseUrl ++ "?" ++ String.join "&" (List.map queryPair args)


queryPair : ( String, String ) -> String
queryPair ( key, value ) =
    queryEscape key ++ "=" ++ queryEscape value


queryEscape : String -> String
queryEscape string =
    String.join "+" (String.split "%20" (Http.encodeUri string))
