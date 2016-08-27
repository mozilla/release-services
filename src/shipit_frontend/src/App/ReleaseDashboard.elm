module App.ReleaseDashboard exposing (..) 

import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Json.Decode as Json exposing (Decoder, (:=))
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
  creator: Contributor,
  assignee: Contributor,
  reviewers: List String, -- Should use Contributor with Maybe
  uplift_request: Maybe UpliftRequest
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
  Json.object7 Bug
    ("id" := Json.int)
    ("bugzilla_id" := Json.int)
    (Json.at ["payload", "bug", "summary"] Json.string)
    (Json.at ["payload", "analysis", "users", "creator"] decodeContributor)
    (Json.at ["payload", "analysis", "users", "assignee"] decodeContributor)
    (Json.at ["payload", "analysis", "users", "reviewers"] (Json.list Json.string))
    (Json.maybe ((Json.at ["payload", "analysis"] decodeUpliftRequest)))

decodeContributor : Decoder Contributor
decodeContributor = 
  Json.object2 Contributor
    ("email" := Json.string)
    ("real_name" := Json.string)

decodeUpliftContributor : Decoder Contributor
decodeUpliftContributor = 
  Json.object2 Contributor
    ("name" := Json.string) -- name is actually the email :/
    ("real_name" := Json.string)

decodeUpliftRequest : Decoder UpliftRequest
decodeUpliftRequest  =
  Json.object3 UpliftRequest
    (Json.at ["uplift_comment", "id"] Json.int)
    ("uplift_author" := decodeUpliftContributor)
    (Json.at ["uplift_comment", "raw_text"] Json.string)

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
    , div [] (List.map viewBug analysis.bugs)
    ]


viewBug: Bug -> Html Msg
viewBug bug =
  div [class "bug"] [
    h4 [] [text bug.summary],
    viewContributor bug.creator "Creator",
    viewContributor bug.assignee "Assignee",
    viewReviewers bug.reviewers,
    viewUpliftRequest bug.uplift_request,
    p [] [
      span [] [text ("#" ++ (toString bug.bugzilla_id))],
      a [href ("https://bugzilla.mozilla.org/show_bug.cgi?id=" ++ (toString bug.bugzilla_id)), target "_blank"] [text "View on bugzilla"]
    ],
    hr [] []
  ]

viewContributor: Contributor -> String -> Html Msg
viewContributor user title = 
  div [class "user"] [
    strong [] [text (title ++ ": ")],
    a [href ("mailto:" ++ user.email)] [text user.name]
  ]

viewReviewers: (List String) -> Html Msg
viewReviewers users = 
  div [class "users"] [
    strong [] [text "Reviewers:"],
    ul [] (List.map viewReviewer users)
  ]
  
viewReviewer: String -> Html Msg
viewReviewer user =
  li [class "user"] [
    a [href ("mailto:" ++ user)] [text user]
  ]

viewUpliftRequest: Maybe UpliftRequest -> Html Msg
viewUpliftRequest maybe =
  case maybe of
    Just request -> 
      div [class "uplift-request", id (toString request.bugzilla_id)] [
        viewContributor request.author "Uplift request",
        blockquote [] [text request.text]
      ]
    Nothing -> 
      div [class "alert alert-warning"] [text "No uplift request."]

