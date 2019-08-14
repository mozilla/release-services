module App.TreeStatus.Types exposing (..)

import App.Types
import Form
import RemoteData exposing (WebData)


type Route
    = AddTreeRoute
    | UpdateTreesRoute
    | DeleteTreesRoute
    | ShowTreesRoute
    | ShowTreeRoute String


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


type alias RecentChangeTreeLastState =
    { reason : String
    , status : String
    , tags : List String
    }


type alias RecentChangeTree =
    { id : Int
    , tree : String
    , last_state : RecentChangeTreeLastState
    }


type alias RecentChange =
    { id : Int
    , trees : List RecentChangeTree
    , when : String
    , who : String
    , status : String
    , reason : String
    }


type alias Model addForm updateForm =
    { baseUrl : String
    , treesAlerts : List App.Types.Alert
    , trees : RemoteData.WebData Trees
    , treesSelected : List String
    , tree : RemoteData.WebData Tree
    , treeLogs : RemoteData.WebData TreeLogs
    , treeLogsAll : RemoteData.WebData TreeLogs
    , showMoreTreeLogs : Bool
    , formAddTree : Form.Form () addForm
    , formUpdateTree : Form.Form () updateForm
    , recentChangesAlerts : List App.Types.Alert
    , recentChanges : RemoteData.WebData (List RecentChange)
    , deleteTreesConfirm : Bool
    , deleteError : Maybe String
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
    | FormAddTreeResult (WebData String)
    | FormUpdateTreesMsg Form.Msg
    | FormUpdateTreesResult (WebData String)
    | SelectAllTrees
    | SelectTree String
    | UnselectAllTrees
    | UnselectTree String
    | DeleteTrees
    | DeleteTreesConfirmToggle
    | DeleteTreesResult (WebData String)
    | RevertChange Int
    | DiscardChange Int
    | RecentChangeResult (WebData String)


possibleTreeStatuses : List ( String, String )
possibleTreeStatuses =
    [ ( "open", "Open" )
    , ( "approval required", "Approval required" )
    , ( "closed", "Closed" )
    ]


possibleTreeTags : List ( String, String )
possibleTreeTags =
    [ ( "checkin_compilation", "Check-in compilation failure" )
    , ( "checkin_test", "Check-in test failure" )
    , ( "infra", "Infrastructure related" )
    , ( "backlog", "Job backlog" )
    , ( "planned", "Planned closure" )
    , ( "merges", "Merges" )
    , ( "waiting_for_coverage", "Waiting for coverage" )
    , ( "other", "Other" )
    ]
