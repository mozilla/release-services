-- FORM/INPUT VALIDATION CODE HERE
module App.NotificationIdentity.Form exposing (..)

import App.NotificationIdentity.Types
import App.NotificationIdentity.Utils exposing (urgencyLevel)
import Html exposing (..)
import Html.Attributes exposing (class, placeholder)
import Html.Events exposing (onClick)
import Form exposing (Form)
import Form.Validate as Validate exposing (..)
import Form.Input as Input
import Form.Init as Init
import Form.Field


initializeFormFromPreference : App.NotificationIdentity.Types.Preference -> Form.Form () App.NotificationIdentity.Types.Preference
initializeFormFromPreference preference =
    let
        channelTuple = Init.setString "channel" preference.channel
        targetTuple = Init.setString "target" preference.target
        nameTuple = Init.setString "name" preference.name
        urgencyTuple = Init.setString "urgency" preference.urgency
    in
        Form.initial [channelTuple, targetTuple, nameTuple, urgencyTuple] editPreferenceValidation


initializeNewIdentityForm : Form.Form () App.NotificationIdentity.Types.Identity
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


editPreferenceValidation : Validation () App.NotificationIdentity.Types.Preference
editPreferenceValidation =
    map4 App.NotificationIdentity.Types.Preference
        (field "channel" string)
        (field "name" string)
        (field "target" string)
        (field "urgency" string)


newPreferenceValidation : Validation () App.NotificationIdentity.Types.InputPreference
newPreferenceValidation =
    map3 App.NotificationIdentity.Types.InputPreference
        (field "channel" string)
        (field "target" string)
        (field "urgency" string)


newIdentityValidation : Validation () App.NotificationIdentity.Types.Identity
newIdentityValidation =
    map2 App.NotificationIdentity.Types.Identity
        (field "name" string)
        (field "preferences" (list newPreferenceValidation))


editPreferenceFormView : Form () App.NotificationIdentity.Types.Preference -> Html Form.Msg
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


editNewPreferenceFormView : Form () App.NotificationIdentity.Types.Identity -> Int -> Html Form.Msg
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


newIdentityFormView : Form () App.NotificationIdentity.Types.Identity -> Html Form.Msg
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


viewEditPreference : App.NotificationIdentity.Types.Model -> Html App.NotificationIdentity.Types.Msg
viewEditPreference model =
    Html.map App.NotificationIdentity.Types.EditPreferenceFormMsg (editPreferenceFormView model.edit_form)


viewNewIdentity : App.NotificationIdentity.Types.Model -> Html App.NotificationIdentity.Types.Msg
viewNewIdentity model =
    Html.map App.NotificationIdentity.Types.NewIdentityFormMsg (newIdentityFormView model.new_identity)
