require('expose?$!expose?jQuery!jquery')
require('expose?Tether!tether')
require('bootstrap')
require("./index.scss")

import {renderApp} from 'neo'
import {App, Layout, Routes} from './app'

renderApp(App, Layout, Routes)
