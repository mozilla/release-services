module App.TryChooser exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)


type alias Model =
    {}


type Msg
    = NothingIsYetHappening


init : Model
init =
    {}


load :
    (Msg -> a)
    -> Cmd a
    -> { b | trychooser : Model }
    -> ( { b | trychooser : Model }, Cmd a )
load outMsg newCmd model =
    ( model, newCmd )


update : (Msg -> a) -> Msg -> b -> ( b, Cmd a )
update outMsg msg model =
    ( model, Cmd.none )


view : Model -> Html Msg
view model =
    div [] [ text "Not yet implemented!" ]
