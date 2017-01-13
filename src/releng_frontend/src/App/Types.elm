module App.Types exposing (..)

import UrlParser
import Hop.Types


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



-- XXX: probably should not be in this module


hopConfig : Hop.Types.Config
hopConfig =
    { hash = False
    , basePath = ""
    }
