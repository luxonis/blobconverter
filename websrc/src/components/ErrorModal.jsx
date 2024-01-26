import React from 'react';
import {connect} from 'react-redux';
import {Button, Modal} from 'react-bootstrap';
import PropTypes from 'prop-types';
import {CHANGE_MODAL} from "../redux/actions/actionTypes";
import {makeAction} from "../redux/actions/makeAction";
import {modalSelector} from "../redux/selectors/page";
import {conversionErrorSelector} from "../redux/selectors/dashboard";

const ErrorModal = ({modal, changeModal, error}) => {
  const close = () => changeModal({error_modal: {open: false}});
  return (
    <Modal id="error-modal" size="lg" show={modal && modal.open} onHide={close}>
      <Modal.Header closeButton>
        <Modal.Title>
          Conversion error
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <div>
          <span>Error message</span>
          <pre>{error.message}</pre>
        </div>
        <div>
          <span>Console output (stdout)</span>
          <pre>{error.stdout}</pre>
        </div>
        <div>
          <span>Error output (stderr)</span>
          <pre>{error.stderr}</pre>
        </div>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="danger" href="https://github.com/luxonis/blobconverter/issues">Report a bug</Button>
        <Button variant="light" onClick={close}>Try again</Button>
      </Modal.Footer>
    </Modal>
  );
}

ErrorModal.propTypes = {
  changeModal: PropTypes.func.isRequired,
  modal: PropTypes.object,
  error: PropTypes.object,
};

const mapStateToProps = (state) => ({
  modal: modalSelector(state).error_modal,
  error: conversionErrorSelector(state)
});

const mapDispatchToProps = {
  changeModal: makeAction(CHANGE_MODAL),
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(React.memo(ErrorModal));
