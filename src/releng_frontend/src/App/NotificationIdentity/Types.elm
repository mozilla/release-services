-- DIFFERENT MODULE TYPES, MESSAGES, ETC HERE
module App.NotificationIdentity.Types exposing (..)

import RemoteData exposing (WebData)


-- Releng Notification Identity FrontEnd Types
type alias Preference =
    { channel : String
    , name : String
    , target : String
    , urgency : String
    }

type alias ApiProblem =
    { description : String
    , message : String
    , status_code : Int
    }

type alias Preferences =
    List Preference

nullPreference : Preference
nullPreference =
    { channel = ""
    , name = ""
    , target = ""
    , urgency = ""
    }

type Route = BaseRoute

type alias Model =
    { baseUrl : String                         -- URL of notification identity service
    , identity_name : Maybe String             -- Name of identity in the input field
    , retrieved_identity : Maybe String        -- Name of identity whose preferences are being displayed
    , preferences : WebData Preferences        -- Preferences retrieved from service for retrieved_identity
    , api_problem : WebData ApiProblem         -- Elm representation of Problem JSON
    , status_message : String                  -- Status of request/service/whatever
    , selected_preference : Maybe Preference   -- Currently selected preference, in case of editing
    , is_service_processing : Bool             -- Flag indicating the status of a request to the service
    }

-- FrontEnd Actions
type Msg =
    NavigateTo Route                                -- Route navigation within page
    | ChangeName String                             -- Update state with name in input box
    | PreferencesRequest                            -- Request preferences from service
    | PreferencesResponse (WebData Preferences)     -- Handle response for preferences request
    | IdentityDeleteRequest                         -- Delete identity from service
    | IdentityDeleteResponse (WebData ApiProblem)   -- Handle identity delete response
    | UrgencyDeleteRequest                          -- Delete identity preference
    | UrgencyDeleteResponse (WebData ApiProblem)    -- Handle preference delete response
--    | GetPreferencesForIdentity String
--    | GetJson
--    | UpdateIdName
--    | ModifyPreferencesForIdentity String
--    | DeleteIdentity String
--    | NewPreference String String
--    | PreferenceJsonReturn (Result Http.Error (List Preference))
--    | GetPreferenceUrgencyForIdentity String String  -- identity, urgency are params
--    | DeletePreferenceUrgencyForIdentity String String  -- identity, urgency are params
--    | SearchUserPreferences String