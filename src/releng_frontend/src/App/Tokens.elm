module App.Tokens exposing (..)

import App.Types
import Html exposing (..)
import UrlParser


type alias Model =
    {}


type Msg
    = Load


page : a -> App.Types.Page a b
page outRoute =
    { title = "Tokens"
    , description =
        "Tokens are used to allow automated services to authenticate to Releng API without being tied to a user's identity."
    , matcher = UrlParser.map outRoute (UrlParser.s "tokens")
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
