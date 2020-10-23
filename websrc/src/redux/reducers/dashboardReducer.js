import * as actionTypes from '../actions/actionTypes';

const DEFAULT_STATE = {
  modelSource: null,
  openVinoVersion: "2020.1",
  availableZooModels: []
};

const dashboardReducer = (state = DEFAULT_STATE, action) => {
  switch (action.type) {
    case '@@router/LOCATION_CHANGE': {
      return DEFAULT_STATE;
    }
    case actionTypes.FETCH_ZOO_MODELS_SUCCESS: {
      return {
        ...state,
        availableZooModels: action.payload.available,
      }
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
