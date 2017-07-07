-- DIFFERENT MODULE TYPES, MESSAGES, ETC HERE
module App.NotificationIdentity.Types exposing (..)

import RemoteData exposing (WebData)
import Form
import Http exposing (Error)


-- Releng Notification Identity FrontEnd Types
type alias Preference =
    { channel : String          -- Notification channel for preference (IRC, EMAIL etc)
    , name : String             -- Name of identity
    , target : String           -- Target on channel (irc chan, irc nick, email)
    , urgency : String          -- Urgency level (LOW, NORMAL etc)
    }

-- Preference without name, for contexts where name is defined elsewhere
type alias InputPreference =
    { channel : String
    , target : String
    , urgency : String
    }


type alias ApiProblem =     -- See https://tools.ietf.org/html/rfc7807
    { detail : Maybe String
    , instance : Maybe String
    , status : Maybe Int
    , title : Maybe String
    , type_ : Maybe String
    }

type alias Preferences =
    List Preference

type alias InputPreferences =
    List InputPreference

type Route = BaseRoute

type alias Identity =
    { name : String                 -- Name of the identity
    , preferences: InputPreferences      -- Notification preferences for the identity
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
    , is_creating_identity : Bool              -- Flag indicating if the user is creating a new identity
    , new_identity : Form.Form () Identity     -- New identity to be added to service
    , edit_form : Form.Form () Preference      -- Form to edit a notification preference
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
    | UrgencyDeleteResponse (WebData String)        -- Handle preference delete response
    | NewIdentityFormDisplay
    | NewIdentityFormMsg Form.Msg
    | NewIdentityRequest                            -- Add new identity request
    | NewIdentityResponse (WebData String)          -- Handle new identity response
    | ModifyIdentityRequest                         -- Modify identity preference
    | ModifyIdentityResponse (WebData String)       -- Handle modify identity response
    | SelectPreference Preference                   -- Click a preference to edit it
    | EditPreferenceFormMsg Form.Msg
    | OperationFail String                          -- Operation failed with the given reason
    | HandleProblemJson (Http.Response String)      -- Handle problem JSON
