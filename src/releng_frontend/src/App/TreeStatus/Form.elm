module App.TreeStatus.Form exposing (..)

import App.TreeStatus.Api
import App.TreeStatus.Types
import Form
import Form.Error
import Form.Field
import Form.Input
import Form.Validate
import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Json.Encode as JsonEncode
import RemoteData
import Utils


type alias AddTree =
    { name : String }


type alias UpdateTree =
    { name : String
    , status : String
    , reason : String
    , message_of_the_day : String
    }


validateAddTree : Form.Validate.Validation () AddTree
validateAddTree =
    Form.Validate.form1 AddTree
        (Form.Validate.get "name" Form.Validate.string)

validateTreeStatus : Form.Field.Field -> Result (Form.Error.Error a) String
validateTreeStatus =
    Form.Validate.string
        `Form.Validate.andThen` Form.Validate.includedIn [ "open"
                                                          , "approval required"
                                                          , "closed"
                                                          ]


validateUpdateTree : Form.Validate.Validation () UpdateTree
validateUpdateTree =
    Form.Validate.form4 UpdateTree
        (Form.Validate.get "name" Form.Validate.string)
        (Form.Validate.get "status" Form.Validate.string)
        (Form.Validate.get "reason" Form.Validate.string)
        (Form.Validate.get "message_of_the_day" Form.Validate.string)


initAddTreeFields : List ( String, Form.Field.Field )
initAddTreeFields =
    [ ( "name", Form.Field.Text "" ) ]


initUpdateTreeFields : List ( String, Form.Field.Field )
initUpdateTreeFields =
    [ ( "name", Form.Field.Text "" )
    , ( "status", Form.Field.Text "" )
    , ( "reason", Form.Field.Text "" )
    , ( "message_of_the_day", Form.Field.Text "" )
    ]


initAddTree : Form.Form () AddTree
initAddTree =
    Form.initial initAddTreeFields validateAddTree


initUpdateTree : Form.Form () UpdateTree
initUpdateTree =
    Form.initial initUpdateTreeFields validateUpdateTree


resetAddTree : Form.Msg
resetAddTree =
    Form.Reset initAddTreeFields


resetUpdateTree : Form.Msg
resetUpdateTree =
    Form.Reset initUpdateTreeFields


updateAddTree :
    App.TreeStatus.Types.Model AddTree UpdateTree
    -> Form.Msg
    -> ( App.TreeStatus.Types.Model AddTree UpdateTree, Maybe { request : Http.Request, route : String } )
updateAddTree model formMsg =
    let
        form =
            Form.update formMsg model.formAddTree

        tree name =
            App.TreeStatus.Types.Tree name "closed" "new tree" ""

        treeStr name =
            JsonEncode.encode 0 (App.TreeStatus.Api.encoderTree (tree name))

        newTreeRequest name =
            Http.Request
                "PUT"
                -- probably this should be in Hawk.elm
                [ ( "Accept", "application/json" )
                , ( "Content-Type", "application/json" )
                ]
                (model.baseUrl ++ "/trees/" ++ name)
                (Http.string (treeStr name))

        ( trees, alerts, hawkRequest ) =
            case formMsg of
                Form.Submit ->
                    if Form.getErrors form /= [] then
                        ( model.trees, [], Nothing )
                    else
                        -- opurtonistic update
                        ( Form.getOutput form
                            |> Maybe.map (\x -> [ tree x.name ])
                            |> Maybe.withDefault []
                            |> (\y -> RemoteData.map (\x -> List.append x y) model.trees)
                        , []
                        , Form.getOutput form
                            |> Maybe.map (\x -> { route = "AddTree", request = newTreeRequest x.name })
                        )

                _ ->
                    ( model.trees, model.alerts, Nothing )
    in
        ( { model
            | formAddTree = form
            , alerts = alerts
            , trees = trees
          }
        , hawkRequest
        )


updateUpdateTree :
    App.TreeStatus.Types.Model AddTree UpdateTree
    -> Form.Msg
    -> ( App.TreeStatus.Types.Model AddTree UpdateTree, Maybe { request : Http.Request, route : String } )
updateUpdateTree model formMsg =
    ( model
    , Nothing
    )


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
        div [ class "list-group" ]
            [ div [ class "list-group-item" ]
                [ h3 [] [ text "Would you like to create new tree?" ]
                , Html.form
                    []
                    [ div [ class nameClass ]
                        [ Form.Input.textInput name
                            [ class "form-control"
                            , placeholder "Tree name ..."
                            , value (Maybe.withDefault "" name.value)
                            ]
                        , span [ class "input-group-btn" ]
                            [ button
                                [ type' "submit"
                                , class "btn btn-outline-primary"
                                , Utils.onClick Form.Submit
                                ]
                                [ text "Add" ]
                            ]
                        ]
                    , nameError
                    ]
                ]
            ]


viewUpdateTree : Form.Form () UpdateTree -> Html Form.Msg
viewUpdateTree form =
    div [ class "list-group" ]
        [ div [ class "list-group-item" ]
              [ h3 [] [ text ("Would you like to update (???) selected trees?") ]
              ]
        ]
