module App.Utils exposing (eventLink)

import Html exposing (a)
import Html.Attributes exposing (href)
import Utils exposing (onClick)


eventLink :
    msg
    -> List (Html.Attribute msg)
    -> List (Html.Html msg)
    -> Html.Html msg
eventLink msg attributes =
    a ([ onClick <| msg, href "#" ] ++ attributes)
