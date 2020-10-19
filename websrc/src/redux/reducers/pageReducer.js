import * as actionTypes from '../actions/actionTypes';

const DEFAULT_STATE = {};

const pageReducer = (state = DEFAULT_STATE, action) => {
  switch (action.type) {
    case '@@router/LOCATION_CHANGE': {
      return DEFAULT_STATE;
    }
    default: {
      return state;
    }
  }
};

export default pageReducer;
