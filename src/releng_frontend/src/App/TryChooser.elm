module App.TryChooser exposing (..)

import App.Types
import Html exposing (..)
import UrlParser


type alias Model =
    {}


type Msg
    = Load


page : a -> App.Types.Page a b
page outRoute =
    { title = "TryChooser"
    , description =
        "Generate parts of try syntax and restrict tests to certain directories."
    , matcher = UrlParser.map outRoute (UrlParser.s "trychooser")
    }


init : Model
init =
    {}


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Load ->
            ( model, Cmd.none )


view : Model -> Html Msg
view model =
    div [] [ text "Not yet implemented!" ]
