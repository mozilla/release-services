module App.TreeStatus.Types exposing (..)

import App.Types
import Form
import Http
import RemoteData


type Route
    = TreesRoute
    | TreeRoute String


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


type alias RecentChange =
    { id : Int
    , trees : List String
    , when : String
    , who : String
    , status : String
    , reason : String
    }


type alias Model addForm updateForm =
    { baseUrl : String
    , alerts : List App.Types.Alert
    , trees : RemoteData.WebData Trees
    , treesSelected : List String
    , tree : RemoteData.WebData Tree
    , treeLogs : RemoteData.WebData TreeLogs
    , treeLogsAll : RemoteData.WebData TreeLogs
    , showMoreTreeLogs : Bool
    , formAddTree : Form.Form () addForm
    , formUpdateTree : Form.Form () updateForm
    , recentChanges : RemoteData.WebData (List RecentChange)
    }


type Msg
    = NavigateTo Route
    | GetTreesResult (RemoteData.WebData Trees)
    | GetTreeResult (RemoteData.WebData Tree)
    | GetTreeLogs String Bool
    | GetTreeLogsResult (RemoteData.WebData TreeLogs)
    | GetTreeLogsAllResult (RemoteData.WebData TreeLogs)
    | GetRecentChangesResult (RemoteData.WebData (List RecentChange))
    | FormAddTreeMsg Form.Msg
    | FormAddTreeResult (RemoteData.RemoteData Http.RawError Http.Response)
    | FormUpdateTreeMsg Form.Msg
    | FormUpdateTreeResult (RemoteData.RemoteData Http.RawError Http.Response)
    | FormUpdateTreesResult (RemoteData.RemoteData Http.RawError Http.Response)
    | SelectTree String
    | UnselectTree String
    | DeleteTrees
    | DeleteTreesResult (RemoteData.RemoteData Http.RawError Http.Response)
    | RevertChange Int
    | DiscardChange Int
    | RecentChangeResult (RemoteData.RemoteData Http.RawError Http.Response)


possibleTreeStatuses : List ( String, String )
possibleTreeStatuses =
    [ ( "open", "Open" )
    , ( "approval required", "Approval required" )
    , ( "closed", "Closed" )
    ]


possibleTreeTags : List ( String, String, String )
possibleTreeTags =
    [ ( "checkin-compilation", "checkin_compilation", "Check-in compilation failure" )
    , ( "checkin-test", "checkin_test", "Check-in test failure" )
    , ( "infra", "infra", "Infrastructure related" )
    , ( "backlog", "backlog", "Job backlog" )
    , ( "planned", "planned", "Planned closure" )
    , ( "other", "other", "Other" )
    ]
