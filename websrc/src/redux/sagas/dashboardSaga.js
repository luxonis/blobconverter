import {all, takeLatest, put, select} from 'redux-saga/effects';
import * as actionTypes from '../actions/actionTypes';
import request, {GET, POST} from '../../services/requests';
import {modelSourceSelector, openVinoVersionSelector} from "../selectors/dashboard";
import downloadFile from 'js-file-download';

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

function* convertModel({payload}) {
  try {
    const modelSource = yield select(modelSourceSelector);
    const data = new FormData();
    switch (modelSource) {
      case 'zoo': {
        data.append('compile_type', 'zoo');
        data.append('model_name', payload["zoo-name"]);
        data.append('model_downloader_params', payload["advanced-option-input-0"]);
        data.append('intermediate_compiler_params', payload["advanced-option-input-1"]);
        data.append('compiler_params', payload["advanced-option-input-2"]);
        break;
      }
      case 'openvino': {
        data.append('compile_type', 'myriad')
        data.append('definition', payload["openvino-xml"])
        data.append('weights', payload["openvino-bin"])
        data.append('compiler_params', payload["advanced-option-input-0"]);
        break;
      }
      case 'caffe': {
        data.append('compile_type', 'model')
        data.append('model_type', 'caffe')
        data.append('model', payload["caffe-model"])
        data.append('proto', payload["caffe-proto"])
        data.append('intermediate_compiler_params', payload["advanced-option-input-0"]);
        data.append('compiler_params', payload["advanced-option-input-1"]);
        break;
      }
      case 'tf': {
        data.append('compile_type', 'model')
        data.append('model_type', 'tf')
        data.append('model', payload["tf-model"])
        data.append('intermediate_compiler_params', payload["advanced-option-input-0"]);
        data.append('compiler_params', payload["advanced-option-input-1"]);
        break;
      }
      default: {
        throw "Unknown model source: " + modelSource;
      }
    }
    const openVinoVersion = yield select(openVinoVersionSelector);
    const response = yield request(POST, 'compile', data, {params: {version: openVinoVersion}, headers: {'Content-Type': 'multipart/form-data'}, responseType: 'arraybuffer'});
    const filename = response.headers["content-disposition"].split("filename=")[1];
    console.log(filename)
    downloadFile(response.data, filename);
    yield put({type: actionTypes.CONVERT_MODEL_SUCCESS, payload: response.data});
  } catch (error) {
    console.error(error);
    yield put({type: actionTypes.CONVERT_MODEL_FAILED, error: error.response.data});
    yield put({type: actionTypes.CHANGE_MODAL, payload: {error_modal: {open: true}}});
  }
}

export default function* dashboardSaga() {
  yield all([
    yield takeLatest([actionTypes.FETCH_ZOO_MODELS, actionTypes.SET_MODEL_SOURCE, actionTypes.SET_OPENVINO_VERSION], fetchModels),
    yield takeLatest(actionTypes.CONVERT_MODEL, convertModel),
  ]);
}
