import {createSelector} from 'reselect';

export const dashboardBranch = state => state.dashboard;

export const openVinoVersionSelector = createSelector(
  dashboardBranch,
  dashboard => dashboard.openVinoVersion
)

export const availableZooModelsSelector = createSelector(
  dashboardBranch,
  dashboard => dashboard.availableZooModels
)

export const conversionInProgressSelector = createSelector(
  dashboardBranch,
  dashboard => dashboard.conversionInProgress
)

export const conversionErrorSelector = createSelector(
  dashboardBranch,
  dashboard => dashboard.conversionError || {}
)

export const modelSourceSelector = createSelector(
  dashboardBranch,
  dashboard => dashboard.modelSource
)

export const submitDisabledSelector = createSelector(
  openVinoVersionSelector,
  modelSourceSelector,
  (openVinoVersion, modelSource) => !openVinoVersion || !modelSource
)

