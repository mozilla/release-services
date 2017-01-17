module App.UserScopes exposing (..)

import Http
import Json.Decode as JsonDecode exposing ((:=))
import Json.Encode as JsonEncode
import RemoteData
import String
import Task
import TaskclusterLogin
import Time


type alias Model =
    { timestamp : Time.Time
    , scopes : List String
    }


type Msg
    = FetchScopes
    | CacheScopes Time.Time
    | FetchedScopes (RemoteData.RemoteData Http.RawError Http.Response)


decoderScopes : JsonDecode.Decoder (List String)
decoderScopes =
    JsonDecode.at [ "scopes" ] (JsonDecode.list JsonDecode.string)


init : Model
init =
    { timestamp = 0.0
    , scopes = []
    }


update :
    Msg
    -> Model
    -> ( Model, Cmd Msg, Maybe { route : String, request : Http.Request } )
update msg model =
    case msg of
        FetchScopes ->
            ( model
            , Task.perform
                (\_ -> Debug.crash "Failed when receiving current time!")
                CacheScopes
                Time.now
            , Nothing
            )

        CacheScopes currentTime ->
            let
                request =
                    Http.Request
                        "GET"
                        [ ( "Accept", "application/json" )
                        , ( "Content-Type", "application/json" )
                        ]
                        "https://auth.taskcluster.net/v1/scopes/current"
                        Http.empty

                ( newModel, hawkCmd ) =
                    if (model.timestamp + 15000) > currentTime then
                        ( model, Nothing )
                    else
                        ( { model | scopes = [] }
                        , Just
                            { route = "FetchedScopes"
                            , request = request
                            }
                        )
            in
                ( newModel, Cmd.none, hawkCmd )

        FetchedScopes result ->
            let
                handleResponse response =
                    case response.value of
                        Http.Text text ->
                            JsonDecode.decodeString decoderScopes text
                                |> Result.withDefault []

                        _ ->
                            []

                scopes =
                    result
                        |> RemoteData.map handleResponse
                        |> RemoteData.withDefault []
            in
                ( { model | scopes = scopes }
                , Cmd.none
                , Nothing
                )


hawkResponse :
    Cmd (RemoteData.RemoteData Http.RawError Http.Response)
    -> String
    -> Cmd Msg
hawkResponse response route =
    case route of
        "FetchedScopes" ->
            Cmd.map FetchedScopes response

        _ ->
            Cmd.none


hasScope : List String -> String -> Bool
hasScope existing scope =
    existing
        |> List.map
            (\x ->
                if String.endsWith "*" x then
                    String.startsWith (String.dropRight 1 x) scope
                else
                    scope == x
            )
        |> List.any Basics.identity


hasScopes : List String -> List String -> Bool
hasScopes existing scopes =
    scopes
        |> List.map (hasScope existing)
        |> List.all Basics.identity
