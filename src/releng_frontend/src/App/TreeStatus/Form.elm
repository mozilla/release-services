module App.TreeStatus.Form exposing (..)

import App.Form
import App.TreeStatus.Api
import App.TreeStatus.Types
import App.Utils
import Form
import Form.Error
import Form.Field
import Form.Input
import Form.Validate
import Hawk
import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import RemoteData
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
    Form.Validate.map AddTree
        (Form.Validate.field "name" Form.Validate.string)


validateUpdateTreeTags : Form.Field.Field -> Result (Form.Error.Error a) UpadateTreeTags
validateUpdateTreeTags =
    Form.Validate.map6 UpadateTreeTags
        (Form.Validate.field "checkin_compilation" Form.Validate.bool)
        (Form.Validate.field "checkin_test" Form.Validate.bool)
        (Form.Validate.field "infra" Form.Validate.bool)
        (Form.Validate.field "backlog" Form.Validate.bool)
        (Form.Validate.field "planned" Form.Validate.bool)
        (Form.Validate.field "other" Form.Validate.bool)


validateUpdateTree : Form.Validate.Validation () UpdateTree
validateUpdateTree =
    Form.Validate.map5 UpdateTree
        (Form.Validate.field "status" Form.Validate.string)
        (Form.Validate.field "reason" Form.Validate.string
            |> Form.Validate.defaultValue ""
        )
        (Form.Validate.field "message_of_the_day" Form.Validate.string
            |> Form.Validate.defaultValue ""
        )
        (Form.Validate.field "tags" validateUpdateTreeTags)
        (Form.Validate.field "remember" Form.Validate.bool)


initAddTreeFields : List ( String, Form.Field.Field )
initAddTreeFields =
    [ ( "name", Form.Field.string "" ) ]


initUpdateTreeFields : List ( String, Form.Field.Field )
initUpdateTreeFields =
    [ ( "status", Form.Field.string "" )
    , ( "reason", Form.Field.string "" )
    , ( "message_of_the_day", Form.Field.string "" )
    , ( "tags"
      , App.TreeStatus.Types.possibleTreeTags
            |> List.map (\( _, x, _ ) -> ( x, Form.Field.bool False ))
            |> Form.Field.group
      )
    , ( "remember", Form.Field.bool True )
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
    -> ( App.TreeStatus.Types.Model AddTree UpdateTree, Maybe Hawk.Request )
updateAddTree model formMsg =
    let
        form =
            Form.update validateAddTree formMsg model.formAddTree

        tree name =
            App.TreeStatus.Types.Tree name "closed" "new tree" ""

        newTreeRequest name =
            Hawk.Request
                "AddTree"
                "PUT"
                (model.baseUrl ++ "/trees/" ++ name)
                -- probably this should be in Hawk.elm
                [ Http.header "Accept" "application/json" ]
                (Http.jsonBody (App.TreeStatus.Api.encoderTree (tree name)))

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
                            |> Maybe.map (\x -> newTreeRequest x.name)
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
    -> ( App.TreeStatus.Types.Model AddTree UpdateTree, Maybe Hawk.Request )
updateUpdateTree route model formMsg =
    let
        form =
            Form.update validateUpdateTree formMsg model.formUpdateTree

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
            Hawk.Request
                "UpdateTrees"
                "PATCH"
                (model.baseUrl ++ "/trees")
                [ Http.header "Accept" "application/json" ]
                ((if List.length model.treesSelected /= 1 then
                    { trees = model.treesSelected
                    , status = data.status
                    , reason = data.reason
                    , tags = tagsToList data.tags
                    , remember = data.remember
                    }
                        |> App.TreeStatus.Api.encoderUpdateTrees
                  else
                    { trees = model.treesSelected
                    , status = data.status
                    , reason = data.reason
                    , tags = tagsToList data.tags
                    , message_of_the_day = data.message_of_the_day
                    , remember = data.remember
                    }
                        |> App.TreeStatus.Api.encoderUpdateTree
                 )
                    |> Http.jsonBody
                )

        ( alerts, hawkRequest ) =
            case formMsg of
                Form.Submit ->
                    if getUpdateTreeErrors form /= [] then
                        ( [], Nothing )
                    else
                        ( []
                        , Form.getOutput form
                            |> Maybe.map (\x -> createRequest x)
                        )

                _ ->
                    ( model.treesAlerts, Nothing )
    in
        ( { model
            | formUpdateTree = form
            , treesAlerts = alerts
          }
        , hawkRequest
        )


getUpdateTreeErrors : Form.Form e o -> List ( String, Form.Error.ErrorValue e )
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
            , if List.length treesSelected /= 1 then
                text ""
              else
                hr [] []
            , if List.length treesSelected /= 1 then
                text ""
              else
                App.Form.viewTextInput
                    (Form.getFieldAsString "message_of_the_day" form)
                    "Message of the day"
                    []
                    [ placeholder "(no change)" ]
            , hr [] []
            , App.Form.viewButton
                "Update"
                [ Utils.onClick Form.Submit
                , disabled (getUpdateTreeErrors form /= [])
                ]
            , div [ class "clearfix" ] []
            ]
        ]
