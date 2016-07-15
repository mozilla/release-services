module App exposing (..)

import Dict exposing ( Dict )
import Exts.RemoteData exposing ( RemoteData(..), WebData )
import Html exposing ( Html, Attribute, div, nav, button, text, a, ul, li, hr
                     , footer, h1, h2, h3, p )
import Html.Attributes exposing ( attribute, id, class, type', href )
import Html.Events as Events
import Json.Decode as JsonDecode
import Navigation exposing ( Location, modifyUrl )
import RouteUrl exposing ( HistoryEntry(..), UrlChange )
import RouteUrl.Builder as Builder exposing ( Builder )
import List.Split exposing ( chunksOfLeft )


-- Root


viewRoot : RouteView
viewRoot model =
    div [] <| List.map viewRootServiceRow
           <| chunksOfLeft 3
           <| Dict.values routes 

viewRootServiceRow row =
    div [ class "row" ] <| List.map viewRootService row

viewRootService route =
    div [ class "col-sm-4" ]
        [ createLink (Maybe route.id) [ class "linked-card" ]
                                      [ div [ class "card card-block" ]
                                            [ h3 [ class "card-title" ] [ text route.title ]
                                            , p [ class "card-text" ] [ text route.description ]
                                            ]
                                      ]
        ]


-- Clobberer

clobberer = createRoute "clobberer" (Just "Clobberer")
                                    (Just "A repairer of buildbot builders and taskcluster worker types.")
                                     Nothing
                                     (Just viewClobberer)
                                     Nothing

viewClobberer: RouteView
viewClobberer model =
    let
        -- XXX: for some reason i can not access clobberer
        --        TypeError: _p4._0.view is not a function   
        clobberer = createRoute "clobberer" (Just "Clobberer")
                                            (Just "A repairer of buildbot builders and taskcluster worker types.")
                                             Nothing
                                             (Just viewClobberer)
                                             Nothing
    in
        div [] [ h1 [] [ text clobberer.title ]
               , p [] [ text clobberer.description ]
               , div [ class "row" ]
                     [ div [ class "col-md-6" ]
                           [ h2 [] [ text "TaskCluster" ]
                           , viewClobbererTaskcluster model
                           ]
                     , div [ class "col-md-6" ]
                           [ h2 [] [ text "Buildbot" ]
                           , viewClobbererBuildbot model
                           ]
                     ]
               ]


viewClobbererTaskcluster model =
    div [] [ text "TODO" ]

viewClobbererBuildbot model' =
    div [] [ text "TODO" ]




-- ROUTING


routes : Dict String Route
routes =
    Dict.fromList 
     [ ( clobberer.id, clobberer )
     --, createRoute2 "slaveloan" "SlaveLoan"
     --, createRoute2 "tokens" "Tokens"
     --, createRoute2 "tooltool" "ToolTool"
     --, createRoute2 "treestatus" "TreeStatus"
     ]

getRoute : String -> Maybe Route
getRoute route_id = Dict.get route_id routes






-- UTILS

onClick msg = Events.onWithOptions "click" (Events.Options False True) (JsonDecode.succeed msg)

createLink page attributes = a ([ onClick <| SetCurrentPage page, href "#"  ] ++ attributes)


-- MODEL

type alias RouteModel = ( Model, Cmd Msg )
type alias RouteView = Model -> Html Msg
type alias RouteUpdate = Msg -> Model -> ( Model, Cmd Msg )

type alias RouteID = String

type alias Route =
    { id: RouteID
    , title : String
    , description : String
    , model: RouteModel
    , view: RouteView
    , update: RouteUpdate
    }


type Page
    = Root
    | NotFound
    | Maybe RouteID



type alias Model =
    { current_page: Page
    }


defaultModel : RouteModel
defaultModel = ( { current_page = Root }, Cmd.none )

defaultView : RouteView
defaultView model = text ""

defaultUpdate : RouteUpdate
defaultUpdate msg model =
    let
      log = Debug.log "MODEL (BEFORE) " model
      log' = Debug.log "MESSAGE " msg
    in
    case msg of
        RedirectToUrl url ->
            ( model , modifyUrl url )
        SetCurrentPage page ->
            ( { model | current_page = page },  Cmd.none )


createRoute : RouteID ->
              Maybe String ->
              Maybe String ->
              Maybe RouteModel ->
              Maybe RouteView ->
              Maybe RouteUpdate ->
              Route
createRoute id title description model view update =
    let
        title' = Maybe.withDefault id title
        description' = Maybe.withDefault "" description
        model' = Maybe.withDefault defaultModel model
        view' = Maybe.withDefault defaultView view
        update' = Maybe.withDefault defaultUpdate update
    in
        Route id title' description' model' view' update'


-- VIEW


view : Model -> Html Msg
view model =
    div []
        [ nav [ id "navbar"
              , class "navbar navbar-full navbar-light"
              ]
              [ div [ class "container" ]
                    [ button [ class "navbar-toggler hidden-md-up"
                             , type' "button"
                             , attribute "data-toggle" "collapse"
                             , attribute "data-target" ".navbar-collapse"
                             , attribute "aria-controls" "navbar-header"
                             ]
                             [ text "&#9776;" ]
                    , createLink Root [ class "navbar-brand" ]
                                      [ text "RelengAPI" ]
                    , div [ class "collapse navbar-toggleable-sm navbar-collapse pull-right" ]
                          [ ul [ class "nav navbar-nav" ]
                               [ li [ class "nav-item" ]
                                    [ div [ class "dropdown" ]
                                          [ a [ class "nav-link dropdown-toggle"
                                              , id "dropdownServices"
                                              , href "#"
                                              , attribute "data-toggle" "dropdown"
                                              , attribute "aria-haspopup" "true"
                                              , attribute "aria-expanded" "false"
                                              ]
                                              [ text "Services" ]
                                          , div [ class "dropdown-menu dropdown-menu-right"
                                                , attribute "aria-labelledby" "dropdownServices"
                                                ]
                                                (
                                                    List.map (\route -> createLink (Maybe route.id) [ class "dropdown-item" ]
                                                                                                    [ text route.title ])
                                                             (Dict.values routes)
                                                )
                                          ]
                                    ]
                               , li [ class "nav-item" ] [] --(viewLoginLogout model.current_user)
                               ]
                          ]
                    ]
              ]
        , div [ id "content" ]
              [ div [ class "container" ]
                     [
                        case model.current_page of
                           Root ->
                               div [] [ viewRoot model ]
                           NotFound ->
                               div [] [ text "NotFound" ]
                           Maybe route_id ->
                               div [] ( case getRoute route_id of
                                            Just route ->
                                                [route.view model]
                                            Nothing -> 
                                                []
                                      )
                     ]
              ]
        , footer [ class "container" ]
                 [ hr [] []
                 , ul [] 
                      [ li [] [ a [ href "#" ] [ text "Github" ]]
                      , li [] [ a [ href "#" ] [ text "Contribute" ]]
                      , li [] [ a [ href "#" ] [ text "Contact" ]]
                      -- TODO: add version / revision
                      ]

                 ]
        ]

viewLoginLogout current_user = --TODO need to include this
    case current_user of
        Success _ ->
            [
                a [ class "nav-link"
                  , href "/logout" --TODO: pick from routes
                  ]
                  [ text "Logout" ]
            ]
        _ ->
            [
                a [ class "nav-link"
                  , href "/login" --TODO: pick from routes
                  ]
                  [ text "Login" ]
            ]


-- UPDATE


type Msg
    = SetCurrentPage Page
    | RedirectToUrl String





-- ROUTER


delta2url : Model -> Model -> Maybe UrlChange
delta2url previous current =
    case current.current_page of
        Root ->
            Just <| UrlChange NewEntry "/"
        NotFound ->
            Just <| UrlChange NewEntry "/404"
        Maybe route_id ->
            Just <| UrlChange NewEntry ("/" ++ route_id)



location2messages : Location -> List Msg
location2messages location =
     case Builder.path <| Builder.fromUrl location.href of
         [] ->
             [ SetCurrentPage Root ]
         ["404"] ->
             [ SetCurrentPage NotFound ]
         first :: rest ->
             case getRoute first of
                 Just route -> 
                     [ SetCurrentPage (Maybe route.id ) ]
                 Nothing ->
                     [ RedirectToUrl "/404" ] 
