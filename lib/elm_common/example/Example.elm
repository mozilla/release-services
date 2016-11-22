port module Example exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Html.App
import Http
import Json.Decode as JsonDecode exposing ((:=))
import RouteUrl exposing ( UrlChange )
import RouteUrl.Builder as Builder exposing ( Builder, builder, replacePath )
import RemoteData exposing ( WebData , RemoteData(..))
import Navigation exposing ( Location )

import BugzillaLogin as Bugzilla
import TaskclusterLogin as User
import Hawk

type Msg = BugzillaMsg Bugzilla.Msg
  | UserMsg User.Msg
  | HawkMsg Hawk.Msg
  | LoadScopes
  | FetchedScopes (WebData (List String))

type alias Model = {
  user : User.Model,
  bugzilla : Bugzilla.Model,
  scopes : WebData (List String)
}

type alias Flags = {
  bugzilla_url: String
}

init : Flags -> (Model, Cmd Msg)
init flags =
    let
        (bz, bzCmd) = Bugzilla.init flags.bugzilla_url
        (user, userCmd) = User.init
    in
    (
      {
        bugzilla = bz,
        user = user,
        scopes = NotAsked
      },
      -- Follow through with sub parts init
      Cmd.batch [
        Cmd.map BugzillaMsg bzCmd,
        Cmd.map UserMsg userCmd
      ]
    )

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of
    BugzillaMsg bzMsg ->
      let
        (newBz, bzCmd) = Bugzilla.update bzMsg model.bugzilla
      in
        (
          { model | bugzilla = newBz },
          Cmd.map BugzillaMsg bzCmd
        )

    UserMsg userMsg ->
      let
        (newUser, userCmd) = User.update userMsg model.user
      in
        (
          { model | user = newUser },
          Cmd.map UserMsg userCmd
        )

    LoadScopes ->
      case model.user.credentials of
        Just credentials ->
          let
            -- Build Taskcluster http request
            url = "https://auth.taskcluster.net/v1/scopes/current"
            request = Http.Request "GET" [] url Http.empty
          in
            (
              model,
              Cmd.map HawkMsg (Hawk.add_header request credentials)
            )
        Nothing ->
            (model, Cmd.none)

    FetchedScopes scopes ->
      -- Save scopes on model
      ( { model | scopes = scopes }, Cmd.none)

    HawkMsg hawkMsg ->
      let

        -- TODO: support multiple decoders
        decoder = JsonDecode.at ["scopes"] (JsonDecode.list JsonDecode.string)

        (hawkCmd, responses) = Hawk.update decoder hawkMsg
      in
        (
          model,
          Cmd.batch [
            Cmd.map HawkMsg hawkCmd,
            Cmd.map FetchedScopes responses 
          ]
        )

-- Demo view
view model =
  div [] [ 
    h1 [] [text "Taskcluster"],
    Html.App.map UserMsg (User.view model.user),
    h1 [] [text "Hawk"],
    viewHawk model,
    h1 [] [text "Bugzilla"],
    Html.App.map BugzillaMsg (Bugzilla.view model.bugzilla)
  ]

viewHawk model = 
  div [] [
    case model.user.credentials of
      Just credentials ->
        button [onClick LoadScopes] [text "Request Taskcluster scopes"]
      Nothing ->
        span [class "text-warning"] [text "Login on Taskcluster first."]
    , case model.scopes of
      Success scopes ->
        ul [] (List.map (\s -> li [] [text s]) scopes)
      Failure err ->
        p [class "text-danger"] [text ("Error: "++(toString err))]
      Loading ->
        p [class "text-info"] [text "Loading scopes..."]
      NotAsked ->
        p [class "text-info"] [text "Scopes not fetched yet."]
  ]

-- Empty Routing
location2messages : Location -> List Msg
location2messages location =
  let
    builder = Builder.fromUrl location.href
  in
    case Builder.path builder of
      first :: rest ->
        case first of
          "login" -> [
            Builder.query builder
            |> User.convertUrlQueryToUser
            |> User.Logging
            |> UserMsg
          ]
          _ -> []

      _ -> []

delta2url : Model -> Model -> Maybe UrlChange
delta2url previous current =
  Nothing

-- Subscriptions
subscriptions : Model -> Sub Msg
subscriptions model =
  Sub.batch [
    Sub.map BugzillaMsg (Bugzilla.bugzillalogin_get (Bugzilla.Logged)),
    Sub.map UserMsg (User.taskclusterlogin_get (User.Logged)),
    Sub.map HawkMsg (Hawk.hawk_send_request (Hawk.SendRequest))
  ]
