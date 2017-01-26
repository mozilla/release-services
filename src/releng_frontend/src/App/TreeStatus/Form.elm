module App.TreeStatus.Form exposing (..)

import App.TreeStatus.Api
import App.TreeStatus.Types
import App.Form
import App.Utils
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
import String
import Utils


type alias AddTree =
    { name : String }


type alias UpadateTreeTags =
    { checkin_compilation : Bool
    , checkin_test : Bool
    , infra : Bool
    , backlog : Bool
    , planned : Bool
    , other : Bool
    }


type alias UpdateTree =
    { status : String
    , reason : String
    , message_of_the_day : String
    , tags : UpadateTreeTags
    , remember : Bool
    }


validateAddTree : Form.Validate.Validation () AddTree
validateAddTree =
    Form.Validate.form1 AddTree
        (Form.Validate.get "name" Form.Validate.string)


validateUpdateTreeTags : Form.Field.Field -> Result (Form.Error.Error a) UpadateTreeTags
validateUpdateTreeTags =
    Form.Validate.form6 UpadateTreeTags
        (Form.Validate.get "checkin_compilation" Form.Validate.bool)
        (Form.Validate.get "checkin_test" Form.Validate.bool)
        (Form.Validate.get "infra" Form.Validate.bool)
        (Form.Validate.get "backlog" Form.Validate.bool)
        (Form.Validate.get "planned" Form.Validate.bool)
        (Form.Validate.get "other" Form.Validate.bool)


validateUpdateTree : Form.Validate.Validation () UpdateTree
validateUpdateTree =
    Form.Validate.form5 UpdateTree
        (Form.Validate.get "status" Form.Validate.string)
        (Form.Validate.get "reason" Form.Validate.string
            |> Form.Validate.defaultValue ""
        )
        (Form.Validate.get "message_of_the_day" Form.Validate.string
            |> Form.Validate.defaultValue ""
        )
        (Form.Validate.get "tags" validateUpdateTreeTags)
        (Form.Validate.get "remember" Form.Validate.bool)


initAddTreeFields : List ( String, Form.Field.Field )
initAddTreeFields =
    [ ( "name", Form.Field.Text "" ) ]


initUpdateTreeFields : List ( String, Form.Field.Field )
initUpdateTreeFields =
    [ ( "status", Form.Field.Text "" )
    , ( "reason", Form.Field.Text "" )
    , ( "message_of_the_day", Form.Field.Text "" )
    , ( "tags"
      , App.TreeStatus.Types.possibleTreeTags
            |> List.map (\( _, x, _ ) -> ( x, Form.Field.Check False ))
            |> Form.Field.group
      )
    , ( "remember", Form.Field.Check True )
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
                    ( model.trees, model.treesAlerts, Nothing )
    in
        ( { model
            | formAddTree = form
            , treesAlerts = alerts
            , trees = trees
          }
        , hawkRequest
        )


updateUpdateTree :
    App.TreeStatus.Types.Route
    -> App.TreeStatus.Types.Model AddTree UpdateTree
    -> Form.Msg
    -> ( App.TreeStatus.Types.Model AddTree UpdateTree, Maybe { request : Http.Request, route : String } )
updateUpdateTree route model formMsg =
    let
        form =
            Form.update formMsg model.formUpdateTree

        tagsToList tags =
            List.filterMap
                (\( x, y ) ->
                    if y then
                        Just x
                    else
                        Nothing
                )
                [ ( "checkin-compilation", tags.checkin_compilation )
                , ( "checkin-test", tags.checkin_test )
                , ( "infra", tags.infra )
                , ( "backlog", tags.backlog )
                , ( "planned", tags.planned )
                , ( "other", tags.other )
                ]

        createRequest data =
            Http.Request
                "PATCH"
                [ ( "Accept", "application/json" )
                , ( "Content-Type", "application/json" )
                ]
                (model.baseUrl ++ "/trees")
                ((if List.length model.treesSelected /= 1 then
                    ({ trees = model.treesSelected
                     , status = data.status
                     , reason = data.reason
                     , tags = tagsToList data.tags
                     , remember = data.remember
                     }
                        |> App.TreeStatus.Api.encoderUpdateTrees
                    )
                  else
                    ({ trees = model.treesSelected
                     , status = data.status
                     , reason = data.reason
                     , tags = tagsToList data.tags
                     , message_of_the_day = data.message_of_the_day
                     , remember = data.remember
                     }
                        |> App.TreeStatus.Api.encoderUpdateTree
                    )
                 )
                    |> JsonEncode.encode 0
                    |> Http.string
                )

        ( alerts, hawkRequest ) =
            case formMsg of
                Form.Submit ->
                    if getUpdateTreeErrors form /= [] then
                        ( [], Nothing )
                    else
                        ( []
                        , Form.getOutput form
                            |> Maybe.map
                                (\x ->
                                    { route = "UpdateTrees"
                                    , request = createRequest x
                                    }
                                )
                        )

                _ ->
                    ( model.treesAlerts, Nothing )
    in
        ( { model
            | formUpdateTree = form
            , treesAlerts = alerts
          }
        , Debug.log "HAWK REQUEST" hawkRequest
        )


getUpdateTreeErrors form =
    let
        validateReason form =
            let
                status =
                    Form.getFieldAsString "status" form

                reason =
                    Form.getFieldAsString "reason" form
            in
                if
                    Maybe.withDefault "" status.value
                        == "closed"
                        && Maybe.withDefault "" reason.value
                        == ""
                then
                    [ ( "reason", Form.Error.Empty ) ]
                else
                    []
    in
        Form.getErrors form
            |> List.append (validateReason form)


fieldClass : { b | error : Maybe a } -> String
fieldClass field =
    case field.error of
        Just error ->
            "input-group has-danger"

        Nothing ->
            "input-group "


fieldError : { b | error : Maybe a } -> Html c
fieldError field =
    case field.error of
        Just error ->
            div [ class "has-danger" ]
                [ span [ class "form-control-feedback" ]
                    [ text (toString error) ]
                ]

        Nothing ->
            text ""


viewAddTree : Form.Form () AddTree -> Html Form.Msg
viewAddTree form =
    let
        state =
            Form.getFieldAsString "name" form
    in
        div
            [ id "treestatus-form" ]
            [ Html.form
                []
                [ App.Form.viewField
                    (if Form.isSubmitted form then
                        state.error
                     else
                        Nothing
                    )
                    (Just "Tree name")
                    []
                    (Form.Input.textInput state
                        [ class "form-control"
                        , value (Maybe.withDefault "" state.value)
                        , placeholder "New tree name ..."
                        ]
                    )
                , App.Form.viewButton
                    "Add"
                    [ Utils.onClick Form.Submit
                    ]
                , div [ class "clearfix" ] []
                ]
            ]


viewUpdateTree :
    List String
    -> RemoteData.WebData App.TreeStatus.Types.Trees
    -> Form.Form () UpdateTree
    -> Html Form.Msg
viewUpdateTree treesSelected trees form =
    div [ id "treestatus-form" ]
        [ div
            []
            ([]
                |> App.Utils.appendItem
                    (text "You are about to update the following trees:")
                |> App.Utils.appendItem
                    (treesSelected
                        |> List.map (\x -> li [] [ text x ])
                        |> ul []
                    )
            )
        , hr [] []
        , Html.form
            []
            [ App.Form.viewSelectInput
                (Form.getFieldAsString "status" form)
                "Status"
                []
                (App.TreeStatus.Types.possibleTreeStatuses
                    |> List.append [ ( "", "" ) ]
                )
                []
            , div
                [ class "form-group" ]
                [ label [ class "control-label" ] [ text "Tags" ]
                , div
                    []
                    (List.map
                        (\( _, x, y ) ->
                            App.Form.viewCheckboxInput
                                (Form.getFieldAsBool ("tags." ++ x) form)
                                y
                        )
                        App.TreeStatus.Types.possibleTreeTags
                    )
                ]
            , App.Form.viewTextInput
                (Form.getFieldAsString "reason" form)
                (if (Form.getFieldAsString "status" form).value == Just "closed" then
                    "Reason (required to close)"
                 else
                    "Reason"
                )
                [ small
                    [ class "form-text text-muted" ]
                    [ p []
                        [ text
                            ("Please indicate the reason for "
                                ++ "closure, preferably with a bug link."
                            )
                        ]
                    , p []
                        [ text
                            ("Please indicate conditions for "
                                ++ "reopening, especially if you might "
                                ++ "disappear before reopening the "
                                ++ "tree yourself."
                            )
                        ]
                    ]
                ]
                [ placeholder "(no reason)" ]
            , div
                [ class "form-group" ]
                [ label [ class "control-label" ] [ text "Remember change" ]
                , div
                    []
                    [ App.Form.viewCheckboxInput
                        (Form.getFieldAsBool "remember" form)
                        "Remember this change to undo later"
                    ]
                ]
            , (if List.length treesSelected /= 1 then
                text ""
               else
                hr [] []
              )
            , (if List.length treesSelected /= 1 then
                text ""
               else
                App.Form.viewTextInput
                    (Form.getFieldAsString "message_of_the_day" form)
                    "Message of the day"
                    []
                    [ placeholder "(no change)" ]
              )
            , hr [] []
            , App.Form.viewButton
                "Update"
                [ Utils.onClick Form.Submit
                , disabled (getUpdateTreeErrors form /= [])
                ]
            , div [ class "clearfix" ] []
            ]
        ]
