port module Redirect exposing (..)


type alias Model =
    { url : String
    , target : Maybe ( String, String )
    , targetName : String
    }



-- TODO: we need to find elm implementation for redirect


port redirect : Model -> Cmd msg
