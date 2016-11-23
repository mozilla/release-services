port module BugzillaLogin exposing (..)

import Http
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onInput, onSubmit)
import RemoteData exposing (WebData, RemoteData(..))
import Json.Decode as JsonDecode
import Task exposing (Task)


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
                Success check' ->
                    if check' && save then
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
        Just creds_ ->
            let
                task =
                    buildRequest creds_
                        model.url
                        "GET"
                        (Http.url "/valid_login"
                            [ ( "login", creds_.login )
                            ]
                        )
                        Nothing

                -- no body
            in
                (Http.fromJson JsonDecode.bool task)
                    |> RemoteData.asCmd
                    |> Cmd.map (CheckedCredentials save)

        Nothing ->
            Cmd.none


buildRequest : Credentials -> String -> String -> String -> Maybe String -> Task Http.RawError Http.Response
buildRequest creds url verb method body =
    let
        body' =
            case body of
                Just b ->
                    Http.string b

                Nothing ->
                    Http.empty

        headers =
            [ -- Use bugzilla token
              ( "x-bugzilla-api-key", creds.token )
            , ( "Accept", "application/json" )
            , ( "Content-Type", "application/json" )
            ]
    in
        -- Always send to Mozilla Bugzilla
        Http.send Http.defaultSettings
            { url = url ++ "/rest" ++ method
            , verb = verb
            , headers = headers
            , body = body'
            }


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
                [ input [ type' "text", class "form-control", onInput UpdateLogin ] []
                ]
            ]
        , div [ class "form-group row" ]
            [ label [ class "col-sm-3 col-form-label" ] [ text "Bugzilla Token" ]
            , div [ class "col-sm-9" ]
                [ input [ type' "password", class "form-control", onInput UpdateToken ] []
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
            span [ class "tag tag-warning" ] [ text "No credentials set" ]

        Loading ->
            span [ class "tag tag-info" ] [ text "Checking credentials" ]

        Failure err ->
            span [ class "tag tag-danger" ] [ text (toString err) ]

        Success check ->
            if check then
                span [ class "tag tag-success" ] [ text "Valid credentials" ]
            else
                span [ class "tag tag-danger" ] [ text "Invalid credentials" ]



-- Ports


port bugzillalogin_get : (Maybe Credentials -> msg) -> Sub msg


port bugzillalogin_load : Bool -> Cmd msg


port bugzillalogin_remove : Bool -> Cmd msg


port bugzillalogin_set : Credentials -> Cmd msg



-- Add this subscription in main App
-- subscriptions = [
--     Sub.map BugzillaMsg (Bugzilla.bugzillalogin_get (Bugzilla.Logged))
--   ]
