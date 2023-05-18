import React from 'react';
import PropTypes from 'prop-types';
import {Button} from "react-bootstrap";
import {connect} from "react-redux";
import {SET_MODEL_SOURCE, SET_OPENVINO_VERSION} from "../redux/actions/actionTypes";
import {makeAction} from "../redux/actions/makeAction";
import {modelSourceSelector, openVinoVersionSelector, submitDisabledSelector} from "../redux/selectors/dashboard";
import borderImg from './border_gray.png'

const openVinoVersions = [
  {label: "2021.2", value: "2021.2"},
  {label: "2021.3", value: "2021.3"},
  {label: "2021.4", value: "2021.4"},
  {label: "2022.1", value: "2022.1", default: true},
  {label: "RVC3", value: "2022.3_RVC3"}
]

const modelSources = [
  {label: "Caffe", value: "caffe"},
  {label: "TensorFlow", value: "tf"},
  {label: "ONNX", value: "onnx"},
  {label: "OpenVino", value: "openvino"},
  {label: "OpenVino Model Zoo", value: "zoo"},
  {label: "DepthAI Model Zoo", value: "zoo-depthai"}
]

const modelSourcesRVC3 = [
  {label: "TensorFlow", value: "tf"},
  {label: "ONNX", value: "onnx"},
  {label: "OpenVino", value: "openvino"},
  {label: "OpenVino Model Zoo", value: "zoo"},
  {label: "DepthAI Model Zoo", value: "zoo-depthai"}
]

const TypeChooser = ({modelSource, openVinoVersion, submitDisabled, nextStep, setOpenVino, setModelSource}) => (
  <div className="type-chooser">
    <div className="cta">
      <h2>Choose OpenVINO version:</h2>
    </div>
    <div className="version-choices">
      {
        /*openVinoVersions.map(version => (
          <Button key={version.value} className={`${openVinoVersion === version.value ? "active" : ''} ${version.default ? 'default' : ''}`} variant="dark" size="lg" onClick={() => setOpenVino(version.value)}>
            {version.label}
            {
              version.default && <span className="default-label">
                <img src={borderImg} alt=""/>
                <p>DepthAI Default</p>
              </span>
            }
          </Button>
        ))*/
        openVinoVersions.map(version => (
          <Button key={version.value} className={`${openVinoVersion === version.value ? "active" : ''} ${version.default ? 'default' : ''}`} variant="dark" size="lg" onClick={() => setOpenVino(version.value)}>
            {version.label}
            {
              version.default && <span className="default-label">
                <p>DepthAI Default</p>
              </span>
            }
          </Button>
        ))
      }
    </div>
    <div className="info">
      <p>All non-RVC3 versions are made for RVC2. See our documentation about <a href="https://docs.luxonis.com/projects/hardware/en/latest/pages/rvc/rvc2.html" target="_blank">RVC2</a> and <a href="https://docs.luxonis.com/projects/hardware/en/latest/pages/rvc/rvc3.html#" target="_blank">RVC3</a> to choose the correct version.</p>
    </div>
    <div className="cta">
      <h2>Choose model source:</h2>
    </div>
    <div className="model-choices">
      { openVinoVersion === "2022.3_RVC3" &&
          modelSourcesRVC3.map(source => (
              <Button key={source.value} className={modelSource === source.value ? "active" : ''} variant="dark" size="lg" onClick={() => setModelSource(source.value)}>{source.label}</Button>
          ))
      }
      { openVinoVersion !== "2022.3_RVC3" &&
        modelSources.map(source => (
          <Button key={source.value} className={modelSource === source.value ? "active" : ''} variant="dark" size="lg" onClick={() => setModelSource(source.value)}>{source.label}</Button>
        ))
      }
    </div>
    <Button variant="outline-secondary" disabled={submitDisabled} onClick={() => nextStep()}>Continue</Button>
  </div>
);

TypeChooser.propTypes = {
  nextStep: PropTypes.func.isRequired,
  setOpenVino: PropTypes.func.isRequired,
  setModelSource: PropTypes.func.isRequired,
  submitDisabled: PropTypes.bool.isRequired,
  openVinoVersion: PropTypes.string,
  modelSource: PropTypes.string,
};

const mapStateToProps = state => ({
  openVinoVersion: openVinoVersionSelector(state),
  modelSource: modelSourceSelector(state),
  submitDisabled: submitDisabledSelector(state),
})

const mapDispatchToProps = {
  setOpenVino: makeAction(SET_OPENVINO_VERSION),
  setModelSource: makeAction(SET_MODEL_SOURCE),
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(TypeChooser);
