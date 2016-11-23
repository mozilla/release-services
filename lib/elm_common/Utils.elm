module Utils exposing (..)

import Html
import Html.Events
import Http
import Json.Decode as JsonDecode


onClick : msg -> Html.Attribute msg
onClick msg =
    Html.Events.onWithOptions
        "click"
        (Html.Events.Options False True)
        (JsonDecode.succeed msg)


onChange : (String -> msg) -> Html.Attribute msg
onChange handler =
    JsonDecode.at [ "target", "value" ] JsonDecode.string
        |> JsonDecode.map handler
        |> Html.Events.on "change"


handleResponse : (String -> a) -> a -> Http.Response -> a
handleResponse handle default response =
    if 200 <= response.status && response.status < 300 then
        case response.value of
            Http.Text text ->
                handle text
            _ ->
                default
    else
        default


decodeResponse decoder default response =
    handleResponse
        (\x -> JsonDecode.decodeString decoder x |> Result.withDefault default)
        default
        response

