module App.TreeStatus.Api exposing (..)

import App.TreeStatus.Types
import Http
import Json.Decode as JsonDecode exposing ((:=))
import Json.Encode as JsonEncode
import RemoteData


encoderTree : App.TreeStatus.Types.Tree -> JsonEncode.Value
encoderTree tree =
    JsonEncode.object
        [ ( "tree", JsonEncode.string tree.name )
        , ( "status", JsonEncode.string tree.status )
        , ( "reason", JsonEncode.string tree.reason )
        , ( "message_of_the_day", JsonEncode.string tree.message_of_the_day )
        ]


decoderTrees : JsonDecode.Decoder App.TreeStatus.Types.Trees
decoderTrees =
    JsonDecode.list decoderTree


decoderTree : JsonDecode.Decoder App.TreeStatus.Types.Tree
decoderTree =
    JsonDecode.object4 App.TreeStatus.Types.Tree
        ("tree" := JsonDecode.string)
        ("status" := JsonDecode.string)
        ("reason" := JsonDecode.string)
        ("message_of_the_day" := JsonDecode.string)


decoderTreeLogs : JsonDecode.Decoder App.TreeStatus.Types.TreeLogs
decoderTreeLogs =
    JsonDecode.list decoderTreeLog


decoderTreeLog : JsonDecode.Decoder App.TreeStatus.Types.TreeLog
decoderTreeLog =
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
        decoderTrees


fetchTree :
    String
    -> String
    -> Cmd App.TreeStatus.Types.Msg
fetchTree url name =
    get App.TreeStatus.Types.GetTreeResult
        (url ++ "/trees/" ++ name)
        decoderTree


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
                decoderTreeLogs

        False ->
            get App.TreeStatus.Types.GetTreeLogsResult
                (url ++ "/trees/" ++ name ++ "/logs?all=0")
                decoderTreeLogs


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
