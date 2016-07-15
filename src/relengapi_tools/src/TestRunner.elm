module Main exposing (..)

import ElmTest exposing (..)
import Pages.Login.Test as PagesLogin exposing (..)

import AppTest

allTests : Test
allTests =
    suite "All tests"
        [ AppTest.all
        , PagesLogin.all
        ]


main : Program Never
main =
    runSuiteHtml allTests
