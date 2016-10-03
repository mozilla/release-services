module App.ReleaseDashboard exposing (..) 

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onClick, onInput, onSubmit)
import String
import Dict
import Json.Decode as Json exposing (Decoder, (:=))
import Json.Decode.Extra as JsonExtra exposing ((|:))
import Json.Encode as JsonEncode
import RemoteData as RemoteData exposing ( WebData, RemoteData(Loading, Success, NotAsked, Failure) )
import Http
import Task exposing (Task)
import Basics exposing (Never)

import App.User as User exposing (Hawk)
import App.Utils exposing (onChange)

-- Models

type alias Contributor = {
  email: String,
  name: String,
  avatar: String
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
  flags_tracking : Dict.Dict String String,

  -- Users
  creator: Contributor,
  assignee: Contributor,
  reviewers: List Contributor,

  uplift_request: Maybe UpliftRequest,

  -- Stats
  changes: Int,

  -- Actions on bug
  editing: Bool,
  edits : Dict.Dict String String
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
   | FetchedBug (WebData Bug)
   | FetchAllAnalysis
   | FetchAnalysis Int
   | StartBugEditor Bug
   | EditBug Bug String String
   | SaveBugEdit Bug
   | SavedBugEdit Bug (WebData (List Int))
   | ProcessWorkflow Hawk
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

    FetchAnalysis analysisId ->
      let
        newModel = { model | current_analysis = Loading }
      in
        fetchAnalysis newModel user analysisId

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

    ProcessWorkflow workflow ->
      -- Process task from workflow
      let
        cmd = case workflow.requestType of
          User.AllAnalysis ->
            processAllAnalysis workflow
          User.Analysis ->
            processAnalysis workflow
          User.BugEdits -> 
            processBugEdits workflow
          _ ->
            Cmd.none
      in
        (model, user, cmd)

    UserMsg msg ->
      -- Process messages for user
      let
        (newUser, workflow, userCmd) = User.update msg user
      in
        ( model, user, Cmd.map UserMsg userCmd)

    StartBugEditor bug ->
      -- Mark a bug as being edited
      let
        model' = updateBug model bug.id (\b -> { b | editing = True })
      in
        (model', user, Cmd.none)

    EditBug bug key value ->
      -- Store a bug edit
      let
        edits = Dict.insert key value bug.edits
        model' = updateBug model bug.id (\b -> { b | edits = edits })
      in
        (model', user, Cmd.none)

    SaveBugEdit bug ->
      -- Send edits to backend
      publishBugEdits model user bug

    FetchedBug bug ->
      -- Store updated bug - post edits
      let
        model' = case bug of
          Success bug' -> updateBug model bug'.id (\b -> bug')
          _ -> model
      in
        (model', user, Cmd.none)

    SavedBugEdit bug edits ->
      let
        -- TODO: mark bug as edited & display to user
        l = Debug.log "Saved bug edit !" edits
      in
        (model, user, Cmd.none)
      

updateBug: Model -> Int -> (Bug -> Bug) -> Model
updateBug model bugId callback =
  -- Update a bug in current analysis
  -- using a callback
  case model.current_analysis of
    Success analysis ->
      let

        -- Rebuild bugs list
        bugs = List.map (\b -> if b.id == bugId then (callback b) else b) analysis.bugs

        -- Rebuild analysis
        analysis' = { analysis | bugs = bugs }

      in
        { model | current_analysis = Success analysis' }

    _ -> model

fetchAllAnalysis : Model -> User.Model -> (Model, User.Model, Cmd Msg)
fetchAllAnalysis model user =
  -- Fetch all analysis summary
  let 
    params = {
      backend = {
        method = "GET",
        url = model.backend_dashboard_url ++ "/analysis"
      },
      target = Nothing,
      body = Nothing,
      requestType = User.AllAnalysis
    }
    (user', workflow, userCmd) = User.update (User.InitHawkRequest params) user
  in
    (
      model,
      user',
      Cmd.map UserMsg userCmd
    )

processAllAnalysis : Hawk -> Cmd Msg
processAllAnalysis workflow =
  -- Decode and save all analysis
  case workflow.task of
    Just task ->
      (Http.fromJson decodeAllAnalysis task)
      |> RemoteData.asCmd
      |> Cmd.map FetchedAllAnalysis

    Nothing ->
        Cmd.none

fetchAnalysis : Model -> User.Model -> Int -> (Model, User.Model, Cmd Msg)
fetchAnalysis model user analysis_id =
  -- Fetch a specific analysis with details
  let 
    params = {
      backend = {
        method = "GET",
        url = model.backend_dashboard_url ++ "/analysis/" ++ (toString analysis_id)
      },
      target = Nothing,
      body = Nothing,
      requestType = User.Analysis
    }
    (user', workflow, userCmd) = User.update (User.InitHawkRequest params) user
  in
    (
      model,
      user',
      Cmd.map UserMsg userCmd
    )

processAnalysis : Hawk -> Cmd Msg
processAnalysis workflow =
  -- Decode and save a single analysis
  case workflow.task of
    Just task ->
      (Http.fromJson decodeAnalysis task)
      |> RemoteData.asCmd
      |> Cmd.map FetchedAnalysis

    Nothing ->
        Cmd.none

encodeBugzillaFlag : (String, String) -> JsonEncode.Value
encodeBugzillaFlag (key, value) = 
  JsonEncode.object [
    ("name", JsonEncode.string key),
    ("value", JsonEncode.string value)
  ]

publishBugEdits: Model -> User.Model -> Bug -> (Model, User.Model, Cmd Msg)
publishBugEdits model user bug =
  -- Publish all bug edits directly to Bugzilla
  case user.bugzilla of
    Just bugzilla ->
      let
        comment = Dict.get "comment" bug.edits |> Maybe.withDefault "Modified from Shipit."

        -- Build payload for bugzilla
        payload = JsonEncode.encode 0 (
          JsonEncode.object [
            ("comment", JsonEncode.string comment),
            ("flags", JsonEncode.list (List.map encodeBugzillaFlag (Dict.toList bug.edits)))
          ]
        )
        l = Debug.log "Bugzilla payload" payload

        task = User.buildBugzillaTask bugzilla {
          method = "PUT",
          url = "/bug/" ++ (toString bug.bugzilla_id)
        } (Just payload)

        cmd = (Http.fromJson decodeBugEdits task)
          |> RemoteData.asCmd
          |> Cmd.map (SavedBugEdit bug)
      in
        (model, user, cmd)

    Nothing ->
      -- No credentials !
      (model, user, Cmd.none)

decodeBugEdits : Decoder (List Int)
decodeBugEdits =
  Json.at ["bugs"] (Json.list (
    Json.at ["id"] Json.int
  ))

processBugEdits : Hawk -> Cmd Msg
processBugEdits workflow =
  -- Decode and save a single analysis
  case workflow.task of
    Just task ->
      (Http.fromJson decodeBug task)
      |> RemoteData.asCmd
      |> Cmd.map FetchedBug

    Nothing ->
        Cmd.none

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
    |: ("flags_tracking" := Json.dict Json.string)
    |: ("creator" := decodeContributor)
    |: ("assignee" := decodeContributor)
    |: ("reviewers" := (Json.list decodeContributor))
    |: (Json.maybe ("uplift" := decodeUpliftRequest))
    |: ("changes_size" := Json.int)
    |: (Json.succeed False) -- not editing at first
    |: (Json.succeed Dict.empty) -- not editing at first
    

decodeContributor : Decoder Contributor
decodeContributor = 
  Json.object3 Contributor
    ("email" := Json.string)
    ("real_name" := Json.string)
    ("avatar" := Json.string)

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
      div [class "alert alert-info"] [text "Please select an analysis in the navbar above."]

    Loading ->
      div [class "alert alert-info"] [text "Loading your bugs..."]

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
      div [class "col-xs-4"] ([
        viewContributor bug.creator "Creator",
        viewContributor bug.assignee "Assignee"
      ] ++ (List.map (\x -> viewContributor x "Reviewer") bug.reviewers)),
      div [class "col-xs-4"] [
        viewUpliftRequest bug.uplift_request
      ],
      div [class "col-xs-4"] [
        if bug.editing then
          viewEditor bug
        else
          viewBugDetails bug
      ]
    ],
    div [class "text-muted"] [
      span [] [text ("#" ++ (toString bug.bugzilla_id))],
      a [href ("https://bugzilla.mozilla.org/show_bug.cgi?id=" ++ (toString bug.bugzilla_id)), target "_blank"] [text "View on bugzilla"]
    ]
  ]

viewContributor: Contributor -> String -> Html Msg
viewContributor user title = 
  div [class "user row"] [
    div [class "col-xs-4 col-sm-1"] [
      img [class "avatar img-fluid img-rounded", src user.avatar] []
    ],
    div [class "col-xs-8 col-sm-11"] [
      p [class "lead"] [text user.name],
      p [] [
        a [href ("mailto:" ++ user.email)] [text user.email]
      ],
      p [] [
        span [class "label label-default"] [text title]
      ]
    ]
  ]

viewUpliftRequest: Maybe UpliftRequest -> Html Msg
viewUpliftRequest maybe =
  case maybe of
    Just request -> 
      div [class "uplift-request", id (toString request.bugzilla_id)] [
        viewContributor request.author "Uplift request",
        div [class "comment"] (List.map (\x -> p [] [text x]) (String.split "\n" request.text))
      ]
    Nothing -> 
      div [class "alert alert-warning"] [text "No uplift request."]

viewBugDetails: Bug -> Html Msg
viewBugDetails bug =
  div [class "details"] [
    viewStats bug,
    viewFlags bug,
  
    -- Start editing
    button [class "btn btn-primary", onClick (StartBugEditor bug)] [text "Edit this bug"]
  ]

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
    flags_status = Dict.filter (\k v -> not (v == "---")) bug.flags_status
    flags_tracking = Dict.filter (\k v -> not (v == "---")) bug.flags_tracking
  in 
    div [class "flags"] [
      h5 [] [text "Status flags"],
      if Dict.isEmpty flags_status then
        p [class "text-warning"] [text "No status flags set."]
      else
        ul [] (List.map viewStatusFlag (Dict.toList flags_status)),

      h5 [] [text "Tracking flags"],
      if Dict.isEmpty flags_tracking then
        p [class "text-warning"] [text "No tracking flags set."]
      else
        ul [] (List.map viewTrackingFlag (Dict.toList flags_tracking))
    ]

viewStatusFlag (key, value) =
  li [] [
    strong [] [text key],
    case value of
      "affected" -> span [class "label label-danger"] [text value]
      "verified" -> span [class "label label-info"] [text value]
      "fixed" -> span [class "label label-success"] [text value]
      "wontfix" -> span [class "label label-warning"] [text value]
      _ -> span [class "label label-default"] [text value]
  ]

editStatusFlag: Bug -> (String, String) -> Html Msg
editStatusFlag bug (key, flag_value) =
  let
    possible_values = ["affected", "verified", "fixed", "wontfix", "---"]
  in
    div [class "form-group row"] [
      label [class "col-sm-6 col-form-label"] [text key],
      div [class "col-sm-6"] [
        select [class "form-control form-control-sm", onChange (EditBug bug ("status_" ++ key))]
          (List.map (\x -> option [ selected (x == flag_value)] [text x]) possible_values)
      ]
    ]

viewTrackingFlag (key, value) =
  li [] [
    strong [] [text key],
    case value of
      "+" -> span [class "label label-success"] [text value]
      "-" -> span [class "label label-danger"] [text value]
      "?" -> span [class "label label-info"] [text value]
      _ -> span [class "label label-default"] [text value]
  ]

editTrackingFlag: Bug -> (String, String) -> Html Msg
editTrackingFlag bug (key, flag_value) =
  let
    possible_values = ["+", "-", "?", "---"]
  in
    div [class "form-group row"] [
      label [class "col-sm-6 col-form-label"] [text key],
      div [class "col-sm-6"] [
        select [class "form-control form-control-sm", onChange (EditBug bug ("tracking_" ++ key))]
          (List.map (\x -> option [ selected (x == flag_value)] [text x]) possible_values)
      ]
    ]

viewEditor: Bug -> Html Msg
viewEditor bug =
  Html.form [class "editor", onSubmit (SaveBugEdit bug)] [
    div [class "col-xs-12 col-sm-6"]
      ([h4 [] [text "Status"] ] ++ (List.map (\x -> editStatusFlag bug x) (Dict.toList bug.flags_status))),
    div [class "col-xs-12 col-sm-6"]
      ([h4 [] [text "Tracking"] ] ++ (List.map (\x -> editTrackingFlag bug x) (Dict.toList bug.flags_tracking))),
    div [class "form-group"] [
      textarea [class "form-control", placeholder "Your comment", onInput (EditBug bug "comment")] []
    ],
    button [class "btn btn-success"] [text "Update bug"]
  ]

viewKeyword: String -> Html Msg
viewKeyword keyword =
  span [class "label label-default"] [text keyword]
