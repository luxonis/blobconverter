import React from 'react';
import PropTypes from 'prop-types';
import stepImg from './step.png';
import {Button, Spinner} from "react-bootstrap";
import {connect} from "react-redux";
import _ from 'lodash';
import {
  availableZooModelsSelector,
  conversionInProgressSelector,
  modelSourceSelector
} from "../redux/selectors/dashboard";
import {makeAction} from "../redux/actions/makeAction";
import {CHANGE_MODAL, CONVERT_MODEL} from "../redux/actions/actionTypes";

const myriad_compile_step = {
  "title": "MyriadX Compile",
  "subtitle": "Model will be compiled using myriad_compile tool",
  "cli_params": "-ip U8"
}
const model_optimizer_step = {
  "title": "Model Optimizer",
  "subtitle": "Model will be optimized and converted to OpenVINO format",
  "cli_params": "--data_type=FP16 --mean_values=[127.5,127.5,127.5] --scale_values=[255,255,255]"
}
const model_downloader_step = {
  "title": "Model Downloader",
  "subtitle": "Model will be downloaded using OpenVINO model downloader",
  "cli_params": "--precisions FP16 --num_attempts 5"
}

const resolveSteps = source => {
  switch (source) {
    case "file":
    case "zoo":
      return [model_downloader_step, model_optimizer_step, myriad_compile_step]
    case "caffe":
    case "tf":
    case "onnx":
      return [model_optimizer_step, myriad_compile_step]
    case "openvino":
      return [myriad_compile_step]
    default: {
      return []
    }
  }
}

const ConversionForm = ({modelSource, prevStep, availableZooModels, convertModel, inProgress, changeModal}) => {
  const [advanced, setAdvanced] = React.useState(true);
  const [shaves, setShaves] = React.useState(4);
  const steps = resolveSteps(modelSource);
  return (

    <form onSubmit={e => {
      e.preventDefault();
      convertModel(Object.fromEntries(new FormData(e.target)))
    }}>
      <div className={`params-form ${advanced ? 'expanded' : ''}`}>
        <div className="params-form-paths">
          <div className="upper-border">Conversion parameters</div>
          <div className="form">
            {
              modelSource === "file" &&
              <>
                <div className="form-group">
                  <label htmlFor="openvino-xml">Model name</label>
                  <input id="config-name" name="config-name" required/>
                </div>
                <div className="form-group">
                  <label htmlFor="openvino-xml">Config file (.yml)</label>
                  <input id="config-file" name="config-file" type="file" accept=".yml" required/>
                </div>
              </>
            }
            {
              modelSource === "openvino" &&
              <>
                <div className="form-group">
                  <label htmlFor="openvino-xml">Definition file (.xml)</label>
                  <input id="openvino-xml" name="openvino-xml" type="file" accept=".xml" required/>
                </div>
                <div className="form-group">
                  <label htmlFor="openvino-bin">Weights file (.bin)</label>
                  <input id="openvino-bin" name="openvino-bin" type="file" accept=".bin" required/>
                </div>
              </>
            }
            {
              modelSource === "caffe" &&
              <>
                <div className="form-group">
                  <label htmlFor="caffe-model">Model file (.caffemodel)</label>
                  <input id="caffe-model" name="caffe-model" type="file" accept=".caffemodel" required/>
                </div>
                <div className="form-group">
                  <label htmlFor="caffe-proto">Proto file (.prototxt)</label>
                  <input id="caffe-proto" name="caffe-proto" type="file" accept=".prototxt" required/>
                </div>
              </>
            }
            {
              modelSource === "tf" &&
              <div className="form-group">
                <label htmlFor="tf-model">Model file (.pb)</label>
                <input id="tf-model" name="tf-model" type="file" accept=".pb" required/>
              </div>
            }
            {
              modelSource === "onnx" &&
              <div className="form-group">
                <label htmlFor="onnx-model">Model file (.onnx)</label>
                <input id="onnx-model" name="onnx-model" type="file" accept=".onnx" required/>
              </div>
            }
            {
              modelSource === "zoo" &&
              <div className="form-group">
                <label htmlFor="zoo-name">Model name</label>
                <select id="zoo-name" name="zoo-name">
                  {
                    availableZooModels.map(model => (
                      <option key={model} value={model}>{model}</option>
                    ))
                  }
                </select>
              </div>
            }
          </div>
          <div className="lower-border">
            By submitting this form, you accept our
            <Button variant="link" size="sm" onClick={() => changeModal({policy: {open: true}})}>Privacy Policy</Button>
          </div>
        </div>
        <div className="params-form-steps">
          <div className="upper-border">Conversion steps</div>
          <div className="steps">
            {
              steps.map((step, index) => (
                <div className="step" key={index}>
                  <img src={stepImg} alt=""/>
                  <span className="step-label">{index + 1}</span>
                  <span className="step-descr">
                    <p className="title">{step.title}</p>
                    <p className="subtitle">{step.subtitle}</p>
                  </span>
                </div>
              ))
            }
          </div>
          <div className="lower-border">
            <Button variant="outline-secondary" onClick={() => {prevStep(); setAdvanced(false)}}>Back</Button>
            <Button variant="outline-success" type="submit" disabled={inProgress}>
              {
                inProgress
                  ? <>
                    <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true"/>
                    <span>Converting...</span>
                  </>
                  : <span>Convert</span>
              }
            </Button>
          </div>
        </div>
        <div className={`params-form-advanced ${advanced ? 'expanded' : ''}`}>
          <div className="upper-border">Advanced options</div>
          <div className="advanced-options">
            {
              _.includes(["onnx", "tf", "caffe"], modelSource) &&
                <div className="advanced-option">
                  <label htmlFor="advanced-option-input-optimizer"><span>Model optimizer</span> params:</label>
                  <input type="text" id="advanced-option-input-optimizer" name="advanced-option-input-optimizer" defaultValue={model_optimizer_step['cli_params']}/>
                </div>
            }
            <div className="advanced-option">
              <label htmlFor="advanced-option-input-compiler"><span>MyriadX compile</span> params:</label>
              <input type="text" id="advanced-option-input-compiler" name="advanced-option-input-compiler" defaultValue={myriad_compile_step['cli_params']}/>
            </div>
            <div className="advanced-option">
              <label htmlFor="advanced-option-input-shaves"><span>Shaves</span>: {shaves}</label>
              <input type="range" id="advanced-option-input-shaves" name="advanced-option-input-shaves" min={1} max={16} onChange={e => setShaves(e.target.value)} value={shaves}/>
              <div className="advanced-option-input-shaves-ticks">
                <span>1</span>
                <span>16</span>
              </div>
            </div>
          </div>
          <div className="lower-border">
            You can read more about advanced options <a href="https://docs.openvinotoolkit.org/latest/openvino_docs_MO_DG_prepare_model_convert_model_Converting_Model.html">here</a>
          </div>
          <div className="expander" onClick={() => setAdvanced(!advanced)}>
            Advanced >
          </div>
        </div>
      </div>
    </form>
  );
}

ConversionForm.propTypes = {
  modelSource: PropTypes.string,
  prevStep: PropTypes.func.isRequired,
  convertModel: PropTypes.func.isRequired,
  changeModal: PropTypes.func.isRequired,
  availableZooModels: PropTypes.arrayOf(PropTypes.string).isRequired,
};

const mapStateToProps = state => ({
  modelSource: modelSourceSelector(state),
  availableZooModels: availableZooModelsSelector(state),
  inProgress: conversionInProgressSelector(state)
})

const mapDispatchToProps = {
  convertModel: makeAction(CONVERT_MODEL),
  changeModal: makeAction(CHANGE_MODAL),
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(ConversionForm);
