module App.ToolTool exposing (..)

import App.Types
import Html exposing (..)
import UrlParser


type alias Model =
    {}


type Msg
    = Load


page : a -> App.Types.Page a b
page outRoute =
    { title = "ToolTool"
    , description =
        "Tooltool is tool for fetching binary artifacts for builds and tests. The web interface lets you browse the files currently available from the service."
    , matcher = UrlParser.map outRoute (UrlParser.s "tooltool")
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
