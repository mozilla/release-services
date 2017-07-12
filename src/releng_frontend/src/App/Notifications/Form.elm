-- FORM/INPUT VALIDATION CODE HERE
module App.Notifications.Form exposing (..)

import App.Notifications.Types
import App.Notifications.Utils exposing (urgencyLevel)
import Html exposing (..)
import Html.Attributes exposing (class, placeholder)
import Html.Events exposing (onClick)
import Form exposing (Form)
import Form.Validate as Validate exposing (..)
import Form.Input as Input
import Form.Init as Init
import Form.Field


initializeFormFromPreference : App.Notifications.Types.Preference -> Form.Form () App.Notifications.Types.Preference
initializeFormFromPreference preference =
    let
        channelTuple = Init.setString "channel" preference.channel
        targetTuple = Init.setString "target" preference.target
        nameTuple = Init.setString "name" preference.name
        urgencyTuple = Init.setString "urgency" preference.urgency
    in
        Form.initial [channelTuple, targetTuple, nameTuple, urgencyTuple] editPreferenceValidation


initializeNewIdentityForm : Form.Form () App.Notifications.Types.Identity
initializeNewIdentityForm =
    let
        nameField = Init.setString "name" ""

        channelTuple = Init.setString "channel" "EMAIL"
        targetTuple = Init.setString "target" ""
        nameTuple = Init.setString "name" ""

        lowUrgencyTuple = Init.setString "urgency" "LOW"
        highUrgencyTuple = Init.setString "urgency" "NORMAL"
        normalUrgencyTuple = Init.setString "urgency" "HIGH"

        preferencesList = Init.setList "preferences"
            [ Form.Field.group [channelTuple, targetTuple, nameTuple, lowUrgencyTuple]
            , Form.Field.group [channelTuple, targetTuple, nameTuple, normalUrgencyTuple]
            , Form.Field.group [channelTuple, targetTuple, nameTuple, highUrgencyTuple]
            ]
    in
        Form.initial [nameField, preferencesList] newIdentityValidation


editPreferenceValidation : Validation () App.Notifications.Types.Preference
editPreferenceValidation =
    map4 App.Notifications.Types.Preference
        (field "channel" string)
        (field "name" string)
        (field "target" string)
        (field "urgency" string)


newPreferenceValidation : Validation () App.Notifications.Types.InputPreference
newPreferenceValidation =
    map3 App.Notifications.Types.InputPreference
        (field "channel" string)
        (field "target" string)
        (field "urgency" string)


newIdentityValidation : Validation () App.Notifications.Types.Identity
newIdentityValidation =
    map2 App.Notifications.Types.Identity
        (field "name" string)
        (field "preferences" (list newPreferenceValidation))


newMessageValidation : Validation () App.Notifications.Types.MessageInstance
newMessageValidation =
    map4 App.Notifications.Types.MessageInstance
        (field "deadline" string)
        (field "message" string)
        (field "shortMessage" string)
        (field "policies" (list policyValidation))


frequencyValidation : Validation () App.Notifications.Types.Frequency
frequencyValidation =
    map3 App.Notifications.Types.Frequency
        (field "minutes" int)
        (field "hours" int)
        (field "days" int)

policyValidation : Validation () App.Notifications.Types.Policy
policyValidation =
    map5 App.Notifications.Types.Policy
        (field "identity" string)
        (field "start_timestamp" string)
        (field "stop_timestamp" string)
        (field "urgency" string)
        (field "frequency" frequencyValidation)

editPreferenceFormView : Form () App.Notifications.Types.Preference -> Html Form.Msg
editPreferenceFormView form =
    let
        -- Error presentation
        errorFor preferenceField =
            case preferenceField.liveError of
                Just error ->
                    div [ class "error" ] [ text (toString error) ]
                Nothing ->
                    text ""

        -- Field states
        channel =
            Form.getFieldAsString "channel" form

        name =
            Form.getFieldAsString "name" form

        target =
            Form.getFieldAsString "target" form

        urgency =
            Form.getFieldAsString "urgency" form

        channel_options =
            [ ("IRC", "IRC")
            , ("EMAIL", "EMAIL")
            ]
    in
        div []
            [ Input.selectInput channel_options channel []
            , Input.textInput target []
            , button [ onClick Form.Submit ]
                [ i [ class "fa fa-floppy-o" ] []
                , text " Save"
                ]
            , button [ onClick (Form.RemoveItem "" 0) ]
                [ i [ class "fa fa-trash" ] []
                , text " Delete"
                ]
            , errorFor channel
            , errorFor target
            ]


editNewPreferenceFormView : Form () App.Notifications.Types.Identity -> Int -> Html Form.Msg
editNewPreferenceFormView form i =
    let
        -- Field states
        channel =
            Form.getFieldAsString ("preferences." ++ (toString i) ++ ".channel" ) form

        name =
            Form.getFieldAsString "name" form

        target =
            Form.getFieldAsString ("preferences." ++ (toString i) ++ ".target" ) form

        urgency =
            Form.getFieldAsString ("preferences." ++ (toString i) ++ ".urgency" ) form

        urgency_string =
            case urgency.value of
                Just urgency -> urgency
                Nothing -> ""

        channel_options =
            [ ("IRC", "IRC")
            , ("EMAIL", "EMAIL")
            ]

        urgency_options =
            [ ("LOW", "LOW")
            , ("NORMAL", "NORMAL")
            , ("HIGH", "HIGH")
            ]
    in
        div [ class "list-group-item justify-content-between" ]
            [ Input.selectInput channel_options channel []
            , Input.textInput target []
            , span [ class ("float-xs-right badge badge-" ++ (urgencyLevel urgency_string)) ] [ text urgency_string ]
            ]


newIdentityFormView : Form () App.Notifications.Types.Identity -> Html Form.Msg
newIdentityFormView form =
    let
        name = Form.getFieldAsString "name" form
        list_indexes = Form.getListIndexes "preferences" form
    in
        div []
            [ hr [] []
            , h3 [] [ text "Create new identity" ]
            , Input.textInput name [ placeholder "New Identity Name" ]
            , div []
                [ div [ class "list-group" ]
                    <| List.map (editNewPreferenceFormView form) list_indexes

                ]
            , button [ onClick Form.Submit ]
                [ i [ class "fa fa-floppy-o" ] [ text " Submit Identity" ]
                ]
            ]


viewEditPreference : App.Notifications.Types.Model -> Html App.Notifications.Types.Msg
viewEditPreference model =
    Html.map App.Notifications.Types.EditPreferenceFormMsg (editPreferenceFormView model.edit_form)


viewNewIdentity : App.Notifications.Types.Model -> Html App.Notifications.Types.Msg
viewNewIdentity model =
    Html.map App.Notifications.Types.NewIdentityFormMsg (newIdentityFormView model.new_identity)
