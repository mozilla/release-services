module App.Contributor exposing (..)

import Dialog
import Hawk
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onClick, onInput, onSubmit)
import Http
import Json.Decode as Json exposing (Decoder)
import Json.Encode as JsonEncode
import RemoteData as RemoteData exposing (RemoteData(Failure, Loading, NotAsked, Success), WebData, isSuccess)
import String
import TaskclusterLogin as User
import Utils exposing (decodeJsonString, onChange)


type Msg
    = Edit Contributor
    | Cancel
    | SetValue FormValue String
    | UpdateContributor
    | UpdatedContributor (WebData String)
      -- Hawk Extension
    | HawkRequest Hawk.Msg


type FormValue
    = CommentPrivate
    | CommentPublic
    | Karma


type alias Model =
    { contributor : Maybe Contributor
    , update : WebData Contributor
    , backend_uplift_url : String
    }


type alias Contributor =
    { id : Int
    , email : String
    , name : String
    , avatar : String
    , roles : List String
    , karma : Int
    , comment_private : Maybe String
    , comment_public : String
    }


init : String -> ( Model, Cmd Msg )
init backend_uplift_url =
    ( { contributor = Nothing
      , update = NotAsked
      , backend_uplift_url = backend_uplift_url
      }
    , Cmd.none
    )


update : Msg -> Model -> User.Model -> ( Model, Cmd Msg )
update msg model user =
    case msg of
        HawkRequest hawkMsg ->
            ( model, Cmd.none )

        Edit contributor ->
            ( { model | contributor = Just contributor, update = NotAsked }
            , Cmd.none
            )

        Cancel ->
            ( { model | contributor = Nothing, update = NotAsked }
            , Cmd.none
            )

        SetValue formValue value ->
            let
                newContributor =
                    case model.contributor of
                        Just contributor ->
                            case formValue of
                                Karma ->
                                    case String.toInt value of
                                        Ok karma ->
                                            Just { contributor | karma = karma }

                                        Err _ ->
                                            Just contributor

                                CommentPublic ->
                                    Just { contributor | comment_public = value }

                                CommentPrivate ->
                                    Just { contributor | comment_private = Just value }

                        Nothing ->
                            Nothing
            in
                ( { model | contributor = newContributor }
                , Cmd.none
                )

        UpdateContributor ->
            ( model
            , sendUpdate model user
            )

        UpdatedContributor response ->
            ( { model | update = decodeJsonString decodeContributor response }
            , Cmd.none
            )


sendUpdate : Model -> User.Model -> Cmd Msg
sendUpdate model user =
    -- Send updated contributor to backend
    case user of
        Just credentials ->
            case model.contributor of
                Just contributor ->
                    let
                        url =
                            model.backend_uplift_url ++ "/contributor/" ++ toString contributor.id

                        body =
                            Http.jsonBody (encodeContributor contributor)

                        request =
                            Hawk.Request "Contributor" "PUT" url [] body
                    in
                        Cmd.map HawkRequest
                            (Hawk.send request credentials)

                Nothing ->
                    Cmd.none

        Nothing ->
            -- No credentials
            Cmd.none



-- Decode from json api


decodeContributor : Decoder Contributor
decodeContributor =
    Json.map8 Contributor
        (Json.field "id" Json.int)
        (Json.field "email" Json.string)
        (Json.field "name" Json.string)
        (Json.field "avatar" Json.string)
        (Json.oneOf
            [ Json.field "roles" (Json.list Json.string)
            , Json.succeed []
              -- no roles on updates
            ]
        )
        (Json.field "karma" Json.int)
        (Json.maybe (Json.field "comment_private" Json.string))
        (Json.field "comment_public" Json.string)


encodeContributor : Contributor -> JsonEncode.Value
encodeContributor contributor =
    -- Only send karma related data
    case contributor.comment_private of
        Just comment_private ->
            JsonEncode.object
                [ ( "id", JsonEncode.int contributor.id )
                , ( "karma", JsonEncode.int contributor.karma )
                , ( "comment_private", JsonEncode.string comment_private )
                , ( "comment_public", JsonEncode.string contributor.comment_public )
                ]

        Nothing ->
            JsonEncode.null



-- Display modal when a contributor is selected


viewModal : Model -> Html Msg
viewModal model =
    Dialog.view
        (case model.contributor of
            Just contributor ->
                Just (dialogConfig contributor model.update)

            Nothing ->
                Nothing
        )



-- Modal configuration to edit a contributor


dialogConfig : Contributor -> WebData Contributor -> Dialog.Config Msg
dialogConfig contributor update =
    { closeMessage = Just Cancel
    , containerClass = Nothing
    , header = Just (h3 [] [ text "Update Contributor" ])
    , body =
        Just
            (div []
                [ viewUpdateStatus update
                , viewForm contributor
                ]
            )
    , footer =
        Just
            (div []
                [ button
                    [ class "btn"
                    , onClick Cancel
                    ]
                    [ text "Cancel" ]
                , button
                    [ class "btn btn-primary", onClick UpdateContributor ]
                    [ text "Update Contributor" ]
                ]
            )
    }


viewUpdateStatus : WebData Contributor -> Html Msg
viewUpdateStatus update =
    div [ class "row" ]
        [ div [ class "col-xs-12" ]
            [ case update of
                NotAsked ->
                    span [] []

                Loading ->
                    div [ class "alert alert-info" ] [ text "Loading..." ]

                Failure f ->
                    div [ class "alert alert-danger" ] [ text ("Failure: " ++ toString f) ]

                Success c ->
                    div [ class "alert alert-success" ] [ text "Successful update !" ]
            ]
        ]



-- Form to edit a contributor


viewForm : Contributor -> Html Msg
viewForm contributor =
    let
        possible_values =
            [ ( "-1", "Negative" )
            , ( "0", "Neutral" )
            , ( "1", "Positive" )
            ]
    in
        case contributor.comment_private of
            Just comment_private ->
                Html.form [ class "form", onSubmit UpdateContributor ]
                    [ div [ class "row" ]
                        [ div [ class "col-sm-2 hidden-xs" ]
                            [ img [ class "avatar img-fluid img-rounded", src contributor.avatar ] [] ]
                        , div [ class "col-xs-8 col-sm-10" ]
                            [ text contributor.name ]
                        ]
                    , div [ class "form-group row" ]
                        [ label [ class "col-sm-4 col-form-label" ] [ text "Karma" ]
                        , div [ class "col-sm-8" ]
                            [ select [ class "form-control form-control-sm", onChange (SetValue Karma) ]
                                (List.map (\( x, name ) -> option [ selected (x == toString contributor.karma), value x ] [ text name ]) possible_values)
                            ]
                        ]
                    , div [ class "form-group row" ]
                        [ label [ class "col-sm-4 col-form-label" ] [ text "Public comment" ]
                        , div [ class "col-sm-8" ]
                            [ textarea [ class "form-control", placeholder "A public comment, visible by everyone on RelMan.", onInput (SetValue CommentPublic) ] [ text contributor.comment_public ]
                            ]
                        ]
                    , div [ class "form-group row" ]
                        [ label [ class "col-sm-4 col-form-label" ] [ text "Private comment" ]
                        , div [ class "col-sm-8" ]
                            [ textarea [ class "form-control", placeholder "A private comment, visible only by admins.", onInput (SetValue CommentPrivate) ] [ text comment_private ]
                            ]
                        ]
                    ]

            Nothing ->
                div [ class "alert alert-danger" ] [ text "You are not an admin" ]



-- View details for a contributor


viewContributor : Model -> Contributor -> Html Msg
viewContributor model contributor =
    div [ class "contributor row" ]
        [ div [ class "pull-sm-left col-sm-2 hidden-xs" ]
            [ img [ class "avatar img-fluid img-rounded", src contributor.avatar ] []
            ]
        , div [ class "col-xs-8 col-sm-10" ]
            [ p [ class "lead" ]
                [ if contributor.karma < 0 then
                    span [ class "karma negative", title contributor.comment_public ] [ text "●" ]
                  else if contributor.karma > 0 then
                    span [ class "karma positive", title contributor.comment_public ] [ text "●" ]
                  else
                    span [ class "karma neutral", title contributor.comment_public ] [ text "●" ]
                , span [] [ text contributor.name ]
                , case contributor.comment_private of
                    Just _ ->
                        button [ class "btn btn-link btn-sm", onClick (Edit contributor) ] [ text "Edit" ]

                    Nothing ->
                        span [] []
                ]
            , p []
                [ a [ href ("mailto:" ++ contributor.email) ] [ text contributor.email ] ]
            , p []
                (List.map
                    (\role ->
                        case role of
                            "creator" ->
                                span [ class "badge badge-success" ] [ text "Bug author" ]

                            "reviewer" ->
                                span [ class "badge badge-info" ] [ text "Reviewer" ]

                            "assignee" ->
                                span [ class "badge badge-danger" ] [ text "Assignee" ]

                            "uplift_author" ->
                                span [ class "badge badge-warning" ] [ text "Uplift author" ]

                            _ ->
                                span [ class "badge badge-default" ] [ text role ]
                    )
                    contributor.roles
                )
            ]
        ]
