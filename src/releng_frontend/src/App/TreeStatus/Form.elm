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


type alias UpdateStack =
    { reason : String
    , tags : String
    }


type alias UpdateLog =
    { reason : String
    , tags : String
    }


type alias UpdateTree =
    { status : String
    , reason : String
    , message_of_the_day : String
    , tags : String
    , remember : Bool
    }


validateAddTree : Form.Validate.Validation () AddTree
validateAddTree =
    Form.Validate.map AddTree
        (Form.Validate.field "name" Form.Validate.string)


validateUpdateLog : String -> Form.Validate.Validation () UpdateLog
validateUpdateLog status =
    if status == "closed" then
        Form.Validate.map2 UpdateLog
            (Form.Validate.field "reason" Form.Validate.string)
            (Form.Validate.field "tags" Form.Validate.string)
    else
        Form.Validate.map2 UpdateLog
            (Form.Validate.field "reason"
                (Form.Validate.oneOf
                    [ Form.Validate.string
                    , Form.Validate.emptyString
                    ]
                )
            )
            (Form.Validate.field "tags"
                (Form.Validate.oneOf
                    [ Form.Validate.string
                    , Form.Validate.emptyString
                    ]
                )
            )


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
        (Form.Validate.field "tags" Form.Validate.string
            |> Form.Validate.defaultValue ""
        )
        (Form.Validate.field "remember" Form.Validate.bool)


initAddTreeFields : List ( String, Form.Field.Field )
initAddTreeFields =
    [ ( "name", Form.Field.string "" ) ]


initUpdateStackFields : String -> String -> List ( String, Form.Field.Field )
initUpdateStackFields reason tags =
    [ ( "reason", Form.Field.string reason )
    , ( "tags", Form.Field.string tags )
    ]


initUpdateLogFields : String -> String -> List ( String, Form.Field.Field )
initUpdateLogFields reason tags =
    [ ( "reason", Form.Field.string reason )
    , ( "tags", Form.Field.string tags )
    ]


initUpdateTreeFields : List ( String, Form.Field.Field )
initUpdateTreeFields =
    [ ( "status", Form.Field.string "" )
    , ( "reason", Form.Field.string "" )
    , ( "message_of_the_day", Form.Field.string "" )
    , ( "tags", Form.Field.string "" )
    , ( "remember", Form.Field.bool True )
    ]


initAddTree : Form.Form () AddTree
initAddTree =
    Form.initial initAddTreeFields validateAddTree


initUpdateStack : String -> Form.Form () UpdateStack
initUpdateStack status =
    Form.initial (initUpdateStackFields "" "") (validateUpdateLog status)


initUpdateLog : String -> Form.Form () UpdateLog
initUpdateLog status =
    Form.initial (initUpdateLogFields "" "") (validateUpdateLog status)


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
    App.TreeStatus.Types.Model AddTree UpdateTree UpdateStack UpdateLog
    -> Form.Msg
    -> ( App.TreeStatus.Types.Model AddTree UpdateTree UpdateStack UpdateLog, Maybe Hawk.Request )
updateAddTree model formMsg =
    let
        form =
            Form.update validateAddTree formMsg model.formAddTree

        tree name =
            App.TreeStatus.Types.Tree name "closed" "new tree" "" []

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


updateUpdateStack :
    App.TreeStatus.Types.Model AddTree UpdateTree UpdateStack UpdateLog
    -> Form.Msg
    -> ( App.TreeStatus.Types.Model AddTree UpdateTree UpdateStack UpdateLog, Maybe Hawk.Request )
updateUpdateStack model formMsg =
    let
        status =
            model.recentChanges
                |> RemoteData.withDefault []
                |> List.filter (\x -> Just x.id == model.showUpdateStackForm)
                |> List.map
                    (\x ->
                        x.trees
                            |> List.head
                            |> Maybe.map (\y -> y.last_state.current_status)
                            |> Maybe.withDefault ""
                    )
                |> List.head
                |> Maybe.withDefault ""

        form =
            Form.update (validateUpdateLog status) formMsg model.formUpdateStack

        formOutput =
            Form.getOutput form

        ( recentChanges, alerts, hawkRequest, showUpdateStackForm ) =
            case ( formMsg, model.recentChanges, model.showUpdateStackForm, formOutput ) of
                ( Form.Submit, RemoteData.Success recentChanges, Just recentChangeId, Just formOutput ) ->
                    let
                        newRecentChanges =
                            List.map updateRecentChange recentChanges

                        updateRecentChange recentChange =
                            if recentChangeId == recentChange.id then
                                { recentChange
                                    | reason = formOutput.reason
                                    , trees = List.map updateRecentChangeTree recentChange.trees
                                }
                            else
                                recentChange

                        updateRecentChangeTree tree =
                            let
                                last_state =
                                    tree.last_state
                            in
                            { tree
                                | last_state =
                                    { last_state
                                        | reason = formOutput.reason
                                        , tags = [ formOutput.tags ]
                                    }
                            }

                        hawkRequest_ =
                            Hawk.Request
                                "UpdateStack"
                                "PATCH"
                                (model.baseUrl ++ "/stack/" ++ toString recentChangeId)
                                [ Http.header "Accept" "application/json" ]
                                (Http.jsonBody (App.TreeStatus.Api.encoderUpdateStack { reason = formOutput.reason, tags = [ formOutput.tags ] }))

                        ( alerts, hawkRequest ) =
                            if getUpdateTreeErrors form == [] then
                                ( [], Just hawkRequest_ )
                            else
                                ( model.recentChangesAlerts, Nothing )
                    in
                    ( RemoteData.Success newRecentChanges, alerts, hawkRequest, model.showUpdateStackForm )

                ( Form.Reset _, _, _, _ ) ->
                    ( model.recentChanges, model.recentChangesAlerts, Nothing, Nothing )

                ( _, _, _, _ ) ->
                    ( model.recentChanges, model.recentChangesAlerts, Nothing, model.showUpdateStackForm )
    in
    ( { model
        | formUpdateStack = form
        , recentChangesAlerts = alerts
        , recentChanges = recentChanges
        , showUpdateStackForm = showUpdateStackForm
      }
    , hawkRequest
    )


updateUpdateLog :
    App.TreeStatus.Types.Model AddTree UpdateTree UpdateStack UpdateLog
    -> Form.Msg
    -> ( App.TreeStatus.Types.Model AddTree UpdateTree UpdateStack UpdateLog, Maybe Hawk.Request )
updateUpdateLog model formMsg =
    let
        status =
            logs
                |> List.filter (\x -> Just x.id == model.showUpdateLog)
                |> List.map (\x -> x.status)
                |> List.head
                |> Maybe.withDefault ""

        logs =
            RemoteData.withDefault []
                (if RemoteData.isSuccess model.treeLogsAll then
                    model.treeLogsAll
                 else
                    model.treeLogs
                )

        formOutput =
            Form.getOutput form |> Maybe.withDefault (UpdateLog "" "")

        form =
            Form.update (validateUpdateLog status) formMsg model.formUpdateLog

        updateLog logId logs =
            List.map
                (\log ->
                    if logId == log.id then
                        { log
                            | reason = formOutput.reason
                            , tags = [ formOutput.tags ]
                        }
                    else
                        log
                )
                logs

        requestBody =
            App.TreeStatus.Api.encoderUpdateStack
                { reason = formOutput.reason
                , tags = [ formOutput.tags ]
                }

        makeHawkRequest logId =
            Hawk.Request
                "UpdateStack"
                "PATCH"
                (model.baseUrl ++ "/log/" ++ toString logId)
                [ Http.header "Accept" "application/json" ]
                (Http.jsonBody requestBody)

        ( showUpdateLog, treeLogs, treeLogsAll, hawkRequest ) =
            case ( formMsg, model.showUpdateLog ) of
                ( Form.Submit, Just logId ) ->
                    let
                        errors =
                            Form.getErrors form
                    in
                    ( if List.isEmpty errors then
                        Nothing
                      else
                        model.showUpdateLog
                      -- TODO: update recentChanges
                    , RemoteData.map (updateLog logId) model.treeLogs
                    , RemoteData.map (updateLog logId) model.treeLogsAll
                      -- TODO: pass in status
                    , if List.isEmpty errors then
                        Just (makeHawkRequest logId)
                      else
                        Nothing
                    )

                ( Form.Reset _, _ ) ->
                    ( Nothing
                    , model.treeLogs
                    , model.treeLogsAll
                    , Nothing
                    )

                ( _, _ ) ->
                    ( model.showUpdateLog
                    , model.treeLogs
                    , model.treeLogsAll
                    , Nothing
                    )
    in
    ( { model
        | formUpdateLog = form
        , showUpdateLog = showUpdateLog
        , treeLogs = treeLogs
        , treeLogsAll = treeLogsAll
      }
    , hawkRequest
    )


updateUpdateTree :
    App.TreeStatus.Types.Route
    -> App.TreeStatus.Types.Model AddTree UpdateTree UpdateStack UpdateLog
    -> Form.Msg
    -> ( App.TreeStatus.Types.Model AddTree UpdateTree UpdateStack UpdateLog, Maybe Hawk.Request )
updateUpdateTree route model formMsg =
    let
        form =
            Form.update validateUpdateTree formMsg model.formUpdateTree

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
                    , tags = [ data.tags ]
                    , remember = data.remember
                    }
                        |> App.TreeStatus.Api.encoderUpdateTrees
                  else
                    { trees = model.treesSelected
                    , status = data.status
                    , reason = data.reason
                    , tags = [ data.tags ]
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
        requiredOnClose field =
            let
                status =
                    Form.getFieldAsString "status" form
                        |> .value
                        |> Maybe.withDefault ""

                data =
                    Form.getFieldAsString field form
                        |> .value
                        |> Maybe.withDefault ""
            in
            if status == "closed" && data == "" then
                [ ( field, Form.Error.Empty ) ]
            else
                []
    in
    Form.getErrors form
        |> List.append (requiredOnClose "reason")
        |> List.append (requiredOnClose "tags")


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


viewUpdateStack :
    App.TreeStatus.Types.RecentChange
    -> Form.Form () UpdateStack
    -> Html Form.Msg
viewUpdateStack recentChange form =
    div [ id "treestatus-form" ]
        [ Html.form
            []
            [ App.Form.viewRadioInput
                (Form.getFieldAsString "tags" form)
                "Reason category"
                []
                (App.TreeStatus.Types.possibleTreeTags
                    |> List.append
                        (if recentChange.status == "closed" then
                            []
                         else
                            [ ( "", "No category" ) ]
                        )
                )
                []
            , App.Form.viewTextInput
                (Form.getFieldAsString "reason" form)
                "Reason"
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
            ]
        , div [ class "btn-group" ]
            [ App.Form.viewButton
                "Update"
                [ Utils.onClick Form.Submit
                ]
            , App.Form.viewButton
                "Cancel"
                [ Utils.onClick (Form.Reset (initUpdateStackFields "" ""))
                , class "btn btn-outline-danger"
                ]
            ]
        , div [ class "clearfix" ] []
        ]


viewUpdateLog :
    String
    -> Form.Form () UpdateLog
    -> Html Form.Msg
viewUpdateLog status form =
    div [ id "treestatus-form" ]
        [ Html.form
            []
            [ App.Form.viewRadioInput
                (Form.getFieldAsString "tags" form)
                "Reason category"
                []
                (App.TreeStatus.Types.possibleTreeTags
                    |> List.append
                        (if status == "closed" then
                            []
                         else
                            [ ( "", "No category" ) ]
                        )
                )
                []
            , App.Form.viewTextInput
                (Form.getFieldAsString "reason" form)
                "Reason"
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
            ]
        , div [ class "btn-group" ]
            [ App.Form.viewButton
                "Update"
                [ Utils.onClick Form.Submit
                ]
            , App.Form.viewButton
                "Cancel"
                -- TODO: this should reset to original fields
                [ Utils.onClick (Form.Reset (initUpdateLogFields "" ""))
                , class "btn btn-outline-danger"
                ]
            ]
        , div [ class "clearfix" ] []
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
                        |> List.map
                            (\treeName ->
                                let
                                    status =
                                        trees
                                            |> RemoteData.map (List.filter (\t -> t.name == treeName))
                                            |> RemoteData.map (List.map (\t -> t.status))
                                            |> RemoteData.toMaybe
                                            |> Maybe.withDefault []
                                            |> List.head
                                            |> Maybe.withDefault "closed"
                                in
                                li []
                                    [ text treeName
                                    , text " ("
                                    , span
                                        [ class ("badge badge-" ++ App.Utils.treeStatusLevel status) ]
                                        [ text status ]
                                    , text ")"
                                    ]
                            )
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
            , App.Form.viewRadioInput
                (Form.getFieldAsString "tags" form)
                (if (Form.getFieldAsString "status" form).value == Just "closed" then
                    "Reason category (required to close)"
                 else
                    "Reason category"
                )
                []
                (App.TreeStatus.Types.possibleTreeTags
                    |> List.append [ ( "", "No category" ) ]
                )
                []
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

                -- TODO, disabled (getUpdateTreeErrors form /= [])
                ]
            , div [ class "clearfix" ] []
            ]
        ]
