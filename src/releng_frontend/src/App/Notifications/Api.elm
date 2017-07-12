-- IO/JSON ENCODE AND DECODE CODE HERE
module App.Notifications.Api exposing (..)

import Json.Decode exposing (..)
import Json.Encode
import App.Notifications.Types exposing (..)
import RemoteData
import RemoteData exposing (WebData)
import Http
import Utils
import Form


type alias NoBody = {}

-- Decoders / Encoders

encodePreference : App.Notifications.Types.Preference -> Json.Encode.Value
encodePreference preference =
    Json.Encode.object
        [ ("channel", Json.Encode.string preference.channel)
        , ("target", Json.Encode.string preference.target)
        , ("urgency", Json.Encode.string preference.urgency)
        ]


encodeInputPreference : App.Notifications.Types.InputPreference -> Json.Encode.Value
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
        Http.get (model.identityUrl ++ "/identity/" ++ identity) preferenceDecoder
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
            , url = model.identityUrl ++ "/identity/" ++ identity
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
                        , url = model.identityUrl ++ "/identity/" ++ new_identity.name
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
                        , url = model.identityUrl ++ "/identity/" ++ id_name
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
                    , url = model.identityUrl ++ "/identity/" ++ identity ++ "/" ++ preference.urgency
                    , body = Http.emptyBody
                    , expect = Http.expectString
                    , timeout = Nothing
                    , withCredentials = False
                    }

            in
                Http.request request_params
                |> RemoteData.sendRequest
                |> Cmd.map UrgencyDeleteResponse



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
    map5 Policy
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

notificationInstancesDecoder : Decoder NotificationInstances
notificationInstancesDecoder =
    let
        channel_field = field "channel" string
        message_field = field "message" string
        targets_field = field "targets" (list string)
        uid_field = field "uid" string
        dec =
            map4 NotificationInstance channel_field message_field targets_field uid_field
    in
        at [ "notifications" ] (list dec)


encodeFrequency : App.Notifications.Types.Frequency -> Json.Encode.Value
encodeFrequency frequency =
    Json.Encode.object
        [ ("minutes", Json.Encode.int frequency.minutes)
        , ("hours", Json.Encode.int frequency.hours)
        , ("days", Json.Encode.int frequency.days)
        ]


encodePolicy : App.Notifications.Types.Policy -> Json.Encode.Value
encodePolicy policy =
    Json.Encode.object
        [ ("identity", Json.Encode.string policy.identity)
        , ("frequency", encodeFrequency policy.frequency)
        , ("start_timestamp", Json.Encode.string policy.start_timestamp)
        , ("stop_timestamp", Json.Encode.string policy.stop_timestamp)
        , ("urgency", Json.Encode.string policy.urgency)
        ]


-- API Requests
getPendingMessages : Model -> Cmd Msg
getPendingMessages model =
    let
        request_url =
            model.policyUrl ++ "/message"
    in
        Http.get request_url messagesDecoder
            |> RemoteData.sendRequest
            |> Cmd.map GetPendingMessagesResponse

deleteMessage : Model -> Cmd Msg
deleteMessage model =
    let
        uid =
            case model.uid of
                Just val -> val
                Nothing -> ""

        request_url =
            model.policyUrl ++ "/message/" ++ uid

        request_params =
            { method = "DELETE"
            , headers = []
            , url = request_url
            , body = Http.emptyBody
            , expect = Http.expectString
            , timeout = Nothing
            , withCredentials = False
            }
    in
        Http.request request_params
            |> RemoteData.sendRequest
            |> Cmd.map DeleteMessageResponse

getMessageByUid : Model -> Cmd Msg
getMessageByUid model =
    let
        uid =
            case model.uid of
                Just val -> val
                Nothing -> ""

        request_url =
            model.policyUrl ++ "/message/" ++ uid
    in
        Http.get request_url messageDecoder
            |> RemoteData.sendRequest
            |> Cmd.map GetMessageResponse


putNewMessage : Model -> Cmd Msg
putNewMessage model =
    let
        new_message_output =
            Form.getOutput model.new_message

    in
        case new_message_output of
            Nothing ->
                Utils.performMsg (OperationFail "No new message data.")

            Just new_message ->
                let
                    encoded_policies =
                        Json.Encode.list (List.map encodePolicy new_message.policies)

                    msg_body =
                        Json.Encode.object
                            [ ("deadline", Json.Encode.string new_message.deadline)
                            , ("message", Json.Encode.string new_message.message)
                            , ("shortMessage", Json.Encode.string new_message.shortMessage)
                            , ("policies", encoded_policies)
                            ]

                    request_params =
                        { method = "PUT"
                        , headers = []
                        , url = model.policyUrl ++ "/message/" ++ "fillerUID"  -- TODO: fix filler uid
                        , body = Http.jsonBody msg_body
                        , expect = Http.expectString
                        , timeout = Nothing
                        , withCredentials = False
                        }
                in
                    Http.request request_params
                        |> RemoteData.sendRequest
                        |> Cmd.map NewMessageResponse


getActivePolicies : Model -> Cmd Msg
getActivePolicies model =
    let
        identity =
            case model.identity_name of
                Just name -> name
                Nothing -> ""

        request_url =
            model.policyUrl ++ "/policy/" ++ identity


    in
        Http.get request_url policiesDecoder
            |> RemoteData.sendRequest
            |> Cmd.map GetActivePoliciesResponse


tickTock : Model -> Cmd Msg
tickTock model =
    Http.get (model.policyUrl ++ "/ticktock") notificationInstancesDecoder
        |> RemoteData.sendRequest
        |> Cmd.map TickTockResponse
