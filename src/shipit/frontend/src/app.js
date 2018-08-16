/* TODO: explain what this file is about
 *
 */

export default {
  init: [{ text: 'Hello world' }],
  update: (message, model) => model,
  view: model => <p>{model.text}</p>
};
