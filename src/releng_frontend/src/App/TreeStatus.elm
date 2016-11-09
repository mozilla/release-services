module App.TreeStatus exposing (..)

import Html exposing (..)

type alias Model =
    { baseUrl : String
    }

init : Model
init =
    { baseUrl = "data-clobberer-url not set"
    }

initPage : String -> Model -> (Model, Cmd Msg)
initPage baseUrl model =
    ( { baseUrl = baseUrl
      }
    , Cmd.none
    )

type Msg = DoSomething


update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        _ -> (model, Cmd.none)


view : Model -> Html Msg
view model =
    div [] []
