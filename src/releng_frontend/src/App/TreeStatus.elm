module App.TreeStatus exposing (..)

import App.Utils
import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Json.Decode as JsonDecode exposing ( (:=) )
import RemoteData
import String


type alias Tree =
    { tree : String
    , status : String
    , reason : String
    , message_of_the_day : String
    }


type alias Trees =
    List Tree


type alias TreeLog =
    { tree : String
    , when : String
    , who : String
    , status : String
    , reason : String
    , tags : List String
    }


type alias TreeLogs =
    List TreeLog


type alias Model =
    { baseUrl : String
    , trees : RemoteData.WebData Trees
    , tree : RemoteData.WebData Tree
    , treeLogs : RemoteData.WebData TreeLogs
    , showMoreTreeLogs : Bool
    }


type Msg
    = FetchedTrees (RemoteData.WebData Trees)
    | FetchedTree (RemoteData.WebData Tree)
    | FetchedTreeLogs (RemoteData.WebData TreeLogs)
    | ShowTrees
    | ShowTree String Bool


init : String -> Model
init url =
    { baseUrl = url
    , trees = RemoteData.Loading
    , tree = RemoteData.NotAsked
    , treeLogs = RemoteData.NotAsked
    , showMoreTreeLogs = False
    }

load: Model -> (Model, Cmd Msg)
load model =
    ( model
    , fetchTrees model.baseUrl
    )

decodeTrees : JsonDecode.Decoder Trees
decodeTrees =
    JsonDecode.list decodeTree

decodeTree : JsonDecode.Decoder Tree
decodeTree =
    JsonDecode.object4 Tree
        ( "tree" := JsonDecode.string )
        ( "status" := JsonDecode.string )
        ( "reason" := JsonDecode.string )
        ( "message_of_the_day" := JsonDecode.string )
    
decodeTreeLogs : JsonDecode.Decoder TreeLogs
decodeTreeLogs =
    JsonDecode.list decodeTreeLog

decodeTreeLog : JsonDecode.Decoder TreeLog
decodeTreeLog =
    JsonDecode.object6 TreeLog
        ( "tree" := JsonDecode.string )
        ( "when" := JsonDecode.string )
        ( "who" := JsonDecode.string )
        ( "status" := JsonDecode.string )
        ( "reason" := JsonDecode.string )
        ( "tags" := JsonDecode.list JsonDecode.string )

fetch :
    (RemoteData.RemoteData Http.Error a -> b)
    -> String
    -> JsonDecode.Decoder a
    -> Cmd b
fetch msg url decoder =
    Http.get decoder url
        |> RemoteData.asCmd
        |> Cmd.map msg


fetchTrees : String -> Cmd Msg
fetchTrees url =
    fetch FetchedTrees
        (url ++ "/trees2")
        decodeTrees


fetchTree : String -> String -> Cmd Msg
fetchTree url tree =
    fetch FetchedTree
        (url ++ "/trees/" ++ tree)
        decodeTree


fetchTreeLogs : String -> String -> Bool -> Cmd Msg
fetchTreeLogs url tree all =
    let
        all' = if all == True then "1" else "0"
    in
        fetch FetchedTreeLogs
            (url ++ "/trees/" ++ tree ++ "/logs?all=" ++ all')
            decodeTreeLogs


update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        FetchedTrees trees ->
            ( { model | trees = trees }, Cmd.none)
        FetchedTree tree ->
            ( { model | tree = tree }, Cmd.none)
        FetchedTreeLogs logs ->
            ( { model | treeLogs = logs }, Cmd.none)
        ShowTrees ->
            ( init model.baseUrl
            , fetchTrees model.baseUrl
            )
        ShowTree tree more ->
            ( { model | treeLogs = RemoteData.Loading
                      , tree = RemoteData.Loading
                      }
            , Cmd.batch
                [ fetchTree model.baseUrl tree
                , fetchTreeLogs model.baseUrl tree more
                ]
            )


view : Model -> Html Msg
view model =
    let
        content = 
            case model.tree of
                RemoteData.Success tree ->
                    viewTree model tree
                _ ->
                    viewTrees model.trees
    in
        div [] 
            [ h1 [] [ text "TreeStatus" ]
            , content
            ]


viewTree : Model -> Tree -> Html Msg
viewTree model tree =
    viewTreeLogs model.treeLogs tree.tree model.showMoreTreeLogs


viewTreeLogs : (RemoteData.WebData TreeLogs) -> String -> Bool -> Html Msg
viewTreeLogs treeLogs tree more =
    let
        logs =
            case treeLogs of
                RemoteData.Success logs' ->
                    List.map
                        (\log ->
                            let
                                who =
                                    if String.startsWith "human:" log.who
                                       then 
                                           log.who
                                               |> String.split "@"
                                               |> List.head
                                               |> Maybe.withDefault
                                                   (String.dropLeft 6 log.who)
                                       else log.who
                            in
                                tr [] [ td [] [ text (who) ]
                                      , td [] [ text log.when ]
                                      , td [ class <| statusColor log.status
                                           , style [ ( "text-transform", "uppercase" ) ]
                                           ]
                                           [ text log.status ]
                                      , td [] [ text log.reason ]
                                      , td [] [ text (String.join ", " log.tags) ]
                                      ]
                        ) <| List.reverse <| List.sortBy .when logs'
                RemoteData.Failure message ->
                    [ tr []
                         [ td [ colspan 6 ]
                              [ App.Utils.error (ShowTree tree False) (toString message) ]
                         ]
                    ]
                RemoteData.Loading ->
                    [ tr [] [ td [ colspan 3 ] [ App.Utils.loading ] ] ]
                RemoteData.NotAsked ->
                    [ tr [] [] ]
    in
       div []
           [ p [ style [ ("text-align", "center") ] ]
               [ a [ href "#"
                   , App.Utils.onClick ShowTrees
                   ]
                   [ text "Back to all trees ..." ]
               ]
           , table [ class "table table-sm table-hover" ]
                   [ thead [ class "thead-inverse" ]
                           [ tr [] [ th [] [ text "User" ]
                                   , th [] [ text "Time (UTC)" ]
                                   , th [] [ text "Action" ]
                                   , th [] [ text "Reason" ]
                                   , th [] [ text "Tags" ]
                                   ]
                           ]
                   , tbody [] logs 
                   ]
           , div [ style [ ("text-align", "center") ] ]
                 [ a [ href "#"
                     , App.Utils.onClick (ShowTree tree True)
                     ]
                     [ text "More ..." ]
                 ]
           ]


statusColor : String -> String
statusColor status =
    case status of
        "closed" ->
            "text-danger"
        "open" ->
            "text-success"
        "approval required" ->
            "text-warning"
        _ -> 
            ""
        
viewTrees : (RemoteData.WebData Trees) -> Html Msg
viewTrees trees' =
    let
        trees =
            case trees' of
                RemoteData.Success trees ->
                    List.map
                        (\tree ->
                            tr [] [ td [] [ a [ href "#"
                                              , App.Utils.onClick <| ShowTree tree.tree False
                                              ]
                                              [ text tree.tree ]
                                          ]
                                  , td [ class <| statusColor tree.status
                                       , style [ ( "text-transform", "uppercase" ) ]
                                       ]
                                       [ text tree.status ]
                                  , td [] [ text tree.reason ]
                                  ]
                        ) <| List.sortBy .tree trees
                RemoteData.Failure message ->
                    [ tr []
                         [ td [ colspan 3 ]
                              [ App.Utils.error ShowTrees (toString message) ]
                         ]
                    ]
                RemoteData.Loading ->
                    [ tr [] [ td [ colspan 3 ] [ App.Utils.loading ] ] ]
                RemoteData.NotAsked ->
                    [ tr [] [] ]
    in
        table [ class "table table-sm table-hover" ]
              [ thead [ class "thead-inverse" ]
                      [ tr [] [ th [ style [ ( "width",  "20%" ) ] ] [ text "Name" ]
                              , th [ style [ ( "width",  "20%" ) ] ] [ text "State" ]
                              , th [] [ text "Reason" ]
                              ]
                      ]
              , tbody [] trees
              ]
