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
import App.TreeStatus as TreeStatus
import App.Utils exposing ( eventLink )


-- ROUTING


type Route
    = HomeRoute
    | TreeStatusRoute


pageLink route = eventLink (NavigateTo route)


delta2url' : Model -> Model -> Maybe Builder
delta2url' previous current =
    case current.route of
        TreeStatusRoute ->
            Maybe.map
                (Builder.prependToPath ["treestatus"])
                (Just builder)
        HomeRoute ->
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
    Maybe.map Builder.toUrlChange <| delta2url' previous current




location2messages' : Builder -> List Msg
location2messages' builder =
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
                        , NavigateTo HomeRoute
                        ]
                    "treestatus" ->
                        [ NavigateTo TreeStatusRoute ]
                    -- TODO: This should redirect to NotFound
                    _ ->
                        [ NavigateTo HomeRoute ]
        _ ->
            [ NavigateTo HomeRoute ]

location2messages : Location -> List Msg
location2messages location =
    location2messages'
        <| Builder.fromUrl location.href



-- MODEL / INIT


type alias Model =
    { route : Route
    , user : Maybe User.Model
    , treestatus : TreeStatus.Model
    }

type alias Flags =
    { user : Maybe User.Model
    , treestatusUrl: String
    }


init : Flags -> (Model, Cmd Msg)
init flags =
    ( { treestatus = TreeStatus.init flags.treestatusUrl
      , route = HomeRoute
      , user = flags.user
      }
    , Cmd.none
    )


-- UPDATE


type Msg
    = NavigateTo Route
    | UserMsg User.Msg
    | TreeStatusMsg TreeStatus.Msg


update : Msg -> Model -> (Model, Cmd Msg)
update msg' model =
    case msg' of
        NavigateTo route ->
            case route of
                HomeRoute ->
                    ( { model | route = route
                              , treestatus = TreeStatus.init model.treestatus.baseUrl
                              }
                    , Cmd.none
                    )

                TreeStatusRoute ->
                    let
                        treestatus = TreeStatus.load model.treestatus
                    in
                        ( { model | route = route 
                                  , treestatus = fst treestatus
                          }
                        , Cmd.map TreeStatusMsg <| snd treestatus
                        )
        TreeStatusMsg msg ->
            let
                (newModel, newCmd) = TreeStatus.update msg model.treestatus
            in
                ( { model | treestatus = newModel }
                , Cmd.map TreeStatusMsg newCmd
                )
        UserMsg msg -> 
            let
                (newModel, newCmd) = User.update msg model.user
            in
                ( { model | user = newModel }
                , Cmd.map UserMsg newCmd
                )


-- VIEW
-- XXX: maybe we want to have this in separate file (eg. App/Layout.elm)


services =
    [ { page = TreeStatusRoute
      , title = "Tree Status"
      }
    ]


viewPage model =
    case model.route of
        HomeRoute ->
            Home.view model
        TreeStatusRoute ->
            Html.App.map TreeStatusMsg (TreeStatus.view model.treestatus)


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
    case model.user of
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
                    , targetName = "target"
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
    , pageLink HomeRoute [ class "navbar-brand" ]
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
        [ Sub.map UserMsg (User.user_get (User.LoggedIn))
        ]
