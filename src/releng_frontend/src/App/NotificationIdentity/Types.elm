-- DIFFERENT MODULE TYPES, MESSAGES, ETC HERE
module App.NotificationIdentity.Types exposing (..)

import RemoteData exposing (WebData)
import Http exposing (Error)


-- Releng Notification Identity FrontEnd Types
type alias Preference =
    { channel : String
    , name : String
    , target : String
    , urgency : String
    }

type alias ApiProblem =
    { detail : Maybe String
    , instance : Maybe String
    , status : Maybe Int
    , title : Maybe String
    , type_ : Maybe String
    }

type alias Preferences =
    List Preference

type Route = BaseRoute

type alias Identity =
    { name : String
    , preferences: Preferences
    }

type alias Model =
    { baseUrl : String                         -- URL of notification identity service
    , identity_name : Maybe String             -- Name of identity in the input field
    , retrieved_identity : Maybe String        -- Name of identity whose preferences are being displayed
    , preferences : WebData Preferences        -- Preferences retrieved from service for retrieved_identity
    , api_problem : WebData ApiProblem         -- Elm representation of Problem JSON
    , status_message : Maybe String            -- Status of request/service/whatever
    , selected_preference : Maybe Preference   -- Currently selected preference, in case of editing
    , is_service_processing : Bool             -- Flag indicating the status of a request to the service
    , new_identity : Maybe Identity            -- New identity to be added to service
    }

-- FrontEnd Actions
type Msg
    = NavigateTo Route                              -- Route navigation within page
    | ChangeName String                             -- Update state with name in input box
    | GetPreferencesRequest                         -- Request preferences from service
    | GetPreferencesResponse (WebData Preferences)  -- Handle response for preferences request
    | IdentityDeleteRequest                         -- Delete identity from service
    | IdentityDeleteResponse (WebData String)       -- Handle identity delete response
    | UrgencyDeleteRequest                          -- Delete identity preference
    | UrgencyDeleteResponse (WebData ApiProblem)    -- Handle preference delete response
    | NewIdentityRequest                            -- Add new identity request
    | NewIdentityResponse (WebData ApiProblem)      -- Handle new identity response
    | OperationFail String                          -- Operation failed with the given reason
    | HandleProblemJson (Http.Response String)      -- Handle problem JSON
