/* TODO: explain what this file is about
 *
 */

export default {
  init: [{ text: 'Not found' }],
  update: (message, model) => model,
  view: model => <p>{model.text}</p>,
};
