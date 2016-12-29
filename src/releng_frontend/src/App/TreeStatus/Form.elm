module App.TreeStatus.Form exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Form
import Form.Validate
import Form.Input
import Utils


type alias AddTree =
    { name : String }



validateAddTree : Form.Validate.Validation () AddTree
validateAddTree =
    Form.Validate.form1 AddTree
        (Form.Validate.get "name" Form.Validate.string)


viewAddTree : Form.Form () AddTree -> Html Form.Msg
viewAddTree form =
    let
        name =
            Form.getFieldAsString "name" form

        ( nameClass, nameError ) =
            case name.liveError of
                Just error ->
                    ( "input-group has-danger"
                    , div [ class "has-danger" ]
                        [ span [ class "form-control-feedback" ]
                            [ text (toString error) ]
                        ]
                    )

                Nothing ->
                    ( "input-group", text "" )
    in
        div [ class "list-group-item" ]
            [ h3 [] [ text "Add new tree" ]
            , Html.form
                []
                [ div [ class nameClass ]
                    [ Form.Input.textInput name
                        [ class "form-control"
                        , placeholder "Tree name ..."
                        ]
                    , span [ class "input-group-btn" ]
                        [ button
                            [ type' "submit"
                            , class "btn btn-secondary"
                            , Utils.onClick Form.Submit
                            ]
                            [ text "Add" ]
                        ]
                    ]
                , nameError
                ]
            ]
