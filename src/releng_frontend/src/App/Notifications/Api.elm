-- IO/JSON ENCODE AND DECODE CODE HERE


module App.Notifications.Api exposing (..)

import App.Notifications.Types exposing (..)
import Json.Decode exposing (..)
import Json.Encode
import RemoteData exposing (WebData)


-- Decoders / Encoders


encodePreference : App.Notifications.Types.Preference -> Json.Encode.Value
encodePreference preference =
    Json.Encode.object
        [ ( "channel", Json.Encode.string preference.channel )
        , ( "target", Json.Encode.string preference.target )
        , ( "urgency", Json.Encode.string preference.urgency )
        ]


preferenceDecoder : Decoder Preferences
preferenceDecoder =
    let
        channel_field =
            field "channel" string

        name_field =
            maybe (field "name" string)

        target_field =
            field "target" string

        urgency_field =
            field "urgency" string

        dec =
            map4 Preference channel_field name_field target_field urgency_field
    in
    at [ "preferences" ] (list dec)


problemDecoder : Decoder ApiProblem
problemDecoder =
    let
        detail =
            maybe (field "detail" string)

        instance =
            maybe (field "instance" string)

        status =
            maybe (field "status" int)

        title =
            maybe (field "title" string)

        type_ =
            maybe (field "type" string)
    in
    map5 ApiProblem detail instance status title type_



--
-- NOTIFICATION POLICY COMPONENTS
--


frequencyDecoder : Decoder Frequency
frequencyDecoder =
    map3 Frequency
        (field "minutes" int)
        (field "hours" int)
        (field "days" int)


policyDecoder : Decoder Policy
policyDecoder =
    map6 Policy
        (field "uid" string)
        (field "identity" string)
        (field "start_timestamp" string)
        (field "stop_timestamp" string)
        (field "urgency" string)
        (field "frequency" frequencyDecoder)


policiesDecoder : Decoder (List Policy)
policiesDecoder =
    at [ "policies" ] (list policyDecoder)


messageDecoder : Decoder MessageInstance
messageDecoder =
    map4 MessageInstance
        (field "deadline" string)
        (field "message" string)
        (field "shortMessage" string)
        (field "policies" (list policyDecoder))


messagesDecoder : Decoder (List MessageInstance)
messagesDecoder =
    at [ "messages" ] (list messageDecoder)


encodeFrequency : App.Notifications.Types.Frequency -> Json.Encode.Value
encodeFrequency frequency =
    Json.Encode.object
        [ ( "minutes", Json.Encode.int frequency.minutes )
        , ( "hours", Json.Encode.int frequency.hours )
        , ( "days", Json.Encode.int frequency.days )
        ]


encodePolicy : App.Notifications.Types.Policy -> Json.Encode.Value
encodePolicy policy =
    Json.Encode.object
        [ ( "identity", Json.Encode.string policy.identity )
        , ( "frequency", encodeFrequency policy.frequency )
        , ( "start_timestamp", Json.Encode.string policy.start_timestamp )
        , ( "stop_timestamp", Json.Encode.string policy.stop_timestamp )
        , ( "urgency", Json.Encode.string policy.urgency )
        ]


hawkResponse : Cmd (WebData String) -> String -> Cmd App.Notifications.Types.Msg
hawkResponse response route =
    case route of
        "DeleteMessage" ->
            Cmd.map App.Notifications.Types.DeleteMessageResponse response

        "GetActivePolicies" ->
            Cmd.map App.Notifications.Types.GetActivePoliciesResponse response

        "GetMessage" ->
            Cmd.map App.Notifications.Types.GetMessageResponse response

        "GetPendingMessages" ->
            Cmd.map App.Notifications.Types.GetPendingMessagesResponse response

        "GetPreferences" ->
            Cmd.map App.Notifications.Types.GetPreferencesResponse response

        "IdentityDelete" ->
            Cmd.map App.Notifications.Types.IdentityDeleteResponse response

        "ModifyIdentity" ->
            Cmd.map App.Notifications.Types.ModifyIdentityResponse response

        "NewIdentity" ->
            Cmd.map App.Notifications.Types.NewIdentityResponse response

        "NewMessage" ->
            Cmd.map App.Notifications.Types.NewMessageResponse response

        "TickTock" ->
            Cmd.map App.Notifications.Types.TickTockResponse response

        "UrgencyDelete" ->
            Cmd.map App.Notifications.Types.UrgencyDeleteResponse response

        _ ->
            Cmd.none
