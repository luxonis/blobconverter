import * as actionTypes from '../actions/actionTypes';

const DEFAULT_STATE = {
  modelSource: null,
  openVinoVersion: "2020.1",
  availableZooModels: [],
  conversionInProgress: false,
  conversionError: null,
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
        availableZooModels: [],
        modelSource: action.payload,
      }
    }
    case actionTypes.SET_OPENVINO_VERSION: {
      return {
        ...state,
        availableZooModels: [],
        openVinoVersion: action.payload,
      }
    }
    case actionTypes.CONVERT_MODEL: {
      return {
        ...state,
        conversionError: null,
        conversionInProgress: true,
      }
    }
    case actionTypes.CONVERT_MODEL_FAILED: {
      return {
        ...state,
        conversionError: action.error,
        conversionInProgress: false,
      }
    }
    case actionTypes.CONVERT_MODEL_SUCCESS: {
      return {
        ...state,
        conversionInProgress: false
      }
    }
    default: {
      return state;
    }
  }
};

export default dashboardReducer;
