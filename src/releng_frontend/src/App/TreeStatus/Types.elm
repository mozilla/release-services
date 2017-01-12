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


type AlertType
    = AlertSuccess
    | AlertInfo
    | AlertWarning
    | AlertDanger


type alias Alert =
    { type_ : AlertType
    , title : String
    , text : String
    }


type alias Model addForm =
    { baseUrl : String
    , alerts : List Alert
    , trees : RemoteData.WebData Trees
    , treesSelected : List String
    , tree : RemoteData.WebData Tree
    , treeLogs : RemoteData.WebData TreeLogs
    , treeLogsAll : RemoteData.WebData TreeLogs
    , showMoreTreeLogs : Bool
    , formAddTree : Form.Form () addForm
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
    | SelectTree String
    | UnselectTree String
    | DeleteTrees
    | DeleteTreesResult (RemoteData.RemoteData Http.RawError Http.Response)
