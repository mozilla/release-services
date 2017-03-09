module App.ReleaseDashboard exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onClick, onInput, onSubmit, onCheck)
import HtmlParser exposing (parse)
import HtmlParser.Util exposing (toVirtualDom)
import String
import Dict
import Date
import Json.Decode as Json exposing (Decoder)
import Json.Decode.Extra as JsonExtra exposing ((|:))
import Json.Encode as JsonEncode
import RemoteData as RemoteData exposing (WebData, RemoteData(Loading, Success, NotAsked, Failure), isSuccess)
import Http
import Basics exposing (Never)
import Utils exposing (onChange)
import TaskclusterLogin as User
import BugzillaLogin as Bugzilla
import Hawk
import App.Contributor as ContribEditor exposing (Contributor, decodeContributor, viewContributor)


-- Models


type BugEditor
    = FlagsEditor
    | ApprovalEditor
    | RejectEditor
    | NoEditor


type alias Changes =
    { bugzilla_id : Int
    , changes :
        Dict.Dict String
            { removed : String
            , added : String
            }
    }


type BugUpdate
    = UpdateFailed String
    | UpdatedBug (List Changes)
    | UpdatedAttachment (List Changes)


type alias UpliftRequest =
    { bugzilla_id : Int
    , comment : String
    }


type alias UpliftVersion =
    { name : String
    , status : String
    , attachments : List String
    }


type alias Patch =
    { source : String
    , additions : Int
    , deletions : Int
    , changes : Int
    , url : String
    , languages : List String
    , merge : Dict.Dict String Bool
    }


type alias Bug =
    { id : Int
    , bugzilla_id : Int
    , url : String
    , summary : String
    , product : String
    , component : String
    , status : String
    , keywords : List String
    , flags_status : Dict.Dict String String
    , flags_tracking : Dict.Dict String String
    , flags_generic : Dict.Dict String String
    , -- Contributors
      contributors : List Contributor
    , -- Uplift
      uplift_request : Maybe UpliftRequest
    , uplift_versions : Dict.Dict String UpliftVersion
    , -- Patches
      patches : Dict.Dict String Patch
    , landings : Dict.Dict String Date.Date
    , -- Actions on bug
      editor : BugEditor
    , edits : Dict.Dict String String
    , attachments : Dict.Dict String (Dict.Dict String String)
    , -- uplift approval
      update : WebData BugUpdate
    }


type alias Analysis =
    { id : Int
    , name : String
    , version : Int
    , count : Int
    , bugs : List Bug
    }


type alias Model =
    { -- All analysis in use
      all_analysis : WebData (List Analysis)
    , -- Current Analysis used
      current_analysis : WebData Analysis
    , -- Backend base endpoint
      backend_uplift_url : String
    , contrib_editor : ContribEditor.Model
    }


type
    Msg
    -- List available analysis
    = FetchAllAnalysis
    | FetchedAllAnalysis (WebData String)
      -- Retrieve detailed analysis
    | FetchAnalysis Int
    | FetchedAnalysis (WebData String)
      -- Edit a bug
    | ShowBugEditor Bug BugEditor
    | EditBug Bug String String
    | EditUplift Bug UpliftVersion Bool
    | FetchedBug (WebData String)
      -- Save bug edits
    | PublishEdits Bug
    | SavedBugEdit Bug (WebData BugUpdate)
      -- Hawk Extension
    | HawkRequest Hawk.Msg
      -- Contributor editor extension
    | ContribEditorMsg ContribEditor.Msg


init : String -> ( Model, Cmd Msg )
init backend_uplift_url =
    -- Init empty model
    let
        ( contrib_editor, cmd ) =
            ContribEditor.init backend_uplift_url
    in
        ( { all_analysis = NotAsked
          , current_analysis = NotAsked
          , backend_uplift_url = backend_uplift_url
          , contrib_editor = contrib_editor
          }
        , Cmd.batch
            [ Cmd.map ContribEditorMsg cmd
            ]
        )



-- Update


routeHawkRequest : Cmd (WebData String) -> String -> Cmd Msg
routeHawkRequest response route =
    case route of
        "AllAnalysis" ->
            Cmd.map FetchedAllAnalysis response

        "Analysis" ->
            Cmd.map FetchedAnalysis response

        "BugUpdate" ->
            Cmd.map FetchedBug response

        "Contributor" ->
            Cmd.map ContribEditorMsg (Cmd.map ContribEditor.UpdatedContributor response)

        _ ->
            Cmd.none


update : Msg -> Model -> User.Model -> Bugzilla.Model -> ( Model, Cmd Msg )
update msg model user bugzilla =
    case msg of
        HawkRequest hawkMsg ->
            ( model, Cmd.none )

        -- Load all Analysis
        FetchAllAnalysis ->
            ( { model | all_analysis = Loading }
            , fetchAllAnalysis model user
            )

        FetchedAllAnalysis response ->
            ( { model
                | all_analysis = Utils.decodeJsonString decodeAllAnalysis response
                , current_analysis = NotAsked
              }
            , Cmd.none
            )

        -- Load a detailed analysis
        FetchAnalysis analysisId ->
            ( { model | current_analysis = Loading }
            , fetchAnalysis model user analysisId
            )

        FetchedAnalysis response ->
            ( { model | current_analysis = Utils.decodeJsonString decodeAnalysis response }
            , Cmd.none
            )

        ShowBugEditor bug show ->
            let
                -- Mark a bug as being edited
                model_ =
                    updateBug model bug.id (\b -> { b | editor = show, edits = Dict.empty, attachments = Dict.empty })
            in
                ( model_, Cmd.none )

        EditBug bug key value ->
            -- Store a bug edit
            let
                edits =
                    Dict.insert key value bug.edits

                model_ =
                    updateBug model bug.id (\b -> { b | edits = edits })
            in
                ( model_, Cmd.none )

        EditUplift bug version checked ->
            -- Store an uplift approval
            -- Inverse data : we must send updates on attachments !
            let
                status =
                    case bug.editor of
                        ApprovalEditor ->
                            if checked then
                                "+"
                            else
                                version.status

                        RejectEditor ->
                            if checked then
                                "-"
                            else
                                version.status

                        _ ->
                            "?"

                attachments =
                    List.map (\a -> ( a, Dict.singleton version.name status )) version.attachments
                        |> Dict.fromList
                        |> Dict.foldl mergeAttachments bug.attachments

                model_ =
                    updateBug model bug.id (\b -> { b | attachments = attachments })
            in
                ( model_, Cmd.none )

        PublishEdits bug ->
            -- Send edits to backend
            case bug.editor of
                FlagsEditor ->
                    publishBugEdits model bugzilla bug

                ApprovalEditor ->
                    publishApproval model bugzilla bug

                RejectEditor ->
                    publishApproval model bugzilla bug

                NoEditor ->
                    ( model, Cmd.none )

        FetchedBug response ->
            ( Utils.decodeJsonString decodeBug response
                |> RemoteData.map (\bug -> updateBug model bug.id (\b -> bug))
                |> RemoteData.withDefault model
            , Cmd.none
            )

        SavedBugEdit bug update ->
            let
                -- Store bug update from bugzilla
                model_ =
                    updateBug model bug.id (\b -> { b | update = update, editor = NoEditor })
            in
                -- Forward update to backend
                case update of
                    Success up ->
                        sendBugUpdate model_ user bug up

                    _ ->
                        ( model_, Cmd.none )

        ContribEditorMsg editorMsg ->
            let
                ( editor, cmd ) =
                    ContribEditor.update editorMsg model.contrib_editor user

                -- Update contributor in every bug referencing him
                newModel =
                    case editor.update of
                        Success contributor ->
                            updateContributor model contributor

                        _ ->
                            model
            in
                ( { newModel | contrib_editor = editor }
                , Cmd.map ContribEditorMsg cmd
                )


mergeAttachments :
    String
    -> Dict.Dict String String
    -> Dict.Dict String (Dict.Dict String String)
    -> Dict.Dict String (Dict.Dict String String)
mergeAttachments aId versions attachments =
    -- Like Dict.union on 2 levels
    let
        out =
            case Dict.get aId attachments of
                Just attachment ->
                    Dict.union versions attachment

                Nothing ->
                    versions

        -- Remove useless versions
        out_ =
            Dict.filter (\k v -> (not (v == "?"))) out
    in
        if out_ == Dict.empty then
            Dict.remove aId attachments
        else
            Dict.insert aId out_ attachments


updateBugs : Model -> (Bug -> Bug) -> Model
updateBugs model callback =
    -- Run a callback on every bugs
    case model.current_analysis of
        Success analysis ->
            let
                -- Rebuild bugs list
                bugs =
                    List.map callback analysis.bugs

                -- Rebuild analysis
                analysis_ =
                    { analysis | bugs = bugs }
            in
                { model | current_analysis = Success analysis_ }

        _ ->
            model


updateBug : Model -> Int -> (Bug -> Bug) -> Model
updateBug model bugId callback =
    -- Update a specific bug in current analysis
    -- using a callback
    updateBugs model
        (\b ->
            if b.id == bugId then
                (callback b)
            else
                b
        )


updateContributor : Model -> Contributor -> Model
updateContributor model contributor =
    -- Update a contributor in every bugs
    -- Only update karma & comments
    updateBugs model
        (\bug ->
            { bug
                | contributors =
                    List.map
                        (\c ->
                            if c.id == contributor.id then
                                { c | karma = contributor.karma, comment_private = contributor.comment_private, comment_public = contributor.comment_public }
                            else
                                c
                        )
                        bug.contributors
            }
        )


fetchAllAnalysis : Model -> User.Model -> Cmd Msg
fetchAllAnalysis model user =
    -- Fetch all analysis summary
    case user of
        Just credentials ->
            let
                -- Build Taskcluster http request
                url =
                    model.backend_uplift_url ++ "/analysis"

                request =
                    Hawk.Request "AllAnalysis" "GET" url [] Http.emptyBody
            in
                Cmd.map HawkRequest
                    (Hawk.send request credentials)

        Nothing ->
            -- No credentials
            Cmd.none


fetchAnalysis : Model -> User.Model -> Int -> Cmd Msg
fetchAnalysis model user analysis_id =
    -- Fetch a specific analysis with details
    case user of
        Just credentials ->
            let
                -- Build Taskcluster http request
                url =
                    model.backend_uplift_url ++ "/analysis/" ++ (toString analysis_id)

                request =
                    Hawk.Request "Analysis" "GET" url [] Http.emptyBody
            in
                Cmd.map HawkRequest
                    (Hawk.send request credentials)

        Nothing ->
            -- No credentials
            Cmd.none


publishBugEdits : Model -> Bugzilla.Model -> Bug -> ( Model, Cmd Msg )
publishBugEdits model bugzilla bug =
    -- Publish all bug edits directly to Bugzilla
    case bugzilla.check of
        Success check ->
            let
                comment =
                    Dict.get "comment" bug.edits |> Maybe.withDefault "Modified from Uplift Dashboard."

                edits =
                    Dict.filter (\k v -> not (k == "comment")) bug.edits

                -- Send directly status & tracking flags in body
                cf_flags =
                    List.map (\( k, v ) -> ( "cf_" ++ k, JsonEncode.string v )) (Dict.toList (Dict.filter (\k v -> (String.startsWith "status_" k) || (String.startsWith "tracking_" k)) edits))

                -- Send generic flags separately
                flags =
                    List.map (\( k, v ) -> encodeFlag ( (String.dropLeft 8 k), v ))
                        (Dict.toList (Dict.filter (\k v -> (String.startsWith "generic_" k)) edits))

                -- Build payload for bugzilla
                payload =
                    JsonEncode.object
                        ([ ( "comment"
                           , JsonEncode.object
                                [ ( "body", JsonEncode.string comment )
                                , ( "is_markdown", JsonEncode.bool True )
                                ]
                           )
                         , ( "flags", JsonEncode.list flags )
                         ]
                            ++ cf_flags
                        )

                request =
                    Http.request
                        { method = "PUT"
                        , headers = Bugzilla.buildHeaders bugzilla []
                        , url = bugzilla.url ++ "/rest/bug/" ++ (toString bug.bugzilla_id)
                        , body = Http.jsonBody payload
                        , expect = Http.expectJson decodeBugUpdate
                        , timeout = Nothing
                        , withCredentials = False
                        }

                cmd =
                    RemoteData.sendRequest request
                        |> Cmd.map (SavedBugEdit bug)

                -- Mark bug as being updated
                model_ =
                    updateBug model bug.id (\b -> { b | update = Loading })
            in
                ( model_, cmd )

        _ ->
            -- No credentials !
            ( model, Cmd.none )


publishApproval : Model -> Bugzilla.Model -> Bug -> ( Model, Cmd Msg )
publishApproval model bugzilla bug =
    case bugzilla.check of
        Success check ->
            let
                -- Make a request per updated attachment
                comment =
                    Dict.get "comment" bug.edits |> Maybe.withDefault "Modified from Uplift Dashboard."

                commands =
                    List.map (updateAttachment bug bugzilla comment) (Dict.toList bug.attachments)

                -- Mark bug as being updatedo
                model_ =
                    updateBug model bug.id (\b -> { b | update = Loading })
            in
                ( model_, Cmd.batch commands )

        _ ->
            -- No credentials !
            ( model, Cmd.none )


updateAttachment : Bug -> Bugzilla.Model -> String -> ( String, Dict.Dict String String ) -> Cmd Msg
updateAttachment bug bugzilla comment ( attachment_id, versions ) =
    -- Build payload for bugzilla
    -- to update an atachment
    let
        flags =
            List.map encodeFlag (Dict.toList versions)

        payload =
            JsonEncode.object
                [ ( "comment", JsonEncode.string comment )
                , ( "flags", JsonEncode.list flags )
                ]

        request =
            Http.request
                { method = "PUT"
                , headers = Bugzilla.buildHeaders bugzilla []
                , url = bugzilla.url ++ "/rest/bug/attachment/" ++ attachment_id
                , body = Http.jsonBody payload
                , expect = Http.expectJson decodeBugUpdate
                , timeout = Nothing
                , withCredentials = False
                }
    in
        RemoteData.sendRequest request
            |> Cmd.map (SavedBugEdit bug)


encodeChanges : String -> List Changes -> JsonEncode.Value
encodeChanges target changes =
    -- Encode bug changes
    (JsonEncode.list
        (List.map
            (\u ->
                JsonEncode.object
                    [ ( "bugzilla_id", JsonEncode.int u.bugzilla_id )
                    , ( "target", JsonEncode.string target )
                    , ( "changes"
                      , JsonEncode.object
                            (-- There is no JsonEncode.dict :/
                             Dict.toList u.changes
                                |> List.map
                                    (\( k, v ) ->
                                        ( k
                                        , JsonEncode.object
                                            [ ( "added", JsonEncode.string v.added )
                                            , ( "removed", JsonEncode.string v.removed )
                                            ]
                                        )
                                    )
                            )
                      )
                    ]
            )
            changes
        )
    )


sendBugUpdate : Model -> User.Model -> Bug -> BugUpdate -> ( Model, Cmd Msg )
sendBugUpdate model user bug update =
    -- Send a bug update to the backend
    -- so it can update the bug payload
    case user of
        Just credentials ->
            let
                payload =
                    case update of
                        UpdatedBug changes ->
                            encodeChanges "bug" changes

                        UpdatedAttachment changes ->
                            encodeChanges "attachment" changes

                        _ ->
                            JsonEncode.null

                -- Build Taskcluster http request
                url =
                    model.backend_uplift_url ++ "/bugs/" ++ (toString bug.bugzilla_id)

                request =
                    Hawk.Request "BugUpdate" "PUT" url [] (Http.jsonBody payload)
            in
                ( model
                , Cmd.map HawkRequest
                    (Hawk.send request credentials)
                )

        Nothing ->
            ( model, Cmd.none )


encodeFlag : ( String, String ) -> JsonEncode.Value
encodeFlag ( name, status ) =
    -- Json encode an attachment flag
    JsonEncode.object
        [ ( "name", JsonEncode.string name )
        , ( "status", JsonEncode.string status )
        ]


decodeBugUpdate : Decoder BugUpdate
decodeBugUpdate =
    Json.oneOf
        [ -- Success decoder after bug update
          Json.map UpdatedBug
            (Json.field "bugs" (Json.list decodeUpdatedBug))
        , -- Success decoder after attachment update
          Json.map UpdatedAttachment
            (Json.field "attachments" (Json.list decodeUpdatedBug))
        , -- Error decoder
          Json.map UpdateFailed
            (Json.field "message" Json.string)
        ]


decodeUpdatedBug : Decoder Changes
decodeUpdatedBug =
    Json.map2 Changes
        (Json.field "id" Json.int)
        (Json.field "changes"
            (Json.dict
                (Json.map2
                    (\r a -> { removed = r, added = a })
                    (Json.field "removed" Json.string)
                    (Json.field "added" Json.string)
                )
            )
        )


decodeAllAnalysis : Decoder (List Analysis)
decodeAllAnalysis =
    Json.list decodeAnalysis


decodeAnalysis : Decoder Analysis
decodeAnalysis =
    Json.map5 Analysis
        (Json.field "id" Json.int)
        (Json.field "name" Json.string)
        (Json.field "version" Json.int)
        (Json.field "count" Json.int)
        (Json.field "bugs" (Json.list decodeBug))


decodeBug : Decoder Bug
decodeBug =
    Json.succeed Bug
        |: (Json.field "id" Json.int)
        |: (Json.field "bugzilla_id" Json.int)
        |: (Json.field "url" Json.string)
        |: (Json.field "summary" Json.string)
        |: (Json.field "product" Json.string)
        |: (Json.field "component" Json.string)
        |: (Json.field "status" Json.string)
        |: (Json.field "keywords" (Json.list Json.string))
        |: (Json.field "flags_status" (Json.dict Json.string))
        |: (Json.field "flags_tracking" (Json.dict Json.string))
        |: (Json.field "flags_generic" (Json.dict Json.string))
        |: (Json.field "contributors" (Json.list decodeContributor))
        |: (Json.maybe (Json.field "uplift" decodeUpliftRequest))
        |: (Json.field "versions" (Json.dict decodeVersion))
        |: (Json.field "patches" (Json.dict decodePatch))
        |: (Json.field "landings" (Json.dict JsonExtra.date))
        |: (Json.succeed NoEditor)
        -- not editing at first
        |:
            (Json.succeed Dict.empty)
        -- not editing at first
        |:
            (Json.succeed Dict.empty)
        -- not editing at first
        |:
            (Json.succeed NotAsked)



-- no updates at first


decodePatch : Decoder Patch
decodePatch =
    Json.map7 Patch
        (Json.field "source" Json.string)
        (Json.field "changes_add" Json.int)
        (Json.field "changes_del" Json.int)
        (Json.field "changes_size" Json.int)
        (Json.field "url" Json.string)
        (Json.field "languages" (Json.list Json.string))
        (Json.field "merge" (Json.dict Json.bool))


decodeVersion : Decoder UpliftVersion
decodeVersion =
    Json.map3 UpliftVersion
        (Json.field "name" Json.string)
        (Json.field "status" Json.string)
        (Json.field "attachments" (Json.list Json.string))


decodeUpliftRequest : Decoder UpliftRequest
decodeUpliftRequest =
    Json.map2 UpliftRequest
        (Json.field "id" Json.int)
        (Json.field "comment" Json.string)



-- Subscriptions


subscriptions : Analysis -> Sub Msg
subscriptions analysis =
    Sub.none



-- Views


view : Model -> Bugzilla.Model -> Html Msg
view model bugzilla =
    case model.current_analysis of
        NotAsked ->
            div [ class "alert alert-info" ] [ text "Please select an analysis in the navbar above." ]

        Loading ->
            div [ class "alert alert-info" ] [ text "Loading your bugs..." ]

        Failure err ->
            div [ class "alert alert-danger" ] [ text ("Error: " ++ toString err) ]

        Success analysis ->
            viewAnalysis model.contrib_editor bugzilla analysis


viewAnalysis : ContribEditor.Model -> Bugzilla.Model -> Analysis -> Html Msg
viewAnalysis editor bugzilla analysis =
    div []
        [ Html.map ContribEditorMsg (ContribEditor.viewModal editor)
        , h1 [] [ text ("Listing all " ++ analysis.name ++ " " ++ (toString analysis.version) ++ " uplifts for review:") ]
        , div [ class "bugs" ] (List.map (viewBug editor bugzilla) analysis.bugs)
        ]


viewBug : ContribEditor.Model -> Bugzilla.Model -> Bug -> Html Msg
viewBug editor bugzilla bug =
    div [ class "bug" ]
        [ h4 [] [ text bug.summary ]
        , p [ class "summary" ]
            [ a [ class "text-muted monospace", href bug.url, target "_blank" ] [ text ("#" ++ (toString bug.bugzilla_id)) ]
            , span [ class "text-muted" ] [ text "is" ]
            , case bug.status of
                "RESOLVED" ->
                    strong [ class "text-success" ] [ text "Resolved" ]

                "ASSIGNED" ->
                    strong [ class "text-info" ] [ text "Assigned" ]

                "VERIFIED" ->
                    strong [ class "text-danger" ] [ text "Assigned" ]

                x ->
                    strong [ class "text-warning" ] [ text x ]
            , span [ class "text-muted" ] [ text "in" ]
            , span [ class "" ] [ text bug.product ]
            , span [ class "text-muted" ] [ text "/" ]
            , span [ class "" ] [ text bug.component ]
            ]
        , p [ class "summary" ]
            ([ span [ class "text-muted" ] [ text "Versions :" ] ]
                ++ (List.map viewVersionbadge (Dict.toList bug.uplift_versions))
                ++ (List.map (\k -> span [ class "badge badge-default" ] [ text k ]) bug.keywords)
            )
        , div [ class "row columns" ]
            [ div [ class "col" ]
                (List.map (\c -> Html.map ContribEditorMsg (viewContributor editor c)) bug.contributors)
            , div [ class "col" ]
                [ viewUpliftRequest bug.uplift_request
                ]
            , div [ class "col" ]
                [ case bug.editor of
                    FlagsEditor ->
                        viewFlagsEditor bugzilla bug

                    ApprovalEditor ->
                        viewApprovalEditor bugzilla bug

                    RejectEditor ->
                        viewApprovalEditor bugzilla bug

                    NoEditor ->
                        viewBugDetails bug
                ]
            ]
        ]


viewVersionbadge : ( String, UpliftVersion ) -> Html Msg
viewVersionbadge ( name, version ) =
    case version.status of
        "?" ->
            span [ class "badge badge-info" ] [ text name ]

        "+" ->
            span [ class "badge badge-success" ] [ text name ]

        "-" ->
            span [ class "badge badge-danger" ] [ text name ]

        _ ->
            span [ class "badge badge-default" ] [ text name ]


viewUpliftRequest : Maybe UpliftRequest -> Html Msg
viewUpliftRequest maybe =
    case maybe of
        Just request ->
            div [ class "uplift-request", id (toString request.bugzilla_id) ]
                [ div [ class "comment" ] (toVirtualDom (parse request.comment))
                ]

        Nothing ->
            div [ class "alert alert-warning" ] [ text "No uplift request." ]


viewBugDetails : Bug -> Html Msg
viewBugDetails bug =
    let
        uplift_hidden =
            (Dict.filter (\k v -> v.status == "?") bug.uplift_versions) == Dict.empty
    in
        div [ class "details" ]
            [ case bug.update of
                Success update ->
                    case update of
                        UpdateFailed error ->
                            div [ class "alert alert-danger" ]
                                [ h4 [] [ text "Error during the update" ]
                                , p [] [ text error ]
                                ]

                        _ ->
                            div [ class "alert alert-success" ] [ text "Bug updated !" ]

                Failure err ->
                    div [ class "alert alert-danger" ]
                        [ h4 [] [ text "Error" ]
                        , p [] [ text ("An error occurred during the update: " ++ (toString err)) ]
                        ]

                _ ->
                    span [] []
            , h5 [] [ text "Patches" ]
            , div [ class "patches" ] (List.map viewPatch (Dict.toList bug.patches))
            , viewFlags bug
            , -- Start editing
              div [ class "actions list-group" ]
                [ button [ hidden uplift_hidden, class "list-group-item list-group-item-action list-group-item-success", onClick (ShowBugEditor bug ApprovalEditor) ] [ text "Approve uplift" ]
                , button [ hidden uplift_hidden, class "list-group-item list-group-item-action list-group-item-danger", onClick (ShowBugEditor bug RejectEditor) ] [ text "Reject uplift" ]
                , button [ class "list-group-item list-group-item-action", onClick (ShowBugEditor bug FlagsEditor) ] [ text "Edit flags" ]
                , a [ class "list-group-item list-group-item-action", href bug.url, target "_blank" ] [ text "View on Bugzilla" ]
                ]
            ]


viewPatch : ( String, Patch ) -> Html Msg
viewPatch ( patchId, patch ) =
    div [ class "patch" ]
        ([ a [ href patch.url, target "_blank", title ("On " ++ patch.source) ]
            [ text
                ((if patch.changes > 0 then
                    "Patch"
                  else
                    "Test"
                 )
                    ++ " "
                    ++ patchId
                )
            ]
         , span [ class "changes" ] [ text "(" ]
         , span [ class "changes additions" ] [ text ("+" ++ (toString patch.additions)) ]
         , span [ class "changes deletions" ] [ text ("-" ++ (toString patch.deletions)) ]
         ]
            ++ (List.map
                    (\l ->
                        span []
                            [ span [ class "changes" ] [ text "/" ]
                            , span [ class "text-info" ] [ text l ]
                            ]
                    )
                    patch.languages
               )
            ++ [ span [ class "changes" ] [ text ")" ] ]
            ++ (List.map
                    (\( version, status ) ->
                        if status then
                            span [ class "merge badge badge-success", title ("Merge successful on " ++ version) ] [ text version ]
                        else
                            span [ class "merge badge badge-danger", title ("Merge failed on " ++ version) ] [ text version ]
                    )
                    (Dict.toList patch.merge)
               )
        )


viewFlagsList : Dict.Dict String String -> String -> Html msg
viewFlagsList all_flags name =
    let
        flags =
            Dict.filter (\k v -> not (v == "---")) all_flags
    in
        div [ class "col-xs-12 col-sm-6" ]
            [ h5 [] [ text name ]
            , if Dict.isEmpty flags then
                p [ class "text-warning" ] [ text ("No " ++ name ++ " set.") ]
              else
                ul [] (List.map viewFlag (Dict.toList flags))
            ]


viewFlags : Bug -> Html Msg
viewFlags bug =
    div [ class "flags" ]
        [ div [ class "row" ]
            [ viewFlagsList bug.flags_status "Status flags"
            , viewFlagsList bug.flags_generic "Generic flags"
            ]
        , div [ class "row" ]
            [ viewFlagsList bug.flags_tracking "Tracking flags"
            , div [ class "col-xs-12 col-sm-6" ]
                [ h5 [] [ text "Landing dates" ]
                , if Dict.isEmpty bug.landings then
                    p [ class "text-warning" ] [ text "No landing dates available." ]
                  else
                    ul [] (List.map viewLandingDate (Dict.toList bug.landings))
                ]
            ]
        ]


viewLandingDate : ( String, Date.Date ) -> Html msg
viewLandingDate ( key, date ) =
    li []
        [ strong [] [ text key ]
        , span []
            [ text
                ((date |> Date.day |> toString)
                    ++ " "
                    ++ (date |> Date.month |> toString)
                    ++ " "
                    ++ (date |> Date.year |> toString)
                )
            ]
        ]


viewFlag : ( String, String ) -> Html msg
viewFlag ( key, value ) =
    li []
        [ strong [] [ text key ]
        , case value of
            "+" ->
                span [ class "badge badge-success" ] [ text value ]

            "-" ->
                span [ class "badge badge-danger" ] [ text value ]

            "?" ->
                span [ class "badge badge-info" ] [ text value ]

            "affected" ->
                span [ class "badge badge-danger" ] [ text value ]

            "verified" ->
                span [ class "badge badge-info" ] [ text value ]

            "fixed" ->
                span [ class "badge badge-success" ] [ text value ]

            "wontfix" ->
                span [ class "badge badge-warning" ] [ text value ]

            _ ->
                span [ class "badge badge-default" ] [ text value ]
        ]


editFlag : Bug -> String -> List String -> ( String, String ) -> Html Msg
editFlag bug prefix possible_values ( key, flag_value ) =
    div [ class "form-group row" ]
        [ label [ class "col col-form-label" ] [ text key ]
        , div [ class "col" ]
            [ select [ class "form-control form-control-sm", onChange (EditBug bug (prefix ++ "_" ++ key)) ]
                (List.map (\x -> option [ selected (x == flag_value) ] [ text x ]) possible_values)
            ]
        ]


viewFlagsEditor : Bugzilla.Model -> Bug -> Html Msg
viewFlagsEditor bugzilla bug =
    -- Show the form to edit flags
    let
        values =
            [ "+", "-", "?", "---" ]

        status_values =
            [ "affected", "verified", "fixed", "wontfix", "---" ]
    in
        Html.form [ class "editor", onSubmit (PublishEdits bug) ]
            [ div [ class "col" ]
                ([ h4 [] [ text "Status" ] ] ++ (List.map (\x -> editFlag bug "status" status_values x) (Dict.toList bug.flags_status)))
            , div [ class "col" ]
                ([ h4 [] [ text "Tracking" ] ] ++ (List.map (\x -> editFlag bug "tracking" values x) (Dict.toList bug.flags_tracking)))
            , div [ class "col" ]
                ([ h4 [] [ text "Generic" ] ] ++ (List.map (\x -> editFlag bug "generic" values x) (Dict.toList bug.flags_generic)))
            , div [ class "form-group" ]
                [ textarea [ class "form-control", placeholder "Your comment", onInput (EditBug bug "comment") ] []
                ]
            , p [ class "text-warning", hidden (isSuccess bugzilla.check) ] [ text "You need to setup your Bugzilla account on the uplift dashboard before using this action." ]
            , p [ class "actions" ]
                [ button [ class "btn btn-success", disabled (not (isSuccess bugzilla.check) || bug.update == Loading) ]
                    [ text
                        (if bug.update == Loading then
                            "Loading..."
                         else
                            "Update bug"
                        )
                    ]
                , span [ class "btn btn-secondary", onClick (ShowBugEditor bug NoEditor) ] [ text "Cancel" ]
                ]
            ]


editApproval : Bug -> ( String, UpliftVersion ) -> Html Msg
editApproval bug ( name, version ) =
    div [ class "row" ]
        [ div [ class "col-xs-12" ]
            [ label [ class "checkbox" ]
                [ input [ type_ "checkbox", onCheck (EditUplift bug version) ] []
                , text version.name
                ]
            ]
        ]


viewApprovalEditor : Bugzilla.Model -> Bug -> Html Msg
viewApprovalEditor bugzilla bug =
    -- Show the form to approve the uplift request
    let
        -- Only show non processed versions
        versions =
            Dict.filter (\k v -> v.status == "?") bug.uplift_versions

        btn_disabled =
            not (isSuccess bugzilla.check) || Dict.empty == bug.attachments || bug.update == Loading
    in
        Html.form [ class "editor", onSubmit (PublishEdits bug) ]
            [ div [ class "col-xs-12" ]
                ([ h4 []
                    [ text
                        (if bug.editor == ApprovalEditor then
                            "Approve uplift"
                         else
                            "Reject uplift"
                        )
                    ]
                 ]
                    ++ (List.map (\x -> editApproval bug x) (Dict.toList versions))
                )
            , div [ class "form-group" ]
                [ textarea [ class "form-control", placeholder "Your comment", onInput (EditBug bug "comment") ] []
                ]
            , p [ class "text-warning", hidden (isSuccess bugzilla.check) ] [ text "You need to setup your Bugzilla account on the uplift dashboard before using this action." ]
            , p [ class "text-warning", hidden (not (Dict.empty == bug.attachments)) ] [ text "You need to pick at least one version." ]
            , p [ class "actions" ]
                [ if bug.editor == ApprovalEditor then
                    button [ class "btn btn-success", disabled btn_disabled ]
                        [ text
                            (if bug.update == Loading then
                                "Loading..."
                             else
                                "Approve uplift"
                            )
                        ]
                  else
                    button [ class "btn btn-danger", disabled btn_disabled ]
                        [ text
                            (if bug.update == Loading then
                                "Loading..."
                             else
                                "Reject uplift"
                            )
                        ]
                , span [ class "btn btn-secondary", onClick (ShowBugEditor bug NoEditor) ] [ text "Cancel" ]
                ]
            ]
