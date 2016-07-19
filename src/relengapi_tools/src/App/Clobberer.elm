module App.Clobberer exposing (..)

import Dict exposing ( Dict )
import Html exposing ( Html, div, text )
import RouteUrl.Builder exposing (Builder, builder, replacePath)


type Msg
    = FetchData



type alias Model' =
    { data : String
    }

type alias Model =
    { buildbot : Model'
    , taskcluster : Model'
    }



type Clobberer
    = Buildbot
    | Taskcluster


view : Model -> Html Msg
view model =
    div [] [ text (toString model) ]


init' : Clobberer -> Model'
init' clobberer =
    case clobberer of
        Buildbot ->
            { data = "buildbot" }
        Taskcluster ->
            { data = "taskcluster" }

init : (Model, Cmd Msg)
init =
    ( { buildbot = init' Buildbot
      , taskcluster = init' Taskcluster
      }
    , Cmd.none
    --, Cmd.batch [ fetchBuildbot, fetchTaskcluster ]
    )

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    ( model, Cmd.none )


-- implementation


--Http.get decodeNews "/news"
--        |> RemoteData.asCmd
--        |> Cmd.map NewsResponse

