import {createSelector} from 'reselect';

export const pageBranch = state => state.page;

export const modalSelector = createSelector(
  pageBranch,
  page => page.modal
);