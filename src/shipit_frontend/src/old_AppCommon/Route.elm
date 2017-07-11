module AppCommon.Route exposing (locationToMsg)


import Navigation
import UrlParser


--locationToMsg : UrlParser.Parser (Route -> a) a -> b -> Navigation.Location -> c -> Result Navigation.Location c
--locationToMsg : Navigation.Location -> Maybe Route
locationToMsg routeParser msg homePage location =
    if String.isEmpty location.pathname then
        Ok homePage
    else 
        UrlParser.parsePath routeParser location
            |> Maybe.withDefault (Err location)

