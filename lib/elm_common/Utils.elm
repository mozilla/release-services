module Utils exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events as Events
import Json.Decode as JsonDecode


onClick msg =
    Events.onWithOptions
        "click"
        (Events.Options False True)
        (JsonDecode.succeed msg)


onChange : (String -> msg) -> Attribute msg
onChange handler =
    Events.on "change" <| JsonDecode.map handler <| JsonDecode.at [ "target", "value" ] JsonDecode.string


eventLink msg attributes =
    a ([ onClick <| msg, href "#" ] ++ attributes)
