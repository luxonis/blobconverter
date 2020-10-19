import React from 'react';
import ReactDOM from 'react-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './index.css';
import App from './components/App';
import * as serviceWorker from './serviceWorker';
import {createBrowserHistory} from "history";
import createSagaMiddleware from 'redux-saga';
import {applyMiddleware, createStore} from "redux";
import rootReducer from './redux/reducers';
import rootSaga from './redux/sagas';
import {routerMiddleware} from 'connected-react-router';
import {composeWithDevTools} from "redux-devtools-extension";
import {Provider} from "react-redux";

const history = createBrowserHistory();
const sagaMiddleware = createSagaMiddleware();

export const store = createStore(
  rootReducer(history),
  composeWithDevTools(
    applyMiddleware(
      routerMiddleware(history),
      sagaMiddleware,
    )
  )
);

sagaMiddleware.run(rootSaga);

ReactDOM.render(
  <Provider store={store}>
    <App/>
  </Provider>,
  document.getElementById('root')
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
