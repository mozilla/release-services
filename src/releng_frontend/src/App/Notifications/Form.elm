-- FORM/INPUT VALIDATION CODE HERE


module App.Notifications.Form exposing (..)

import App.Notifications.Types
import App.Notifications.Utils exposing (urgencyLevel)
import Form exposing (Form)
import Form.Field
import Form.Init as Init
import Form.Input as Input
import Form.Validate as Validate exposing (..)
import Html exposing (..)
import Html.Attributes exposing (class, placeholder)
import Html.Events exposing (onClick)


--
-- INITIALIZERS
--


initializeFormFromPreference : App.Notifications.Types.Preference -> Form.Form () App.Notifications.Types.Preference
initializeFormFromPreference preference =
    let
        channelTuple =
            Init.setString "channel" preference.channel

        targetTuple =
            Init.setString "target" preference.target

        nameTuple =
            case preference.name of
                Just name ->
                    Init.setString "name" name

                Nothing ->
                    Init.setString "name" ""

        urgencyTuple =
            Init.setString "urgency" preference.urgency
    in
        Form.initial [ channelTuple, targetTuple, nameTuple, urgencyTuple ] preferenceValidation


initializeNewIdentityForm : Form.Form () App.Notifications.Types.Identity
initializeNewIdentityForm =
    let
        nameField =
            Init.setString "name" ""

        channelTuple =
            Init.setString "channel" "EMAIL"

        targetTuple =
            Init.setString "target" ""

        nameTuple =
            Init.setString "name" ""

        lowUrgencyTuple =
            Init.setString "urgency" "LOW"

        highUrgencyTuple =
            Init.setString "urgency" "NORMAL"

        normalUrgencyTuple =
            Init.setString "urgency" "HIGH"

        preferencesList =
            Init.setList "preferences"
                [ Form.Field.group [ channelTuple, targetTuple, nameTuple, lowUrgencyTuple ]
                , Form.Field.group [ channelTuple, targetTuple, nameTuple, normalUrgencyTuple ]
                , Form.Field.group [ channelTuple, targetTuple, nameTuple, highUrgencyTuple ]
                ]
    in
        Form.initial [ nameField, preferencesList ] newIdentityValidation



--
-- VALIDATORS
--


preferenceValidation : Validation () App.Notifications.Types.Preference
preferenceValidation =
    map4 App.Notifications.Types.Preference
        (field "channel" string)
        (maybe (field "name" string))
        (field "target" string)
        (field "urgency" string)


newIdentityValidation : Validation () App.Notifications.Types.Identity
newIdentityValidation =
    map2 App.Notifications.Types.Identity
        (field "name" string)
        (field "preferences" (list preferenceValidation))


frequencyValidation : Validation () App.Notifications.Types.Frequency
frequencyValidation =
    map3 App.Notifications.Types.Frequency
        (field "minutes" int)
        (field "hours" int)
        (field "days" int)


policyValidation : Validation () App.Notifications.Types.Policy
policyValidation =
    map6 App.Notifications.Types.Policy
        (field "uid" string)
        (field "identity" string)
        (field "start_timestamp" string)
        (field "stop_timestamp" string)
        (field "urgency" string)
        (field "frequency" frequencyValidation)



--
-- FORM VIEWS
--


editPreferenceFormView : Form () App.Notifications.Types.Preference -> Html Form.Msg
editPreferenceFormView form =
    let
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
            [ ( "IRC", "IRC" )
            , ( "EMAIL", "EMAIL" )
            ]

        is_missing_target =
            case target.liveError of
                Just error ->
                    True

                Nothing ->
                    False
    in
        div
            [ class
                ("justify-content-between form-group form-inline"
                    ++ (if is_missing_target == True then
                            " has-danger"
                        else
                            ""
                       )
                )
            ]
            [ hr [] []
            , Input.selectInput channel_options channel [ class "form-control" ]
            , Input.textInput target
                [ class
                    ("form-control"
                        ++ (if is_missing_target == True then
                                " form-control-danger"
                            else
                                ""
                           )
                    )
                ]
            , button [ onClick Form.Submit, class "btn btn-outline-primary form-control" ]
                [ i [ class "fa fa-check" ] []
                , text " Submit"
                ]
            ]


editNewPreferenceFormView : Form () App.Notifications.Types.Identity -> Int -> Html Form.Msg
editNewPreferenceFormView form_ i =
    let
        -- Field states
        channel =
            Form.getFieldAsString ("preferences." ++ toString i ++ ".channel") form_

        placeholderText =
            case channel.value of
                Just value ->
                    case value of
                        "EMAIL" ->
                            "Email Address"

                        "IRC" ->
                            "IRC Nick or #channel"

                        _ ->
                            ""

                Nothing ->
                    ""

        name =
            Form.getFieldAsString "name" form_

        target =
            Form.getFieldAsString ("preferences." ++ toString i ++ ".target") form_

        urgency =
            Form.getFieldAsString ("preferences." ++ toString i ++ ".urgency") form_

        urgency_string =
            case urgency.value of
                Just urgency ->
                    urgency

                Nothing ->
                    ""

        channel_options =
            [ ( "IRC", "IRC" )
            , ( "EMAIL", "EMAIL" )
            ]

        urgency_options =
            [ ( "LOW", "LOW" )
            , ( "NORMAL", "NORMAL" )
            , ( "HIGH", "HIGH" )
            ]

        is_missing_target =
            case target.value of
                Just value ->
                    if String.isEmpty value then
                        True
                    else
                        False

                Nothing ->
                    True
    in
        form
            [ class
                ("list-group-item form-inline d-inline-flex justify-content-between"
                    ++ (if is_missing_target == True then
                            " has-danger"
                        else
                            ""
                       )
                )
            ]
            [ Input.selectInput channel_options channel [ class "form-control" ]
            , Input.textInput target
                [ class
                    ("form-control align-self-stretch"
                        ++ (if is_missing_target == True then
                                " form-control-danger"
                            else
                                ""
                           )
                    )
                , placeholder placeholderText
                ]
            , span [ class ("float-xs-right badge badge-" ++ urgencyLevel urgency_string) ] [ text urgency_string ]
            ]


newIdentityFormView : Form () App.Notifications.Types.Identity -> Html Form.Msg
newIdentityFormView form =
    let
        name =
            Form.getFieldAsString "name" form

        list_indexes =
            Form.getListIndexes "preferences" form

        is_missing_name =
            case name.liveError of
                Just error ->
                    True

                Nothing ->
                    False
    in
        div
            [ class
                ("form-group"
                    ++ (if is_missing_name == True then
                            " has-danger"
                        else
                            ""
                       )
                )
            ]
            [ hr [] []
            , h3 [] [ text "Create new identity" ]
            , Input.textInput name
                [ placeholder "New Identity Name"
                , class
                    ("form-control"
                        ++ (if is_missing_name == True then
                                " form-control-danger"
                            else
                                ""
                           )
                    )
                ]
            , div [ class "list-group" ] <|
                List.map (editNewPreferenceFormView form) list_indexes
            , button [ onClick Form.Submit, class "btn btn-outline-primary form-control" ]
                [ i [ class "fa fa-check" ] [ text " Submit Identity" ]
                ]
            ]


viewEditPreference : App.Notifications.Types.Model -> Html App.Notifications.Types.Msg
viewEditPreference model =
    Html.map App.Notifications.Types.EditPreferenceFormMsg (editPreferenceFormView model.edit_form)


viewNewIdentity : App.Notifications.Types.Model -> Html App.Notifications.Types.Msg
viewNewIdentity model =
    Html.map App.Notifications.Types.NewIdentityFormMsg (newIdentityFormView model.new_identity)
