module App.Clobberer exposing (..)

import Dict exposing ( Dict )
import Focus exposing ( set, create, Focus, (=>) )
import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Json.Decode as JsonDecode exposing ( (:=) )
import RemoteData as RemoteData exposing ( WebData, RemoteData(Loading) )
import RouteUrl.Builder exposing ( Builder, builder, replacePath )
import Task exposing ( Task )


-- TYPES

type alias BackendItem =
    { name : String
    , data : Dict String (List String)
    }

type alias BackendData = List BackendItem

type alias ModelBackend =
    { title : String
    , data : WebData BackendData
    }

type alias Model =
    { baseUrl : String
    , buildbot : ModelBackend
    , taskcluster : ModelBackend
    }

type Backend 
    = BuildbotBackend
    | TaskclusterBackend


type Msg
    = FetchData (WebData BackendData)


-- API

viewBackend : ModelBackend -> Html Msg
viewBackend backend =
    div [] [ text (toString backend) ]

view : Model -> Html Msg
view model =
    div [] 
        [ h1 [] [ text "Clobberer" ]
        , p [] [ text "A repairer of buildbot builders and taskcluster worker types." ]
        , p [] [ text "TODO: link to documentation" ]
        , div [ class "row" ]
              [ div [ class "col-md-6" ]
                    [ h2 [] [ text "Taskcluster" ]
                    , viewBackend model.taskcluster
                    ]
              , div [ class "col-md-6" ]
                    [ h2 [] [ text "Clobberer" ]
                    , viewBackend model.taskcluster
                    ]
              ]
        ]


initBackend : String -> ModelBackend
initBackend title  =
    { title = title
    , data = Loading
    }

init : Model
init =
    { buildbot = initBackend "Buildbot"
    , taskcluster = initBackend "Taskcluster"
    , baseUrl = "http://127.0.0.1:5500/clobberer"
    }

initPage : String -> Model -> (Model, Cmd Msg)
initPage  baseUrl model =
    ( { buildbot = initBackend "Buildbot"
      , taskcluster = initBackend "Taskcluster"
      , baseUrl = baseUrl
      }
    , Cmd.batch [ fetchBackend (baseUrl ++ "/buildbot")
                , fetchBackend (baseUrl ++ "/taskcluster")
                ]
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

taskcluster : Focus { record | taskcluster : a } a
taskcluster = create .taskcluster (\f r -> { r | taskcluster = f r.taskcluster })

data : Focus { record | data : a } a
data = create .data (\f r -> { r | data = f r.data })

decodeData : JsonDecode.Decoder (List BackendItem)
decodeData =
    JsonDecode.at [ "result" ]
       ( JsonDecode.list
           ( JsonDecode.object2  BackendItem
                                 ( "name" := JsonDecode.string )
                                 ( "data" := JsonDecode.dict (JsonDecode.list JsonDecode.string) )
           )
       )

fetchBackend : String -> Cmd Msg
fetchBackend  url =
    Http.get decodeData url
        |> RemoteData.asCmd
        |> Cmd.map FetchData


-- UTILS



-- TODO: this should work but header is never sent
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
