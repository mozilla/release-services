module App.Home exposing (..)

import App
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
            "TreeStatus"
            "Current status of Mozilla's version-control repositories."
            (Utils.onClick <| App.NavigateTo (App.TreeStatusRoute App.TreeStatus.Types.ShowTreesRoute))
        , viewCard
            "ToolTool"
            "Tooltool is tool for fetching binary artifacts for builds and tests. The web interface lets you browse the files currently available from the service."
            (href "/tooltool")
        ]
