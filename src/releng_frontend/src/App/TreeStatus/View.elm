module App.TreeStatus.View exposing (..)

import App.TreeStatus.Form
import App.TreeStatus.Types
import App.UserScopes
import App.Form
import App.Utils
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import RemoteData
import String
import TaskclusterLogin
import Utils


hasScope scope scopes =
    App.UserScopes.hasScope scopes ("project:releng:treestatus/" ++ scope)


onClickGoTo route =
    Utils.onClick (App.TreeStatus.Types.NavigateTo route)


treeStatusLevel : String -> String
treeStatusLevel status =
    case status of
        "closed" ->
            "danger"

        "open" ->
            "success"

        "approval required" ->
            "warning"

        _ ->
            "default"


bugzillaBugAsLink : String -> List (Html a)
bugzillaBugAsLink text' =
    let
        words =
            String.words text'

        previousWords =
            Nothing :: (List.map Just words)

        asLink number =
            a [ href ("https://bugzilla.mozilla.org/show_bug.cgi?id=" ++ number) ]
                [ text ("Bug " ++ number) ]
    in
        List.map2 (\x y -> ( x, y )) previousWords words
            |> List.filter (\( x, y ) -> y /= "Bug")
            |> List.map
                (\( x, y ) ->
                    if x == Just "Bug" then
                        asLink y
                    else
                        text (" " ++ y ++ " ")
                )


viewRecentChange plural recentChange =
    let
        treeLabel =
            if plural then
                "trees "
            else
                "tree "

        recentChangeReason =
            let
                words =
                    bugzillaBugAsLink recentChange.reason
            in
                if List.isEmpty words then
                    []
                else
                    (text " with reason: ") :: words

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
        div
            [ class "list-group-item" ]
            [ div
                [ class "float-xs-right btn-group" ]
                [ button
                    [ type' "button"
                    , class "btn btn-sm btn-outline-success"
                    , Utils.onClick (App.TreeStatus.Types.RevertChange recentChange.id)
                    ]
                    [ text "Restore" ]
                , button
                    [ type' "button"
                    , class "btn btn-sm btn-outline-warning"
                    , Utils.onClick (App.TreeStatus.Types.DiscardChange recentChange.id)
                    ]
                    [ text "Discard" ]
                ]
            , div
                []
                (List.append
                    [ text "At "
                    , text (parseTimestamp recentChange.when)
                    , text (" " ++ (TaskclusterLogin.shortUsername recentChange.who))
                    , text " changed "
                    , text treeLabel
                    , em [] [ text (String.join ", " recentChange.trees) ]
                    , text " to "
                    , span
                        [ class ("tag tag-" ++ (treeStatusLevel recentChange.status)) ]
                        [ text recentChange.status ]
                    ]
                    recentChangeReason
                )
            ]


viewRecentChanges :
    RemoteData.WebData (List App.TreeStatus.Types.RecentChange)
    -> List (Html App.TreeStatus.Types.Msg)
viewRecentChanges recentChanges =
    case recentChanges of
        RemoteData.Success data ->
            let
                title =
                    if List.isEmpty data then
                        []
                    else
                        [ h2 [] [ text "Recent Changes" ] ]
            in
                []
                    |> App.Utils.appendItems title
                    |> App.Utils.appendItems
                        (List.map
                            (viewRecentChange (List.length data > 1))
                            data
                        )
                    |> (\x ->
                            [ div
                                [ id "treestatus-recentchanges"
                                , class "list-group"
                                ]
                                x
                            ]
                       )

        _ ->
            []


viewTreesItem scopes treesSelected tree =
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
            "float-xs-right tag tag-" ++ (treeStatusLevel tree.status)

        checkboxItem =
            if hasScope "trees/update" scopes || hasScope "trees/delete" scopes then
                [ label
                    [ class "custom-control custom-checkbox" ]
                    [ input
                        [ type' "checkbox"
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
                [ h5 [ class "list-group-item-heading" ]
                    [ text tree.name
                    , span [ class treeTagClass ]
                        [ text tree.status ]
                    ]
                , p [ class "list-group-item-text" ]
                    [ text tree.reason ]
                ]
    in
        div [ class itemClass ]
            (List.append checkboxItem [ treeItem ])


viewTrees :
    List String
    -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
    -> List (Html App.TreeStatus.Types.Msg)
viewTrees scopes model =
    case model.trees of
        RemoteData.Success trees ->
            trees
                |> List.sortBy .name
                |> List.map (viewTreesItem scopes model.treesSelected)
                |> div
                    [ id "treestatus-trees"
                    , class "list-group"
                    ]
                |> (\x -> [ x ])

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


viewConfirmDelete model =
    [ div
        [ id "treestatus-form" ]
        [ div
            []
            ([]
                |> App.Utils.appendItem
                    (text "You are about to delete the following trees:")
                |> App.Utils.appendItem
                    (model.treesSelected
                        |> List.map (\x -> li [] [ text x ])
                        |> ul []
                    )
            )
        , hr [] []
        , div
            [ class ("form-group " ++ (App.Form.errorClass model.deleteError)) ]
            ([]
                |> App.Utils.appendItem
                    (label
                        [ class "custom-control custom-checkbox" ]
                        [ input
                            [ type' "checkbox"
                            , class "custom-control-input"
                            , checked model.deleteTreesConfirm
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
                    [ class ("tag tag-" ++ (treeStatusLevel tree.status)) ]
                    [ text tree.status ]
                , p [ class "lead" ] (bugzillaBugAsLink tree.message_of_the_day)
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
            [ div [ class <| "timeline-badge tag-" ++ (treeStatusLevel log.status) ]
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
                                [ class "tag tag-default" ]
                                [ App.TreeStatus.Types.possibleTreeTags
                                    |> List.filterMap
                                        (\( x, _, y ) ->
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
    -> App.TreeStatus.Types.Model App.TreeStatus.Form.AddTree App.TreeStatus.Form.UpdateTree
    -> String
    -> List (Html App.TreeStatus.Types.Msg)
viewTree scopes model name =
    [ div
        [ id "treestatus-form" ]
        [ viewTreeDetails model.tree
        , hr [] []
        , viewTreeLogs name model.treeLogs model.treeLogsAll
        ]
    ]
