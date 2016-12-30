module App.TreeStatus exposing (..)

import App.TreeStatus.Form
import App.TreeStatus.Types
import App.Types
import App.Utils
import Form
import Hop
import Hop.Types
import Html exposing (..)
import Html.App
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as JsonDecode exposing ((:=))
import Json.Encode as JsonEncode
import Navigation
import RemoteData
import String
import Task
import UrlParser
import UrlParser exposing ((</>))
import Utils


-- TODO:
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


init : String -> App.TreeStatus.Types.Model
init url =
    { baseUrl = url
    , trees = RemoteData.NotAsked
    , tree = RemoteData.NotAsked
    , treeLogs = RemoteData.NotAsked
    , treeLogsAll = RemoteData.NotAsked
    , showMoreTreeLogs = False
    , formAddTree = App.TreeStatus.Form.initAddTree []
    }


load :
    App.TreeStatus.Types.Route
    -> (App.TreeStatus.Types.Msg -> a)
    -> Cmd a
    -> { b | treestatus : App.TreeStatus.Types.Model }
    -> ( { b | treestatus : App.TreeStatus.Types.Model }, Cmd a )
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
    -> App.TreeStatus.Types.Model
    -> ( App.TreeStatus.Types.Model
       , Cmd App.TreeStatus.Types.Msg
       )
load_ route model =
    case route of
        App.TreeStatus.Types.TreesRoute ->
            ( { model | trees = RemoteData.Loading }
            , Cmd.batch
                [ fetchTrees model.baseUrl
                ]
            )

        App.TreeStatus.Types.TreeRoute name ->
            ( { model
                | tree = RemoteData.Loading
                , treeLogs = RemoteData.Loading
              }
            , Cmd.batch
                [ fetchTree model.baseUrl name
                , fetchTreeLogs model.baseUrl name False
                ]
            )


encoderTree : App.TreeStatus.Types.Tree -> JsonEncode.Value
encoderTree tree =
    JsonEncode.object
        [ ("tree", JsonEncode.string tree.name)
        , ("status", JsonEncode.string tree.status)
        , ("reason", JsonEncode.string tree.reason)
        , ("message_of_the_day", JsonEncode.string tree.message_of_the_day)
        ]


decodeTrees : JsonDecode.Decoder App.TreeStatus.Types.Trees
decodeTrees =
    JsonDecode.list decodeTree


decodeTree : JsonDecode.Decoder App.TreeStatus.Types.Tree
decodeTree =
    JsonDecode.object4 App.TreeStatus.Types.Tree
        ("tree" := JsonDecode.string)
        ("status" := JsonDecode.string)
        ("reason" := JsonDecode.string)
        ("message_of_the_day" := JsonDecode.string)


decodeTreeLogs : JsonDecode.Decoder App.TreeStatus.Types.TreeLogs
decodeTreeLogs =
    JsonDecode.list decodeTreeLog


decodeTreeLog : JsonDecode.Decoder App.TreeStatus.Types.TreeLog
decodeTreeLog =
    JsonDecode.object6 App.TreeStatus.Types.TreeLog
        ("tree" := JsonDecode.string)
        ("when" := JsonDecode.string)
        ("who" := JsonDecode.string)
        ("status" := JsonDecode.string)
        ("reason" := JsonDecode.string)
        ("tags" := JsonDecode.list JsonDecode.string)


get :
    (RemoteData.RemoteData Http.Error a -> b)
    -> String
    -> JsonDecode.Decoder a
    -> Cmd b
get msg url decoder =
    Http.get decoder url
        |> RemoteData.asCmd
        |> Cmd.map msg



fetchTrees :
    String
    -> Cmd App.TreeStatus.Types.Msg
fetchTrees url =
    get App.TreeStatus.Types.GetTreesResult
        (url ++ "/trees2")
        decodeTrees


fetchTree :
    String
    -> String
    -> Cmd App.TreeStatus.Types.Msg
fetchTree url name =
    get App.TreeStatus.Types.GetTreeResult
        (url ++ "/trees/" ++ name)
        decodeTree


fetchTreeLogs :
    String
    -> String
    -> Bool
    -> Cmd App.TreeStatus.Types.Msg
fetchTreeLogs url name all =
    case all of
        True ->
            get App.TreeStatus.Types.GetTreeLogsAllResult
                (url ++ "/trees/" ++ name ++ "/logs?all=1")
                decodeTreeLogs

        False ->
            get App.TreeStatus.Types.GetTreeLogsResult
                (url ++ "/trees/" ++ name ++ "/logs?all=0")
                decodeTreeLogs


hawkResponse :
    Cmd (RemoteData.RemoteData Http.RawError Http.Response)
    -> String
    -> Cmd App.TreeStatus.Types.Msg
hawkResponse response route =
    case route of
        "AddTree" ->
            Cmd.map App.TreeStatus.Types.FormAddTreeResult response
        _ ->
            Cmd.none


update :
    (App.TreeStatus.Types.Msg -> b)
    -> App.TreeStatus.Types.Msg
    -> { c | treestatus : App.TreeStatus.Types.Model }
    -> (String -> Http.Request -> Cmd b)
    -> ( { c | treestatus : App.TreeStatus.Types.Model }, Cmd b )
update outMsg msg model hawkSend =
    let
        ( treestatus, cmd, hawkRequest ) =
            update_ msg model.treestatus
    in
        ( { model | treestatus = treestatus }
        , hawkRequest
            |> Maybe.map (\x -> [hawkSend x.route x.request])
            |> Maybe.withDefault []
            |> List.append [Cmd.map outMsg cmd]
            |> Cmd.batch
        )


update_ :
    App.TreeStatus.Types.Msg
    -> App.TreeStatus.Types.Model
    -> ( App.TreeStatus.Types.Model
       , Cmd App.TreeStatus.Types.Msg
       , Maybe { request : Http.Request
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
            , fetchTreeLogs model.baseUrl name True
            , Nothing
            )

        App.TreeStatus.Types.FormAddTreeMsg formMsg ->
            let
                form = Form.update formMsg model.formAddTree
                tree name = App.TreeStatus.Types.Tree name "closed" "new tree" ""
                treeStr name = JsonEncode.encode 0 (encoderTree (tree name))
                newTreeRequest name =
                    Http.Request
                        "PUT"
                        -- probably this should be in Hawk.elm
                        [ ("Accept",       "application/json")
                        , ("Content-Type", "application/json")
                        ]
                        (model.baseUrl ++ "/trees/" ++ name)
                        (Http.string (treeStr name))
                hawkRequest =
                    case formMsg of
                        Form.Submit ->
                            if Form.getErrors form /= []
                               then
                                   Nothing
                               else
                                   Form.getOutput form
                                       |> Maybe.map (\x -> { route = "AddTree", request = newTreeRequest x.name })
                        _ ->
                            Nothing
            in
                ( { model | formAddTree = form }
                , Cmd.none
                , hawkRequest
                )

        App.TreeStatus.Types.FormAddTreeResult tree ->
            let
                _ = Debug.log "TREE" tree
            in
            ( model, Cmd.none, Nothing )




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


view :
    App.TreeStatus.Types.Route
    -> App.TreeStatus.Types.Model
    -> Html App.TreeStatus.Types.Msg
view route model =
    case route of
        App.TreeStatus.Types.TreesRoute ->
            div [ class "container" ]
                [ h1 [] [ text "TreeStatus" ]
                , p [ class "lead" ]
                    [ text "Current status of Mozilla's version-control repositories." ]
                -- TODO: only show forms when user has a needed scope 
                , div [ id "treestatus-forms"
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
