-- IO/JSON ENCODE AND DECODE CODE HERE
module App.NotificationIdentity.Api exposing (..)

import Json.Decode exposing (..)
import App.NotificationIdentity.Types exposing (..)
import RemoteData
import Http

pref_decoder : Decoder (List Preference)
pref_decoder =
    let
        dec = map4 Preference (field "channel" string) (field "name" string) (field "target" string) (field "urgency" string)
    in
        at [ "preferences" ] (list dec)


problem_decoder : Decoder ApiProblem
problem_decoder =
    map3 ApiProblem (field "description" string) (field "message" string) (field "status_code" int)



getPreferences : Model -> Cmd Msg
getPreferences model =
    Http.get (model.baseUrl ++ "/identity/" ++ model.identity_name) pref_decoder
        |> RemoteData.sendRequest
        |> Cmd.map PreferencesResponse


deleteIdentity : Model -> Cmd Msg
deleteIdentity model =
    let
        request_params =
            { method = "DELETE"
            , headers = []
            , url = model.baseUrl ++ "/identity/" ++ model.identity_name
            , body = Http.emptyBody
            , expect = Http.expectJson problem_decoder
            , timeout = Nothing
            , withCredentials = False
            }
    in
        Http.request request_params
            |> RemoteData.sendRequest
            |> Cmd.map IdentityDeleteResponse


