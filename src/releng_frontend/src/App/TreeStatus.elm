module App.TreeStatus exposing (..)

import App.TreeStatus.Api
import App.TreeStatus.Form
import App.TreeStatus.Types
import App.TreeStatus.View
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
import Title
import UrlParser
import UrlParser exposing ((</>))
import Utils


--
-- ROUTING
--


routes : UrlParser.Parser (App.TreeStatus.Types.Route -> a) a
routes =
    UrlParser.oneOf
        [ UrlParser.format App.TreeStatus.Types.ShowTreesRoute (UrlParser.s "")
        , UrlParser.format App.TreeStatus.Types.AddTreeRoute (UrlParser.s "add")
        , UrlParser.format App.TreeStatus.Types.UpdateTreesRoute (UrlParser.s "update")
        , UrlParser.format App.TreeStatus.Types.DeleteTreesRoute (UrlParser.s "delete")
        , UrlParser.format App.TreeStatus.Types.ShowTreeRoute (UrlParser.s "show" </> UrlParser.string)
        ]


reverse : App.TreeStatus.Types.Route -> String
reverse route =
    case route of
        App.TreeStatus.Types.ShowTreesRoute ->
            "/treestatus"

        App.TreeStatus.Types.AddTreeRoute ->
            "/treestatus/add"

        App.TreeStatus.Types.UpdateTreesRoute ->
            "/treestatus/update"

        App.TreeStatus.Types.DeleteTreesRoute ->
            "/treestatus/delete"

        App.TreeStatus.Types.ShowTreeRoute name ->
            "/treestatus/show/" ++ name


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
    , treesAlerts = []
    , trees = RemoteData.NotAsked
    , treesSelected = []
    , tree = RemoteData.NotAsked
    , treeLogs = RemoteData.NotAsked
    , treeLogsAll = RemoteData.NotAsked
    , showMoreTreeLogs = False
    , formAddTree = App.TreeStatus.Form.initAddTree
    , formUpdateTree = App.TreeStatus.Form.initUpdateTree
    , recentChangesAlerts = []
    , recentChanges = RemoteData.NotAsked
    , deleteTreesConfirm = False
    , deleteError = Nothing
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
update currentRoute msg model =
    case msg of
        App.TreeStatus.Types.NavigateTo route ->
            let
                fetchIfNotAsked data fetch =
                    if data == RemoteData.NotAsked then
                        fetch
                    else
                        Cmd.none

                fetchRecentChangesIfNotAsked =
                    fetchIfNotAsked
                        model.recentChanges
                        (App.TreeStatus.Api.fetchRecentChanges model.baseUrl)

                showAllTrees =
                    ( { model | trees = RemoteData.Loading }
                    , Cmd.batch
                        [ Title.set_title "TreeStatus"
                        , App.TreeStatus.Api.fetchTrees model.baseUrl
                        , App.TreeStatus.Api.fetchRecentChanges model.baseUrl
                        ]
                    )

                redirectToTrees =
                    List.isEmpty model.treesSelected
                        && (currentRoute
                                == App.TreeStatus.Types.UpdateTreesRoute
                                || currentRoute
                                == App.TreeStatus.Types.DeleteTreesRoute
                           )

                ( newModel, newCmd ) =
                    -- in case there are no trees selected and we end up on update
                    -- url we should redirect to ShowTreesRoute
                    if redirectToTrees then
                        showAllTrees
                    else
                        (case route of
                            App.TreeStatus.Types.ShowTreesRoute ->
                                showAllTrees

                            App.TreeStatus.Types.AddTreeRoute ->
                                ( { model | treesAlerts = [] }
                                , fetchIfNotAsked
                                    model.recentChanges
                                    (App.TreeStatus.Api.fetchRecentChanges model.baseUrl)
                                )

                            App.TreeStatus.Types.UpdateTreesRoute ->
                                ( { model | treesAlerts = [] }
                                , fetchRecentChangesIfNotAsked
                                )

                            App.TreeStatus.Types.DeleteTreesRoute ->
                                ( { model
                                    | treesAlerts = []
                                    , deleteTreesConfirm = False
                                    , deleteError = Nothing
                                  }
                                , fetchRecentChangesIfNotAsked
                                )

                            App.TreeStatus.Types.ShowTreeRoute name ->
                                ( { model
                                    | tree = RemoteData.Loading
                                    , treeLogs = RemoteData.Loading
                                    , treesSelected = [ name ]
                                  }
                                , Cmd.batch
                                    [ App.TreeStatus.Api.fetchTree model.baseUrl name
                                    , App.TreeStatus.Api.fetchTreeLogs model.baseUrl name False
                                    , fetchRecentChangesIfNotAsked
                                    ]
                                )
                        )

                newRoute =
                    if redirectToTrees then
                        App.TreeStatus.Types.ShowTreesRoute
                    else
                        route
            in
                ( newModel
                , Cmd.batch
                    [ Hop.outputFromPath App.Types.hopConfig (reverse newRoute)
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
                ( { model | treesAlerts = alerts }
                , Cmd.batch
                    [ Utils.performMsg App.TreeStatus.Form.resetAddTree
                        |> Cmd.map App.TreeStatus.Types.FormAddTreeMsg
                    , Hop.outputFromPath App.Types.hopConfig (reverse App.TreeStatus.Types.ShowTreesRoute)
                        |> Navigation.newUrl
                    ]
                , Nothing
                )

        App.TreeStatus.Types.FormUpdateTreesMsg formMsg ->
            let
                ( newModel, hawkRequest ) =
                    App.TreeStatus.Form.updateUpdateTree currentRoute model formMsg
            in
                ( newModel
                , Cmd.none
                , hawkRequest
                )

        App.TreeStatus.Types.FormUpdateTreesResult result ->
            let
                alerts =
                    result
                        |> RemoteData.map App.Utils.handleResponse
                        |> RemoteData.withDefault []
            in
                ( { model | treesAlerts = alerts }
                , Cmd.batch
                    [ App.TreeStatus.Api.fetchTrees model.baseUrl
                    , App.TreeStatus.Api.fetchRecentChanges model.baseUrl
                    , Utils.performMsg App.TreeStatus.Form.resetUpdateTree
                        |> Cmd.map App.TreeStatus.Types.FormUpdateTreesMsg
                    , Hop.outputFromPath App.Types.hopConfig (reverse App.TreeStatus.Types.ShowTreesRoute)
                        |> Navigation.newUrl
                    ]
                , Nothing
                )

        App.TreeStatus.Types.SelectAllTrees ->
            let
                treesSelected =
                    case model.trees of
                        RemoteData.Success trees ->
                            List.map .name trees

                        _ ->
                            []
            in
                ( { model | treesSelected = treesSelected }
                , Cmd.none
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

        App.TreeStatus.Types.UnselectAllTrees ->
            ( { model | treesSelected = [] }
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
                if model.deleteTreesConfirm then
                    ( { model
                        | treesSelected = []
                        , trees = RemoteData.map filterOutTrees model.trees
                      }
                    , Cmd.none
                    , Just { route = "DeleteTrees", request = request }
                    )
                else
                    ( { model | deleteError = Just "You need to confirm to be able to delete tree(s)." }
                    , Cmd.none
                    , Nothing
                    )

        App.TreeStatus.Types.DeleteTreesResult result ->
            let
                alerts =
                    result
                        |> RemoteData.map App.Utils.handleResponse
                        |> RemoteData.withDefault []
            in
                ( { model | treesAlerts = alerts }
                , Hop.outputFromPath App.Types.hopConfig (reverse App.TreeStatus.Types.ShowTreesRoute)
                    |> Navigation.newUrl
                , Nothing
                )

        App.TreeStatus.Types.RevertChange stack ->
            ( { model | recentChangesAlerts = [] }
            , Cmd.none
            , Just
                { route = "RevertChange"
                , request =
                    Http.Request
                        "DELETE"
                        [ ( "Accept", "application/json" )
                        , ( "Content-Type", "application/json" )
                        ]
                        (model.baseUrl ++ "/stack2/restore/" ++ (toString stack))
                        Http.empty
                }
            )

        App.TreeStatus.Types.DiscardChange stack ->
            ( { model | recentChangesAlerts = [] }
            , Cmd.none
            , Just
                { route = "DiscardChange"
                , request =
                    Http.Request
                        "DELETE"
                        [ ( "Accept", "application/json" )
                        , ( "Content-Type", "application/json" )
                        ]
                        (model.baseUrl ++ "/stack2/discard/" ++ (toString stack))
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
                ( { model | recentChangesAlerts = alerts }
                , Cmd.batch
                    [ App.TreeStatus.Api.fetchRecentChanges model.baseUrl
                    , App.TreeStatus.Api.fetchTrees model.baseUrl
                    ]
                , Nothing
                )

        App.TreeStatus.Types.DeleteTreesConfirmToggle ->
            ( { model | deleteTreesConfirm = Basics.not model.deleteTreesConfirm }
            , Cmd.none
            , Nothing
            )


view :
    App.TreeStatus.Types.Route
    -> List String
    -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
    -> Html App.TreeStatus.Types.Msg
view route scopes model =
    div [ class "container" ]
        [ h1 [] [ text "TreeStatus" ]
        , p [ class "lead" ]
            [ text "Current status of Mozilla's version-control repositories." ]
        , div []
            ([]
                |> App.Utils.appendItem
                    (App.Utils.viewAlerts model.recentChangesAlerts)
                |> App.Utils.appendItems
                    (App.TreeStatus.View.viewRecentChanges scopes model.recentChanges)
                |> App.Utils.appendItem
                    (App.Utils.viewAlerts model.treesAlerts)
                |> App.Utils.appendItem
                    (App.TreeStatus.View.viewTreesTitle route)
                |> App.Utils.appendItem
                    (App.TreeStatus.View.viewButtons route scopes model)
                |> App.Utils.appendItems
                    (case route of
                        App.TreeStatus.Types.ShowTreesRoute ->
                            App.TreeStatus.View.viewTrees scopes model

                        App.TreeStatus.Types.AddTreeRoute ->
                            [ App.TreeStatus.Form.viewAddTree model.formAddTree
                                |> Html.App.map App.TreeStatus.Types.FormAddTreeMsg
                            ]

                        App.TreeStatus.Types.UpdateTreesRoute ->
                            [ App.TreeStatus.Form.viewUpdateTree model.treesSelected model.trees model.formUpdateTree
                                |> Html.App.map App.TreeStatus.Types.FormUpdateTreesMsg
                            ]

                        App.TreeStatus.Types.DeleteTreesRoute ->
                            App.TreeStatus.View.viewConfirmDelete model

                        App.TreeStatus.Types.ShowTreeRoute name ->
                            App.TreeStatus.View.viewTree scopes model name
                    )
            )
        ]
