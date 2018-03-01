-- DIFFERENT MODULE TYPES, MESSAGES, ETC HERE


module App.Notifications.Types exposing (..)

import Form
import Html exposing (Html)
import Http exposing (Error)
import RemoteData exposing (WebData)


-- Releng Notification Identity FrontEnd Types


type alias Preference =
    { channel :
        String

    -- Notification channel for preference (IRC, EMAIL etc)
    , name :
        Maybe String

    -- Name of identity
    , target :
        String

    -- Target on channel (irc chan, irc nick, email)
    , urgency :
        String

    -- Urgency level (LOW, NORMAL etc)
    }


type alias ApiProblem =
    -- See https://tools.ietf.org/html/rfc7807
    { detail : Maybe String
    , instance : Maybe String
    , status : Maybe Int
    , title : Maybe String
    , type_ : Maybe String
    }


type alias Preferences =
    List Preference


type alias MessageInstance =
    { deadline : String
    , message : String
    , shortMessage : String
    , policies : List Policy
    }


type alias Frequency =
    { minutes : Int
    , hours : Int
    , days : Int
    }


type alias Policy =
    { uid : String
    , identity : String
    , start_timestamp : String
    , stop_timestamp : String
    , urgency : String
    , frequency : Frequency
    }


type Route
    = BaseRoute
    | ShowPreferencesRoute String
    | ShowMessageRoute String
    | NewIdentityRoute
    | PolicyRoute
    | HelpRoute


type alias Identity =
    { name :
        String

    -- Name of the identity
    , preferences :
        Preferences

    -- Notification preferences for the identity
    }


type alias Model =
    { identityUrl :
        String

    -- URL of notification identity service
    , policyUrl :
        String

    -- URL of notification policy service
    , input_value :
        Maybe String

    -- Name of identity in the input field
    , retrieved_identity :
        Maybe String

    -- Name of identity whose preferences are being displayed
    , preferences :
        WebData Preferences

    -- Preferences retrieved from service for retrieved_identity
    , api_problem :
        WebData ApiProblem

    -- Elm representation of Problem JSON
    , selected_preference :
        Maybe Preference

    -- Currently selected preference, in case of editing
    , is_service_processing :
        Bool

    -- Flag indicating the status of a request to the service
    , new_identity :
        Form.Form () Identity

    -- New identity to be added to service
    , edit_form :
        Form.Form () Preference

    -- Form to edit a notification preference
    , new_message :
        Maybe String

    -- New Message create form
    , uid :
        Maybe String

    -- String in the UID input field
    , status_html :
        Maybe (Html Msg)

    -- HTML with user interaction feedback
    , policies :
        WebData (List Policy)

    -- List of policies retrieved from policy service
    , retrieved_message :
        WebData MessageInstance

    -- Message instance retrieved by pressign "search messages"
    }



-- FrontEnd Actions


type
    Msg
    -- Messages for the "Identity" service
    = ChangeName String
      -- Update state with name in input box
    | GetPreferencesRequest
      -- Request preferences from service
    | GetPreferencesResponse (WebData String)
    | IdentityDeleteRequest
      -- Delete identity from service
    | IdentityDeleteResponse (WebData String)
      -- Handle identity delete response
    | UrgencyDeleteRequest
      -- Delete identity preference
    | UrgencyDeleteResponse (WebData String)
      -- Handle preference delete response
    | NewIdentityFormDisplay
      -- Handle onClick event for "New Identity" button
    | NewIdentityFormMsg Form.Msg
      -- Handle events for "New Identity" form
    | NewIdentityRequest
      -- Add new identity request
    | NewIdentityResponse (WebData String)
      -- Handle new identity response
    | ModifyIdentityRequest
      -- Modify identity preference
    | ModifyIdentityResponse (WebData String)
      -- Handle modify identity response
    | SelectPreference Preference
      -- Click a preference to edit it
    | EditPreferenceFormMsg Form.Msg
      -- Message for the "Policy" service
    | NewMessageDisplay
      -- Display new message UI
    | TickTockRequest
      -- Trigger TickTock
    | TickTockResponse (WebData String)
      -- Handle TickTock response
    | GetPendingMessagesRequest
      -- Get all pending messages
    | GetPendingMessagesResponse (WebData String)
      -- Handle pending messages response
    | GetMessageRequest
      -- Get message by uid
    | GetMessageResponse (WebData String)
      -- Handle message by uid response
    | DeleteMessageRequest
      -- Delete message
    | DeleteMessageResponse (WebData String)
      -- Handle delete message response
    | NewMessageRequest
      -- Create new message request
    | NewMessageResponse (WebData String)
      -- Handle new message response
    | NewMessageUpdate String
      -- Update new message textarea
    | NewMessageUIDUpdate String
      -- Update new message UID text input
    | GetActivePoliciesRequest
      -- Get all active policies for a user
    | GetActivePoliciesResponse (WebData String)
      -- Handles active policies response
      -- Error handlers, other
    | OperationFail Msg String
      -- Operation failed with the given reason
    | HandleProblemJson Msg (Http.Response String)
      -- Handle problem JSON
    | ClearStatusMessage
      -- Clear the status indicator message
    | NavigateTo Route
      -- Change the route
    | HelpDisplay



-- Display help menu
