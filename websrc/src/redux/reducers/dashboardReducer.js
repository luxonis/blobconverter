import * as actionTypes from '../actions/actionTypes';

const DEFAULT_STATE = {
  modelSource: null,
  openVinoVersion: "2020_1",
};

const dashboardReducer = (state = DEFAULT_STATE, action) => {
  switch (action.type) {
    case '@@router/LOCATION_CHANGE': {
      return DEFAULT_STATE;
    }
    case actionTypes.SET_MODEL_SOURCE: {
      return {
        ...state,
        modelSource: action.payload,
      }
    }
    case actionTypes.SET_OPENVINO_VERSION: {
      return {
        ...state,
        openVinoVersion: action.payload,
      }
    }
    default: {
      return state;
    }
  }
};

export default dashboardReducer;
