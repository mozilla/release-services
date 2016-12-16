module App.Types exposing (..)

import UrlParser
import Hop.Types


type alias Page a b =
    { title : String
    , description : String
    , matcher : UrlParser.Parser (a -> b) b
    }



-- XXX: probably should not be in this module


hopConfig : Hop.Types.Config
hopConfig =
    { hash = False
    , basePath = ""
    }
