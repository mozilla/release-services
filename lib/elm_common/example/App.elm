port module App exposing (program)

import Html.App

-- Boot
update main extensions msg model =
  -- TODO: replace True

  let
    -- (a, b) = msg
    ll = Debug.log "Message in common update" msg
    --ext = List.filter (\e -> True) extensions
    --  |> List.map (\(m, i, update, s) -> update)
    --  |> List.head 
    --l = Debug.log "Extension" l
  in
    -- Hawk.update msg model
    main msg model
    

  --(List.filter (\e -> True) extensions
  --  |> List.map (\e -> e.update)
  --  |> List.head 
  --  |> Maybe.withDefault main) msg model


subscriptions main extensions = 
  -- Build subscriptions batch
  let 

    allSubscriptions = List.map (\(msg, i, u, subs) -> List.map (\s -> Sub.map msg s) subs) extensions
      |> List.concat

    l = Debug.log "all subs" allSubscriptions

  in
    --(\x -> Sub.batch allSubscriptions)
    (\x -> Sub.none)

program x = Html.App.program 
  { 
    init = x.init 
    , update = update x.update x.extensions
    , view = x.view
    , subscriptions = subscriptions x.subscriptions x.extensions
    --, subscriptions = (\x -> Sub.none)
  }
