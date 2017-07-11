port module AppCommon.Bugzilla exposing (..)

import Http
import HttpBuilder
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onInput, onSubmit)
import RemoteData exposing (WebData, RemoteData(..))
import Json.Decode as JsonDecode


type Msg
    = SaveCredentials
    | Logged (Maybe Credentials)
    | CheckedCredentials Bool (WebData Bool)
    | UpdateLogin String
    | UpdateToken String


type alias Credentials =
    { login : String
    , token : String
    }


type alias Model =
    { url : String
    , -- Bugzilla server
      check : WebData Bool
    , credentials : Maybe Credentials
    }


init : String -> Maybe Credentials -> ( Model, Cmd Msg )
init url credentials =
    ( { url = url
      , check = NotAsked
      , credentials = credentials
      }
    , -- Initial credentials loading
      bugzillalogin_load True
    )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Logged credentials ->
            let
                model_ =
                    { model | credentials = credentials }
            in
                -- Check credentials when received from storage
                ( model_, checkCredentials model_ False )

        UpdateLogin login ->
            let
                newCreds =
                    case model.credentials of
                        Just creds ->
                            { creds | login = login }

                        Nothing ->
                            { login = login, token = "" }
            in
                ( { model | credentials = Just newCreds }, Cmd.none )

        UpdateToken token ->
            let
                newCreds =
                    case model.credentials of
                        Just creds ->
                            { creds | token = token }

                        Nothing ->
                            { login = "", token = token }
            in
                ( { model | credentials = Just newCreds }, Cmd.none )

        SaveCredentials ->
            -- Check credentials before saving them
            ( model, checkCredentials model True )

        CheckedCredentials save check ->
            ( { model | check = check }
            , -- Save credentials stored in model when valid
              case check of
                Success check_ ->
                    if check_ && save then
                        case model.credentials of
                            Just creds ->
                                bugzillalogin_set creds

                            Nothing ->
                                Cmd.none
                    else
                        Cmd.none

                _ ->
                    Cmd.none
            )


checkCredentials : Model -> Bool -> Cmd Msg
checkCredentials model save =
    -- Check bugzilla auth is still valid
    case model.credentials of
        Just credentials ->
            HttpBuilder.get (model.url ++ "/rest/valid_login")
                |> HttpBuilder.withQueryParams [ ("login", credentials.login) ]
                |> withCredentials credentials
                |> HttpBuilder.withHeaders [ ( "Accept", "application/json" )
                                           , ( "Content-Type", "application/json" )
                                           ]
                |> HttpBuilder.withExpect (Http.expectJson JsonDecode.bool)
                |> HttpBuilder.toRequest
                |> RemoteData.sendRequest
                |> Cmd.map (CheckedCredentials save)

        Nothing ->
            Cmd.none


withCredentials : Credentials
            -> HttpBuilder.RequestBuilder a
            -> HttpBuilder.RequestBuilder a
withCredentials credentials builder =
    { builder | headers = (Http.header "X-Bugzilla-Api-Key" credentials.token) :: builder.headers }


view : Model -> Html Msg
view user =
    div [ id "bugzilla", class "container" ]
        [ h1 [] [ text "Manage your Bugzilla credentials" ]
        , viewEditor user
        , hr [] []
        , div [ class "alert alert-info" ]
            [ strong [] [ text "Heads up !" ]
            , p [] [ text "Your Bugzilla credentials are stored only in your browser, using localStorage. They are NOT sent to any backend for storage." ]
            ]
        ]


viewEditor : Model -> Html Msg
viewEditor user =
    Html.form [ onSubmit SaveCredentials ]
        [ div [ class "form-group row" ]
            [ label [ class "col-sm-3 col-form-label" ] [ text "Bugzilla Email" ]
            , div [ class "col-sm-9" ]
                [ input [ type_ "text", class "form-control", onInput UpdateLogin ] []
                ]
            ]
        , div [ class "form-group row" ]
            [ label [ class "col-sm-3 col-form-label" ] [ text "Bugzilla Token" ]
            , div [ class "col-sm-9" ]
                [ input [ type_ "password", class "form-control", onInput UpdateToken ] []
                ]
            ]
        , div [ class "form-group row" ]
            [ label [ class "col-sm-3 col-form-label" ] [ text "Status" ]
            , div [ class "col-sm-9" ]
                [ viewStatus user
                ]
            ]
        , button [ class "btn btn-success" ] [ text "Save credentials" ]
        ]


viewStatus : Model -> Html Msg
viewStatus model =
    case model.check of
        NotAsked ->
            span [ class "badge badge-warning" ] [ text "No credentials set" ]

        Loading ->
            span [ class "badge badge-info" ] [ text "Checking credentials" ]

        Failure err ->
            span [ class "badge badge-danger" ] [ text (toString err) ]

        Success check ->
            if check then
                span [ class "badge badge-success" ] [ text "Valid credentials" ]
            else
                span [ class "badge badge-danger" ] [ text "Invalid credentials" ]



-- Ports


port bugzillalogin_get : (Maybe Credentials -> msg) -> Sub msg


port bugzillalogin_load : Bool -> Cmd msg


port bugzillalogin_remove : Bool -> Cmd msg


port bugzillalogin_set : Credentials -> Cmd msg



-- Add this subscription in main App
-- subscriptions = [
--     Sub.map BugzillaMsg (Bugzilla.bugzillalogin_get (Bugzilla.Logged))
--   ]
