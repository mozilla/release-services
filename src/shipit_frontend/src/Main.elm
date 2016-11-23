module Main exposing (..)

import RouteUrl


-- TODO: restore FULL app
--import App

import AppTest as App


main : Program App.Flags
main =
    RouteUrl.programWithFlags
        { delta2url = App.delta2url
        , location2messages = App.location2messages
        , init = App.init
        , update = App.update
        , view = App.view
        , subscriptions = App.subscriptions
        }
