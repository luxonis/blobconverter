import {combineReducers} from "redux";
import { connectRouter } from 'connected-react-router';
import dashboard from './dashboardReducer';
import page from './pageReducer';

export default history => combineReducers({
    dashboard,
    page,
    router: connectRouter(history),
});
