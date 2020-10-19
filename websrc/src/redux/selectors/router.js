import {createSelector} from 'reselect';

export const routerBranch = state => state.router;

export const locationBranch = createSelector(
    routerBranch,
    router => router.location
);

export const currentLocation = createSelector(
    locationBranch,
    location => location.pathname
);