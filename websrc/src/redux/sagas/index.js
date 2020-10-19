import {all} from 'redux-saga/effects';
import dashboardSaga from './dashboardSaga';


export default function* index() {
    yield all([
      dashboardSaga(),
    ]);
}