port module TaskclusterLogin exposing (..)

import Redirect
import Maybe

type alias Certificate =
    { version : Int
    , scopes : List String
    , start : Int
    , expiry : Int
    , seed : String
    , signature : String
    , issuer : String
    }

type alias Model = {
  clientId : String,
  accessToken : String,
  certificate : Maybe Certificate
}

type Msg
  = Login Redirect.Model
  | Logging Model
  | Logged (Maybe Model)
  | Logout

init = {}

subscriptions = 
  [
    (taskclusterlogin_get (Logged))
  ]

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of
    Login url ->
      ( model, Redirect.redirect url )

    Logging user ->
      ( model, taskclusterlogin_set user )

    Logged newModel ->
      (
        Maybe.withDefault model newModel,
        Cmd.none
      )

    Logout ->
      ( model, taskclusterlogin_remove True )

-- decodeCertificate : String -> Result String Certificate

-- Ports

port taskclusterlogin_get : (Maybe Model -> msg) -> Sub msg
port taskclusterlogin_load : Bool -> Cmd msg
port taskclusterlogin_remove : Bool -> Cmd msg
port taskclusterlogin_set : Model -> Cmd msg
