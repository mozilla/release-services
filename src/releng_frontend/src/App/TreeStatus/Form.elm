module App.TreeStatus.Form exposing (..)

import App.TreeStatus.Api
import App.TreeStatus.Types
import Form
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


validateAddTree : Form.Validate.Validation () AddTree
validateAddTree =
    Form.Validate.form1 AddTree
        (Form.Validate.get "name" Form.Validate.string)


initAddTreeFields : List ( String, Form.Field.Field )
initAddTreeFields =
    [ ( "name", Form.Field.Text "" ) ]


initAddTree : Form.Form () AddTree
initAddTree =
    Form.initial initAddTreeFields validateAddTree


resetAddTree : Form.Msg
resetAddTree =
    Form.Reset initAddTreeFields


updateAddTree :
    App.TreeStatus.Types.Model AddTree
    -> Form.Msg
    -> ( App.TreeStatus.Types.Model AddTree, Maybe { request : Http.Request, route : String } )
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

        ( trees, error, hawkRequest ) =
            case formMsg of
                Form.Submit ->
                    if Form.getErrors form /= [] then
                        ( model.trees, Nothing, Nothing )
                    else
                        -- opurtonistic update
                        ( Form.getOutput form
                            |> Maybe.map (\x -> [ tree x.name ])
                            |> Maybe.withDefault []
                            |> (\y -> RemoteData.map (\x -> List.append x y) model.trees)
                        , Nothing
                        , Form.getOutput form
                            |> Maybe.map (\x -> { route = "AddTree", request = newTreeRequest x.name })
                        )

                _ ->
                    ( model.trees, model.formAddTreeError, Nothing )
    in
        ( { model
            | formAddTree = form
            , formAddTreeError = error
            , trees = trees
          }
        , hawkRequest
        )


viewAddTree : Form.Form () AddTree -> Maybe String -> Html Form.Msg
viewAddTree form error =
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

        errorNode =
            error
                |> Maybe.map
                    (\x ->
                        div [ class "alert alert-danger" ]
                            [ text x ]
                    )
                |> Maybe.withDefault (div [] [])
    in
        div [ class "list-group-item" ]
            [ h3 [] [ text "Add new tree" ]
            , errorNode
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
                            , class "btn btn-primary"
                            , Utils.onClick Form.Submit
                            ]
                            [ text "Add" ]
                        ]
                    ]
                , nameError
                ]
            ]
