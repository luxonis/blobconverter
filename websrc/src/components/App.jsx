import React from 'react';
import './App.scss';
import {makeAction} from "../redux/actions/makeAction";
import {FETCH_ZOO_MODELS} from "../redux/actions/actionTypes";
import {connect} from "react-redux";
import PropTypes from 'prop-types';
import Content from "./Content";
import ErrorModal from "./ErrorModal";
import ApiDocs from "./ApiDocs";
import ApiDocsModal from "./ApiDocsModal";
import PolicyModal from "./PolicyModal";


class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      formAdvanced: false,
    }
  }

  render() {
    return (
      <div className="App">
        <div className="content">
          <Content/>
          <ErrorModal/>
          <ApiDocsModal/>
          <PolicyModal/>
          <ApiDocs/>
        </div>
      </div>
    );
  }
}

App.propTypes = {
  fetchZooModels: PropTypes.func.isRequired,
};

const mapStateToProps = () => ({});

const mapDispatchToProps = {
  fetchZooModels: makeAction(FETCH_ZOO_MODELS)
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(App);
