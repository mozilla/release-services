port module Hawk exposing (..)

{-}

Depends on:
 - User.elm
 - evancz/elm-http
 - elm-lang/core

To be able to make hawk enabled requests

-}
import Http
import User

type alias Request =
    { user : User.Model
    , verb : String
    , headers : List (String, String)
    , url : String
    , body : Http.Body
    }

type alias Header = String

type Msg
    = BuildHeader Request
    | HeaderBuilt Header Request 


update : Msg -> model -> (model, Cmd Msg)
update msg model = 
    case msg of
        BuildHeader request ->
            ( model, hawk_build request )
        HeaderBuilt header request ->
            ( model
            , Http.send Http.defaultSettings
                { request | headers = request.headers ++
                               [ ( "Authorization", header),
                                 ( "Accept", "application/json" ),
                                 ( "Content-Type", "application/json" )
                               ]
                }

            )


send : Request -> Cmd Msg
send request =
    Cmd.map <| BuildHeader request


-- TODO: implement getStrin/get/post aka HIGH-LEVEL REQUESTS from
-- evancz/elm-http



port hawk_get_header : (Maybe Response -> msg) -> Sub msg
port hawk_build_header : Request -> Cmd msg
