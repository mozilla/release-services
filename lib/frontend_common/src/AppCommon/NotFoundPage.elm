module AppCommon.NotFoundPage exposing (..)


import Navigation
import Html exposing (..)


type alias Model = Navigation.Location


view : Model -> Html a
view model =
    div [] [ text "This is not found page!!!" ]

