port module AppTest exposing (..)

import Html exposing (..)
import Html.App
import RouteUrl exposing ( UrlChange )
import Navigation exposing ( Location )

import BugzillaLogin as Bugzilla

type Msg = BugzillaMsg Bugzilla.Msg

type alias Model = {
  bugzilla : Bugzilla.Model
}

type alias Flags = {
  backend_dashboard_url: String,
  bugzilla_url: String
}

init : Flags -> (Model, Cmd Msg)
init flags =
    let
        (bz, bzCmd) = Bugzilla.init flags.bugzilla_url
    in
    (
      {
         bugzilla = bz
      },
      -- Follow through with sub parts init
      Cmd.batch [
        Cmd.map BugzillaMsg bzCmd
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

-- Empty view
view model =
    div [] [ 
      Html.App.map BugzillaMsg (Bugzilla.view model.bugzilla)
    ]

-- Empty Routing
location2messages : Location -> List Msg
location2messages location =
  []

delta2url : Model -> Model -> Maybe UrlChange
delta2url previous current =
  Nothing

-- Subscriptions
subscriptions : Model -> Sub Msg
subscriptions model =
  Sub.batch [
    Sub.map BugzillaMsg (Bugzilla.bugzillalogin_get (Bugzilla.Logged))

  ]
