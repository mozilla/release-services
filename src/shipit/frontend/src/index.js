import 'bootstrap/dist/css/bootstrap.min.css';
import 'font-awesome/css/font-awesome.min.css';

import React from 'react';
import { render } from 'react-dom';
import App from './App';
import {
  SHIPIT_API_URL,
  RELEASE_CHANNEL,
  RELEASE_VERSION,
} from './config';

const root = document.getElementById('root');
const load = () => {
  render(
    <App
      backend_url={SHIPIT_API_URL}
      release_version={RELEASE_VERSION}
      release_channel={RELEASE_CHANNEL}
    />,
    root,
  );
};

load();
