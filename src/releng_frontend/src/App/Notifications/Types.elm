-- DIFFERENT MODULE TYPES, MESSAGES, ETC HERE
module App.Notifications.Types exposing (..)

import RemoteData exposing (WebData)
import Form
import Http exposing (Error)
import Html exposing (Html)


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

type alias MessageInstance =
    { deadline : String
    , message : String
    , shortMessage : String
    , policies : List Policy
    }

type alias NotificationInstance =
    { channel : String
    , message : String
    , target : List String
    , uid : String
    }

type alias Frequency =
    { minutes : Int
    , hours : Int
    , days : Int
    }

type alias Policy =
    { identity : String
    , start_timestamp : String
    , stop_timestamp : String
    , urgency : String
    , frequency : Frequency
    }

type alias NotificationInstances =
    List NotificationInstance


type Route
    = BaseRoute
    | ShowPreferencesRoute String
    | NewIdentityRoute
    | PolicyRoute

type alias Identity =
    { name : String                      -- Name of the identity
    , preferences: InputPreferences      -- Notification preferences for the identity
    }

type alias Model =
    { identityUrl : String                          -- URL of notification identity service
    , policyUrl : String                            -- URL of notification policy service
    , identity_name : Maybe String                  -- Name of identity in the input field
    , retrieved_identity : Maybe String             -- Name of identity whose preferences are being displayed
    , preferences : WebData Preferences             -- Preferences retrieved from service for retrieved_identity
    , api_problem : WebData ApiProblem              -- Elm representation of Problem JSON
    , selected_preference : Maybe Preference        -- Currently selected preference, in case of editing
    , is_service_processing : Bool                  -- Flag indicating the status of a request to the service
    , new_identity : Form.Form () Identity          -- New identity to be added to service
    , edit_form : Form.Form () Preference           -- Form to edit a notification preference
    , new_message : Form.Form () MessageInstance    -- New Message create form
    , uid : Maybe String                            -- String in the UID input field
    , status_html : Maybe (Html Msg)
    }

-- FrontEnd Actions
type Msg
    -- Messages for the "Identity" service
    = ChangeName String                             -- Update state with name in input box
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

    -- Message for the "Policy" service
    | PolicyDisplay
    | TickTockRequest
    | TickTockResponse (WebData NotificationInstances)
    | GetPendingMessagesRequest
    | GetPendingMessagesResponse (WebData (List MessageInstance))
    | GetMessageRequest
    | GetMessageResponse (WebData MessageInstance)
    | DeleteMessageRequest
    | DeleteMessageResponse (WebData String)
    | NewMessageRequest
    | NewMessageResponse (WebData String)
    | GetActivePoliciesRequest
    | GetActivePoliciesResponse (WebData (List Policy))
    | UpdateUID String

    -- Error handlers
    | OperationFail Msg String                          -- Operation failed with the given reason
    | HandleProblemJson Msg (Http.Response String)      -- Handle problem JSON
    | ClearStatusMessage
