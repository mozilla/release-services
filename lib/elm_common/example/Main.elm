module Main exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import App
import Redirect
import TaskclusterLogin
import Hawk

type alias Extension init msg subscriptions update = 
  {
    msg : msg,
    init : init,
    update : update,
    subscriptions : subscriptions
  }



main = App.program 
  {
    init = init,
    update = update,
    subscriptions = subscriptions,
    view = view,
    extensions = [
      -- Extension HawkMsg Hawk.init Hawk.update Hawk.subscriptions
      (HawkMsg, Hawk.init, Hawk.update, Hawk.subscriptions),
      (TCLoginMsg, TaskclusterLogin.init, TaskclusterLogin.update, TaskclusterLogin.subscriptions)
    ]
  }

type alias Counter = Int

type alias Model =
    { counter : Counter
    }

init : (Model, Cmd Msg)
init =
    ({ counter = 0, }, Cmd.none)

type Msg
    = IncCounter
    | DecCounter
    | SetCounter Counter
    | Goto String
    | HawkRequest String
    | HawkMsg Hawk.Msg -- specific implem
    | TCLoginMsg TaskclusterLogin.Msg -- specific implem


-- UPDATE

update : Msg -> Model -> (Model, Cmd Msg)
update msg model = 
    case Debug.log "Message" msg of
        IncCounter ->
            ( { model | counter = model.counter + 1 }
            , Cmd.none
            )
        DecCounter ->
            ( { model | counter = model.counter - 1 }
            , Cmd.none
            )
        SetCounter newCounter->
            ( { model | counter = newCounter }
            , Cmd.none
            )
        Goto url ->
            let
              redirection = Redirect.Model url Nothing "demo"
              l = Debug.log "redirect" redirection
            in
            (
              model,
              Redirect.redirect redirection             
            )
        HawkRequest url ->
            let
              user = TaskclusterLogin.Model "testclient" "mytoken1221" Nothing
              l = Debug.log "user" user
              request = Http.Request "GET" [] url Http.empty
            in
            (
              model,
              -- Hawk.AddHeader request
              Cmd.none
            )

        HawkMsg msg ->
          let
            l = Debug.log "Got an HAWK message !" msg
          in
            (model, Cmd.none)

        TCLoginMsg msg ->
          let
            l = Debug.log "Got a TC login message !" msg
          in
            (model, Cmd.none)

-- VIEW

view : Model -> Html Msg
view model =
    ul
        [ ]
        [ div [] [ text (toString model.counter) ]
        , button [ onClick IncCounter ]
                 [ text "Up" ]
        , button [ onClick DecCounter ]
                 [ text "Down" ]
        , button [ SetCounter 10 |> onClick ]
                 [ text "Set to 10" ]
        , button [ Goto "https://mozilla.org" |> onClick ]
                 [ text "Go on mozilla.org" ]
        , button [ HawkRequest "http://bugzilla-dev.allizom.org" |> onClick ]
                 [ text "HAWK Request" ]
        ]

subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.none
