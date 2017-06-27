-- IO/JSON ENCODE AND DECODE CODE HERE
module App.NotificationIdentity.Api exposing (..)

import Json.Decode exposing (..)
import App.NotificationIdentity.Types exposing (..)
import RemoteData
import Http


type alias NoBody = {}

-- Decoders

pref_decoder : Decoder (List Preference)
pref_decoder =
    let
        channel_field = (field "channel" string)
        name_field = (field "name" string)
        target_field = (field "target" string)
        urgency_field = (field "urgency" string)
        dec = map4 Preference channel_field name_field target_field urgency_field
    in
        at [ "preferences" ] (list dec)


problem_decoder : Decoder ApiProblem
problem_decoder =
    map3 ApiProblem (field "description" string) (field "message" string) (field "status_code" int)


-- Commands

getPreferences : Model -> Cmd Msg
getPreferences model =
    let
        identity =
            case model.identity_name of
                Just val ->
                    val
                Nothing ->
                    ""
    in
        Http.get (model.baseUrl ++ "/identity/" ++ identity) pref_decoder
            |> RemoteData.sendRequest
            |> Cmd.map PreferencesResponse


deleteIdentity : Model -> Cmd Msg
deleteIdentity model =
    let
        identity =
            case model.identity_name of
                Just val ->
                    val

                Nothing ->
                    ""

        request_params =
            { method = "DELETE"
            , headers = []
            , url = model.baseUrl ++ "/identity/" ++ identity
            , body = Http.emptyBody
            , expect = Http.expectJson (Json.Decode.oneOf [problem_decoder, succeed (ApiProblem "" "" 200)])
            , timeout = Nothing
            , withCredentials = False
            }
    in
        Http.request request_params
            |> RemoteData.sendRequest
            |> Cmd.map IdentityDeleteResponse

deletePreferenceByUrgency : Model -> Cmd Msg
deletePreferenceByUrgency model =
    let
        pref =
            case model.selected_preference of
                Nothing ->
                    nullPreference

                Just p ->
                    p

        identity =
            case model.identity_name of
                Just val ->
                    val

                Nothing ->
                    ""

        request_params =
            { method = "DELETE"
            , headers = []
            , url = model.baseUrl ++ "/identity/" ++ identity ++ "/" ++ pref.urgency
            , body = Http.emptyBody
            , expect = Http.expectJson (Json.Decode.oneOf [problem_decoder, succeed ((ApiProblem "" "" 200))])
            , timeout = Nothing
            , withCredentials = False
            }

    in
        Http.request request_params
        |> RemoteData.sendRequest
        |> Cmd.map UrgencyDeleteResponse
