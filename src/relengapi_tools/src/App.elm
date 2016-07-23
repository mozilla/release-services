module App exposing (..)


import Dict exposing ( Dict )
import Html exposing (..)
import Html.App
import Html.Attributes exposing (..)
import Json.Decode as JsonDecode exposing ( (:=) )
import Navigation exposing ( Location )
import RouteUrl exposing ( UrlChange )
import RouteUrl.Builder as Builder exposing ( Builder, builder, replacePath )
import Result exposing ( Result(Ok, Err))

import App.User as User
import App.Home as Home
import App.Clobberer as Clobberer
import App.Utils exposing ( eventLink )




-- ROUTING


type Page
    = Home
    | Clobberer


pageLink page = eventLink (ShowPage page)


delta2url' : Model -> Model -> Maybe Builder
delta2url' previous current =
    case current.currentPage of
        Clobberer ->
            Maybe.map
                (Builder.prependToPath ["clobberer"])
                (Just builder)
        Home ->
            Maybe.map
                (Builder.prependToPath [])
                (Just builder)
        -- TODO: we currently redirect to Home but we should redirect to
        --       notfound page
        --NotFound ->
        --    Maybe.map
        --        (Builder.prependToPath ["404"])
        --        (Just builder)

delta2url : Model -> Model -> Maybe UrlChange
delta2url previous current =
    Maybe.map Builder.toUrlChange <| delta2url'
        (Debug.log "DELTA2URL (PREVIOUS)" previous)
        (Debug.log "DELTA2URL  (CURRENT)" current)




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
                        [ 
                          Builder.query builder
                              |> User.convertUrlQueryToModel
                              |> User.LoggingIn
                              |> UserMsg
                        , ShowPage Home
                        ]
                    "clobberer" ->
                        [ ShowPage Clobberer ]
                    -- TODO: This should redirect to NotFound
                    _ ->
                        [ ShowPage Home ]
        _ ->
            [ ShowPage Home ]

location2messages : Location -> List Msg
location2messages location =
    location2messages'
        <| Builder.fromUrl (Debug.log "LOCATION2MESSAGES (LOCATION)" location).href



-- MODEL / INIT


type alias Model =
    { currentPage : Page
    , currentUser : Maybe User.Model
    , clobberer : Clobberer.Model
    , clobbererUrl : String
    }

type alias Flags =
    { user : Maybe User.Model
    , clobbererUrl : String
    }


init : Flags -> (Model, Cmd Msg)
init flags =
    ( { clobberer = Clobberer.init
      , clobbererUrl = flags.clobbererUrl
      , currentPage = Home
      , currentUser = flags.user
      }
    , Cmd.none
    )


-- UPDATE


type Msg
    = ShowPage Page
    | UserMsg User.Msg
    | ClobbererMsg Clobberer.Msg


updatePage model page =
    case page of
        Clobberer ->
            let
                clobberer = Clobberer.initPage
                    model.clobbererUrl model.clobberer
            in
                ( { model | currentPage = page
                          , clobberer = fst clobberer
                  }
                , Cmd.map ClobbererMsg <| snd clobberer
                )
        _ ->
            ( { model | currentPage = page }, Cmd.none )


update : Msg -> Model -> (Model, Cmd Msg)
update msg' model =
    let
        log1 = Debug.log "UPDATE   (MSG)" msg'
        log2 = Debug.log "UPDATE (MODEL)" model
    in
        case msg' of
            ShowPage page -> updatePage model page
            ClobbererMsg msg ->
                let
                    (newModel, newCmd) = Clobberer.update msg model.clobberer
                in
                    ( { model | clobberer = newModel }
                    , Cmd.map ClobbererMsg newCmd
                    )
            UserMsg msg -> 
                let
                    (newModel, newCmd) = User.update msg model.currentUser
                in
                    ( { model | currentUser = newModel }
                    , Cmd.map UserMsg newCmd
                    )


-- VIEW
-- XXX: maybe we want to have this in separate file (eg. App/Layout.elm)


services =
    [ { page = Clobberer
      , title = "Clobberer"
      }
    ]


viewPage model =
    case model.currentPage of
        Home ->
            Home.view model
        Clobberer ->
            Html.App.map ClobbererMsg (Clobberer.view model.clobberer)


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
    case model.currentUser of
        Just user ->
            viewDropdown (Maybe.withDefault "UNKNOWN" user.clientId )
                    [ a [ class "dropdown-item"
                        , href "https://tools.taskcluster.net/credentials"
                        , target "_blank"
                        ]
                        [ text "Manage credentials" ]
                    , eventLink (UserMsg User.Logout)
                                [ class "dropdown-item" ]
                                [ text "Logout" ]
                    ]
        Nothing ->
            let
                loginTarget =
                    Just ( "/login"
                         , "RelengAPI is a collection of Release Engineering services"
                         )
                loginUrl =
                    { url = "https://login.taskcluster.net"
                    , target = loginTarget
                    }
                loginMsg = UserMsg <| User.Login loginUrl
            in
                [ eventLink loginMsg [ class "nav-link" ] [ text "Login" ]
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
                    ( viewDropdown "Services" ( List.map (\x -> pageLink x.page [ class "dropdown-item" ]
                                                                                [ text x.title ]) services ))
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



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
    [ Sub.map UserMsg (User.localstorage_get (User.LoggedIn))
    ]
