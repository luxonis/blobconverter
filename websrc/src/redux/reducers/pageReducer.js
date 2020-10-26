import * as actionTypes from '../actions/actionTypes';
import {CHANGE_MODAL} from "../actions/actionTypes";

const DEFAULT_STATE = {
  modal: {},
};

const pageReducer = (state = DEFAULT_STATE, action) => {
  switch (action.type) {
    case '@@router/LOCATION_CHANGE': {
      return DEFAULT_STATE;
    }
    case CHANGE_MODAL: {
      return {
        ...state,
        modal: {
          ...state.modal,
          ...action.payload,
        }
      }
    }
    default: {
      return state;
    }
  }
};

export default pageReducer;
