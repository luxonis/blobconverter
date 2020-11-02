import React from 'react';
import PropTypes from 'prop-types';
import {Button} from "react-bootstrap";
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import { faBook } from '@fortawesome/free-solid-svg-icons'
import {makeAction} from "../redux/actions/makeAction";
import {CHANGE_MODAL} from "../redux/actions/actionTypes";
import {connect} from "react-redux";

const ApiDocs = ({changeModal}) => (
  <Button variant="info" id="api-docs" onClick={() => changeModal({docs: {open: true}})}>
    <span><FontAwesomeIcon icon={faBook} /></span>
    <span>Use API</span>
  </Button>
);

ApiDocs.propTypes = {
  changeModal: PropTypes.func.isRequired,
};

const mapDispatchToProps = {
  changeModal: makeAction(CHANGE_MODAL),
}

export default connect(
  null,
  mapDispatchToProps
)(ApiDocs);
