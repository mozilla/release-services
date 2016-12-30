module App.TreeStatus.Api exposing (..)

import App.TreeStatus.Types
import Http
import Json.Decode as JsonDecode exposing ((:=))
import Json.Encode as JsonEncode
import RemoteData


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
