module App.TreeStatus exposing (..)

import App.TreeStatus.Api
import App.TreeStatus.Form
import App.TreeStatus.Types
import App.Types
import App.Utils
import Form
import Form.Error
import Hop
import Html exposing (..)
import Html.App
import Html.Attributes exposing (..)
import Http
import Json.Encode as JsonEncode
import Json.Decode as JsonDecode exposing ((:=))
import Navigation
import RemoteData
import String
import UrlParser
import UrlParser exposing ((</>))
import Utils


-- TODO:
--  * first fetch scopes of the user when making requests, expire them in 15 minutes
--  * mark optimistic updates with different color
--  * don do optimistinc update if we already have a duplicate
--  * show spinner over the grayed form when form gets submitted
--
--  * add from should be on the right side if a person is logged in
--  * create update trees form on the right side below add tree form
--  * only show forms if user has enough scopes, scopes should be cached for 5min
--  * create update Tree form

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


init : String -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree
init url =
    { baseUrl = url
    , alerts = []
    , trees = RemoteData.NotAsked
    , tree = RemoteData.NotAsked
    , treeLogs = RemoteData.NotAsked
    , treeLogsAll = RemoteData.NotAsked
    , showMoreTreeLogs = False
    , formAddTree = App.TreeStatus.Form.initAddTree
    }


load :
    App.TreeStatus.Types.Route
    -> (App.TreeStatus.Types.Msg -> a)
    -> Cmd a
    -> { b | treestatus : App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree }
    -> ( { b | treestatus : App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree }, Cmd a )
load route outMsg outCmd model =
    let
        ( newModel, newCmd ) =
            load_ route model.treestatus
    in
        ( { model | treestatus = newModel }
        , Cmd.batch
            [ outCmd
            , Cmd.map outMsg newCmd
            ]
        )


load_ :
    App.TreeStatus.Types.Route
    -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree
    -> ( App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree, Cmd App.TreeStatus.Types.Msg )
load_ route model =
    case route of
        App.TreeStatus.Types.TreesRoute ->
            ( { model | trees = RemoteData.Loading }
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


update :
    (App.TreeStatus.Types.Msg -> b)
    -> App.TreeStatus.Types.Msg
    -> { c | treestatus : App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree }
    -> (String -> Http.Request -> Cmd b)
    -> ( { c | treestatus : App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree }, Cmd b )
update outMsg msg model hawkSend =
    let
        ( treestatus, cmd, hawkRequest ) =
            update_ msg model.treestatus
    in
        ( { model | treestatus = treestatus }
        , hawkRequest
            |> Maybe.map (\x -> [ hawkSend x.route x.request ])
            |> Maybe.withDefault []
            |> List.append [ Cmd.map outMsg cmd ]
            |> Cmd.batch
        )


update_ :
    App.TreeStatus.Types.Msg
    -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree
    -> ( App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree
       , Cmd App.TreeStatus.Types.Msg
       , Maybe
            { request : Http.Request
            , route : String
            }
       )
update_ msg model =
    case msg of
        App.TreeStatus.Types.NavigateTo route ->
            let
                ( newModel, newCmd ) =
                    load_ route model
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
                handleResponse response =
                    let
                        decoderError =
                            JsonDecode.object4 App.TreeStatus.Types.Error
                                ("type" := JsonDecode.string)
                                ("detail" := JsonDecode.string)
                                ("status" := JsonDecode.int)
                                ("title" := JsonDecode.string)

                        alerts =
                            if 200 <= response.status && response.status < 300 then
                                case response.value of
                                    Http.Text text ->
                                        []

                                    _ ->
                                        [ App.TreeStatus.Types.Alert
                                            App.TreeStatus.Types.AlertDanger
                                            "Error!"
                                            "Response body is a blob, expecting a string."
                                        ]
                            else
                                [ App.TreeStatus.Types.Alert
                                    App.TreeStatus.Types.AlertDanger
                                    "Error!"
                                    ( case response.value of
                                        Http.Text text ->
                                            case JsonDecode.decodeString decoderError text of
                                                Ok obj ->
                                                    obj.detail

                                                Err error ->
                                                    text

                                        r ->
                                            response.statusText
                                    )
                                ]
                    in
                        ( { model | alerts = alerts }
                        , Cmd.batch
                            [ App.TreeStatus.Api.fetchTrees model.baseUrl
                            , Utils.performMsg App.TreeStatus.Form.resetAddTree
                                |> Cmd.map App.TreeStatus.Types.FormAddTreeMsg
                            ]
                        )

                ( newModel, newCmd ) =
                    result
                        |> RemoteData.map handleResponse
                        |> RemoteData.withDefault ( model, Cmd.none )
            in
                ( newModel
                , newCmd
                , Nothing
                )


viewTrees :
    RemoteData.WebData App.TreeStatus.Types.Trees
    -> List (Html App.TreeStatus.Types.Msg)
viewTrees trees_ =
    case trees_ of
        RemoteData.Success trees ->
            List.map
                (\tree ->
                    a
                        [ href "#"
                        , class "list-group-item list-group-item-action"
                        , App.TreeStatus.Types.TreeRoute tree.name
                            |> App.TreeStatus.Types.NavigateTo
                            |> Utils.onClick
                        ]
                        [ h5 [ class "list-group-item-heading" ]
                            [ text tree.name
                            , span [ class <| "float-xs-right tag tag-" ++ treeStatus tree.status ]
                                [ text tree.status ]
                            ]
                        , p [ class "list-group-item-text" ]
                            [ text tree.reason ]
                        ]
                )
            <|
                List.sortBy .name trees

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


viewAlerts :
    List App.TreeStatus.Types.Alert
    -> Html App.TreeStatus.Types.Msg
viewAlerts alerts =
    let
        getAlertTypeAsString alert =
            case alert.type_ of
                App.TreeStatus.Types.AlertSuccess ->
                    "success"

                App.TreeStatus.Types.AlertInfo ->
                    "info"

                App.TreeStatus.Types.AlertWarning ->
                    "warning"

                App.TreeStatus.Types.AlertDanger ->
                    "danger"

        createAlert alert =
            div [ class ("alert alert-" ++ (getAlertTypeAsString alert)) ]
                [ strong [] [ text alert.title ]
                , text alert.text
                ]
    in
        alerts
            |> List.map createAlert
            |> div []


view :
    App.TreeStatus.Types.Route
    -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree
    -> Html App.TreeStatus.Types.Msg
view route model =
    case route of
        App.TreeStatus.Types.TreesRoute ->
            div [ class "container" ]
                [ h1 [] [ text "TreeStatus" ]
                , p [ class "lead" ]
                    [ text "Current status of Mozilla's version-control repositories." ]
                , viewAlerts model.alerts
                  -- TODO: only show forms when user has a needed scope
                , div
                    [ id "treestatus-forms"
                    , class "list-group"
                    ]
                    [ App.TreeStatus.Form.viewAddTree model.formAddTree
                        |> Html.App.map App.TreeStatus.Types.FormAddTreeMsg
                    ]
                , div [ class "list-group" ] (viewTrees model.trees)
                ]

        App.TreeStatus.Types.TreeRoute name ->
            let
                treeStatus =
                    viewTreeLogs name model.treeLogs model.treeLogsAll
                        |> List.append (viewTree name model.tree)

                updateForm =
                    []
            in
                div [] (List.append treeStatus updateForm)


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
