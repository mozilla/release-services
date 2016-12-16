module App.TreeStatus exposing (..)

import App.Types
import App.Utils
import Form
import Form.Validate
import Form.Input
import Hop
import Hop.Types
import Html exposing (..)
import Html.App
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as JsonDecode exposing ((:=))
import Navigation
import RemoteData
import String
import Task
import UrlParser
import UrlParser exposing ((</>))
import Utils


-- TODO:
--  * [x] change from table to list-group / indicate status with tag
--  * [x] use sub route to show logs
--  * [x] each route gets unique id at the top of the dom
--  * [ ] show status of the tree / description / status
--  * [ ] create add tree form with input group button addons
--  * [ ] add from should be on the right side if a person is logged in
--  * [ ] create update trees form on the right side below add tree form
--  * [ ] only show forms if user has enough scopes, scopes should be cached for 5min
--  * [ ] add description below title
--  * [ ] create update Tree form


type alias TreeName =
    String


type Route
    = TreesRoute
    | TreeRoute TreeName


routes =
    UrlParser.oneOf
        [ UrlParser.format TreesRoute (UrlParser.s "")
        , UrlParser.format TreeRoute (UrlParser.string)
        ]


reverse : Route -> String
reverse route =
    case route of
        TreesRoute ->
            "/treestatus"

        TreeRoute name ->
            "/treestatus/" ++ name


page : (Route -> a) -> App.Types.Page a b
page outRoute =
    { title = "TreeStatus"
    , description = "Current status of Mozilla's version-control repositories."
    , matcher = UrlParser.format outRoute (UrlParser.s "treestatus" </> routes)
    }


type alias Tree =
    { name : String
    , status : String
    , reason : String
    , message_of_the_day : String
    }


type alias Trees =
    List Tree


type alias TreeLog =
    { name : String
    , when : String
    , who : String
    , status : String
    , reason : String
    , tags : List String
    }


type alias TreeLogs =
    List TreeLog


type alias FormAddTree =
    { name : String }


type alias Model =
    { baseUrl : String
    , trees : RemoteData.WebData Trees
    , tree : RemoteData.WebData Tree
    , treeLogs : RemoteData.WebData TreeLogs
    , treeLogsAll : RemoteData.WebData TreeLogs
    , showMoreTreeLogs : Bool
    , formAddTree : Form.Form () FormAddTree
    }


type Msg
    = NavigateTo Route
    | FetchedTrees (RemoteData.WebData Trees)
    | FetchedTree (RemoteData.WebData Tree)
    | FetchedTreeLogs (RemoteData.WebData TreeLogs)
    | FetchedTreeLogsAll (RemoteData.WebData TreeLogs)
    | FetchTreeLogs String Bool
    | FormAddTreeMsg Form.Msg


init : String -> Model
init url =
    { baseUrl = url
    , trees = RemoteData.NotAsked
    , tree = RemoteData.NotAsked
    , treeLogs = RemoteData.NotAsked
    , treeLogsAll = RemoteData.NotAsked
    , showMoreTreeLogs = False
    , formAddTree = Form.initial [] validateAddTree
    }


validateAddTree : Form.Validate.Validation () FormAddTree
validateAddTree =
    Form.Validate.form1 FormAddTree
        (Form.Validate.get "name" Form.Validate.string)


load :
    Route
    -> (Msg -> a)
    -> Cmd a
    -> { b | treestatus : Model }
    -> ( { b | treestatus : Model }, Cmd a )
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


load_ : Route -> Model -> ( Model, Cmd Msg )
load_ route model =
    case route of
        TreesRoute ->
            ( { model | trees = RemoteData.Loading }
            , Cmd.batch
                [ fetchTrees model.baseUrl
                ]
            )

        TreeRoute name ->
            ( { model
                | tree = RemoteData.Loading
                , treeLogs = RemoteData.Loading
              }
            , Cmd.batch
                [ fetchTree model.baseUrl name
                , fetchTreeLogs model.baseUrl name False
                ]
            )


decodeTrees : JsonDecode.Decoder Trees
decodeTrees =
    JsonDecode.list decodeTree


decodeTree : JsonDecode.Decoder Tree
decodeTree =
    JsonDecode.object4 Tree
        ("tree" := JsonDecode.string)
        ("status" := JsonDecode.string)
        ("reason" := JsonDecode.string)
        ("message_of_the_day" := JsonDecode.string)


decodeTreeLogs : JsonDecode.Decoder TreeLogs
decodeTreeLogs =
    JsonDecode.list decodeTreeLog


decodeTreeLog : JsonDecode.Decoder TreeLog
decodeTreeLog =
    JsonDecode.object6 TreeLog
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



--put_:
--    JsonDecode.Decoder value
--    -> String
--    -> a
--    -> Task.Task Http.Error value
--put_ decoder url body =
--  let request =
--        { verb = "PUT"
--        , headers = []
--        , url = url
--        , body = body
--        }
--  in
--      Http.fromJson decoder (Http.send Http.defaultSettings request)
--
--put:
--    (RemoteData.RemoteData Http.Error a -> b)
--    -> String
--    -> c
--    -> JsonDecode.Decoder a
--    -> Cmd b
--put msg url body decoder =
--    put_ decoder url body
--        |> RemoteData.asCmd
--        |> Cmd.map msg
--
--
--createTree : String -> String -> Cmd Msg
--createTree url name =
--    put FormAddedTree
--        (url ++ "/trees/" ++ name)
--        { name = name
--        , status = "closed"
--        , reason = "new tree"
--        , message_of_the_day = ""
--        }
--        decodeTree


fetchTrees : String -> Cmd Msg
fetchTrees url =
    get FetchedTrees
        (url ++ "/trees2")
        decodeTrees


fetchTree : String -> TreeName -> Cmd Msg
fetchTree url name =
    get FetchedTree
        (url ++ "/trees/" ++ name)
        decodeTree


fetchTreeLogs : String -> TreeName -> Bool -> Cmd Msg
fetchTreeLogs url name all =
    case all of
        True ->
            get FetchedTreeLogsAll
                (url ++ "/trees/" ++ name ++ "/logs?all=1")
                decodeTreeLogs

        False ->
            get FetchedTreeLogs
                (url ++ "/trees/" ++ name ++ "/logs?all=0")
                decodeTreeLogs


update :
    (Msg -> a)
    -> Msg
    -> { b | treestatus : Model }
    -> ( { b | treestatus : Model }, Cmd a )
update outMsg msg model =
    let
        ( newModel, newCmd ) =
            update_ msg model.treestatus
    in
        ( { model | treestatus = newModel }
        , Cmd.map outMsg newCmd
        )


update_ : Msg -> Model -> ( Model, Cmd Msg )
update_ msg model =
    case msg of
        NavigateTo route ->
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
                )

        FetchedTrees trees ->
            ( { model | trees = trees }, Cmd.none )

        FetchedTree tree ->
            ( { model | tree = tree }, Cmd.none )

        FetchedTreeLogs logs ->
            ( { model | treeLogs = logs }, Cmd.none )

        FetchedTreeLogsAll logs ->
            ( { model | treeLogsAll = logs }, Cmd.none )

        FetchTreeLogs name all ->
            ( model
            , fetchTreeLogs model.baseUrl name True
            )

        FormAddTreeMsg formMsg ->
            let
                form =
                    Form.update formMsg model.formAddTree

                outMsg =
                    case formMsg of
                        Form.Submit ->
                            Cmd.none

                        -- TODO:
                        --if Form.getErrors form /= []
                        --   then Cmd.none
                        --   else createTree <| Form.getOutput form
                        _ ->
                            Cmd.none
            in
                ( { model | formAddTree = form }
                , outMsg
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


viewTrees : RemoteData.WebData Trees -> List (Html Msg)
viewTrees trees_ =
    case trees_ of
        RemoteData.Success trees ->
            List.map
                (\tree ->
                    a
                        [ href "#"
                        , class "list-group-item list-group-item-action"
                        , NavigateTo (TreeRoute tree.name) |> Utils.onClick
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
                (NavigateTo TreesRoute)
                (toString message)
            ]

        RemoteData.Loading ->
            [ App.Utils.loading ]

        RemoteData.NotAsked ->
            []


viewTree : TreeName -> RemoteData.WebData Tree -> List (Html Msg)
viewTree name tree_ =
    let
        title =
            h1 []
                [ a
                    [ href "#"
                    , class "float-xs-left"
                    , Utils.onClick (NavigateTo TreesRoute)
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
                        , Utils.onClick (NavigateTo TreesRoute)
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
                , App.Utils.error (NavigateTo TreesRoute) (toString message)
                ]

            RemoteData.Loading ->
                [ title
                , App.Utils.loading
                ]

            RemoteData.NotAsked ->
                [ title ]


viewTreeLog : TreeLog -> Html Msg
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
    -> RemoteData.WebData TreeLogs
    -> RemoteData.WebData TreeLogs
    -> List (Html Msg)
viewTreeLogs name treeLogs_ treeLogsAll_ =
    let
        ( moreButton, treeLogsAll ) =
            case treeLogsAll_ of
                RemoteData.Success treeLogs ->
                    ( []
                    , List.drop 5 treeLogs
                    )

                RemoteData.Failure message ->
                    ( [ App.Utils.error (NavigateTo TreesRoute) (toString message) ]
                    , []
                    )

                RemoteData.Loading ->
                    ( [ button
                            [ class "btn btn-secondary"
                            , Utils.onClick <| FetchTreeLogs name True
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
                            , Utils.onClick <| FetchTreeLogs name True
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
                [ App.Utils.error (NavigateTo TreesRoute) (toString message) ]

            RemoteData.Loading ->
                [ App.Utils.loading ]

            RemoteData.NotAsked ->
                []


view : Route -> Model -> Html Msg
view route model =
    case route of
        TreesRoute ->
            div [ class "container" ]
                [ h1 [] [ text "TreeStatus" ]
                , p [ class "lead" ]
                    [ text "Current status of Mozilla's version-control repositories." ]
                , div [ class "list-group" ] (viewTrees model.trees)
                  -- TODO: only show when correct scope is there
                  -- TODO:, Html.App.map FormAddTreeMsg (viewAddTree model.formAddTree)
                ]

        TreeRoute name ->
            let
                treeStatus =
                    viewTreeLogs name model.treeLogs model.treeLogsAll
                        |> List.append (viewTree name model.tree)

                updateForm =
                    []
            in
                div [] (List.append treeStatus updateForm)


viewAddTree : Form.Form () FormAddTree -> Html Form.Msg
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
        div [ class "list-group-item" ]
            [ h3 [] [ text "Add tree" ]
            , Html.form
                []
                [ div [ class nameClass ]
                    [ Form.Input.textInput name
                        [ class "form-control"
                        , placeholder "Tree name ..."
                        ]
                    , span [ class "input-group-btn" ]
                        [ button
                            [ type' "submit"
                            , class "btn btn-secondary"
                            , Utils.onClick Form.Submit
                            ]
                            [ text "Add" ]
                        ]
                    ]
                , nameError
                ]
            ]
