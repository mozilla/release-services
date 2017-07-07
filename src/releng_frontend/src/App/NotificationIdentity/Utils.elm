module App.NotificationIdentity.Utils exposing (..)

import App.NotificationIdentity.Types


-- Map notification urgency level to badge colour class
urgencyLevel : String -> String
urgencyLevel urgency =
    case urgency of
        "LOW" -> "success"
        "NORMAL" -> "warning"
        "HIGH" -> "danger"
        _ -> "default"


-- Method to use for sorting preferences
preferenceSort : App.NotificationIdentity.Types.Preference -> Int
preferenceSort preference =
    case preference.urgency of
        "LOW" -> 1
        "NORMAL" -> 2
        "HIGH" -> 3
        "DO_YESTERDAY" -> 4
        _ -> -1
