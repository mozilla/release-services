module App.TreeStatus.Types exposing (..)

import Form
import RemoteData
import Http


type Route
    = TreesRoute
    | TreeRoute String


type alias Error =
    { type_ : String
    , detail : String
    , status : Int
    , title : String
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


type alias Model addForm =
    { baseUrl : String
    , trees : RemoteData.WebData Trees
    , tree : RemoteData.WebData Tree
    , treeLogs : RemoteData.WebData TreeLogs
    , treeLogsAll : RemoteData.WebData TreeLogs
    , showMoreTreeLogs : Bool
    , formAddTree : Form.Form () addForm
    , formAddTreeError : Maybe String
    }


type Msg
    = NavigateTo Route
    | GetTreesResult (RemoteData.WebData Trees)
    | GetTreeResult (RemoteData.WebData Tree)
    | GetTreeLogs String Bool
    | GetTreeLogsResult (RemoteData.WebData TreeLogs)
    | GetTreeLogsAllResult (RemoteData.WebData TreeLogs)
    | FormAddTreeMsg Form.Msg
    | FormAddTreeResult (RemoteData.RemoteData Http.RawError Http.Response)
