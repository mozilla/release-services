/* TODO: explain what this file is about
 *
 */

export default {
  init: [{ text: 'ERROR' }],
  update: (message, model) => model,
  view: model => <p>{model.text}</p>,
};
