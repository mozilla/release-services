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
    }


update :
    App.TreeStatus.Types.Msg
    -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
    -> ( App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
       , Cmd App.TreeStatus.Types.Msg
       , Maybe
            { request : Http.Request
            , route : String
            }
       )
update msg model =
    case msg of
        App.TreeStatus.Types.NavigateTo route ->
            let
                ( newModel, newCmd ) =
                    case route of
                        App.TreeStatus.Types.TreesRoute ->
                            ( { model | trees = RemoteData.Loading
                                      , treesSelected = []
                              }
                            , Cmd.batch
                                [ App.TreeStatus.Api.fetchTrees model.baseUrl
                                ]
                            )

                        App.TreeStatus.Types.TreeRoute name ->
                            ( { model
                                | tree = RemoteData.Loading
                                , treeLogs = RemoteData.Loading
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
                    App.TreeStatus.Form.updateUpdateTree model formMsg
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
            in
                ( { model | alerts = alerts }
                , Cmd.batch
                    [ Utils.performMsg App.TreeStatus.Form.resetUpdateTree
                        |> Cmd.map App.TreeStatus.Types.FormUpdateTreeMsg
                    ]
                , Nothing
                )

        App.TreeStatus.Types.SelectTree name ->
            let
                treesSelected =
                    if List.member name model.treesSelected
                       then model.treesSelected
                       else name :: model.treesSelected
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
                ( { model | treesSelected = []
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
                                hasScope "project:releng:treestatus/update_trees" ||
                                hasScope "project:releng:treestatus/kill_tree"

                            checkboxItem =
                                if hasScopes
                                   then [ input [ type' "checkbox"
                                                , checked isChecked
                                                , onCheck checking
                                                ]
                                                []
                                        ]
                                   else  []

                            itemClass =
                                if hasScopes
                                   then "list-group-item list-group-item-with-checkbox"
                                   else "list-group-item"

                            treeItem =
                                a [ href "#"
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
        title =
            h1 []
                [ a
                    [ href "#"
                    , class "float-xs-left"
                    , Utils.onClick (App.TreeStatus.Types.NavigateTo App.TreeStatus.Types.TreesRoute)
                    ]
                    [ text "TreeStatus" ]
                , span
                    [ class "float-xs-left"
                    , style [ ( "margin-right", "0.3em" ) ]
                    ]
                    [ text ":" ]
                , span [ class "font-weight-bold" ] [ text name ]
                ]
    in
        case tree_ of
            RemoteData.Success tree ->
                [ h1 [ class "clearfix" ]
                    [ a
                        [ href "#"
                        , class "float-xs-left"
                        , Utils.onClick (App.TreeStatus.Types.NavigateTo App.TreeStatus.Types.TreesRoute)
                        ]
                        [ text "TreeStatus" ]
                    , span
                        [ class "float-xs-left"
                        , style [ ( "margin-right", "0.3em" ) ]
                        ]
                        [ text ":" ]
                    , span [ class "float-xs-left font-weight-bold" ] [ text (" " ++ name) ]
                    , span [ class <| "float-xs-right tag tag-" ++ treeStatus tree.status ]
                        [ text tree.status ]
                    ]
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
                , p [] <| List.map (\tag -> span [ class "tag tag-default" ] [ text tag ]) log.tags
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


view :
    App.TreeStatus.Types.Route
    -> List String
    -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
    -> Html App.TreeStatus.Types.Msg
view route scopes model =
    let
        addForm =
            App.TreeStatus.Form.viewAddTree model.formAddTree
                |> Html.App.map App.TreeStatus.Types.FormAddTreeMsg

        selectedItems =
            model.treesSelected
                |> List.length
                |> toString

        deleteForm =
            div [ class "list-group" ]
                [ div [ class "list-group-item" ]
                      [ h3 [] [ text ("Would you like to delete (" ++ selectedItems ++ ") selected trees?") ]
                      , button [ class "btn btn-outline-danger"
                               , Utils.onClick App.TreeStatus.Types.DeleteTrees
                               ]
                               [ text "Yes, please delete them." ]
                      ]
                ]

        updateForm =
            App.TreeStatus.Form.viewUpdateTree model.formUpdateTree
                |> Html.App.map App.TreeStatus.Types.FormUpdateTreeMsg

        appendForm scope form nodes =
            if App.UserScopes.hasScope scopes ("project:releng:treestatus/" ++ scope)
               then List.append nodes [ form ]
               else nodes

        ifNotEmpty appendForm2 nodes =
            if List.isEmpty model.treesSelected
               then nodes
               else appendForm2 nodes

    in
        case route of
            App.TreeStatus.Types.TreesRoute ->
                div [ class "container" ]
                    [ h1 [] [ text "TreeStatus" ]
                    , p [ class "lead" ]
                        [ text "Current status of Mozilla's version-control repositories." ]
                    , App.Utils.viewAlerts model.alerts
                    , div
                        [ id "treestatus-forms" ]
                        ([]
                            |> appendForm "make_tree" addForm
                            |> ifNotEmpty (appendForm "kill_tree" deleteForm)
                            |> ifNotEmpty (appendForm "update_trees" updateForm)
                        )
                    , div [ id "treestatus-trees"
                          , class "list-group"
                          ]
                          (viewTrees model scopes)
                    ]

            App.TreeStatus.Types.TreeRoute name ->
                div [ class "container" ]
                    (List.append
                        (viewTree name model.tree)
                        (viewTreeLogs name model.treeLogs model.treeLogsAll)
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
