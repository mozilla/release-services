module App.TryChooser exposing (..)

import App.Types
import Html exposing (..)
import Html.Attributes exposing (..)
import UrlParser


type alias Model =
    {}


type Msg
    = NothingIsYetHappening


page : a -> App.Types.Page a b
page outRoute =
    { title = "TryChooser"
    , description =
        "Generate parts of try syntax and restrict tests to certain directories."
    , matcher = UrlParser.format outRoute (UrlParser.s "trychooser")
    }


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
