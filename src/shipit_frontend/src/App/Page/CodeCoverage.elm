module App.Page.CodeCoverage exposing (..)


import Html exposing (..)


type alias Model =
    { pipelines : List String
    }


type Msg
    = NoOp


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    ( model, Cmd.none )


view : Model -> Html Msg
view model =
    div [] [ text "This is CODE COVERAGE page!!!" ]
