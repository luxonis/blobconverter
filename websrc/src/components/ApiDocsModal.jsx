import React from 'react';
import {connect} from 'react-redux';
import {Modal} from 'react-bootstrap';
import PropTypes from 'prop-types';
import {modalSelector} from "../redux/selectors/page";
import {CHANGE_MODAL} from "../redux/actions/actionTypes";
import {makeAction} from "../redux/actions/makeAction";
import {caffe, openvino, tf, zoo} from "./source_codes";

const ApiDocsModal = ({modal, changeModal}) => (
  <Modal size="xl" id="docs-modal" show={modal && modal.open} onHide={() => changeModal({docs: {open: false}})}>
    <Modal.Header closeButton>
      <Modal.Title>
        API integration guide
      </Modal.Title>
    </Modal.Header>
    <Modal.Body>
      <div className="code-section">
        <h3>Convert OpenVINO model</h3>
        <pre><code>{openvino}</code></pre>
      </div>
      <div className="code-section">
        <h3>Convert Caffe model</h3>
        <pre><code>{caffe}</code></pre>
      </div>
      <div className="code-section">
        <h3>Convert TensorFlow model</h3>
        <pre><code>{tf}</code></pre>
      </div>
      <div className="code-section">
        <h3>Download model from model zoo</h3>
        <pre><code>{zoo}</code></pre>
      </div>
    </Modal.Body>
    <Modal.Footer/>
  </Modal>
);

ApiDocsModal.propTypes = {
  changeModal: PropTypes.func.isRequired,
  modal: PropTypes.object,
};

const mapStateToProps = (state) => ({
  modal: modalSelector(state).docs,
});

const mapDispatchToProps = {
  changeModal: makeAction(CHANGE_MODAL),
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(React.memo(ApiDocsModal));
