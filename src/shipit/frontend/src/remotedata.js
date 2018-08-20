import { mapEffect } from 'raj-compose';
import { union } from 'tagmeme';

/* eslint-disable no-underscore-dangle */
export default (subModelId, OuterMsg, fetch) => {
  const Msg = union([
    'NOT_ASKED',
    'LOADING',
    'FAILURE',
    'SUCCESS',
  ]);
  const notAsked = () => ({ _status: 'NOT_ASKED' });
  const loading = () => ({ _status: 'LOADING' });
  const failure = error => ({ _status: 'FAILURE', _data: error });
  const success = response => ({ _status: 'SUCCESS', _data: response });
  const initModel = notAsked();
  const initEffect = mapEffect(dispatch => dispatch(Msg.LOADING()), OuterMsg);
  const toMsg = model => Msg[model[subModelId]._status](model[subModelId]._data);
  const update = (msg, model) => {
    if (OuterMsg()._kind === msg._kind) {
      console.log(msg._data._kind);
      const [subModel, subEffect] = Msg.match(msg._data, {
        NOT_ASKED: () => [notAsked()],
        // only trigger effect when we "enter" LOADING state
        LOADING: () => [loading(), (msg._data._kind === 'LOADING' && model[subModelId]._status !== 'LOADING') ? fetch(Msg.SUCCESS, Msg.FAILURE) : undefined],
        FAILURE: error => [failure(error)],
        SUCCESS: response => [success(response)],
      });
      const newModel = { ...model };
      newModel[subModelId] = subModel;
      return [newModel, mapEffect(subEffect, OuterMsg)];
    }
    return [model];
  };
  const view = (
    model,
    dispatch,
    notAskedView,
    loadingView,
    failureView,
    successView,
  ) => Msg.match(toMsg(model), {
    NOT_ASKED: () => (notAskedView ? notAskedView(model, dispatch) : undefined),
    LOADING: () => loadingView(model, dispatch),
    FAILURE: () => failureView(model[subModelId]._data, dispatch, model),
    SUCCESS: () => successView(model[subModelId]._data, dispatch, model),
  });
  return {
    Msg,
    notAsked,
    loading,
    failure,
    success,
    initModel,
    initEffect,
    update,
    view,
  };
};
/* eslint-enable */
