module App.ReleaseDashboard exposing (..) 

import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import String
import Json.Decode as Json exposing (Decoder, (:=))
import Json.Decode.Extra as JsonExtra exposing ((|:))
import RemoteData as RemoteData exposing ( WebData, RemoteData(Loading, Success, NotAsked, Failure) )

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
  bugs: List Bug
}

type alias Model = {
  -- All analysis in use
  analysis : WebData (List Analysis),

  -- Current connected user
  current_user : Maybe User.Model
}

type Msg
   = FetchedAnalysis (WebData (List Analysis))


init : (Maybe User.Model) -> (Model, Cmd Msg)
init user =
  (
    {
      analysis = NotAsked,
      current_user = user
    }, 
    -- Initial fetch of every analysis in model
    fetchAnalysis user
  )

-- Update

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of
    FetchedAnalysis allAnalysis ->
      (
        { model | analysis = allAnalysis },
        Cmd.none
      )

fromJust : Maybe a -> a
fromJust x = case x of
    Just y -> y
    Nothing -> Debug.crash "error: fromJust Nothing"
    
fetchAnalysis : (Maybe User.Model) -> Cmd Msg
fetchAnalysis maybeUser =
  -- Load all analysis
  case maybeUser of
    Just user ->
      -- With Credentials
      let 
        -- TODO: use dashboardUrl
        baseUrl = "http://localhost:5000/analysis" 
        url = Http.url baseUrl [
          ("clientId", fromJust user.clientId),
          ("accessToken", fromJust user.accessToken)
        ]
        log' = Debug.log "URL to fetch analysis" url
      in
        Http.get decodeAnalysis url
          |> RemoteData.asCmd
          |> Cmd.map FetchedAnalysis

    Nothing ->
      -- No credentials
      let
        log = Debug.log "No credentials to fetch analysis"
      in
        Cmd.none


decodeAnalysis : Decoder (List Analysis)
decodeAnalysis =
  Json.list (
    Json.object3 Analysis
      ("id" := Json.int)
      ("name" := Json.string)
      ("bugs" := Json.list decodeBug)
  )

decodeBug : Decoder Bug
decodeBug =
  Json.succeed Bug
    |: ("id" := Json.int)
    |: ("bugzilla_id" := Json.int)
    |: ("summary" := Json.string)
    |: ("keywords" := Json.list Json.string)
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
  case model.analysis of
    NotAsked ->
      div [class "alert alert-info"] [text "Initialising ..."]

    Loading ->
      div [class "alert alert-info"] [text "Loading ..."]

    Failure err ->
      div [class "alert alert-danger"] [text ("Error: " ++ toString err)]

    Success allAnalysis ->
      div []
        (List.map viewAnalysis allAnalysis)


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
        viewStats bug
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

viewKeyword: String -> Html Msg
viewKeyword keyword =
  span [class "label label-default"] [text keyword]
