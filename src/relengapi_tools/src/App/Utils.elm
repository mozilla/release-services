module App.Utils exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events as Events
import Json.Decode as JsonDecode


-- TODO: add types

onClick msg =
    Events.onWithOptions
        "click"
        (Events.Options False True)
        (JsonDecode.succeed msg)


eventLink msg attributes =
    a ([ onClick <| msg, href "#"  ] ++ attributes)
