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

  -- Current Analysis used
  current_analysis : WebData (Analysis),

  -- Backend base endpoint
  backend_dashboard_url : String
}

type Msg
   = FetchedAllAnalysis (WebData (List Analysis))
   | FetchedAnalysis (WebData Analysis)
   | FetchAllAnalysis
   | FetchAnalysis Analysis
   | ProcessHawkRequest
   | UserMsg User.Msg


init : String -> (Model, Cmd Msg)
init backend_dashboard_url =
  -- Init empty model
  ({
    all_analysis = NotAsked,
    current_analysis = NotAsked,
    backend_dashboard_url = backend_dashboard_url
  }, Cmd.none)

-- Update

update : Msg -> Model -> User.Model -> (Model, User.Model, Cmd Msg)
update msg model user =
  case msg of
    FetchAllAnalysis ->
      let
        newModel = { model | all_analysis = Loading }
      in
        fetchAllAnalysis newModel user

    FetchAnalysis analysis ->
      let
        newModel = { model | current_analysis = Loading }
      in
        fetchAnalysis newModel user analysis.id

    FetchedAllAnalysis allAnalysis ->
      (
        { model | all_analysis = allAnalysis },
        user,
        Cmd.none
      )

    FetchedAnalysis analysis ->
      (
        { model | current_analysis = analysis },
        user,
        Cmd.none
      )
  
    ProcessHawkRequest ->
      -- Process awaiting tasks from HAWK
      case user.hawk.requestType of
        User.AllAnalysis ->
          processAllAnalysis model user
        User.Analysis ->
          processAnalysis model user
        _ ->
          (model, user, Cmd.none)

    UserMsg msg ->
      -- Process messages for user
      let
        (newUser, userCmd) = User.update msg user
      in
        ( model, user, Cmd.map UserMsg userCmd)


fetchAllAnalysis : Model -> User.Model -> (Model, User.Model, Cmd Msg)
fetchAllAnalysis model user =
  -- Fetch all analysis summary
  let 
    url = model.backend_dashboard_url ++ "/analysis"
    (user', userCmd) = User.update (User.InitHawkRequest "GET" url User.AllAnalysis) user
  in
    (
      model,
      user',
      Cmd.map UserMsg userCmd
    )

processAllAnalysis : Model -> User.Model -> (Model, User.Model, Cmd Msg)
processAllAnalysis model user =
  -- Decode and save all analysis
  case user.hawk.task of
    Just task ->
      (
        model,
        user,
        (Http.fromJson decodeAllAnalysis task)
        |> RemoteData.asCmd
        |> Cmd.map FetchedAllAnalysis
      )
    Nothing ->
        ( model, user, Cmd.none )

fetchAnalysis : Model -> User.Model -> Int -> (Model, User.Model, Cmd Msg)
fetchAnalysis model user analysis_id =
  -- Fetch a specific analysis with details
  let 
    url = model.backend_dashboard_url ++ "/analysis/" ++ (toString analysis_id)
    (user', userCmd) = User.update (User.InitHawkRequest "GET" url User.Analysis) user
  in
    (
      model,
      user',
      Cmd.map UserMsg userCmd
    )

processAnalysis : Model -> User.Model -> (Model, User.Model, Cmd Msg)
processAnalysis model user =
  -- Decode and save a single analysis
  case user.hawk.task of
    Just task ->
      (
        model,
        user,
        (Http.fromJson decodeAnalysis task)
        |> RemoteData.asCmd
        |> Cmd.map FetchedAnalysis
      )
    Nothing ->
        ( model, user, Cmd.none )

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
