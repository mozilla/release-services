module Main exposing (main)

import App.Page.CodeCoverage
import App.Page.Home
import App.Page.Pipeline
import App.Page.Uplift
import App.Route
import AppCommon.Bugzilla
import AppCommon.ErrorPage
import AppCommon.Layout
import AppCommon.NotFoundPage
import AppCommon.Taskcluster
import Html exposing (..)
import Navigation
import RemoteData
import Task


type Page
    = NotFound AppCommon.NotFoundPage.Model
    | Error AppCommon.ErrorPage.Model
    | Home App.Page.Home.Model
    | CodeCoverage App.Page.CodeCoverage.Model
    | Uplift App.Page.Uplift.Model
    | Pipeline App.Page.Pipeline.Model


type RemotePage
    = Empty
    | Loading Page
    | Loaded Page



-- VIEW --

withContent : RemotePage -> AppCommon.Layout.Layout Msg -> AppCommon.Layout.Layout Msg
withContent page layout =
    case page of
        Empty ->
            layout
        Loaded page_ ->
            layout
                |> AppCommon.Layout.withContent (viewPage page_)
        Loading page_ ->
            layout
                |> AppCommon.Layout.isLoading
                |> AppCommon.Layout.withContent (viewPage page_)


viewPage : Page -> Html Msg
viewPage page =
    case page of
        NotFound location ->
            AppCommon.NotFoundPage.view location

        Error error ->
            AppCommon.ErrorPage.view error
                |> Html.map ErrorMsg

        Home model ->
            App.Page.Home.view model
                |> Html.map HomeMsg

        CodeCoverage model ->
            App.Page.CodeCoverage.view model
                |> Html.map CodeCoverageMsg

        Uplift model ->
            App.Page.Uplift.view model
                |> Html.map UpliftMsg

        Pipeline model ->
            App.Page.Pipeline.view model
                |> Html.map PipelineMsg


view : Model -> Html Msg
view model =
    AppCommon.Layout.init model.session.taskcluster
        |> withContent model.page
        |> AppCommon.Layout.toView


-- MODEL --


type alias Session =
    { taskcluster : AppCommon.Taskcluster.Model
    , bugzilla : AppCommon.Bugzilla.Model
    }


type alias Model =
    { page : RemotePage
    , session : Session
    , shipit_uplift_url : String
    , bugzilla_url : String
    }


init : Flags -> Navigation.Location -> ( Model, Cmd Msg )
init flags location =
    let
        ( taskcluster, taskclusterCmd ) =
            AppCommon.Taskcluster.init flags.taskcluster

        ( bugzilla, bugzillaCmd ) =
            AppCommon.Bugzilla.init flags.bugzilla_url flags.bugzilla

        ( model, cmd ) =
            setRoute (App.Route.locationToRoute location)
                { page = Empty
                , session =
                    { taskcluster = taskcluster
                    , bugzilla = bugzilla
                    }
                , shipit_uplift_url = flags.shipit_uplift_url
                , bugzilla_url = flags.bugzilla_url
                }
    in
        ( model
        , Cmd.batch
            [ cmd
            , Cmd.map BugzillaMsg bugzillaCmd
            , Cmd.map TaskclusterMsg taskclusterCmd
            ]
        )



-- SUBSCRIPTIONS --


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.none
    -- TODO per page subscriptions


-- UPDATE --


type Msg
    -- Routing
    = SetRoute (Result Navigation.Location App.Route.Route)
    --| NavigateTo App.Route.Route
    -- AppCommon extensions
    | BugzillaMsg AppCommon.Bugzilla.Msg
    | TaskclusterMsg AppCommon.Taskcluster.Msg
    -- Pages
    | ErrorMsg AppCommon.ErrorPage.Msg
    | HomeLoaded (Result AppCommon.ErrorPage.Model App.Page.Home.Model)
    | HomeMsg App.Page.Home.Msg
    | CodeCoverageLoaded (Result AppCommon.ErrorPage.Model App.Page.CodeCoverage.Model)
    | CodeCoverageMsg App.Page.CodeCoverage.Msg
    | UpliftLoaded (Result AppCommon.ErrorPage.Model App.Page.Uplift.Model)
    | UpliftMsg App.Page.Uplift.Msg
    | PipelineLoaded (Result AppCommon.ErrorPage.Model App.Page.Pipeline.Model)
    | PipelineMsg App.Page.Pipeline.Msg


setRoute : Result Navigation.Location App.Route.Route -> Model -> ( Model, Cmd Msg )
setRoute route model =
    --let
    --    transition toMsg task =
    --        ( { model | page = Loading (getPage model.page) }
    --        , Task.attempt toMsg task
    --        )
    --in
    case route of
        Err location ->
            ( { model | page = Loaded (NotFound location)}
            , Cmd.none
            )

        Ok route ->
            --transition HomeLoaded (App.Page.Home.init model.session)
            ( { model | page = Empty }
            , Cmd.none
            )


routeHawkResponse : Cmd (RemoteData.WebData String) -> AppCommon.Taskcluster.Request -> ( Cmd Msg )
routeHawkResponse httpCmd request =
    -- TODO: example of hawk routing for subpages
    --if String.startsWith "Uplift" request.id then
    --    request.id
    --        |> String.dropLeft (String.length "Uplift")
    --        |> App.Request.Uplift.hawkResponse httpCmd
    --        |> Cmd.map UpliftMsg
    --else
    Cmd.none


pageLoaded
    : Result AppCommon.ErrorPage.Model a
    -> Model 
    -> (a -> Page)
    -> ( Model, Cmd Msg )
pageLoaded result model page =
    case result of
        Ok model_ ->
            ( { model | page = Loaded (page model_ ) }
            , Cmd.none
            )

        Err error ->
            ( { model | page = Loaded (Error error) }
            , Cmd.none
            )

update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of

        BugzillaMsg msg_ ->
            let
                ( newModel, newCmd ) =
                    AppCommon.Bugzilla.update msg_ model.session.bugzilla
                session = model.session
                newSession  =
                    { session | bugzilla = newModel }
            in
                ( { model | session = newSession }
                , Cmd.map BugzillaMsg newCmd
                )

        TaskclusterMsg msg_ ->
            let
                ( newModel, newCmd, newHawkCmd ) =
                    AppCommon.Taskcluster.update routeHawkResponse msg_ model.session.taskcluster
                session = model.session
                newSession  =
                    { session | taskcluster = newModel }
            in
                ( { model | session = newSession }
                , Cmd.batch
                    [ Cmd.map TaskclusterMsg newCmd
                    , newHawkCmd
                    ]
                )

        ErrorMsg msg_ ->
            ( model
            , AppCommon.ErrorPage.update msg_
                  |> Cmd.map ErrorMsg
            )

        SetRoute route ->
            setRoute route model

        HomeLoaded result ->
            pageLoaded result model Home

        HomeMsg msg_ ->
            case model.page of
                Loaded (Home model_) ->
                    let
                        ( newModel, newCmd ) =
                            App.Page.Home.update msg_ model_
                    in
                        ( { model | page = Loaded (Home newModel) }
                        , Cmd.map HomeMsg newCmd
                        )
                _ ->
                    ( model, Cmd.none )

        CodeCoverageLoaded result ->
            pageLoaded result model CodeCoverage

        CodeCoverageMsg msg_ ->
            case model.page of
                Loaded (CodeCoverage model_) ->
                    let
                        ( newModel, newCmd ) =
                            App.Page.CodeCoverage.update msg_ model_
                    in
                        ( { model | page = Loaded (CodeCoverage newModel) }
                        , Cmd.map CodeCoverageMsg newCmd
                        )
                _ ->
                    ( model, Cmd.none )

        UpliftLoaded result ->
            pageLoaded result model Uplift

        UpliftMsg msg_ ->
            case model.page of
                Loaded (Uplift model_) ->
                    let
                        ( newModel, newCmd ) =
                            App.Page.Uplift.update msg_ model_
                    in
                        ( { model | page = Loaded (Uplift newModel) }
                        , Cmd.map UpliftMsg newCmd
                        )
                _ ->
                    ( model, Cmd.none )

        PipelineLoaded result ->
            pageLoaded result model Pipeline

        PipelineMsg msg_ ->
            case model.page of
                Loaded (Pipeline model_) ->
                    let
                        ( newModel, newCmd ) =
                            App.Page.Pipeline.update msg_ model_
                    in
                        ( { model | page = Loaded (Pipeline newModel) }
                        , Cmd.map PipelineMsg newCmd
                        )
                _ ->
                    ( model, Cmd.none )


-- MAIN --


type alias Flags =
    { taskcluster : Maybe AppCommon.Taskcluster.Credentials
    , bugzilla : Maybe AppCommon.Bugzilla.Credentials
    , shipit_uplift_url : String
    , bugzilla_url : String
    }


main : Program Flags Model Msg
main =
    Navigation.programWithFlags (App.Route.locationToRoute >> SetRoute)
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }
