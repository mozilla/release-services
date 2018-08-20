/* TODO: explain what this file is about
 *
 */

import withLayout from './../layout';

export const createProgram = () => ({
  init: [{ text: 'Not found' }],
  update: (message, model) => model,
  view: model => <p>{model.text}</p>,
});

export default withLayout(createProgram);
