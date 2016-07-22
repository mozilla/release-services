port module App exposing (..)

import Dict exposing ( Dict )
import Html exposing ( Html, div, nav, button, text, a, ul, li, footer, hr )
import Html.App
import Html.Attributes exposing ( attribute, id, class, type', href, target )
import Html.Events as Events
import Json.Decode as JsonDecode exposing ( (:=) )
import Navigation exposing ( Location )
import RouteUrl exposing ( UrlChange )
import RouteUrl.Builder as Builder exposing ( Builder, builder, replacePath )
import Result exposing ( Result(Ok, Err))

import App.Home as Home 
import App.ReleaseDashboard as ReleaseDashboard



-- TODO:
--   - add NotFound page and redirect to it when route not found
--


type Page
    = Home
    | ReleaseDashboard

type alias UserCertificate =
    { version : Int
    , scopes : List String
    , start : Int
    , expiry : Int
    , seed : String
    , signature : String
    , issuer : String
    }

type alias User =
    { client_id : Maybe String
    , access_token : Maybe String
    , certificate : Maybe UserCertificate
    }

type alias Model =
    { releaseDashboard : ReleaseDashboard.Model
    , current_page : Page
    , current_user : Maybe User
    }

type alias RedirectUrl =
    { url : String
    , target : Maybe (String, String)
    }

type Msg
    = ShowPage Page
    | SaveCredentials User
    | LoadCredentials (Maybe User)
    | ClearCredentials
    | Redirect RedirectUrl
    | ReleaseDashboardMsg ReleaseDashboard.Msg



onClick msg =
    Events.onWithOptions
        "click"
        (Events.Options False True)
        (JsonDecode.succeed msg)

eventLink msg attributes =
    a ([ onClick <| msg, href "#"  ] ++ attributes)

pageLink page attributes =
    eventLink (ShowPage page) attributes


delta2url' : Model -> Model -> Maybe Builder
delta2url' previous current =
    case current.current_page of
        ReleaseDashboard ->
            Maybe.map
                (Builder.prependToPath ["release-dashboard"])
                (Just builder)
        _ ->
            Maybe.map
                (Builder.prependToPath [])
                (Just builder)

delta2url : Model -> Model -> Maybe UrlChange
delta2url previous current =
    let
        log' = Debug.log "DELTA2URL (PREVIOUS)" previous
        log = Debug.log "DELTA2URL(CURRENT)" current
    in
    Maybe.map Builder.toUrlChange <| delta2url' previous current


pages =
    [ { page = ReleaseDashboard
      , title = "Release Dashboard"
      }
    ]


decodeUserCertificate : String -> Result String UserCertificate
decodeUserCertificate text =
    JsonDecode.decodeString
        (JsonDecode.object7 UserCertificate
            ( "version"     := JsonDecode.int )
            ( "scopes"      := JsonDecode.list JsonDecode.string )
            ( "start"       := JsonDecode.int )
            ( "expiry"      := JsonDecode.int )
            ( "seed"        := JsonDecode.string )
            ( "signature"   := JsonDecode.string )
            ( "issuer"      := JsonDecode.string )
        ) text

convertQueryToUser : Dict String String -> User
convertQueryToUser query =
    User (Dict.get "clientId" query)
         (Dict.get "accessToken" query)
         (case Dict.get "certificate" query of
             Just certificate -> Result.toMaybe <| decodeUserCertificate certificate
             Nothing -> Nothing
         )

location2messages' : Builder -> List Msg
location2messages' builder =
    let
        log = Debug.log "LOCATION2MESSAGES (PATH)" Builder.path builder
    in
    case Builder.path builder of
        first :: rest ->
            let
                builder' = Builder.replacePath rest builder
            in
                case first of
                    "login" ->
                        [ SaveCredentials (convertQueryToUser <| Builder.query builder),
                          ShowPage Home
                        ]
                    "release-dashboard" ->
                        [ ShowPage ReleaseDashboard ] --:: List.map ReleaseDashboardMsg ( ReleaseDashboard.location2messages builder' )
                    _ ->
                        [ ShowPage Home ]
        _ ->
            [ ShowPage Home ]

location2messages : Location -> List Msg
location2messages location =
    let
        log = Debug.log "LOCATION2MESSAGES (LOCATION)" location
    in
    location2messages' (Builder.fromUrl location.href)

type alias Flags = { user : Maybe User }

init : Flags -> (Model, Cmd Msg)
init flags =
    ( { releaseDashboard = fst ReleaseDashboard.init
      , current_page = Home 
      , current_user = 
          case flags.user of
              Just user -> Just (User user.client_id user.access_token user.certificate)
              Nothing -> Nothing

      }
    , Cmd.none
    )


update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    let
        log' = Debug.log "UPDATE (MSG)" msg
        log = Debug.log "UPDATE (MODEL)" model 
    in
    case msg of
        Redirect url ->
            ( model, redirect url )
        ShowPage page ->
            case page of
                ReleaseDashboard ->
                    ( { model | current_page = page
                              , releaseDashboard =  fst ReleaseDashboard.init
                      }
                    , Cmd.map ReleaseDashboardMsg <| snd ReleaseDashboard.init
                    )
                _ ->
                    ( { model | current_page = page }, Cmd.none )
        ReleaseDashboardMsg msg' ->
            let
                (newModel, newCmd) = ReleaseDashboard.update msg' model.releaseDashboard
            in
                ( { model | releaseDashboard = newModel }, Cmd.map ReleaseDashboardMsg newCmd )
        SaveCredentials user ->
            ( model, save_credentials user )
        LoadCredentials user ->
            ( { model | current_user = user }, Cmd.none )
        ClearCredentials ->
            ( { model | current_user = Nothing }, clear_credentials "")


viewPage model =
    case model.current_page of
        Home ->
            Home.view model
        ReleaseDashboard ->
            Html.App.map ReleaseDashboardMsg (ReleaseDashboard.view model.releaseDashboard)


viewDropdown title pages =
    [ div [ class "dropdown" ]
          [ a [ class "nav-link dropdown-toggle"
              , id ("dropdown" ++ title)
              , href "#"
              , attribute "data-toggle" "dropdown"
              , attribute "aria-haspopup" "true"
              , attribute "aria-expanded" "false"
              ]
              [ text title ]
          , div [ class "dropdown-menu dropdown-menu-right"
                , attribute "aria-labelledby" "dropdownServices"
                ] pages
          ]
    ]

viewUser model =
    case model.current_user of
        Just user ->
            viewDropdown (Maybe.withDefault "UNKNOWN" user.client_id )
                    [ a [ class "dropdown-item"
                        , href "https://tools.taskcluster.net/credentials"
                        , target "_blank"
                        ]
                        [ text "Manage credentials" ]
                    , eventLink ClearCredentials
                                [ class "dropdown-item" ]
                                [ text "Logout" ]
                    ]
        Nothing ->
            [ eventLink
                  ( Redirect
                      ( RedirectUrl "https://login.taskcluster.net"
                          ( Just ( "/login", "RelengAPI is a collection of Release Engineering services" )
                          )
                      )
                  )
                  [ class "nav-link" ]
                  [ text "Login" ]
            ]


viewNavBar model =
    [ button [ class "navbar-toggler hidden-md-up"
             , type' "button"
             , attribute "data-toggle" "collapse"
             , attribute "data-target" ".navbar-collapse"
             , attribute "aria-controls" "navbar-header"
             ]
             [ text "&#9776;" ]
    , pageLink Home [ class "navbar-brand" ]
                    [ text "RelengAPI" ]
    , div [ class "collapse navbar-toggleable-sm navbar-collapse pull-right" ]
          [ ul [ class "nav navbar-nav" ]
               [ li [ class "nav-item" ]
                    ( viewDropdown "Pages" ( List.map (\x -> pageLink x.page [ class "dropdown-item" ]
                                                                                [ text x.title ]) pages ))
               , li [ class "nav-item" ] ( viewUser model )
               ]
          ]
    ]

viewFooter =
    [ hr [] []
    , ul [] 
         [ li [] [ a [ href "#" ] [ text "Github" ]]
         , li [] [ a [ href "#" ] [ text "Contribute" ]]
         , li [] [ a [ href "#" ] [ text "Contact" ]]
         -- TODO: add version / revision
         ]

    ]

view : Model -> Html Msg
view model =
    let
        log = Debug.log "VIEW (MODEL)" model 
        log' = Debug.log "LOCATION" (builder)
    in
    div []
        [ nav [ id "navbar", class "navbar navbar-full navbar-light" ]
              [ div [ class "container" ] ( viewNavBar model ) ]
        , div [ id "content" ]
              [ div [ class "container" ] [ viewPage model ] ]
        , footer [ class "container" ] viewFooter
        ]


-- XXX: needs to be above subscriptions
port load_credentials : (Maybe User -> msg) -> Sub msg

subscriptions : Model -> Sub Msg
subscriptions model =
    load_credentials LoadCredentials


port redirect : RedirectUrl -> Cmd msg
port save_credentials : User -> Cmd msg
port clear_credentials : String -> Cmd msg

