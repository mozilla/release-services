/* TODO: explain what this file is about
 *
 */
import React from 'react';
import { render } from 'react-dom';
import { program } from 'raj-react';

export const App = {
  init: [{ text: 'Hello world' }],
  update: (message, model) => model,
  view: model => <p>{model.text}</p>
};

export default () => {
  const ReactApp = program(React.Component, () => App);
  render(<ReactApp />, document.getElementById('root'));
};
