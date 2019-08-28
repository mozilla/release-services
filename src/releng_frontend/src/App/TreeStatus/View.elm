module App.TreeStatus.View exposing (..)

import App.Form
import App.TreeStatus.Form
import App.TreeStatus.Types
import App.UserScopes
import App.Utils
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import RemoteData
import String
import TaskclusterLogin
import Utils


hasScope : String -> List String -> Bool
hasScope scope scopes =
    App.UserScopes.hasScope scopes ("project:releng:treestatus/" ++ scope)


onClickGoTo : App.TreeStatus.Types.Route -> Attribute App.TreeStatus.Types.Msg
onClickGoTo route =
    Utils.onClick (App.TreeStatus.Types.NavigateTo route)


bugzillaBugAsLink : String -> List (Html a)
bugzillaBugAsLink text_ =
    let
        words =
            String.words text_

        previousWords =
            Nothing :: List.map Just words
    in
    List.map2 (\x y -> ( x, y )) previousWords words
        |> List.filter (\( _, word ) -> word /= "Bug")
        |> List.map
            (\( previousWord, number ) ->
                if previousWord == Just "Bug" then
                    a [ href ("https://bugzilla.mozilla.org/show_bug.cgi?id=" ++ number) ]
                        [ text ("Bug " ++ number) ]
                else
                    text (" " ++ number ++ " ")
            )


viewRecentChangeTree : String -> App.TreeStatus.Types.RecentChangeTree -> Html App.TreeStatus.Types.Msg
viewRecentChangeTree status tree =
    li []
        [ em [] [ text tree.tree ]
        , span [] [ text " from " ]
        , span
            [ class ("badge badge-" ++ App.Utils.treeStatusLevel tree.last_state.status) ]
            [ text tree.last_state.status ]
        , span [] [ text " to " ]
        , span
            [ class ("badge badge-" ++ App.Utils.treeStatusLevel status) ]
            [ text status ]
        ]


viewRecentChange :
    List String
    ->
        { a
            | id : Int
            , reason : String
            , trees : List App.TreeStatus.Types.RecentChangeTree
            , when : String
            , who : String
            , status : String
        }
    -> List (Html App.TreeStatus.Types.Msg)
viewRecentChange scopes recentChange =
    let
        reason =
            bugzillaBugAsLink recentChange.reason

        parseTimestamp timestamp =
            timestamp
                |> String.split "T"
                |> List.drop 1
                |> List.take 1
                |> List.append
                    (timestamp
                        |> String.split "T"
                        |> List.take 1
                    )
                |> String.join " "
                |> String.split "."
                |> List.head
                |> Maybe.withDefault timestamp
    in
    if hasScope "recent_changes/revert" scopes then
        [ div
            [ class "list-group-item justify-content-between" ]
            [ div
                []
                [ p
                    []
                    [ text "At "
                    , em [] [ text (parseTimestamp recentChange.when) ]
                    , b [] [ text (" " ++ TaskclusterLogin.shortUsername recentChange.who) ]
                    , text " changed trees:"
                    ]
                , ul
                    []
                    (List.map (viewRecentChangeTree recentChange.status) recentChange.trees)
                , if List.isEmpty reason then
                    text ""
                  else
                    p [] [ text "With reason: ", b [] reason ]
                ]
            , div
                [ class "btn-group" ]
                [ button
                    [ type_ "button"
                    , class "btn btn-sm btn-outline-success"
                    , Utils.onClick (App.TreeStatus.Types.RevertChange recentChange.id)
                    ]
                    [ text "Restore" ]
                , button
                    [ type_ "button"
                    , class "btn btn-sm btn-outline-warning"
                    , Utils.onClick (App.TreeStatus.Types.DiscardChange recentChange.id)
                    ]
                    [ text "Discard" ]
                ]
            ]
        ]
    else
        []


viewRecentChanges :
    List String
    -> RemoteData.WebData (List App.TreeStatus.Types.RecentChange)
    -> List (Html App.TreeStatus.Types.Msg)
viewRecentChanges scopes recentChanges =
    case recentChanges of
        RemoteData.Success data ->
            let
                title =
                    if List.isEmpty data then
                        []
                    else
                        [ h2 [] [ text "Recent Changes" ] ]

                recentChanges =
                    data
                        |> List.map (viewRecentChange scopes)
                        |> List.concat
            in
            [ div
                [ id "treestatus-recentchanges"
                , class "list-group"
                ]
                ([]
                    |> App.Utils.appendItems title
                    |> App.Utils.appendItems recentChanges
                )
            ]

        _ ->
            []


viewTreesCategoryItem :
    List String
    -> List String
    -> { a | reason : String, status : String, name : String, tags : List String }
    -> Html App.TreeStatus.Types.Msg
viewTreesCategoryItem scopes treesSelected tree =
    let
        isChecked =
            List.member tree.name treesSelected

        checking checked =
            case checked of
                True ->
                    App.TreeStatus.Types.SelectTree tree.name

                False ->
                    App.TreeStatus.Types.UnselectTree tree.name

        openTree =
            App.TreeStatus.Types.ShowTreeRoute tree.name
                |> App.TreeStatus.Types.NavigateTo

        treeTagClass =
            "float-xs-right badge badge-" ++ App.Utils.treeStatusLevel tree.status

        checkboxItem =
            if hasScope "trees/update" scopes || hasScope "trees/delete" scopes then
                [ label
                    [ class "custom-control custom-checkbox" ]
                    [ input
                        [ type_ "checkbox"
                        , class "custom-control-input"
                        , checked isChecked
                        , onCheck checking
                        ]
                        []
                    , span
                        [ class "custom-control-indicator" ]
                        []
                    ]
                ]
            else
                []

        itemClass =
            if hasScope "trees/update" scopes || hasScope "trees/delete" scopes then
                "list-group-item list-group-item-with-checkbox"
            else
                "list-group-item"

        treeItem =
            a
                [ href "#"
                , class "list-group-item-action"
                , Utils.onClick openTree
                ]
                ([]
                    |> List.append
                        (if tree.reason == "" then
                            []
                         else
                            [ p [ class "list-group-item-text" ]
                                [ text tree.reason ]
                            ]
                        )
                    |> List.append
                        [ h5 [ class "list-group-item-heading" ]
                            [ text tree.name
                            , span [ style [ ( "margin-left", "1em" ) ] ]
                                (List.map
                                    (\tag ->
                                        span
                                            [ class "badge badge-default" ]
                                            [ App.TreeStatus.Types.possibleTreeTags
                                                |> List.filterMap
                                                    (\( x, y ) ->
                                                        if x == tag then
                                                            Just y
                                                        else
                                                            Nothing
                                                    )
                                                |> List.head
                                                |> Maybe.withDefault tag
                                                |> text
                                            ]
                                    )
                                    tree.tags
                                )
                            , span [ class treeTagClass ]
                                [ text tree.status ]
                            ]
                        ]
                )
    in
    div [ class itemClass ]
        (List.append checkboxItem [ treeItem ])


type Category
    = Development
    | ReleaseStabilization
    | Try
    | CommRepositories
    | Other


categoryTitle : Category -> String
categoryTitle category =
    case category of
        Development ->
            "Development"

        ReleaseStabilization ->
            "Release Stabilization"

        Try ->
            "Try"

        CommRepositories ->
            "Comm Repositories"

        Other ->
            "Other"


categorizeTrees :
    App.TreeStatus.Types.Trees
    -> List ( Category, App.TreeStatus.Types.Trees )
categorizeTrees trees =
    let
        ( developmentTrees, developmentTreesOther ) =
            List.partition
                (\tree ->
                    List.member tree.name
                        [ "autoland"
                        , "mozilla-inbound"
                        , "mozilla-central"
                        ]
                )
                trees

        ( releaseStabilizationTrees, releaseStabilizationTreesOther ) =
            List.partition
                (\tree ->
                    List.member tree.name
                        [ "mozilla-beta"
                        , "mozilla-release"
                        , "mozilla-esr60"
                        , "mozilla-esr52"
                        ]
                )
                developmentTreesOther

        ( tryTrees, tryTreesOther ) =
            List.partition
                (\tree ->
                    List.member tree.name
                        [ "try"
                        , "try-comm-central"
                        , "nss-try"
                        ]
                )
                releaseStabilizationTreesOther

        ( commRepositoriesTrees, otherTrees ) =
            List.partition
                (\tree ->
                    List.member tree.name
                        [ "comm-central-thunderbird"
                        , "comm-central-seamonkey"
                        , "comm-beta-thunderbird"
                        , "comm-beta-seamonkey"
                        , "comm-release-thunderbird"
                        , "comm-release-seamonkey"
                        , "comm-esr60-thunderbird"
                        , "comm-esr60-seamonkey"
                        , "comm-esr52-thunderbird"
                        , "comm-esr52-seamonkey"
                        ]
                )
                tryTreesOther
    in
    [ ( Development, developmentTrees )
    , ( ReleaseStabilization, releaseStabilizationTrees )
    , ( Try, tryTrees )
    , ( CommRepositories, commRepositoriesTrees )
    , ( Other, otherTrees )
    ]


viewTreesCategory :
    List String
    -> List String
    -> ( Category, App.TreeStatus.Types.Trees )
    -> List (Html App.TreeStatus.Types.Msg)
viewTreesCategory scopes treesSelected ( category, trees ) =
    if List.isEmpty trees then
        []
    else
        [ h4 [] [ text (categoryTitle category) ]
        , div
            [ id "treestatus-trees"
            , class "list-group"
            ]
            (trees
                |> List.sortBy .name
                |> List.map (viewTreesCategoryItem scopes treesSelected)
                |> (\x ->
                        [ div
                            [ id "treestatus-trees"
                            , class "list-group"
                            ]
                            x
                        ]
                   )
            )
        ]


viewTrees :
    List String
    -> RemoteData.WebData App.TreeStatus.Types.Trees
    -> List String
    -> List (Html App.TreeStatus.Types.Msg)
viewTrees scopes trees treesSelected =
    case trees of
        RemoteData.Success trees ->
            categorizeTrees trees
                |> List.map (viewTreesCategory scopes treesSelected)
                |> List.concat

        RemoteData.Failure message ->
            [ App.Utils.error
                (App.TreeStatus.Types.NavigateTo App.TreeStatus.Types.ShowTreesRoute)
                (toString message)
            ]

        RemoteData.Loading ->
            [ App.Utils.loading ]

        RemoteData.NotAsked ->
            []


viewButtons :
    App.TreeStatus.Types.Route
    -> List String
    -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
    -> Html App.TreeStatus.Types.Msg
viewButtons route scopes model =
    let
        allSelected =
            List.length (RemoteData.withDefault [] model.trees)
                == List.length model.treesSelected

        appendIf condition button =
            if condition then
                App.Utils.appendItem button
            else
                List.append []

        treeRoute =
            case route of
                App.TreeStatus.Types.ShowTreeRoute name ->
                    Just name

                _ ->
                    Nothing
    in
    div
        [ id "treestatus-trees-buttons"
        , class "btn-group"
        ]
        ([]
            |> appendIf
                (route /= App.TreeStatus.Types.ShowTreesRoute)
                (button
                    [ class "btn btn-outline-info btn-sm btn-pill"
                    , onClickGoTo App.TreeStatus.Types.ShowTreesRoute
                    ]
                    [ text "Show All Trees" ]
                )
            |> appendIf
                (route
                    == App.TreeStatus.Types.ShowTreesRoute
                    && (hasScope "trees/delete" scopes || hasScope "trees/update" scopes)
                )
                (button
                    [ class "btn btn-outline-info btn-sm btn-pill"
                    , Utils.onClick
                        (if allSelected then
                            App.TreeStatus.Types.UnselectAllTrees
                         else
                            App.TreeStatus.Types.SelectAllTrees
                        )
                    ]
                    [ text
                        (if allSelected then
                            "Unselect all trees"
                         else
                            "Select all trees"
                        )
                    ]
                )
            |> appendIf
                (route
                    == App.TreeStatus.Types.ShowTreesRoute
                    && hasScope "trees/create" scopes
                )
                (button
                    [ class "btn btn-outline-success btn-sm btn-pill"
                    , onClickGoTo App.TreeStatus.Types.AddTreeRoute
                    ]
                    [ text "Add Tree" ]
                )
            |> appendIf
                ((route == App.TreeStatus.Types.ShowTreesRoute || treeRoute /= Nothing)
                    && hasScope "trees/update" scopes
                )
                (button
                    (if List.isEmpty model.treesSelected then
                        [ class "btn btn-outline-primary btn-sm btn-pill tooltip2"
                        , disabled (List.isEmpty model.treesSelected)
                        , title "You need to select some trees"
                        ]
                     else
                        [ class "btn btn-outline-primary btn-sm btn-pill"
                        , onClickGoTo App.TreeStatus.Types.UpdateTreesRoute
                        ]
                    )
                    [ text
                        ("Update "
                            ++ (if treeRoute == Nothing then
                                    "Tree(s)"
                                else
                                    "Tree"
                               )
                        )
                    ]
                )
            |> appendIf
                ((route == App.TreeStatus.Types.ShowTreesRoute || treeRoute /= Nothing)
                    && hasScope "trees/delete" scopes
                )
                (button
                    (if List.isEmpty model.treesSelected then
                        [ class "btn btn-outline-danger btn-sm btn-pill tooltip2"
                        , disabled (List.isEmpty model.treesSelected)
                        , title "You need to select some trees"
                        ]
                     else
                        [ class "btn btn-outline-danger btn-sm btn-pill"
                        , onClickGoTo App.TreeStatus.Types.DeleteTreesRoute
                        ]
                    )
                    [ text
                        ("Delete "
                            ++ (if treeRoute == Nothing then
                                    "Tree(s)"
                                else
                                    "Tree"
                               )
                        )
                    ]
                )
        )


viewConfirmDelete :
    Maybe String
    -> Bool
    -> List String
    -> List (Html App.TreeStatus.Types.Msg)
viewConfirmDelete deleteError deleteTreesConfirm treesSelected =
    [ div
        [ id "treestatus-form" ]
        [ div
            []
            ([]
                |> App.Utils.appendItem
                    (text "You are about to delete the following trees:")
                |> App.Utils.appendItem
                    (treesSelected
                        |> List.map (\x -> li [] [ text x ])
                        |> ul []
                    )
            )
        , hr [] []
        , div
            [ class ("form-group " ++ App.Form.errorClass deleteError) ]
            ([]
                |> App.Utils.appendItem
                    (label
                        [ class "custom-control custom-checkbox" ]
                        [ input
                            [ type_ "checkbox"
                            , class "custom-control-input"
                            , checked deleteTreesConfirm
                            , onCheck (\x -> App.TreeStatus.Types.DeleteTreesConfirmToggle)
                            ]
                            []
                        , span
                            [ class "custom-control-indicator" ]
                            []
                        , span
                            [ class "custom-control-description" ]
                            [ text "I acknowledge this action is irreversible." ]
                        ]
                    )
            )
        , hr [] []
        , button
            [ class "btn btn-outline-danger"
            , Utils.onClick App.TreeStatus.Types.DeleteTrees
            ]
            [ text "Delete" ]
        , div [ class "clearfix" ] []
        ]
    ]


viewTreesTitle : App.TreeStatus.Types.Route -> Html msg
viewTreesTitle route =
    case route of
        App.TreeStatus.Types.ShowTreesRoute ->
            h2 [ class "float-xs-left" ] [ text "Trees" ]

        App.TreeStatus.Types.AddTreeRoute ->
            h2 [ class "float-xs-left" ] [ text "Add Tree" ]

        App.TreeStatus.Types.UpdateTreesRoute ->
            h2 [ class "float-xs-left" ] [ text "Update Tree(s)" ]

        App.TreeStatus.Types.DeleteTreesRoute ->
            h2 [ class "float-xs-left" ] [ text "Delete Tree(s)" ]

        App.TreeStatus.Types.ShowTreeRoute name ->
            h2 [ class "float-xs-left" ] [ text ("Tree: " ++ name) ]


treeRulesLink : String -> String
treeRulesLink treeName =
    case treeName of
        "autoland" ->
            "https://wiki.mozilla.org/Tree_Rules#autoland.2FLando"

        "mozilla-inbound" ->
            "https://wiki.mozilla.org/Tree_Rules#mozilla-inbound"

        "mozilla-central" ->
            "https://wiki.mozilla.org/Tree_Rules#mozilla-central_.28Nightly_channel.29"

        "mozilla-beta" ->
            "https://wiki.mozilla.org/Tree_Rules#mozilla-beta"

        "mozilla-release" ->
            "https://wiki.mozilla.org/Tree_Rules#mozilla-release"

        _ ->
            if String.startsWith "mozilla-esr" treeName then
                "https://wiki.mozilla.org/Release_Management/ESR_Landing_Process"
            else if String.startsWith "comm-" treeName then
                "https://wiki.mozilla.org/Tree_Rules/comm-central"
            else
                "https://wiki.mozilla.org/Tree_Rules"


viewTreeDetails :
    RemoteData.RemoteData a { b | message_of_the_day : String, name : String, status : String }
    -> Html App.TreeStatus.Types.Msg
viewTreeDetails remote =
    case remote of
        RemoteData.Success tree ->
            div
                [ id "treestatus-tree-details" ]
                [ span
                    []
                    [ text tree.name ]
                , text " status is "
                , span
                    [ class ("badge badge-" ++ App.Utils.treeStatusLevel tree.status) ]
                    [ text tree.status ]
                , p [ class "lead" ] (bugzillaBugAsLink tree.message_of_the_day)
                , p [] [ a [ href (treeRulesLink tree.name) ] [ text "Tree rules" ] ]
                ]

        RemoteData.Failure message ->
            App.Utils.error (App.TreeStatus.Types.NavigateTo App.TreeStatus.Types.ShowTreesRoute) (toString message)

        RemoteData.Loading ->
            App.Utils.loading

        RemoteData.NotAsked ->
            text ""


viewTreeLog :
    App.TreeStatus.Types.TreeLog
    -> Html App.TreeStatus.Types.Msg
viewTreeLog log =
    let
        who2 =
            if String.startsWith "human:" log.who then
                log.who
                    |> String.dropLeft 6
            else
                log.who

        who =
            who2
                |> String.split "@"
                |> List.head
                |> Maybe.withDefault who2
    in
    div [ class "timeline-item" ]
        --TODO: show status in hover of the badge
        [ div [ class <| "timeline-badge badge-" ++ App.Utils.treeStatusLevel log.status ]
            [ text " " ]
        , div [ class "timeline-panel" ]
            [ div [ class "timeline-time" ]
                [ text log.when ]
            , h5 [] [ text who ]
            , p [] [ text log.reason ]
            , p
                []
                (List.map
                    (\tag ->
                        span
                            [ class "badge badge-default" ]
                            [ App.TreeStatus.Types.possibleTreeTags
                                |> List.filterMap
                                    (\( x, y ) ->
                                        if x == tag then
                                            Just y
                                        else
                                            Nothing
                                    )
                                |> List.head
                                |> Maybe.withDefault tag
                                |> text
                            ]
                    )
                    log.tags
                )
            ]
        ]


viewTreeLogs :
    String
    -> RemoteData.WebData App.TreeStatus.Types.TreeLogs
    -> RemoteData.WebData App.TreeStatus.Types.TreeLogs
    -> Html App.TreeStatus.Types.Msg
viewTreeLogs name treeLogs_ treeLogsAll_ =
    let
        ( moreButton, treeLogsAll ) =
            case treeLogsAll_ of
                RemoteData.Success treeLogs ->
                    ( []
                    , List.drop 5 treeLogs
                    )

                RemoteData.Failure message ->
                    ( [ App.Utils.error (App.TreeStatus.Types.NavigateTo App.TreeStatus.Types.ShowTreesRoute) (toString message) ]
                    , []
                    )

                RemoteData.Loading ->
                    ( [ button
                            [ class "btn btn-secondary"
                            , Utils.onClick <| App.TreeStatus.Types.GetTreeLogs name True
                            ]
                            [ text "Loading"
                            , i [ class "fa fa-circle-o-notch fa-spin" ] []
                            ]
                      ]
                    , []
                    )

                RemoteData.NotAsked ->
                    ( [ button
                            [ class "btn btn-secondary"
                            , Utils.onClick <| App.TreeStatus.Types.GetTreeLogs name True
                            ]
                            [ text "Load more" ]
                      ]
                    , []
                    )
    in
    case treeLogs_ of
        RemoteData.Success treeLogs ->
            div [ class "timeline" ]
                (List.append
                    (List.append
                        (List.map viewTreeLog treeLogs)
                        (List.map viewTreeLog treeLogsAll)
                    )
                    [ div [ class "timeline-item timeline-more" ]
                        [ div [ class "timeline-panel" ] moreButton ]
                    ]
                )

        RemoteData.Failure message ->
            App.Utils.error (App.TreeStatus.Types.NavigateTo App.TreeStatus.Types.ShowTreesRoute) (toString message)

        RemoteData.Loading ->
            App.Utils.loading

        RemoteData.NotAsked ->
            text ""


viewTree :
    List String
    -> RemoteData.WebData App.TreeStatus.Types.Tree
    -> RemoteData.WebData App.TreeStatus.Types.TreeLogs
    -> RemoteData.WebData App.TreeStatus.Types.TreeLogs
    -> String
    -> List (Html App.TreeStatus.Types.Msg)
viewTree scopes tree treeLogs treeLogsAll name =
    [ div
        [ id "treestatus-form" ]
        [ viewTreeDetails tree
        , hr [] []
        , viewTreeLogs name treeLogs treeLogsAll
        ]
    ]
