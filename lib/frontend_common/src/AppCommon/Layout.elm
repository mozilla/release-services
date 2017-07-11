module AppCommon.Layout exposing (Layout, init, toView, withContent, isLoading)


import Html exposing (..)
import AppCommon.Taskcluster


type alias Layout a =
    { loading : Bool
    , content : Maybe (Html a)
    , session : Maybe AppCommon.Taskcluster.Credentials
    }


init : Maybe AppCommon.Taskcluster.Credentials -> Layout a
init session =
    { loading = False
    , content = Nothing
    , session = session
    }


isLoading :  Layout a -> Layout a
isLoading layout =
    { layout | loading = True }


withContent : Html a -> Layout a -> Layout a
withContent content layout =
    { layout | content = Just content }


toView : Layout a -> Html a
toView layout =
    div [] [ text "layout works" ]
