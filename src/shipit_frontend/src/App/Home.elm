module App.Home exposing (..)

import Html exposing (Html, div, text)


type Msg
    = Nothing


view : a -> Html Msg
view model =
    div [] [ text "Home" ]
