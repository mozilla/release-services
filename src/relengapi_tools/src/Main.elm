module Main exposing (main)

import App
import RouteUrl


-- MAIN


main : Program Never
main =
    RouteUrl.program
        { delta2url = App.delta2url
        , location2messages = App.location2messages
        , init = App.defaultModel
        , update = App.defaultUpdate
        , view = App.view
        , subscriptions = subscriptions
        }



-- SUBSCRIPTIONS


subscriptions : App.Model -> Sub App.Msg
subscriptions model =
    Sub.none
