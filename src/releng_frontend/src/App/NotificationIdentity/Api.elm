-- IO/JSON ENCODE AND DECODE CODE HERE
module App.NotificationIdentity.Api exposing (..)

import Json.Decode exposing (..)
import Json.Encode
import App.NotificationIdentity.Types exposing (..)
import RemoteData
import RemoteData exposing (WebData)
import Http
import Utils


type alias NoBody = {}

-- Decoders / Encoders

encodePreference : Preference -> Json.Encode.Value
encodePreference preference =
    Json.Encode.object
        [ ("channel", Json.Encode.string preference.channel)
        , ("target", Json.Encode.string preference.target)
        , ("urgency", Json.Encode.string preference.urgency)
        ]


pref_decoder : Decoder Preferences
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
    let
        detail = maybe (field "detail" string)
        instance = maybe (field "instance" string)
        status = maybe (field "status" int)
        title = maybe (field "title" string)
        type_ = maybe (field "type" string)
    in
        map5 ApiProblem detail instance status title type_


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
            |> Cmd.map GetPreferencesResponse


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
            , expect = Http.expectString
            , timeout = Nothing
            , withCredentials = False
            }
    in
        Http.request request_params
            |> RemoteData.sendRequest
            |> Cmd.map IdentityDeleteResponse


newIdentity : Model -> Cmd Msg
newIdentity model =
    case model.new_identity of
        Just new_identity ->
            let
                encoded_preference_list = Json.Encode.list (List.map encodePreference new_identity.preferences)

                msg_body = Json.Encode.object
                    [ ("preferences", encoded_preference_list)
                    ]

                request_params =
                    { method = "PUT"
                    , headers = []
                    , url = model.baseUrl ++ "/identity/" ++ new_identity.name
                    , body = Http.jsonBody msg_body
                    , expect = Http.expectJson (Json.Decode.oneOf [problem_decoder])
                    , timeout = Nothing
                    , withCredentials = False
                    }

            in
                Http.request request_params
                    |> RemoteData.sendRequest
                    |> Cmd.map NewIdentityResponse

        Nothing ->
            Utils.performMsg (OperationFail "No new identity data.")


deletePreferenceByUrgency : Model -> Cmd Msg
deletePreferenceByUrgency model =
    case model.selected_preference of
        Nothing ->
            Utils.performMsg (OperationFail "Please select a preference to delete.")

        Just preference ->
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
                    , url = model.baseUrl ++ "/identity/" ++ identity ++ "/" ++ preference.urgency
                    , body = Http.emptyBody
                    , expect = Http.expectJson (Json.Decode.oneOf [problem_decoder])
                    , timeout = Nothing
                    , withCredentials = False
                    }

            in
                Http.request request_params
                |> RemoteData.sendRequest
                |> Cmd.map UrgencyDeleteResponse
