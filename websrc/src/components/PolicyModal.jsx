import React from 'react';
import {connect} from 'react-redux';
import {Modal} from 'react-bootstrap';
import PropTypes from 'prop-types';
import {makeAction} from "../redux/actions/makeAction";
import {CHANGE_MODAL} from "../redux/actions/actionTypes";

const PolicyModal = ({modal, changeModal}) => (
  <Modal size="xl" id="policy-modal" show={modal && modal.open} onHide={() => changeModal({policy: {open: false}})}>
    <Modal.Header closeButton>
      <Modal.Title/>
    </Modal.Header>
    <Modal.Body>
      <h1>Privacy Policy for Luxonis</h1>

      <p>At BlobConverter, accessible from http://69.164.214.171:8083/, one of our main priorities is the privacy of our
        visitors. This Privacy Policy document contains types of information that is collected and recorded by
        BlobConverter and how we use it.</p>

      <p>If you have additional questions or require more information about our Privacy Policy, do not hesitate to
        contact us.</p>

      <p>This Privacy Policy applies only to our online activities and is valid for visitors to our website with regards
        to the information that they shared and/or collect in BlobConverter. This policy is not applicable to any
        information collected offline or via channels other than this website. </p>

      <h2>Consent</h2>

      <p>By using our website, you hereby consent to our Privacy Policy and agree to its terms. </p>

      <h2>Information we collect</h2>

      <p>The data you are asked to provide, and the reasons why you are asked to provide it, will
        be made clear to you at the point we ask you to provide your personal information.</p>
      <p>If you contact us directly, we may receive additional information about you such as your name, email address,
        phone number, the contents of the message and/or attachments you may send us, and any other information you may
        choose to provide.</p>

      <h2>How we use your information</h2>

      <p>We use the information we collect to provide services by your request</p>
    </Modal.Body>
    <Modal.Footer/>
  </Modal>
);

PolicyModal.propTypes = {
  changeModal: PropTypes.func.isRequired,
  modal: PropTypes.object,
};

const mapStateToProps = (state) => ({
  modal: state.page.modal.policy,
});

const mapDispatchToProps = {
  changeModal: makeAction(CHANGE_MODAL),
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(React.memo(PolicyModal));
