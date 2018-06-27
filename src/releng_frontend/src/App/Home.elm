module App.Home exposing (..)

import App
import App.Notifications.Types
import App.TreeStatus.Types
import Html exposing (..)
import Html.Attributes exposing (..)
import Utils


viewCard : String -> String -> Attribute msg -> Html msg
viewCard title description href =
    div [ class "col-sm-6" ]
        [ a
            [ class "card card-block"
            , href
            ]
            [ h4 [ class "card-title" ]
                [ text title ]
            , p [ class "card-text" ]
                [ text description ]
            ]
        ]


view : App.Model -> Html App.Msg
view model =
    div [ class "row" ]
        [ viewCard
            "TryChooser"
            "Generate parts of try syntax and restrict tests to certain directories."
            (href "/trychooser")
        , viewCard
            "TreeStatus"
            "Current status of Mozilla's version-control repositories."
            (Utils.onClick <| App.NavigateTo (App.TreeStatusRoute App.TreeStatus.Types.ShowTreesRoute))
        , viewCard
            "Tokens"
            "Tokens are used to allow automated services to authenticate to Releng API without being tied to a user's identity."
            (href "/trychooser")
        , viewCard
            "ToolTool"
            "Tooltool is tool for fetching binary artifacts for builds and tests. The web interface lets you browse the files currently available from the service."
            (href "/tooltool")
        , viewCard
            "Notifications"
            "Manage notification policies and preferences for RelEng Notification services (aka NagBot)."
            (Utils.onClick <| App.NavigateTo (App.NotificationRoute App.Notifications.Types.BaseRoute))
        ]
