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
  | HawkRequest Hawk.Msg
  | HawkResponse (RemoteData Http.RawError Http.Response)
  | LoadScopes
  | LoadRoles

type alias Role = {
  roleId : String,
  scopes : List String
}

type alias Model = {
  user : User.Model,
  bugzilla : Bugzilla.Model,
  scopes : List String,
  roles : List Role
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
      scopes = [],
      roles = []
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
              Cmd.map HawkRequest (Hawk.add_header request credentials)
            )
        Nothing ->
            (model, Cmd.none)

    LoadRoles ->
      case model.user.credentials of
        Just credentials ->
          let
            -- Build Taskcluster http request
            url = "https://auth.taskcluster.net/v1/roles"
            request = Http.Request "GET" [] url Http.empty
          in
            (
              model,
              Cmd.map HawkRequest (Hawk.add_header request credentials)
            )
        Nothing ->
            (model, Cmd.none)

    HawkRequest hawkMsg ->
      let
        (cmd, response) = Hawk.update hawkMsg
      in
        (
          model,
          Cmd.batch [
            Cmd.map HawkRequest cmd,
            Cmd.map HawkResponse response
          ]
        )

    HawkResponse response ->
      case response of
        Success response_ ->
          -- Apply successive decoders on response
          (
            Hawk.applyDecoders model [
              decodeScopes,
              decodeRoles
            ] response_,
            Cmd.none
          )

        _ ->
          ( model, Cmd.none)


decodeScopes: Model -> String -> Model
decodeScopes model response =
  let 
    decoder = JsonDecode.at ["scopes"] (JsonDecode.list JsonDecode.string)
  in
    case JsonDecode.decodeString decoder response of
      Ok scopes ->
        {model | scopes = scopes }
      Err _ ->
        model

decodeRoles: Model -> String -> Model
decodeRoles model response =
  let 
    decoder = JsonDecode.list 
      (JsonDecode.object2 Role
        ("roleId" := JsonDecode.string)
        ("scopes" := JsonDecode.list JsonDecode.string)
      )
  in
    case JsonDecode.decodeString decoder response of
      Ok roles ->
        {model | roles = roles }
      Err _ ->
        model
    

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
        p [] [
          button [onClick LoadScopes] [text "Request Taskcluster scopes"],
          button [onClick LoadRoles] [text "Request Taskcluster roles"]
        ]
      Nothing ->
        span [class "text-warning"] [text "Login on Taskcluster first."]
    , div [] [
      viewScopes model.scopes,
      div [] (List.map viewRole model.roles)
    ]
  ]

viewScopes scopes =
  ul [] (List.map (\s -> li [] [text s]) scopes)

viewRole role =
  div [] [
    h5 [] [text ("Role: "++role.roleId)],
    viewScopes role.scopes
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
    Sub.map HawkRequest (Hawk.hawk_send_request (Hawk.SendRequest))
  ]
