module App.Route exposing (..)


import Navigation
import UrlParser
--import AppCommon.Route


type Route
    = Home


routeParser : UrlParser.Parser (Route -> a) a
routeParser =
    UrlParser.oneOf
        [ UrlParser.map Home (UrlParser.s "")
        ]


locationToRoute : Navigation.Location -> Result Navigation.Location Route
locationToRoute location =
    if String.isEmpty location.pathname then
        Ok Home
    else 
        UrlParser.parsePath routeParser location
            |> Result.fromMaybe location
