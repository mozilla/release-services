module App.Types exposing (..)

import UrlParser


type alias Page a b =
    { title : String
    , description : String
    , matcher : UrlParser.Parser (a -> b) b
    }


type alias ResponseError =
    { type_ : String
    , detail : String
    , status : Int
    , title : String
    }


type AlertType
    = AlertSuccess
    | AlertInfo
    | AlertWarning
    | AlertDanger


type alias Alert =
    { type_ : AlertType
    , title : String
    , text : String
    }
