module App exposing (..)

import Html exposing (..)
import Html.App
import Html.Attributes exposing (..)
import Json.Decode as JsonDecode exposing ((:=))
import Navigation exposing (Location)
import RouteUrl exposing (UrlChange)
import RouteUrl.Builder as Builder exposing (Builder, builder, replacePath)
import Result exposing (Result(Ok, Err))
import App.Utils exposing (eventLink)
import App.TreeStatus
import App.Home
import Hawk
import TaskclusterLogin as User


-- ROUTING


type Route
    = HomeRoute
    | TreeStatusRoute



-- TODO: add NotFoundRoute


pageLink route =
    eventLink (NavigateTo route)


delta2url' : Model -> Maybe Builder
delta2url' model =
    case model.route of
        HomeRoute ->
            Maybe.map
                (Builder.prependToPath [])
                (Just builder)

        TreeStatusRoute ->
            Maybe.map
                (Builder.prependToPath [ "treestatus" ])
                (Just builder)


delta2url : Model -> Model -> Maybe UrlChange
delta2url previous current =
    delta2url' current
        |> Maybe.map Builder.toUrlChange


location2messages : Location -> List Msg
location2messages location =
    let
        builder =
            Builder.fromUrl location.href
    in
        case Builder.path builder of
            first :: rest ->
                -- Extensions integration
                case first of
                    "login" ->
                        [ Builder.query builder
                            |> User.convertUrlQueryToUser
                            |> User.Logging
                            |> UserMsg
                        ]

                    "treestatus" ->
                        [ NavigateTo TreeStatusRoute ]

                    _ ->
                        []

            _ ->
                []



-- MODEL / INIT


type alias Model =
    { route : Route
    , user : User.Model
    , treestatus : App.TreeStatus.Model
    }


type alias Flags =
    { user : User.Model
    , treestatusUrl : String
    }


init : Flags -> ( Model, Cmd Msg )
init flags =
    ( { user = flags.user
      , route = HomeRoute
      , treestatus = App.TreeStatus.init flags.treestatusUrl
      }
    , Cmd.none
    )



-- UPDATE


type Msg
    = UserMsg User.Msg
    | HawkRequest Hawk.Msg
    | NavigateTo Route
      --TODO: | App.HomeMsg App.Home.Msg
    | TreeStatusMsg App.TreeStatus.Msg


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        UserMsg userMsg ->
            let
                ( newUser, userCmd ) =
                    User.update userMsg model.user
            in
                ( { model | user = newUser }
                , Cmd.map UserMsg userCmd
                )

        HawkRequest hawkMsg ->
            let
                ( requestId, cmd, response ) =
                    Hawk.update hawkMsg

                routeHawkRequest route =
                    case route of
                        --TOD:
                        --"LoadScopes" ->
                        --    Cmd.map SetScopes response
                        _ ->
                            Cmd.none

                appCmd =
                    requestId
                        |> Maybe.map routeHawkRequest
                        |> Maybe.withDefault Cmd.none
            in
                ( model
                , Cmd.batch
                    [ Cmd.map HawkRequest cmd
                    , appCmd
                    ]
                )

        NavigateTo route ->
            case route of
                HomeRoute ->
                    ( { model
                        | route = route
                        , treestatus = App.TreeStatus.init model.treestatus.baseUrl
                      }
                    , Cmd.none
                    )

                TreeStatusRoute ->
                    let
                        treestatus =
                            App.TreeStatus.load model.treestatus
                    in
                        ( { model
                            | route = route
                            , treestatus = fst treestatus
                          }
                        , Cmd.map TreeStatusMsg <| snd treestatus
                        )

        TreeStatusMsg treestatusMsg ->
            let
                ( newModel, newCmd ) =
                    App.TreeStatus.update treestatusMsg model.treestatus
            in
                ( { model | treestatus = newModel }
                , Cmd.map TreeStatusMsg newCmd
                )



-- VIEW


services =
    [ { page = TreeStatusRoute
      , title = "Tree Status"
      }
    ]


viewPage model =
    case model.route of
        HomeRoute ->
            --TODO: Html.App.map App.HomeMsg (App.Home.view model)
            App.Home.view model 

        TreeStatusRoute ->
            Html.App.map TreeStatusMsg (App.TreeStatus.view model.treestatus)


viewDropdown title pages =
    [ div [ class "dropdown" ]
        [ a
            [ class "nav-link dropdown-toggle"
            , id ("dropdown" ++ title)
            , href "#"
            , attribute "data-toggle" "dropdown"
            , attribute "aria-haspopup" "true"
            , attribute "aria-expanded" "false"
            ]
            [ text title ]
        , div
            [ class "dropdown-menu dropdown-menu-right"
            , attribute "aria-labelledby" "dropdownServices"
            ]
            pages
        ]
    ]


viewUser model =
    case model.user of
        Just user ->
            viewDropdown user.clientId
                [ a
                    [ class "dropdown-item"
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
                    Just
                        ( "/login"
                        , "RelengAPI is a collection of Release Engineering services"
                        )

                loginUrl =
                    { url = "https://login.taskcluster.net"
                    , target = loginTarget
                    , targetName = "target"
                    }

                loginMsg =
                    UserMsg <| User.Login loginUrl
            in
                [ eventLink loginMsg [ class "nav-link" ] [ text "Login" ]
                ]


viewNavBar model =
    [ button
        [ class "navbar-toggler hidden-md-up"
        , type' "button"
        , attribute "data-toggle" "collapse"
        , attribute "data-target" ".navbar-collapse"
        , attribute "aria-controls" "navbar-header"
        ]
        [ text "&#9776;" ]
    , pageLink HomeRoute
        [ class "navbar-brand" ]
        [ text "RelengAPI" ]
    , div [ class "collapse navbar-toggleable-sm navbar-collapse pull-right" ]
        [ ul [ class "nav navbar-nav" ]
            [ li [ class "nav-item" ]
                 ( viewDropdown "Services" [ a [ href "/trychooser"
                                               , class "dropdown-item"
                                               ]
                                               [ text "TryChooser" ]
                                           ]
                 )
                --(viewDropdown "Services"
                --    (List.map
                --        (\x ->
                --            pageLink x.page
                --                [ class "dropdown-item" ]
                --                [ text x.title ]
                --        )
                --        services
                --    )
                --)
            , li [ class "nav-item" ] (viewUser model)
            ]
        ]
    ]


viewFooter =
    [ hr [] []
    , ul []
        [ li [] [ a [ href "#" ] [ text "Github" ] ]
        , li [] [ a [ href "#" ] [ text "Contribute" ] ]
        , li [] [ a [ href "#" ] [ text "Contact" ] ]
          -- TODO: add version / revision
        ]
    ]


view : Model -> Html Msg
view model =
    div []
        [ nav
            [ id "navbar"
            , class "navbar navbar-full navbar-light"
            ]
            [ div [ class "container" ] (viewNavBar model) ]
        , div [ id "content" ]
            [ div [ class "container" ] [ viewPage model ] ]
        , footer [ class "container" ] viewFooter
        ]



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ Sub.map UserMsg (User.taskclusterlogin_get (User.Logged))
        , Sub.map HawkRequest (Hawk.hawk_send_request (Hawk.SendRequest))
        ]
