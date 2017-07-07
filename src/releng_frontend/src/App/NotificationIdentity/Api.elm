-- IO/JSON ENCODE AND DECODE CODE HERE
module App.NotificationIdentity.Api exposing (..)

import Json.Decode exposing (..)
import Json.Encode
import App.NotificationIdentity.Types exposing (..)
import RemoteData
import RemoteData exposing (WebData)
import Http
import Utils
import Form


type alias NoBody = {}

-- Decoders / Encoders

encodePreference : App.NotificationIdentity.Types.Preference -> Json.Encode.Value
encodePreference preference =
    Json.Encode.object
        [ ("channel", Json.Encode.string preference.channel)
        , ("target", Json.Encode.string preference.target)
        , ("urgency", Json.Encode.string preference.urgency)
        ]


encodeInputPreference : App.NotificationIdentity.Types.InputPreference -> Json.Encode.Value
encodeInputPreference inputPreference =
    Json.Encode.object
        [ ("channel", Json.Encode.string inputPreference.channel)
        , ("target", Json.Encode.string inputPreference.target)
        , ("urgency", Json.Encode.string inputPreference.urgency)
        ]


preferenceDecoder : Decoder Preferences
preferenceDecoder =
    let
        channel_field = (field "channel" string)
        name_field = (field "name" string)
        target_field = (field "target" string)
        urgency_field = (field "urgency" string)
        dec = map4 Preference channel_field name_field target_field urgency_field
    in
        at [ "preferences" ] (list dec)


problemDecoder : Decoder ApiProblem
problemDecoder =
    let
        detail = maybe (field "detail" string)
        instance = maybe (field "instance" string)
        status = maybe (field "status" int)
        title = maybe (field "title" string)
        type_ = maybe (field "type" string)
    in
        map5 ApiProblem detail instance status title type_


--
-- Commands
--
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
        Http.get (model.baseUrl ++ "/identity/" ++ identity) preferenceDecoder
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
    let
        new_id_output = Form.getOutput model.new_identity
    in
        case new_id_output of
            Just new_identity ->
                let
                    encoded_preference_list = Json.Encode.list (List.map encodeInputPreference new_identity.preferences)

                    msg_body = Json.Encode.object
                        [ ("preferences", encoded_preference_list)
                        ]

                    request_params =
                        { method = "PUT"
                        , headers = []
                        , url = model.baseUrl ++ "/identity/" ++ new_identity.name
                        , body = Http.jsonBody msg_body
                        , expect = Http.expectString
                        , timeout = Nothing
                        , withCredentials = False
                        }

                in
                    Http.request request_params
                        |> RemoteData.sendRequest
                        |> Cmd.map NewIdentityResponse

            Nothing ->
                Utils.performMsg (OperationFail "No new identity data.")


modifyIdentity : Model -> Cmd Msg
modifyIdentity model =
    let
        modified_preference = Form.getOutput model.edit_form
    in
        case modified_preference of
            Just selected_preference ->
                let
                    encoded_preference_list = Json.Encode.list (List.map encodePreference [selected_preference])


                    id_name =  -- TODO remove hard coded name, infer from retrieved_identity
                        case model.retrieved_identity of
                            Just identity -> identity
                            Nothing -> ""

                    msg_body = Json.Encode.object
                        [ ("preferences", encoded_preference_list)
                        ]

                    request_params =
                        { method = "POST"
                        , headers = []
                        , url = model.baseUrl ++ "/identity/" ++ id_name
                        , body = Http.jsonBody msg_body
                        , expect = Http.expectString
                        , timeout = Nothing
                        , withCredentials = False
                        }
                in
                    Http.request request_params
                        |> RemoteData.sendRequest
                        |> Cmd.map ModifyIdentityResponse

            Nothing ->
                Utils.performMsg (OperationFail "No preference selected.")



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
                    , expect = Http.expectString
                    , timeout = Nothing
                    , withCredentials = False
                    }

            in
                Http.request request_params
                |> RemoteData.sendRequest
                |> Cmd.map UrgencyDeleteResponse
