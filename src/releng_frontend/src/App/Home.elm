module App.Home exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)


view model =
    div [ class "row" ]
        [ div [ class "col-sm-3" ]
              [ a [ class "card card-block"
                  , href "/trychooser"
                  ]
                  [ h4 [ class "card-title" ] [ text "TryChooser" ]
                  , p [ class "card-text" ]
                      [ text "Generate parts of try syntax and restrict tests to certain directories." ]
                  ]
              ]
        ]




