module App.TreeStatus exposing (..)

import App.TreeStatus.Api
import App.TreeStatus.Form
import App.TreeStatus.Types
import App.Types
import App.UserScopes
import App.Utils
import Form
import Form.Error
import Hop
import Html exposing (..)
import Html.App
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Encode as JsonEncode
import Navigation
import RemoteData
import String
import TaskclusterLogin
import UrlParser
import UrlParser exposing ((</>))
import Utils


-- TODO:
--  * get rid of performMsg (call update on itself)
--
-- ROUTING
--


routes : UrlParser.Parser (App.TreeStatus.Types.Route -> a) a
routes =
    UrlParser.oneOf
        [ UrlParser.format App.TreeStatus.Types.TreesRoute (UrlParser.s "")
        , UrlParser.format App.TreeStatus.Types.TreeRoute (UrlParser.string)
        ]


reverse : App.TreeStatus.Types.Route -> String
reverse route =
    case route of
        App.TreeStatus.Types.TreesRoute ->
            "/treestatus"

        App.TreeStatus.Types.TreeRoute name ->
            "/treestatus/" ++ name


page : (App.TreeStatus.Types.Route -> a) -> App.Types.Page a b
page outRoute =
    { title = "TreeStatus"
    , description = "Current status of Mozilla's version-control repositories."
    , matcher = UrlParser.format outRoute (UrlParser.s "treestatus" </> routes)
    }



--
-- UPDATE
--


init : String -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
init url =
    { baseUrl = url
    , alerts = []
    , trees = RemoteData.NotAsked
    , treesSelected = []
    , tree = RemoteData.NotAsked
    , treeLogs = RemoteData.NotAsked
    , treeLogsAll = RemoteData.NotAsked
    , showMoreTreeLogs = False
    , formAddTree = App.TreeStatus.Form.initAddTree
    , formUpdateTree = App.TreeStatus.Form.initUpdateTree
    , recentChanges = RemoteData.NotAsked
    }


update :
    App.TreeStatus.Types.Route
    -> App.TreeStatus.Types.Msg
    -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
    -> ( App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
       , Cmd App.TreeStatus.Types.Msg
       , Maybe
            { request : Http.Request
            , route : String
            }
       )
update route msg model =
    case msg of
        App.TreeStatus.Types.NavigateTo route ->
            let
                ( newModel, newCmd ) =
                    case route of
                        App.TreeStatus.Types.TreesRoute ->
                            ( { model
                                | trees = RemoteData.Loading
                                , treesSelected = []
                              }
                            , Cmd.batch
                                [ App.TreeStatus.Api.fetchTrees model.baseUrl
                                , App.TreeStatus.Api.fetchRecentChanges model.baseUrl
                                ]
                            )

                        App.TreeStatus.Types.TreeRoute name ->
                            ( { model
                                | tree = RemoteData.Loading
                                , treeLogs = RemoteData.Loading
                                , treesSelected = [ name ]
                              }
                            , Cmd.batch
                                [ App.TreeStatus.Api.fetchTree model.baseUrl name
                                , App.TreeStatus.Api.fetchTreeLogs model.baseUrl name False
                                ]
                            )
            in
                ( newModel
                , Cmd.batch
                    [ Hop.outputFromPath App.Types.hopConfig (reverse route)
                        |> Navigation.newUrl
                    , newCmd
                    ]
                , Nothing
                )

        App.TreeStatus.Types.GetTreesResult trees ->
            ( { model | trees = trees }, Cmd.none, Nothing )

        App.TreeStatus.Types.GetTreeResult tree ->
            ( { model | tree = tree }, Cmd.none, Nothing )

        App.TreeStatus.Types.GetTreeLogsResult logs ->
            ( { model | treeLogs = logs }, Cmd.none, Nothing )

        App.TreeStatus.Types.GetTreeLogsAllResult logs ->
            ( { model | treeLogsAll = logs }, Cmd.none, Nothing )

        App.TreeStatus.Types.GetRecentChangesResult recentChanges ->
            ( { model | recentChanges = recentChanges }, Cmd.none, Nothing )

        App.TreeStatus.Types.GetTreeLogs name all ->
            ( model
            , App.TreeStatus.Api.fetchTreeLogs model.baseUrl name True
            , Nothing
            )

        App.TreeStatus.Types.FormAddTreeMsg formMsg ->
            let
                ( newModel, hawkRequest ) =
                    App.TreeStatus.Form.updateAddTree model formMsg
            in
                ( newModel
                , Cmd.none
                , hawkRequest
                )

        App.TreeStatus.Types.FormAddTreeResult result ->
            let
                alerts =
                    result
                        |> RemoteData.map App.Utils.handleResponse
                        |> RemoteData.withDefault []
            in
                ( { model | alerts = alerts }
                , Cmd.batch
                    [ App.TreeStatus.Api.fetchTrees model.baseUrl
                    , Utils.performMsg App.TreeStatus.Form.resetAddTree
                        |> Cmd.map App.TreeStatus.Types.FormAddTreeMsg
                    ]
                , Nothing
                )

        App.TreeStatus.Types.FormUpdateTreeMsg formMsg ->
            let
                ( newModel, hawkRequest ) =
                    App.TreeStatus.Form.updateUpdateTree route model formMsg
            in
                ( newModel
                , Cmd.none
                , hawkRequest
                )

        App.TreeStatus.Types.FormUpdateTreeResult result ->
            let
                alerts =
                    result
                        |> RemoteData.map App.Utils.handleResponse
                        |> RemoteData.withDefault []

                resetCmd =
                    Utils.performMsg App.TreeStatus.Form.resetUpdateTree
                        |> Cmd.map App.TreeStatus.Types.FormUpdateTreeMsg
            in
                ( { model | alerts = alerts }
                , [ resetCmd ]
                    |> List.append
                        (case (List.head model.treesSelected) of
                            Just treeName ->
                                [ App.TreeStatus.Api.fetchTree model.baseUrl treeName
                                , App.TreeStatus.Api.fetchTreeLogs model.baseUrl treeName False
                                ]

                            Nothing ->
                                []
                        )
                    |> Cmd.batch
                , Nothing
                )

        App.TreeStatus.Types.FormUpdateTreesResult result ->
            let
                alerts =
                    result
                        |> RemoteData.map App.Utils.handleResponse
                        |> RemoteData.withDefault []
            in
                ( { model
                    | alerts = alerts
                    , treesSelected = []
                  }
                , Cmd.batch
                    [ App.TreeStatus.Api.fetchTrees model.baseUrl
                    , Utils.performMsg App.TreeStatus.Form.resetUpdateTree
                        |> Cmd.map App.TreeStatus.Types.FormUpdateTreeMsg
                    ]
                , Nothing
                )

        App.TreeStatus.Types.SelectTree name ->
            let
                treesSelected =
                    if List.member name model.treesSelected then
                        model.treesSelected
                    else
                        name :: model.treesSelected
            in
                ( { model | treesSelected = treesSelected }
                , Cmd.none
                , Nothing
                )

        App.TreeStatus.Types.UnselectTree name ->
            let
                treesSelected =
                    List.filter (\x -> x /= name) model.treesSelected
            in
                ( { model | treesSelected = treesSelected }
                , Cmd.none
                , Nothing
                )

        App.TreeStatus.Types.DeleteTrees ->
            let
                filterOutTrees =
                    List.filter
                        (\x -> Basics.not (List.member x.name model.treesSelected))

                filterTrees =
                    List.filter
                        (\x -> List.member x.name model.treesSelected)

                treesToDelete =
                    model.trees
                        |> RemoteData.map filterTrees
                        |> RemoteData.withDefault []

                request =
                    Http.Request
                        "DELETE"
                        [ ( "Accept", "application/json" )
                        , ( "Content-Type", "application/json" )
                        ]
                        (model.baseUrl ++ "/trees2")
                        (treesToDelete
                            |> App.TreeStatus.Api.encoderTreeNames
                            |> JsonEncode.encode 0
                            |> Http.string
                        )
            in
                ( { model
                    | treesSelected = []
                    , trees = RemoteData.map filterOutTrees model.trees
                  }
                , Cmd.none
                , Just { route = "DeleteTrees", request = request }
                )

        App.TreeStatus.Types.DeleteTreesResult result ->
            let
                alerts =
                    result
                        |> RemoteData.map App.Utils.handleResponse
                        |> RemoteData.withDefault []
            in
                ( { model | alerts = alerts }
                , App.TreeStatus.Api.fetchTrees model.baseUrl
                , Nothing
                )

        App.TreeStatus.Types.RevertChange stack ->
            ( { model | alerts = [] }
            , Cmd.none
            , Just
                { route = "RevertChange"
                , request =
                    Http.Request
                        "DELETE"
                        [ ( "Accept", "application/json" )
                        , ( "Content-Type", "application/json" )
                        ]
                        (model.baseUrl ++ "/stack/" ++ (toString stack) ++ "?revert=1")
                        Http.empty
                }
            )

        App.TreeStatus.Types.DiscardChange stack ->
            ( { model | alerts = [] }
            , Cmd.none
            , Just
                { route = "DiscardChange"
                , request =
                    Http.Request
                        "DELETE"
                        [ ( "Accept", "application/json" )
                        , ( "Content-Type", "application/json" )
                        ]
                        (model.baseUrl ++ "/stack/" ++ (toString stack) ++ "?revert=0")
                        Http.empty
                }
            )

        App.TreeStatus.Types.RecentChangeResult result ->
            let
                alerts =
                    result
                        |> RemoteData.map App.Utils.handleResponse
                        |> RemoteData.withDefault []
            in
                ( { model | alerts = alerts }
                , App.TreeStatus.Api.fetchRecentChanges model.baseUrl
                , Nothing
                )


viewTrees :
    App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
    -> List String
    -> List (Html App.TreeStatus.Types.Msg)
viewTrees model scopes =
    case model.trees of
        RemoteData.Success trees ->
            trees
                |> List.sortBy .name
                |> List.map
                    (\tree ->
                        let
                            isChecked =
                                List.member tree.name model.treesSelected

                            checking checked =
                                case checked of
                                    True ->
                                        App.TreeStatus.Types.SelectTree tree.name

                                    False ->
                                        App.TreeStatus.Types.UnselectTree tree.name

                            openTree =
                                App.TreeStatus.Types.TreeRoute tree.name
                                    |> App.TreeStatus.Types.NavigateTo

                            treeTagClass =
                                "float-xs-right tag tag-" ++ (treeStatus tree.status)

                            hasScope =
                                App.UserScopes.hasScope scopes

                            hasScopes =
                                hasScope "project:releng:treestatus/update_trees"
                                    || hasScope "project:releng:treestatus/kill_tree"

                            checkboxItem =
                                if hasScopes then
                                    [ label
                                        [ class "custom-control custom-checkbox" ]
                                        [ input
                                            [ type' "checkbox"
                                            , class "custom-control-input"
                                            , checked isChecked
                                            , onCheck checking
                                            ]
                                            []
                                        , span
                                            [ class "custom-control-indicator" ]
                                            []
                                        ]
                                    ]
                                else
                                    []

                            itemClass =
                                if hasScopes then
                                    "list-group-item list-group-item-with-checkbox"
                                else
                                    "list-group-item"

                            treeItem =
                                a
                                    [ href "#"
                                    , class "list-group-item-action"
                                    , Utils.onClick openTree
                                    ]
                                    [ h5 [ class "list-group-item-heading" ]
                                        [ text tree.name
                                        , span [ class treeTagClass ]
                                            [ text tree.status ]
                                        ]
                                    , p [ class "list-group-item-text" ]
                                        [ text tree.reason ]
                                    ]
                        in
                            div [ class itemClass ]
                                (List.append checkboxItem [ treeItem ])
                    )

        RemoteData.Failure message ->
            [ App.Utils.error
                (App.TreeStatus.Types.NavigateTo App.TreeStatus.Types.TreesRoute)
                (toString message)
            ]

        RemoteData.Loading ->
            [ App.Utils.loading ]

        RemoteData.NotAsked ->
            []


viewTree :
    String
    -> RemoteData.WebData App.TreeStatus.Types.Tree
    -> List (Html App.TreeStatus.Types.Msg)
viewTree name tree_ =
    let
        withTitle nodes =
            h2
                [ class "clearfix" ]
                (List.append
                    [ span
                        [ class "float-xs-left"
                        , style [ ( "margin-right", "0.3em" ) ]
                        ]
                        [ text "Tree:" ]
                    ]
                    nodes
                )

        title =
            withTitle
                [ span
                    [ class "float-xs-left font-weight-bold" ]
                    [ text name ]
                ]
    in
        case tree_ of
            RemoteData.Success tree ->
                [ withTitle
                    [ span
                        [ class "float-xs-left font-weight-bold" ]
                        [ text (" " ++ name) ]
                    , span
                        [ class ("float-xs-right tag tag-" ++ (treeStatus tree.status)) ]
                        [ text tree.status ]
                    ]
                , p [ class "lead" ] [ text tree.message_of_the_day ]
                , hr [] []
                ]

            RemoteData.Failure message ->
                [ title
                , App.Utils.error (App.TreeStatus.Types.NavigateTo App.TreeStatus.Types.TreesRoute) (toString message)
                ]

            RemoteData.Loading ->
                [ title
                , App.Utils.loading
                ]

            RemoteData.NotAsked ->
                [ title ]


viewTreeLog :
    App.TreeStatus.Types.TreeLog
    -> Html App.TreeStatus.Types.Msg
viewTreeLog log =
    let
        who2 =
            if String.startsWith "human:" log.who then
                log.who
                    |> String.dropLeft 6
            else
                log.who

        who =
            who2
                |> String.split "@"
                |> List.head
                |> Maybe.withDefault who2
    in
        div [ class "timeline-item" ]
            --TODO: show status in hover of the badge
            [ div [ class <| "timeline-badge tag-" ++ (treeStatus log.status) ]
                [ text " " ]
            , div [ class "timeline-panel" ]
                [ div [ class "timeline-time" ]
                    [ text log.when ]
                , h5 [] [ text who ]
                , p [] [ text log.reason ]
                , p
                    []
                    (List.map
                        (\tag ->
                            span
                                [ class "tag tag-default" ]
                                [ App.TreeStatus.Types.possibleTreeTags
                                    |> List.filterMap
                                        (\( x, _, y ) ->
                                            if x == tag then
                                                Just y
                                            else
                                                Nothing
                                        )
                                    |> List.head
                                    |> Maybe.withDefault tag
                                    |> text
                                ]
                        )
                        log.tags
                    )
                ]
            ]


viewTreeLogs :
    String
    -> RemoteData.WebData App.TreeStatus.Types.TreeLogs
    -> RemoteData.WebData App.TreeStatus.Types.TreeLogs
    -> List (Html App.TreeStatus.Types.Msg)
viewTreeLogs name treeLogs_ treeLogsAll_ =
    let
        ( moreButton, treeLogsAll ) =
            case treeLogsAll_ of
                RemoteData.Success treeLogs ->
                    ( []
                    , List.drop 5 treeLogs
                    )

                RemoteData.Failure message ->
                    ( [ App.Utils.error (App.TreeStatus.Types.NavigateTo App.TreeStatus.Types.TreesRoute) (toString message) ]
                    , []
                    )

                RemoteData.Loading ->
                    ( [ button
                            [ class "btn btn-secondary"
                            , Utils.onClick <| App.TreeStatus.Types.GetTreeLogs name True
                            ]
                            [ text "Loading"
                            , i [ class "fa fa-circle-o-notch fa-spin" ] []
                            ]
                      ]
                    , []
                    )

                RemoteData.NotAsked ->
                    ( [ button
                            [ class "btn btn-secondary"
                            , Utils.onClick <| App.TreeStatus.Types.GetTreeLogs name True
                            ]
                            [ text "Load more" ]
                      ]
                    , []
                    )
    in
        case treeLogs_ of
            RemoteData.Success treeLogs ->
                [ div [ class "timeline" ]
                    (List.append
                        (List.append
                            (List.map viewTreeLog treeLogs)
                            (List.map viewTreeLog treeLogsAll)
                        )
                        [ div [ class "timeline-item timeline-more" ]
                            [ div [ class "timeline-panel" ] moreButton ]
                        ]
                    )
                ]

            RemoteData.Failure message ->
                [ App.Utils.error (App.TreeStatus.Types.NavigateTo App.TreeStatus.Types.TreesRoute) (toString message) ]

            RemoteData.Loading ->
                [ App.Utils.loading ]

            RemoteData.NotAsked ->
                []


viewRecentChange recentChange plural =
    let
        treeLabel =
            if plural then
                "trees"
            else
                "tree"
    in
        div
            [ class "list-group-item" ]
            [ div
                [ class "float-xs-right btn-group" ]
                [ button
                    [ type' "button"
                    , class "btn btn-sm btn-outline-success"
                    , Utils.onClick (App.TreeStatus.Types.RevertChange recentChange.id)
                    ]
                    [ text "Restore" ]
                , button
                    [ type' "button"
                    , class "btn btn-sm btn-outline-warning"
                    , Utils.onClick (App.TreeStatus.Types.DiscardChange recentChange.id)
                    ]
                    [ text "Discard" ]
                ]
            , div
                []
                [ text "At "
                , text recentChange.when
                , text " UTC, "
                , text (TaskclusterLogin.shortUsername recentChange.who)
                , text " changed "
                , text treeLabel
                , em [] [ text (String.join ", " recentChange.trees) ]
                , text " to "
                , span
                    [ class ("tag tag-" ++ (treeStatus recentChange.status)) ]
                    [ text recentChange.status ]
                , if recentChange.reason == "" then
                    text ""
                  else
                    text (" with reason: " ++ recentChange.reason)
                , text "."
                ]
            ]


view :
    App.TreeStatus.Types.Route
    -> List String
    -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
    -> Html App.TreeStatus.Types.Msg
view route scopes model =
    let
        hasScope scope =
            App.UserScopes.hasScope scopes ("project:releng:treestatus/" ++ scope)

        viewForms forms =
            let
                formsInScope =
                    List.filter (\x -> hasScope x.scope) forms

                activeFormId =
                    List.filter (\x -> Basics.not x.disabled) formsInScope
                        |> List.map (\x -> x.id)
                        |> List.head
                        |> Maybe.withDefault ""

                addClass condition className =
                    if condition then
                        " " ++ className
                    else
                        ""

                viewTab form =
                    li
                        [ class "nav-item" ]
                        [ a
                            [ class
                                ("nav-link"
                                    ++ (addClass (form.id == activeFormId) "active")
                                    ++ (addClass form.disabled "disabled")
                                )
                            , attribute "data-toggle" "tab"
                            , href ("#" ++ form.id)
                            , disabled form.disabled
                            , attribute "role" "tab"
                            ]
                            [ text form.label ]
                        ]

                viewForm form =
                    div
                        [ class
                            ("tab-pane"
                                ++ (addClass (form.id == activeFormId) "active")
                            )
                        , id form.id
                        , attribute "role" "tabpanel"
                        ]
                        [ form.form ]
            in
                if List.isEmpty formsInScope then
                    text ""
                else
                    div
                        [ id "treestatus-forms" ]
                        [ ul
                            [ class "nav nav-tabs"
                            , attribute "role" "tablist"
                            ]
                            (List.map (viewTab) forms)
                        , div
                            [ class "tab-content" ]
                            (List.map viewForm forms)
                        ]

        viewSelected labelText form =
            div
                []
                [ h4 [] [ text labelText ]
                , ul
                    []
                    (List.map (\x -> li [] [ text x ]) model.treesSelected)
                , form
                ]

        subRoute =
            case route of
                App.TreeStatus.Types.TreesRoute ->
                    [ App.Utils.viewAlerts model.alerts
                    , viewForms
                        [ { id = "recent-changes"
                          , label = "Recent Changes"
                          , scope = "recent_changes/revert"
                          , disabled =
                                case model.recentChanges of
                                    RemoteData.Success data ->
                                        List.isEmpty data

                                    _ ->
                                        True
                          , form =
                                case model.recentChanges of
                                    RemoteData.Success recentChanges ->
                                        div
                                            [ class "list-group" ]
                                            (List.map
                                                (\x -> viewRecentChange x (List.length recentChanges > 1))
                                                recentChanges
                                            )

                                    _ ->
                                        text ""
                          }
                        , { id = "add-tree"
                          , label = "Add Tree"
                          , scope = "trees/create"
                          , disabled = False
                          , form =
                                App.TreeStatus.Form.viewAddTree model.formAddTree
                                    |> Html.App.map App.TreeStatus.Types.FormAddTreeMsg
                          }
                        , { id = "delete-trees"
                          , label = "Delete Trees"
                          , scope = "trees/delete"
                          , disabled = List.isEmpty model.treesSelected
                          , form =
                                viewSelected
                                    "Trees to delete:"
                                    (button
                                        [ class "btn btn-outline-danger"
                                        , Utils.onClick App.TreeStatus.Types.DeleteTrees
                                        , disabled (List.isEmpty model.treesSelected)
                                        ]
                                        [ text "Delete" ]
                                    )
                          }
                        , { id = "update-trees"
                          , label = "Update Trees"
                          , scope = "trees/change"
                          , disabled = List.isEmpty model.treesSelected
                          , form =
                                viewSelected
                                    "Trees to update:"
                                    (App.TreeStatus.Form.viewUpdateTree
                                        model.treesSelected
                                        model.formUpdateTree
                                        |> Html.App.map App.TreeStatus.Types.FormUpdateTreeMsg
                                    )
                          }
                        ]
                    , div
                        [ id "treestatus-trees"
                        , class "list-group"
                        ]
                        (viewTrees model scopes)
                    ]

                App.TreeStatus.Types.TreeRoute name ->
                    [ viewForms
                        [ { id = "update-trees"
                          , label = "Update Tree"
                          , scope = "update_trees"
                          , disabled = List.isEmpty model.treesSelected
                          , form =
                                App.TreeStatus.Form.viewUpdateTree
                                    model.treesSelected
                                    model.formUpdateTree
                                    |> Html.App.map App.TreeStatus.Types.FormUpdateTreeMsg
                          }
                        ]
                    ]
                        |> List.append [ App.Utils.viewAlerts model.alerts ]
                        |> List.append (viewTreeLogs name model.treeLogs model.treeLogsAll)
                        |> List.append (viewTree name model.tree)
                        |> List.append
                            [ div
                                [ class "clearfix" ]
                                [ a
                                    [ href "#"
                                    , Utils.onClick
                                        (App.TreeStatus.Types.NavigateTo App.TreeStatus.Types.TreesRoute)
                                    ]
                                    [ text "Back to all trees" ]
                                ]
                            , hr [] []
                            ]
    in
        div [ class "container" ]
            (subRoute
                |> List.append
                    [ h1 [] [ text "TreeStatus" ]
                    , p [ class "lead" ]
                        [ text "Current status of Mozilla's version-control repositories." ]
                    ]
            )


treeStatus : String -> String
treeStatus status =
    case status of
        "closed" ->
            "danger"

        "open" ->
            "success"

        "approval required" ->
            "warning"

        _ ->
            "default"
