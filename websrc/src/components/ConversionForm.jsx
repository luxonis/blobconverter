import React from 'react';
import PropTypes from 'prop-types';
import stepImg from './step.png';
import {Button} from "react-bootstrap";
import {connect} from "react-redux";
import {availableZooModelsSelector, modelSourceSelector} from "../redux/selectors/dashboard";

const myriad_compile_step = {
  "title": "MyriadX Compile",
  "subtitle": "Model will be compiled using myriad_compile tool",
  "cli_params": "-ip U8 -VPU_MYRIAD_PLATFORM VPU_MYRIAD_2480 -VPU_NUMBER_OF_SHAVES 4 -VPU_NUMBER_OF_CMX_SLICES 4"
}
const model_optimizer_step = {
  "title": "Model Optimizer",
  "subtitle": "Model will be optimized and converted to OpenVINO format",
  "cli_params": "--data_type=FP16 --mean_values [127.5,127.5,127.5] --scale_values [255,255,255]"
}
const model_downloader_step = {
  "title": "Model Downloader",
  "subtitle": "Model will be downloaded from OpenVINO Model Zoo",
  "cli_params": "--precisions FP16 --num_attempts 5"
}

const resolveSteps = source => {
  switch (source) {
    case "zoo":
      return [model_downloader_step, model_optimizer_step, myriad_compile_step]
    case "caffe":
    case "tf":
      return [model_optimizer_step, myriad_compile_step]
    case "openvino":
      return [myriad_compile_step]
    default: {
      return []
    }
  }
}

const ConversionForm = ({modelSource, prevStep, availableZooModels}) => {
  const [advanced, setAdvanced] = React.useState(false);
  const steps = resolveSteps(modelSource);
  return (

    <form onSubmit={e => e.preventDefault()}>
      <div className={`params-form ${advanced ? 'expanded' : ''}`}>
        <div className="params-form-paths">
          <div className="upper-border">Conversion parameters</div>
          <div className="form">
            {
              modelSource === "openvino" &&
              <>
                <div className="form-group">
                  <label htmlFor="openvino-xml">Definition file (.xml)</label>
                  <input id="openvino-xml" type="file"/>
                </div>
                <div className="form-group">
                  <label htmlFor="openvino-bin">Weights file (.bin)</label>
                  <input id="openvino-bin" type="file"/>
                </div>
              </>
            }
            {
              modelSource === "caffe" &&
              <>
                <div className="form-group">
                  <label htmlFor="caffe-model">Model file (.caffemodel)</label>
                  <input id="caffe-model" type="file"/>
                </div>
                <div className="form-group">
                  <label htmlFor="caffe-proto">Proto file (.prototxt)</label>
                  <input id="caffe-proto" type="file"/>
                </div>
              </>
            }
            {
              modelSource === "tf" &&
              <div className="form-group">
                <label htmlFor="tf-model">Model file (.pb)</label>
                <input id="tf-model" type="file"/>
              </div>
            }
            {
              modelSource === "zoo" &&
              <div className="form-group">
                <label htmlFor="zoo-name">Model name</label>
                <select id="zoo-name">
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
            By submitting this form, you accept our <a href="#">Privacy Policy</a>
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
            <Button variant="outline-success">Convert</Button>
          </div>
        </div>
        <div className={`params-form-advanced ${advanced ? 'expanded' : ''}`}>
          <div className="upper-border">Advanced options</div>
          <div className="advanced-options">
            {
              steps.map((step, index) => (
                <div className="advanced-option" key={index}>
                  <label htmlFor={"advanced-option-input-" + index}><span>{step.title}</span> params</label>
                  <input type="text" id={"advanced-option-input-" + index} defaultValue={step.cli_params}/>
                </div>
              ))
            }
          </div>
          <div className="lower-border">
            You can read more about advanced options <a href="#">here</a>
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
  availableZooModels: PropTypes.arrayOf(PropTypes.string).isRequired,
};

const mapStateToProps = state => ({
  modelSource: modelSourceSelector(state),
  availableZooModels: availableZooModelsSelector(state),
})

export default connect(
  mapStateToProps
)(ConversionForm);
