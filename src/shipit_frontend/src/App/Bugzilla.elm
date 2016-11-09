module App.Bugzilla exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onInput, onSubmit)
import RemoteData as RemoteData exposing ( RemoteData(Loading, Success, NotAsked, Failure) )

import App.User as User

type Msg
  = SaveCredentials
  | UpdateLogin String
  | UpdateToken String
  
update : Msg -> User.Model -> (User.Model, Cmd User.Msg)
update msg user =
  case msg of
    UpdateLogin login ->
      let
        newCreds = case user.bugzilla of
          Just creds -> { creds | login = login }
          Nothing -> { login = login, token = "", url = user.bugzilla_url}
      in
        ({ user | bugzilla = Just newCreds}, Cmd.none)
      
    UpdateToken token ->
      let
        newCreds = case user.bugzilla of
          Just creds -> { creds | token = token }
          Nothing -> { login = "" , token = token, url = user.bugzilla_url}
      in
        ({ user | bugzilla = Just newCreds}, Cmd.none)
      
    SaveCredentials ->
      -- Check credentials before saving them
      (user, User.checkBugzillaAuth user.bugzilla True)


view: User.Model -> Html Msg
view user =
  div [id "bugzilla", class "container"] [
    h1 [] [text "Manage your Bugzilla credentials"],
    viewEditor user,
    hr [] [],
    div [class "alert alert-info"] [
      strong [] [text "Heads up !"],
      p [] [text "Your Bugzilla credentials are stored only in your browser, using localStorage. They are NOT sent to any backend for storage."]
    ]
  ]

viewEditor: User.Model -> Html Msg
viewEditor user =
  Html.form [onSubmit SaveCredentials] [
    div [class "form-group row"] [
      label [class "col-sm-3 col-form-label"] [text "Bugzilla Email"],
      div [class "col-sm-9"] [
        input [type' "text", class "form-control", onInput UpdateLogin] []
      ]
    ],
    div [class "form-group row"] [
      label [class "col-sm-3 col-form-label"] [text "Bugzilla Token"],
      div [class "col-sm-9"] [
        input [type' "password", class "form-control", onInput UpdateToken] []
      ]
    ],
    div [class "form-group row"] [
      label [class "col-sm-3 col-form-label"] [text "Status"],
      div [class "col-sm-9"] [
        viewStatus user
      ]
    ],
    button [class "btn btn-success"] [text "Save credentials"]
  ]

viewStatus: User.Model -> Html Msg
viewStatus user =
  case user.bugzilla_check of
    NotAsked ->
      span [class "tag tag-warning"] [text "No credentials set"]

    Loading -> 
      span [class "tag tag-info"] [text "Checking credentials"]

    Failure err ->
      span [class "tag tag-danger"] [text (toString err)]

    Success check -> 
      if check then
        span [class "tag tag-success"] [text "Valid credentials"]
      else
        span [class "tag tag-danger"] [text "Invalid credentials"]
