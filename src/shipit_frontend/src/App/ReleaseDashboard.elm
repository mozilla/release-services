module App.ReleaseDashboard exposing (..) 

import Html exposing (..)
import Html.Attributes exposing (..)
import String
import Dict
import Json.Decode as Json exposing (Decoder, (:=))
import Json.Decode.Extra as JsonExtra exposing ((|:))
import RemoteData as RemoteData exposing ( WebData, RemoteData(Loading, Success, NotAsked, Failure) )
import Http
import Task exposing (Task)
import Basics exposing (Never)

import App.User as User
import App.Hawk as Hawk

-- Models

type alias Contributor = {
  email: String,
  name: String
}

type alias UpliftRequest = {
  bugzilla_id: Int,
  author: Contributor,
  text: String
}

type alias Bug = {
  id: Int,
  bugzilla_id: Int,
  summary: String,
  keywords: List String,
  flags_status : Dict.Dict String String,

  -- Users
  creator: Contributor,
  assignee: Contributor,
  reviewers: List Contributor,

  uplift_request: Maybe UpliftRequest,

  -- Stats
  changes: Int
}

type alias Analysis = {
  id: Int,
  name: String,
  count: Int,
  bugs: List Bug
}

type alias Model = {
  -- All analysis in use
  all_analysis : WebData (List Analysis),

  -- Current connected user
  current_user : Maybe User.Model,

  -- Current Analysis used
  current_analysis : WebData (Analysis),

  -- Backend base endpoint
  backend_dashboard_url : String
}

type Msg
   = FetchedAllAnalysis (WebData (List Analysis))
   | FetchedAnalysis (WebData Analysis)
   | SelectAnalysis Analysis
   | UserUpdate (Maybe User.Model)
   | FetchFailure Never


init : String -> (Model, Cmd Msg)
init backend_dashboard_url =
  -- Init empty model
  ({
    all_analysis = NotAsked,
    current_analysis = NotAsked,
    current_user = Nothing,
    backend_dashboard_url = backend_dashboard_url
  }, Cmd.none)

-- Update

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of
    FetchedAllAnalysis allAnalysis ->
      (
        { model | all_analysis = allAnalysis },
        Cmd.none
      )

    FetchedAnalysis analysis ->
      (
        { model | current_analysis = analysis },
        Cmd.none
      )
  
    SelectAnalysis analysis ->
      (
        { model | current_analysis = Loading },
        fetchAnalysis model analysis.id
      )

    UserUpdate user ->
      let
        newModel = { model | current_user = user }
      in
      (
        newModel,
        -- Reload all analysis
        fetchAllAnalysis newModel
      )

    FetchFailure never ->
      let
        l = Debug.log "Should never happen" never
      in
        ( model, Cmd.none)


fetchAllAnalysis : Model -> Cmd Msg
fetchAllAnalysis model =
  -- Fetch all analysis summary
  let 
    url = model.backend_dashboard_url ++ "/analysis"
  in
    (Hawk.workflow model.current_user "GET" url decodeAllAnalysis)
    |> RemoteData.fromTask
    |> Task.perform FetchFailure FetchedAllAnalysis

fetchAnalysis : Model -> Int -> Cmd Msg
fetchAnalysis model analysis_id =
  -- Fetch a specific analysis with details
  let 
    url = model.backend_dashboard_url ++ "/analysis/" ++ (toString analysis_id)
  in
    (Hawk.workflow model.current_user "GET" url decodeAnalysis)
    |> RemoteData.fromTask
    |> Task.perform FetchFailure FetchedAnalysis

decodeAllAnalysis : Decoder (List Analysis)
decodeAllAnalysis =
  Json.list decodeAnalysis

decodeAnalysis : Decoder Analysis
decodeAnalysis =
  Json.object4 Analysis
    ("id" := Json.int)
    ("name" := Json.string)
    ("count" := Json.int)
    ("bugs" := Json.list decodeBug)

decodeBug : Decoder Bug
decodeBug =
  Json.succeed Bug
    |: ("id" := Json.int)
    |: ("bugzilla_id" := Json.int)
    |: ("summary" := Json.string)
    |: ("keywords" := Json.list Json.string)
    |: ("flags_status" := Json.dict Json.string)
    |: ("creator" := decodeContributor)
    |: ("assignee" := decodeContributor)
    |: ("reviewers" := (Json.list decodeContributor))
    |: (Json.maybe ("uplift" := decodeUpliftRequest))
    |: ("changes_size" := Json.int)
    

decodeContributor : Decoder Contributor
decodeContributor = 
  Json.object2 Contributor
    ("email" := Json.string)
    ("real_name" := Json.string)

decodeUpliftRequest : Decoder UpliftRequest
decodeUpliftRequest  =
  Json.object3 UpliftRequest
    ("id" := Json.int)
    ("author" := decodeContributor)
    ("comment" := Json.string)

-- Subscriptions

subscriptions : Analysis -> Sub Msg
subscriptions analysis =
  Sub.none


-- Views

view : Model -> Html Msg
view model =
  case model.current_analysis of
    NotAsked ->
      div [class "alert alert-info"] [text "Initialising ..."]

    Loading ->
      div [class "alert alert-info"] [text "Loading ..."]

    Failure err ->
      div [class "alert alert-danger"] [text ("Error: " ++ toString err)]

    Success analysis ->
      viewAnalysis analysis


viewAnalysis: Analysis -> Html Msg
viewAnalysis analysis =
  div []
    [ h1 [] [text ("Analysis: " ++ analysis.name)]
    , div [class "bugs"] (List.map viewBug analysis.bugs)
    ]


viewBug: Bug -> Html Msg
viewBug bug =
  div [class "bug"] [
    h4 [] [text bug.summary],
    div [class "row"] [
      div [class "col-xs-4"] [
        viewContributor bug.creator "Creator",
        viewContributor bug.assignee "Assignee",
        viewReviewers bug.reviewers
      ],
      div [class "col-xs-4"] [
        viewUpliftRequest bug.uplift_request
      ],
      div [class "col-xs-4"] [
        viewStats bug,
        viewFlags bug
      ]
    ],
    div [class "text-muted"] [
      span [] [text ("#" ++ (toString bug.bugzilla_id))],
      a [href ("https://bugzilla.mozilla.org/show_bug.cgi?id=" ++ (toString bug.bugzilla_id)), target "_blank"] [text "View on bugzilla"]
    ]
  ]

viewContributor: Contributor -> String -> Html Msg
viewContributor user title = 
  div [class "user"] [
    strong [] [text (title ++ ": ")],
    a [href ("mailto:" ++ user.email)] [text user.name]
  ]

  
viewReviewers: (List Contributor) -> Html Msg
viewReviewers users =
  div [] [
    strong [] [text "Reviewers:"],
    ul [class "users"] (List.map viewReviewer users)
  ]

viewReviewer: Contributor -> Html Msg
viewReviewer user =
  li [class "user"] [
    a [href ("mailto:" ++ user.email)] [text user.name]
  ]

viewUpliftRequest: Maybe UpliftRequest -> Html Msg
viewUpliftRequest maybe =
  case maybe of
    Just request -> 
      div [class "uplift-request", id (toString request.bugzilla_id)] [
        viewContributor request.author "Uplift request",
        div [class "comment"] (List.map viewUpliftText (String.split "\n" request.text))
      ]
    Nothing -> 
      div [class "alert alert-warning"] [text "No uplift request."]


viewUpliftText: String -> Html Msg
viewUpliftText upliftText =
  p [] [text upliftText]

viewStats: Bug -> Html Msg
viewStats bug =
  div [class "stats"] [
    p [] (List.map viewKeyword bug.keywords),
    p [] [
      span [class "label label-info"] [text "Changes"],
      span [] [text (toString bug.changes)]
    ]
  ]

viewFlags: Bug -> Html Msg
viewFlags bug =
  let
    useful_flags = Dict.filter (\k v -> not (v == "---")) bug.flags_status
  in 
    div [class "flags"] [
      h5 [] [text "Tracking flags - status"],
      ul [] (List.map viewFlag (Dict.toList useful_flags))
    ]

viewFlag tuple =
  let
    (key, value) = tuple
  in
    li [] [
      strong [] [text key],
      case value of
        "affected" -> span [class "label label-danger"] [text value]
        "verified" -> span [class "label label-info"] [text value]
        "fixed" -> span [class "label label-success"] [text value]
        "wontfix" -> span [class "label label-warning"] [text value]
        _ -> span [class "label label-default"] [text value]
      
    ]

viewKeyword: String -> Html Msg
viewKeyword keyword =
  span [class "label label-default"] [text keyword]
