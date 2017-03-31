module App.UserScopes exposing (..)

import Http
import Json.Decode as JsonDecode
import RemoteData exposing (WebData)
import String
import Task
import Hawk
import Utils
import Time


type alias Model =
    { timestamp : Time.Time
    , scopes : List String
    }


type Msg
    = FetchScopes
    | CacheScopes Time.Time
    | FetchedScopes (WebData String)


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
    -> ( Model, Cmd Msg, Maybe Hawk.Request )
update msg model =
    case (Debug.log "XXX" msg) of
        FetchScopes ->
            ( model
            , Task.perform CacheScopes Time.now
            , Nothing
            )

        CacheScopes currentTime ->
            let
                headers =
                    [ Http.header "Accept" "application/json" ]

                url =
                    "https://auth.taskcluster.net/v1/scopes/current"

                request =
                    Hawk.Request "FetchedScopes" "GET" url headers Http.emptyBody

                ( newModel, hawkCmd ) =
                    if (model.timestamp + 15000) > currentTime then
                        let
                            _ =
                                Debug.log "XXX" "CACHING"
                        in
                            ( model, Nothing )
                    else
                        let
                            _ =
                                Debug.log "XXX" "FETCHING"
                        in
                            ( { model | scopes = [] }
                            , Just request
                            )
            in
                ( newModel, Cmd.none, hawkCmd )

        FetchedScopes result ->
            let
                scopes =
                    Utils.decodeJsonString decoderScopes result
                        |> RemoteData.withDefault []
            in
                ( { model | scopes = scopes }
                , Cmd.none
                , Nothing
                )


hawkResponse :
    Cmd (WebData String)
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
