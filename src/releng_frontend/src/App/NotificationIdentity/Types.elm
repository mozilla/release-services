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

type Route = BaseRoute


type alias Model =
    { baseUrl : String
    , identity_name : String
    , preferences : WebData Preferences
    , api_problem : WebData ApiProblem
    , status_message : String
    }

-- FrontEnd Actions
type Msg =
    NavigateTo Route
    | ChangeName String
    | PreferencesRequest
    | PreferencesResponse (WebData Preferences)
    | IdentityDeleteRequest
    | IdentityDeleteResponse (WebData ApiProblem)
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