import {all, takeLatest, put, select} from 'redux-saga/effects';
import * as actionTypes from '../actions/actionTypes';
import request, {GET, POST} from '../../services/requests';
import {modelSourceSelector, openVinoVersionSelector} from "../selectors/dashboard";
import downloadFile from 'js-file-download';
import _ from 'lodash';

function generateYaml({filenames, precision, task_type, framework, optimizer_params=null}) {
  let optimizerStr = "";
  if(optimizer_params) {
    optimizerStr = `model_optimizer_args:
${optimizer_params.split(' ').filter(item => !!item.trim()).map(item => "  - " + item).join("\n")}
`
  }
  const file_string = filename => `
  - name: ${precision}/${filename}
    source:
      $type: http
      url: $REQUEST/${filename}`
  const config = `
task_type: ${task_type}
files: ${filenames.map(filename => file_string(filename)).join('')}
framework: ${framework}
${optimizerStr ? optimizerStr : ""}
`
  return config
}

function readAsJson(blob) {
  return new Promise((resolve, reject) => {
    const reader  = new FileReader();
    reader.onload = () => resolve(JSON.parse(reader.result))
    reader.onerror = reject
    reader.readAsText(blob)
  })
}

function isValidName(name) {
  return name.split('.').length <= 2 && name.split('=').length === 1;
}

function* fetchModels() {
  try {
    const modelSource = yield select(modelSourceSelector);
    if (modelSource !== 'zoo' && modelSource !== 'zoo-depthai') {
      return;
    }
    let zooType = "intel"
    if (modelSource === 'zoo-depthai') {
      zooType = "depthai"
    }

    const openVinoVersion = yield select(openVinoVersionSelector);
    const response = yield request(GET, 'zoo_models', {}, {params: {version: openVinoVersion, zoo_type: zooType}});
    yield put({type: actionTypes.FETCH_ZOO_MODELS_SUCCESS, payload: response.data});
  } catch (error) {
    console.error(error);
    yield put({type: actionTypes.FETCH_ZOO_MODELS_FAILED, error});
  }
}

function* convertModel({payload}) {
  console.log(payload);
  try {
    const modelSource = yield select(modelSourceSelector);
    const openVinoVersion = yield select(openVinoVersionSelector);
    const precision = "FP16"
    const data = new FormData();
    if(modelSource === "zoo") {
      data.append('name', payload["zoo-name"]);
      data.append('use_zoo', "true");
      data.append('zoo_type', "intel")
    } else if(modelSource === "zoo-depthai") {
      data.append('name', payload["zoo-name"]);
      data.append('use_zoo', "true");
      data.append('zoo_type', "depthai")
    } else if(modelSource === "file") {
      data.append('config', payload["config-file"]);
      data.append('name', payload["config-name"]);
      data.append('use_zoo', "true");
    } else {
      let framework = "";
      let optimizer_additional = "";
      let valid_names = true;
      switch (modelSource) {
        case 'caffe': {
          framework = "caffe";
          // Check for valid name
          valid_names = isValidName(payload['caffe-model'].name) && isValidName(payload['caffe-proto'].name)
          console.log("FILENAMES: ", payload['caffe-model'].name, payload['caffe-proto'].name,  valid_names)
          optimizer_additional = ` --input_model=$dl_dir/${precision}/${payload['caffe-model'].name} --input_proto=$dl_dir/${precision}/${payload['caffe-proto'].name}`
          break;
        }
        case 'openvino': {
          framework = "dldt";
          // Check for valid name
          valid_names = isValidName(payload['openvino-bin'].name) && isValidName(payload['openvino-xml'].name)
          console.log("FILENAMES: ", payload['openvino-bin'].name, payload['openvino-xml'].name, valid_names)
          break;
        }
        case 'tf': {
          framework = "tf";
          // Check for valid name
          valid_names = isValidName(payload['tf-model'].name)
          console.log("FILENAME: ", payload['tf-model'].name, valid_names)
          optimizer_additional = ` --input_model=$dl_dir/${precision}/${payload['tf-model'].name}`
          break;
        }
        case 'onnx': {
          framework = "onnx";
          // Check for valid name
          valid_names = isValidName(payload['onnx-model'].name)
          console.log("FILENAME: ", payload['onnx-model'].name, valid_names)
          optimizer_additional = ` --input_model=$dl_dir/${precision}/${payload['onnx-model'].name}`
          break;
        }
      }
      if (!valid_names) {
        yield put({type: actionTypes.CONVERT_MODEL_FAILED, error: {"message": "Input model files must not contain '.' or '=' characters!"}});
        yield put({type: actionTypes.CHANGE_MODAL, payload: {error_modal: {open: true}}});
        return;
      }
      const filenames = Object.values(payload).map(item => item.name).filter(item => !!item)
      const yml = generateYaml({
        filenames: filenames,
        precision: precision,
        task_type: "detection",
        framework: framework,
        optimizer_params: payload["advanced-option-input-optimizer"] + optimizer_additional,
      })
      console.log("Generated config: " + yml)
      const blob = new Blob([yml],{type:"text/yaml"});
      data.append('config', blob)
      Object.values(payload).forEach(item => item.name && data.append(item.name, item))
      data.append('name', filenames[0].split('.')[0]);
    }
    
    data.append('myriad_shaves', payload["advanced-option-input-shaves"]);
    data.append('myriad_params_advanced', payload["advanced-option-input-compiler"]);

    console.log(openVinoVersion)
    console.log(openVinoVersion.includes("RVC3"))
    if(openVinoVersion.includes("RVC3")){
      data.append('quantization_domain', payload["advanced-option-input-quantization"]);
      data.append('data_type', payload["advanced-option-input-int8"] !== undefined ? payload["advanced-option-input-int8"] : "FP16")
    }

    const response = yield request(
      POST,
      'compile',
      data,
      {
        params: {version: openVinoVersion},
        headers: {'Content-Type': 'multipart/form-data'},
        responseType: 'blob',
      }
    );
    const filename = response.headers["content-disposition"].split("filename=")[1];
    console.log("Downloading " + filename)
    downloadFile(response.data, filename);
    yield put({type: actionTypes.CONVERT_MODEL_SUCCESS, payload: response.data});
  } catch (error) {
    console.error(error);
    if (_.has(error, 'response')) {
      console.log(error.response.data);
      const data = yield readAsJson(error.response.data);
      yield put({type: actionTypes.CONVERT_MODEL_FAILED, error: data});
      yield put({type: actionTypes.CHANGE_MODAL, payload: {error_modal: {open: true}}});
    }
  }
}

export default function* dashboardSaga() {
  yield all([
    yield takeLatest([actionTypes.FETCH_ZOO_MODELS, actionTypes.SET_MODEL_SOURCE, actionTypes.SET_OPENVINO_VERSION], fetchModels),
    yield takeLatest(actionTypes.CONVERT_MODEL, convertModel),
  ]);
}
