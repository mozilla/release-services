module App exposing (..)

import Html exposing (..)
import Html.App
import Html.Attributes exposing (..)
import Json.Decode as JsonDecode exposing ((:=))
import RouteUrl exposing (UrlChange)
import RouteUrl.Builder as Builder exposing (Builder, builder, replacePath)
import Result exposing (Result(Ok, Err))
import App.TreeStatus
import Hawk
import TaskclusterLogin


type Route
    = NotFoundRoute
    | HomeRoute
    | TreeStatusRoute


type alias Model =
    { route : Route
    , user : TaskclusterLogin.Model
    , treestatus : App.TreeStatus.Model
    , docsUrl : String
    , version : String
    }


type alias Flags =
    { user : TaskclusterLogin.Model
    , treestatusUrl : String
    , docsUrl : String
    , version : String
    }


type Msg
    = TaskclusterLoginMsg TaskclusterLogin.Msg
    | HawkMsg Hawk.Msg
    | NavigateTo Route
    | TreeStatusMsg App.TreeStatus.Msg
