module App.CodeCoverage exposing (..)

import Http
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onClick)
import RemoteData exposing (WebData, RemoteData(..))
import TaskclusterLogin as User
import Json.Decode as JsonDecode exposing (Decoder)
import Dict exposing (Dict)


-- Models


type alias Directory =
    { current : Float
    , previous : Float
    , bugs : List Int
    }


type alias Directories =
    Dict String Directory


type alias Model =
    { backend_uplift_url : String
    , directories : WebData Directories
    , path : Maybe String
    }


type Msg
    = LoadedArtifact (WebData Directories)
    | SetDirectory (Maybe String)


init : String -> ( Model, Cmd Msg )
init backend_uplift_url =
    let
        -- Init empty model
        model =
            { backend_uplift_url = backend_uplift_url
            , directories = NotAsked
            , path = Nothing
            }
    in
        -- Load code coverage data
        ( model, loadArtifact model )



-- Update


update : Msg -> Model -> User.Model -> ( Model, Cmd Msg )
update msg model user =
    case msg of
        LoadedArtifact directories ->
            ( { model | directories = directories }, Cmd.none )

        SetDirectory path ->
            setDirectory model path


setDirectory : Model -> Maybe String -> ( Model, Cmd Msg )
setDirectory model path =
    ( { model | path = path }, Cmd.none )


loadArtifact : Model -> Cmd Msg
loadArtifact model =
    let
        -- TODO: use environment variables here
        hookGroup =
            "project-releng"

        hookId =
            "services-staging-shipit-code-coverage-bot"

        artifact =
            "coverage_by_dir.json"

        url =
            (model.backend_uplift_url ++ "/hook/artifact/" ++ hookGroup ++ "/" ++ hookId ++ "/" ++ artifact)

        request =
            Http.request
                { method = "GET"
                , headers = []
                , url = url
                , body = Http.emptyBody
                , expect = Http.expectJson decodeArtifact
                , timeout = Nothing
                , withCredentials = False
                }
    in
        -- send request as webdata
        RemoteData.sendRequest request
            |> Cmd.map LoadedArtifact


decodeArtifact : Decoder Directories
decodeArtifact =
    JsonDecode.dict decodeDirectory


decodeDirectory : Decoder Directory
decodeDirectory =
    JsonDecode.map3 Directory
        (JsonDecode.field "cur" JsonDecode.float)
        (JsonDecode.field "prev" JsonDecode.float)
        (JsonDecode.field "bugs" (JsonDecode.list JsonDecode.int))


filterDirectories : Directories -> Maybe String -> Directories
filterDirectories directories path =
    case path of
        Just parentPath ->
            -- Shows sub directories
            Dict.filter (\p dir -> String.startsWith parentPath p) directories

        Nothing ->
            -- Shows top directories only
            Dict.filter (\p dir -> not (String.contains "/" p)) directories



-- Views


view : Model -> Html Msg
view model =
    div [ class "container-fluid" ]
        [ case model.directories of
            Failure err ->
                div [ class "alert alert-danger" ] [ text ("Error loading code coverage: " ++ (toString err)) ]

            Success directories ->
                let
                    title =
                        case model.path of
                            Just path ->
                                ("Directiory: " ++ path)

                            Nothing ->
                                "Top Directory"
                in
                    div []
                        [ h1 [] [ text title ]
                        , viewDirectories (filterDirectories directories model.path)
                        ]

            _ ->
                div [ class "alert alert-info" ] [ text "Loading code coverage..." ]
        ]


viewDirectories : Directories -> Html Msg
viewDirectories directories =
    table [ class "table table-striped" ]
        ([ tr []
            [ th [] [ text "Path" ]
            , th [] [ text "Current" ]
            , th [] [ text "Previous" ]
            , th [] [ text "Bugs" ]
            ]
         ]
            ++ (List.map viewDirectory (Dict.toList directories))
        )


viewDirectory : ( String, Directory ) -> Html Msg
viewDirectory ( path, directory ) =
    let
        style =
            if directory.current < directory.previous then
                "table-danger"
            else if directory.current > directory.previous then
                "table-success"
            else
                "table-info"
    in
        tr [ class style ]
            [ td [] [ span [ class "btn btn-link", onClick (SetDirectory (Just path)) ] [ text path ] ]
            , td [] [ text (toString directory.current) ]
            , td [] [ text (toString directory.previous) ]
            , td [] [ ul [] (List.map viewBug directory.bugs) ]
            ]


viewBug : Int -> Html Msg
viewBug bugzillaId =
    li []
        [ a [ href ("https://bugzil.la/" ++ (toString bugzillaId)), target "_blank" ]
            [ text (toString bugzillaId)
            ]
        ]
