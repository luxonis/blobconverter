import {all, takeLatest, put, select} from 'redux-saga/effects';
import * as actionTypes from '../actions/actionTypes';
import request, {GET} from '../../services/requests';
import {modelSourceSelector, openVinoVersionSelector} from "../selectors/dashboard";

function* fetchModels() {
  try {
    const modelSource = yield select(modelSourceSelector);
    if(modelSource !== 'zoo') {
      return;
    }
    const openVinoVersion = yield select(openVinoVersionSelector);
    const response = yield request(GET, 'zoo_models', {}, {params: {version: openVinoVersion}});
    yield put({type: actionTypes.FETCH_ZOO_MODELS_SUCCESS, payload: response.data});
  } catch (error) {
    console.error(error);
    yield put({type: actionTypes.FETCH_ZOO_MODELS_FAILED, error});
  }
}

export default function* dashboardSaga() {
  yield all([
    yield takeLatest([actionTypes.FETCH_ZOO_MODELS, actionTypes.SET_MODEL_SOURCE, actionTypes.SET_OPENVINO_VERSION], fetchModels)
  ]);
}
