import React from 'react';
import './App.scss';
import {makeAction} from "../redux/actions/makeAction";
import {FETCH_ZOO_MODELS} from "../redux/actions/actionTypes";
import {connect} from "react-redux";
import PropTypes from 'prop-types';
import Particles from "react-particles-js";
import Content from "./Content";
import ErrorModal from "./ErrorModal";
import ApiDocs from "./ApiDocs";
import ApiDocsModal from "./ApiDocsModal";


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
        <Particles
          canvasClassName="particles-canvas"
          params={{
            particles: {
              number: {
                value: 50,
                density: {
                  enable: true,
                  value_area: 1000,
                }
              },
            },
            interactivity: {
              detectsOn: "canvas",
              events: {
                onHover: {
                  enable: true,
                  mode: "repulse",
                },
              },
              modes: {
                repulse: {
                  distance: 200,
                  duration: 0.4,
                },
              },
            },
          }}
        />
        <div className="content">
          <Content/>
          <ErrorModal/>
          <ApiDocsModal/>
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
