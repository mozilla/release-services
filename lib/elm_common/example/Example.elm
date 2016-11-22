port module Example exposing (..)

import Html exposing (..)
import Html.App
import RouteUrl exposing ( UrlChange )
import RouteUrl.Builder as Builder exposing ( Builder, builder, replacePath )
import Navigation exposing ( Location )

import BugzillaLogin as Bugzilla
import TaskclusterLogin as User

type Msg = BugzillaMsg Bugzilla.Msg
  | UserMsg User.Msg

type alias Model = {
  user : User.Model,
  bugzilla : Bugzilla.Model
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
        user = user
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

-- Empty view
view model =
    div [] [ 
      h1 [] [text "Taskcluster"],
      Html.App.map UserMsg (User.view model.user),
      h1 [] [text "Bugzilla"],
      Html.App.map BugzillaMsg (Bugzilla.view model.bugzilla)
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
    Sub.map UserMsg (User.taskclusterlogin_get (User.Logged))
  ]
