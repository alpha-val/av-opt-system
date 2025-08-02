import { createSelector } from 'reselect';

const nodesSelector = (state) => state.nodes;

export const memoizedNodesSelector = createSelector(
    [nodesSelector],
    (nodes) => nodes // Memoizes the nodes object
);