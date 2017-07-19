module AppCommon.ErrorPage exposing (..)


import Html exposing (..)


type alias Model =
    { retryCount : Int
    }


type Msg
    = Retry


update : Msg -> Cmd Msg
update msg =
    Cmd.none


view : Model -> Html Msg
view model =
    div [] [ text "This is ERROR page!!!" ]
