import React from 'react';
import PropTypes from 'prop-types';
import {Button} from "react-bootstrap";
import {connect} from "react-redux";
import {SET_MODEL_SOURCE, SET_OPENVINO_VERSION} from "../redux/actions/actionTypes";
import {makeAction} from "../redux/actions/makeAction";
import {modelSourceSelector, openVinoVersionSelector, submitDisabledSelector} from "../redux/selectors/dashboard";
import borderImg from './border.png'

const openVinoVersions = [
  {label: "2019.R3", value: "2019_R3"},
  {label: "2020.1", value: "2020_1", "default": true},
  {label: "2020.2", value: "2020_2"},
  {label: "2020.3", value: "2020_3"},
  {label: "2020.4", value: "2020_4"},
]

const modelSources = [
  {label: "Caffe Model", value: "caffe"},
  {label: "TensorFlow Model", value: "tf"},
  {label: "OpenVino Model", value: "openvino"},
  {label: "OpenVino Zoo Model", value: "zoo"},
]

const TypeChooser = ({modelSource, openVinoVersion, submitDisabled, nextStep, setOpenVino, setModelSource}) => (
  <div className="type-chooser">
    <div className="cta">
      <h2>Choose OpenVINO version:</h2>
    </div>
    <div className="version-choices">
      {
        openVinoVersions.map(version => (
          <Button key={version.value} className={`${openVinoVersion === version.value ? "active" : ''} ${version.default ? 'default' : ''}`} variant="dark" size="lg" onClick={() => setOpenVino(version.value)}>
            {version.label}
            {
              version.default && <span className="default-label">
                <img src={borderImg} alt=""/>
                <p>DepthAI Supported</p>
              </span>
            }
          </Button>
        ))
      }
    </div>
    <div className="cta">
      <h2>Choose model source:</h2>
    </div>
    <div className="model-choices">
      {
        modelSources.map(source => (
          <Button key={source.value} className={modelSource === source.value ? "active" : ''} variant="dark" size="lg" onClick={() => setModelSource(source.value)}>{source.label}</Button>
        ))
      }
    </div>
    <Button variant="outline-success" disabled={submitDisabled} onClick={() => nextStep()}>Continue</Button>
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
