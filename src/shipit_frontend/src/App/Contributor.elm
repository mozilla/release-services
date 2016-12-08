module App.Contributor exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Json.Decode as Json exposing (Decoder, (:=))
import Html.Events exposing (onClick, onInput, onSubmit)
import Utils exposing (onChange)
import String
import Dialog


type Msg
    = Edit Contributor
    | Cancel
    | SetValue FormValue String


type FormValue
    = CommentPrivate
    | CommentPublic
    | Karma


type alias Model =
    -- TODO: skip dictionnary
    { contributor : Maybe Contributor
    }


type alias Contributor =
    { email : String
    , name : String
    , avatar : String
    , roles : List String
    , karma : Int
    , comment_private : String
    , comment_public : String
    }


init : ( Model, Cmd Msg )
init =
    ( { contributor = Nothing
      }
    , Cmd.none
    )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Edit contributor ->
            ( { model | contributor = Just contributor }
            , Cmd.none
            )

        Cancel ->
            ( { model | contributor = Nothing }
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
                                    Just { contributor | comment_private = value }

                        Nothing ->
                            Nothing
            in
                ( { model | contributor = newContributor }
                , Cmd.none
                )



-- Decode from json api


decodeContributor : Decoder Contributor
decodeContributor =
    Json.object7 Contributor
        ("email" := Json.string)
        ("name" := Json.string)
        ("avatar" := Json.string)
        ("roles" := Json.list Json.string)
        -- TODO: use api data
        (Json.succeed 0)
        (Json.succeed "")
        (Json.succeed "")



-- Display modal when a contributor is selected


viewModal : Model -> Html Msg
viewModal model =
    Dialog.view
        (case model.contributor of
            Just contributor ->
                Just (dialogConfig contributor)

            Nothing ->
                Nothing
        )



-- Modal configuration to edit a contributor


dialogConfig : Contributor -> Dialog.Config Msg
dialogConfig contributor =
    { closeMessage = Just Cancel
    , containerClass = Nothing
    , header = Just (h3 [] [ text ("Update " ++ contributor.name) ])
    , body = Just (viewForm contributor)
    , footer =
        Just
            (div []
                [ button
                    [ class "btn"
                    , onClick Cancel
                    ]
                    [ text "Cancel" ]
                , button
                    [ class "btn btn-primary" ]
                    [ text "Update Contributor" ]
                ]
            )
    }



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
        Html.form [ class "form" ]
            [ div [ class "form-group row" ]
                [ label [ class "col-sm-4 col-form-label" ] [ text "Karma" ]
                , div [ class "col-sm-8" ]
                    [ select [ class "form-control form-control-sm", onChange (SetValue Karma) ]
                        (List.map (\( x, name ) -> option [ selected (x == (toString contributor.karma)), value x ] [ text name ]) possible_values)
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
                    [ textarea [ class "form-control", placeholder "A private comment, visible only by admins.", onInput (SetValue CommentPrivate) ] [ text contributor.comment_private ]
                    ]
                ]
            ]



-- View details for a contributor


viewContributor : Model -> Contributor -> Html Msg
viewContributor model contributor =
    div [ class "user row" ]
        [ div [ class "pull-sm-left col-sm-2 hidden-xs" ]
            [ img [ class "avatar img-fluid img-rounded", src contributor.avatar ] []
            ]
        , div [ class "col-xs-8 col-sm-10" ]
            [ p [ class "lead" ] [ text contributor.name ]
            , p []
                [ a [ href ("mailto:" ++ contributor.email) ] [ text contributor.email ] ]
            , p []
                [ strong [ title contributor.comment_public ] [ text "Karma: " ]
                , span [] [ text (toString contributor.karma) ]
                , button [ class "btn btn-outline-danger btn-sm", onClick (Edit contributor) ]
                    [ text "Edit" ]
                ]
            , p []
                (List.map
                    (\role ->
                        case role of
                            "creator" ->
                                span [ class "tag tag-success" ] [ text "Bug author" ]

                            "reviewer" ->
                                span [ class "tag tag-info" ] [ text "Reviewer" ]

                            "assignee" ->
                                span [ class "tag tag-danger" ] [ text "Assignee" ]

                            "uplift_author" ->
                                span [ class "tag tag-warning" ] [ text "Uplift author" ]

                            _ ->
                                span [ class "tag tag-default" ] [ text role ]
                    )
                    contributor.roles
                )
            ]
        ]
