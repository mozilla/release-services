module Main exposing (..)

import App
import RouteUrl


main : RouteUrl.RouteUrlProgram App.Flags App.Model App.Msg
main =
    RouteUrl.programWithFlags
        { delta2url = App.delta2url
        , location2messages = App.location2messages
        , init = App.init
        , update = App.update
        , view = App.view
        , subscriptions = App.subscriptions
        }
