port module App exposing (..)

import App.CodeCoverage as CodeCoverage
import App.Home as Home
import App.ReleaseDashboard as ReleaseDashboard
import App.Utils exposing (eventLink)
import BugzillaLogin as Bugzilla
import Hawk
import Html exposing (..)
import Html.Attributes exposing (..)
import Navigation exposing (Location)
import RemoteData exposing (RemoteData(..), WebData)
import RouteUrl exposing (UrlChange)
import RouteUrl.Builder as Builder exposing (Builder, builder, replacePath)
import String
import TaskclusterLogin as User
import Utils


type Page
    = Home
    | ReleaseDashboard
    | CodeCoverage
    | Bugzilla


type
    Msg
    -- Extensions integration
    = BugzillaMsg Bugzilla.Msg
    | UserMsg User.Msg
    | HomeMsg Home.Msg
    | HawkRequest Hawk.Msg
      -- App code
    | ShowCodeCoverage (Maybe String)
    | ShowReleaseDashboard Int
    | ShowPage Page
    | ReleaseDashboardMsg ReleaseDashboard.Msg
    | CodeCoverageMsg CodeCoverage.Msg


type alias Role =
    { roleId : String
    , scopes : List String
    }


type alias Model =
    { -- Extensions integration
      user : User.Model
    , bugzilla :
        Bugzilla.Model

    -- App code
    , current_page : Page
    , release_dashboard : ReleaseDashboard.Model
    , code_coverage : CodeCoverage.Model
    }


type alias Flags =
    { auth0 : Maybe User.Tokens
    , bugzilla : Maybe Bugzilla.Credentials
    , backend_uplift_url : String
    , bugzilla_url : String
    }


init : Flags -> ( Model, Cmd Msg )
init flags =
    let
        -- Extensions integration
        ( bz, bzCmd ) =
            Bugzilla.init flags.bugzilla_url flags.bugzilla

        ( user, userCmd ) =
            User.init flags.backend_uplift_url flags.auth0

        -- App init
        ( dashboard, dashboardCmd ) =
            ReleaseDashboard.init flags.backend_uplift_url

        ( code_coverage, ccCmd ) =
            CodeCoverage.init flags.backend_uplift_url

        model =
            { bugzilla = bz
            , user = user
            , current_page = Home
            , release_dashboard = dashboard
            , code_coverage = code_coverage
            }
    in
    ( model
    , -- Follow through with sub parts init
      Cmd.batch
        [ -- Extensions integration
          Cmd.map BugzillaMsg bzCmd
        , Cmd.map UserMsg userCmd
        , Cmd.map CodeCoverageMsg ccCmd
        , loadAllAnalysis model
        ]
    )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        -- Extensions integration
        BugzillaMsg bzMsg ->
            let
                ( newBz, bzCmd ) =
                    Bugzilla.update bzMsg model.bugzilla
            in
            ( { model | bugzilla = newBz }
            , Cmd.map BugzillaMsg bzCmd
            )

        UserMsg userMsg ->
            let
                -- Update current user
                ( user, userCmd ) =
                    User.update userMsg model.user

                -- Store in model
                model_ =
                    { model | user = user }

                -- Load analysis on user login
                commands =
                    List.concat
                        [ [ Cmd.map UserMsg userCmd ]
                        , case userMsg of
                            User.LoadedTaskclusterCredentials _ ->
                                [ loadAllAnalysis model_ ]

                            _ ->
                                []
                        ]
            in
            ( model_, Cmd.batch commands )

        HawkRequest hawkMsg ->
            let
                -- Always Redirect to release dashboard
                -- If we need another module, a prefix in requestId would be needed
                ( requestId, cmd, response ) =
                    Hawk.update hawkMsg

                dashboardCmd =
                    requestId
                        |> Maybe.map (ReleaseDashboard.routeHawkRequest response)
                        |> Maybe.withDefault Cmd.none
            in
            ( model
            , Cmd.batch
                [ Cmd.map HawkRequest cmd
                , Cmd.map ReleaseDashboardMsg dashboardCmd
                ]
            )

        -- Routing
        ShowCodeCoverage path ->
            let
                ( cc, ccCmd ) =
                    CodeCoverage.setDirectory model.code_coverage path
            in
            ( { model | code_coverage = cc, current_page = CodeCoverage }
            , Cmd.map CodeCoverageMsg ccCmd
            )

        ShowReleaseDashboard analysisId ->
            -- Fetch analysis and set page
            let
                rdCmd =
                    ReleaseDashboard.fetchAnalysis model.release_dashboard model.user analysisId
            in
            ( { model | current_page = ReleaseDashboard }
            , Cmd.map ReleaseDashboardMsg rdCmd
            )

        ShowPage page ->
            ( { model | current_page = page }, Cmd.none )

        HomeMsg homeMsg ->
            -- Does nothing
            ( model, Cmd.none )

        -- Dashboard updates
        ReleaseDashboardMsg dashMsg ->
            let
                ( dashboard, cmd ) =
                    ReleaseDashboard.update dashMsg model.release_dashboard model.user model.bugzilla
            in
            ( { model | release_dashboard = dashboard }
            , Cmd.map ReleaseDashboardMsg cmd
            )

        CodeCoverageMsg ccMsg ->
            let
                ( code_coverage, cmd ) =
                    CodeCoverage.update ccMsg model.code_coverage model.user
            in
            ( { model | code_coverage = code_coverage }
            , Cmd.map CodeCoverageMsg cmd
            )


loadAllAnalysis : Model -> Cmd Msg
loadAllAnalysis model =
    -- (Re)Load all dashboard analysis
    -- when user is loaded or is logged in
    case model.user.credentials of
        Just user ->
            Cmd.map ReleaseDashboardMsg (ReleaseDashboard.fetchAllAnalysis model.release_dashboard model.user)

        Nothing ->
            Cmd.none



-- Demo view


view : Model -> Html Msg
view model =
    div []
        [ nav [ class "navbar navbar-toggleable-md navbar-inverse bg-inverse" ]
            (viewNavBar model)
        , div [ id "content" ] [ viewPage model ]
        , viewFooter
        ]


viewPage : Model -> Html Msg
viewPage model =
    case model.current_page of
        Home ->
            Html.map HomeMsg (Home.view model)

        Bugzilla ->
            Html.map BugzillaMsg (Bugzilla.view model.bugzilla)

        CodeCoverage ->
            Html.map CodeCoverageMsg (CodeCoverage.view model.code_coverage)

        ReleaseDashboard ->
            Html.map ReleaseDashboardMsg (ReleaseDashboard.view model.release_dashboard model.user model.bugzilla)


viewNavBar : Model -> List (Html Msg)
viewNavBar model =
    [ button
        [ class "navbar-toggler hidden-md-up navbar-toggler-right"
        , type_ "button"
        , attribute "data-toggle" "collapse"
        , attribute "data-target" ".navbar-collapse"
        , attribute "aria-controls" "navbar-header"
        ]
        [ text "Menu" ]
    , pageLink Home
        [ class "navbar-brand" ]
        [ text "Uplift Dashboard" ]
    , div [ class "collapse navbar-collapse" ]
        [ ul [ class "navbar-nav mr-auto " ]
            (viewNavDashboard model
                ++ [ li [ class "nav-item" ]
                        [ eventLink (ShowCodeCoverage Nothing) [ class "nav-link" ] [ text "Code Coverage" ]
                        ]
                   ]
            )
        , ul [ class "navbar-nav" ] (viewUser model)
        ]
    ]


viewUser : Model -> List (Html Msg)
viewUser model =
    case model.user.credentials of
        Just user ->
            viewDropdown user.clientId
                [ -- Link to TC manager
                  a
                    [ class "dropdown-item"
                    , href "https://tools.taskcluster.net/credentials"
                    , target "_blank"
                    ]
                    [ text "Manage credentials" ]

                -- Display bugzilla status
                , viewBugzillaCreds model.bugzilla
                , -- Logout from TC
                  div [ class "dropdown-divider" ] []
                , a
                    [ Utils.onClick (UserMsg User.Logout)
                    , href "#"
                    , class "dropdown-item"
                    ]
                    [ text "Logout" ]
                ]

        Nothing ->
            viewLogin model.user


viewBugzillaCreds : Bugzilla.Model -> Html Msg
viewBugzillaCreds bugzilla =
    case bugzilla.check of
        NotAsked ->
            a [ class "dropdown-item text-info" ]
                [ span [] [ text "No bugzilla auth" ]
                , span [] viewLoginBugzilla
                ]

        Loading ->
            a [ class "dropdown-item text-info disabled" ] [ text "Loading Bugzilla auth." ]

        Failure err ->
            a [ class "dropdown-item text-danger" ]
                [ span [] [ text ("Error while loading bugzilla auth: " ++ toString err) ]
                , span [] viewLoginBugzilla
                ]

        Success valid ->
            if valid then
                a [ class "dropdown-item text-success disabled" ] [ text "Valid bugzilla auth" ]
            else
                a [ class "dropdown-item text-danger" ]
                    [ span [] [ text "Invalid bugzilla auth" ]
                    , span [] viewLoginBugzilla
                    ]


viewLoginBugzilla : List (Html Msg)
viewLoginBugzilla =
    [ eventLink (ShowPage Bugzilla) [ class "nav-link" ] [ text "Login Bugzilla" ]
    ]


viewNavDashboard : Model -> List (Html Msg)
viewNavDashboard model =
    case model.release_dashboard.all_analysis of
        NotAsked ->
            []

        Loading ->
            [ li [ class "nav-item text-info" ] [ text "Loading Bugs analysis..." ]
            ]

        Failure err ->
            [ li [ class "nav-item text-danger" ] [ text "No analysis available." ]
            ]

        Success allAnalysis ->
            List.map viewNavAnalysis allAnalysis


viewNavAnalysis : ReleaseDashboard.Analysis -> Html Msg
viewNavAnalysis analysis =
    li [ class "nav-item analysis" ]
        [ eventLink (ShowReleaseDashboard analysis.id)
            [ class "nav-link" ]
            [ span [ class "name" ] [ text analysis.full_name ]
            , if analysis.count > 0 then
                span [ class "badge badge-pill badge-primary" ] [ text (toString analysis.count) ]
              else
                span [ class "badge badge-pill badge-success" ] [ text (toString analysis.count) ]
            ]
        ]


viewLogin : User.Model -> List (Html Msg)
viewLogin user =
    [ a
        [ Utils.onClick (UserMsg <| User.Login)
        , href "#"
        , class "nav-link"
        ]
        [ text "Login TaskCluster" ]
    ]


viewFooter : Html msg
viewFooter =
    footer []
        [ ul []
            [ li [] [ a [ href "https://github.com/mozilla-releng/services" ] [ text "Github" ] ]
            , li [] [ a [ href "#" ] [ text "Contribute" ] ]
            , li [] [ a [ href "#" ] [ text "Contact" ] ]

            -- TODO: add version / revision
            ]
        ]


viewDropdown : String -> List (Html msg) -> List (Html msg)
viewDropdown title pages =
    [ div [ class "dropdown" ]
        [ a
            [ class "nav-link dropdown-toggle btn btn-primary"
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



-- Routing


pageLink : Page -> List (Attribute Msg) -> List (Html Msg) -> Html Msg
pageLink page attributes =
    eventLink (ShowPage page) attributes


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
                        |> User.convertUrlQueryToCode
                        |> Maybe.map
                            (\x ->
                                x
                                    |> User.Logging
                                    |> UserMsg
                            )
                        |> Maybe.withDefault (ShowPage Home)
                    , ShowPage Home
                    ]

                "bugzilla" ->
                    [ ShowPage Bugzilla
                    ]

                "code-coverage" ->
                    let
                        path =
                            if List.length rest > 0 then
                                Just (String.join "/" rest)
                            else
                                Nothing
                    in
                    [ ShowCodeCoverage path ]

                "release-dashboard" ->
                    let
                        messages =
                            if List.length rest == 1 then
                                case List.head rest of
                                    Just analysisId ->
                                        case String.toInt analysisId |> Result.toMaybe of
                                            Just analysisId_ ->
                                                -- Load specified analysis
                                                [ ReleaseDashboardMsg (ReleaseDashboard.FetchAnalysis analysisId_) ]

                                            Nothing ->
                                                []

                                    -- not a string
                                    Nothing ->
                                        []
                                -- empty string
                            else
                                []

                        -- No sub query parts
                    in
                    -- Finish by showing the page
                    messages ++ [ ShowPage ReleaseDashboard ]

                _ ->
                    [ ShowPage Home ]

        _ ->
            [ ShowPage Home ]


delta2url : Model -> Model -> Maybe UrlChange
delta2url previous current =
    Maybe.map Builder.toUrlChange <|
        case current.current_page of
            ReleaseDashboard ->
                let
                    path =
                        case current.release_dashboard.current_analysis of
                            Success analysis ->
                                [ "release-dashboard", toString analysis.id ]

                            _ ->
                                [ "release-dashboard" ]
                in
                Maybe.map
                    (Builder.prependToPath path)
                    (Just builder)

            Bugzilla ->
                Maybe.map
                    (Builder.prependToPath [ "bugzilla" ])
                    (Just builder)

            CodeCoverage ->
                let
                    parts =
                        case current.code_coverage.path of
                            Just path ->
                                String.split "/" path

                            Nothing ->
                                []
                in
                Maybe.map
                    (Builder.prependToPath ([ "code-coverage" ] ++ parts))
                    (Just builder)

            _ ->
                Maybe.map
                    (Builder.prependToPath [])
                    (Just builder)



-- Subscriptions


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ -- Extensions integration
          Sub.map BugzillaMsg (Bugzilla.bugzillalogin_get Bugzilla.Logged)
        , User.subscriptions UserMsg
        , Sub.map HawkRequest (Hawk.hawk_send_request Hawk.SendRequest)
        ]
