module App.Clobberer exposing (..)

import Dict exposing ( Dict )
import Focus exposing ( set, create, Focus, (=>) )
import Html exposing ( Html, div, text )
import Http
import Json.Decode as JsonDecode exposing ( (:=) )
import RemoteData as RemoteData exposing ( WebData, RemoteData(Loading) )
import RouteUrl.Builder exposing ( Builder, builder, replacePath )
import Task exposing ( Task )


-- TYPES

type Msg
    = FetchData (WebData DataItems)

type alias DataItem =
    { name : String
    , data : Dict String (List String)
    }

type alias DataItems = List DataItem

type alias Model' =
    { data : WebData DataItems
    }

type alias Model =
    { buildbot : Model'
    --, taskcluster : Model'
    }
type Clobberer
    = Buildbot
    --| Taskcluster


-- API

view : Model -> Html Msg
view model =
    div [] [ text (toString model) ]


init' : Clobberer -> Model'
init' clobberer =
    case clobberer of
        Buildbot ->
            { data = Loading }
        --Taskcluster ->
        --    { data = "taskcluster" }

init : (Model, Cmd Msg)
init =
    ( { buildbot = init' Buildbot
      --, taskcluster = init' Taskcluster
      }
    , Cmd.batch [ fetchData ]
    )

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        FetchData newData ->
            ( set (buildbot => data) newData model
            , Cmd.none
            )


-- IMPLEMENTATION


buildbot : Focus { record | buildbot : a } a
buildbot = create .buildbot (\f r -> { r | buildbot = f r.buildbot })

data : Focus { record | data : a } a
data = create .data (\f r -> { r | data = f r.data })

decodeData : JsonDecode.Decoder (List DataItem)
decodeData =
    JsonDecode.at [ "result" ]
       ( JsonDecode.list
           ( JsonDecode.object2  DataItem
                                 ( "name" := JsonDecode.string )
                                 ( "data" := JsonDecode.dict (JsonDecode.list JsonDecode.string) )
           )
       )

fetchData: Cmd Msg
fetchData =
    Http.get decodeData "http://127.0.0.1:8000/__api__/clobberer/buildbot"
        |> RemoteData.asCmd
        |> Cmd.map FetchData


-- UTILS



-- TODO: this should work
getJson : JsonDecode.Decoder value -> String -> Task Http.Error value
getJson decoder url =
  let request =
        { verb = "GET"
        , headers = [( "Content-Type", "application/json" )]
        , url = url
        , body = Http.empty
        }
  in
    Http.fromJson decoder
        (Http.send Http.defaultSettings request)
