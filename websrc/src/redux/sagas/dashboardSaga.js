import {all, takeLatest, put} from 'redux-saga/effects';
import * as actionTypes from '../actions/actionTypes';
import request, {GET} from '../../services/requests';

function* fetchModels() {
  try {
    const response = yield request(GET, 'zoo_models');
    yield put({type: actionTypes.FETCH_ZOO_MODELS_SUCCESS, payload: response.data});
  } catch (error) {
    console.error(error);
    yield put({type: actionTypes.FETCH_ZOO_MODELS_FAILED, error});
  }
}

export default function* dashboardSaga() {
  yield all([
    yield takeLatest(actionTypes.FETCH_ZOO_MODELS, fetchModels)
  ]);
}
