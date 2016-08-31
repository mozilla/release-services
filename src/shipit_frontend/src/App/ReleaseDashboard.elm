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
  backend_url : String
}

type Msg
   = FetchedAllAnalysis (WebData (List Analysis))
   | FetchedAnalysis (WebData Analysis)
   | SelectAnalysis Analysis


init : (Maybe User.Model) -> String -> (Model, Cmd Msg)
init user backend_url =
  let
    model = {
      all_analysis = NotAsked,
      current_analysis = NotAsked,
      current_user = user,
      backend_url = backend_url
    }
  in
  (
    model,
    -- Initial fetch of every analysis in model
    fetchAllAnalysis model
  )

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

fromJust : Maybe a -> a
fromJust x = case x of
    Just y -> y
    Nothing -> Debug.crash "error: fromJust Nothing"

sendRequest: Model -> String -> Decoder value -> Maybe (Platform.Task Http.Error value)
sendRequest model url decoder =
  case model.current_user of
    Just user ->
      let
        request = {
          verb = "GET",
          headers = [
            -- TODO: use Hawk port here
            -- ("Authorization", user.accessToken),
            ( "Accept", "application/json" )
          ],
          url = model.backend_url ++ url,
          body = Http.empty
        }
      in
        Just (Http.fromJson decoder
          (Http.send Http.defaultSettings request))

    Nothing ->
      -- No credentials
      let
        log = Debug.log "No credentials to fetch analysis"
      in
        Nothing
    
fetchAllAnalysis : Model -> Cmd Msg
fetchAllAnalysis model =
  -- Load all analysis
  let
    response = sendRequest model "/analysis" decodeAllAnalysis 
  in
    case response of
      Just response' ->
          -- Process request
          response'
            |> RemoteData.asCmd
            |> Cmd.map FetchedAllAnalysis
      Nothing ->
        Cmd.none

fetchAnalysis : Model -> Int -> Cmd Msg
fetchAnalysis model analysis_id =
  -- With Credentials
  let 
    url = "/analysis/" ++ (toString analysis_id)
    response = sendRequest model url decodeAnalysis 
  in
    case response of
      Just response' ->
          -- Process request
          response'
            |> RemoteData.asCmd
            |> Cmd.map FetchedAnalysis
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
