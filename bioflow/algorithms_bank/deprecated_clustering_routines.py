"""
Mostly deprecated clustering and data structural analysis routines.

"""

from typing import Tuple

import numpy as np
from matplotlib import pyplot as plt
from scipy import sparse as spmat

from bioflow.annotation_network.knowledge_access_analysis import ref_param_set, \
    get_go_interface_instance
from bioflow.configs.main_configs import NewOutputs
from bioflow.utils.dataviz import kde_compute, render_2d_matrix
from bioflow.utils.linalg_routines import cluster_nodes, normalize_laplacian, \
    average_off_diag_in_sub_matrix, average_interset_linkage


def local_indexed_select(tri_array, array_column, selection_span):
    """
    Convenient small function to local_indexed_select a from tri_array all the elements where the column
    number array_column is within the selection span

    :param tri_array: the matrix on which we will be performing the selection
    :param array_column: column on which the selection span will be applied
    :param selection_span: span for which we are going to keep the column.
    :return:
    """
    selector = np.logical_and(
        selection_span[0] < tri_array[
            array_column, :], tri_array[
            array_column, :] < selection_span[1])

    if not any(selector):
        return np.array([[0.0, 0.0, 0.0]])

    decvec = tri_array[:, selector]

    return decvec


# REFACTOR: Legacy code containing static analysis and clustering logic
def deprectated_show_correlations(
        background_curr_deg_conf,
        mean_correlations,
        eigenvalues,
        selector,
        true_sample_tri_corr_array,
        test_mean_correlation,
        eigenvalue,
        re_samples,
        go_interface_instance=None,
        sparse=False,
        param_set=ref_param_set,
        save_path: NewOutputs = None):

    # TODO: there is a lot of repetition depending on which values are the biggest,
    # test-setted or real setted. In all, we should be able to reduce it to two functions:
    # scatterplot and histogram with two sets that should go into the dataviz module
    """
    A general function that performs demonstration of an example of random samples of the
     same size as our sample
    and of our sample and conducts the statistical tests on whether any of nodes or
     functional groups in our sample are non-random

    :param background_curr_deg_conf: [[current, informativity, confusion_potential], ...] -
    characteristics of the random samples
    :param mean_correlations: [[cluster size, average internode connection], ...] -
    characteristics of clustering random samples with the same parameters
    :param eigenvalues: eigenvalues associated to the interconnection matrix of random samples
    :param selector: range on which we would like to visually zoom and plot a histogram
    :param true_sample_tri_corr_array: [[current, informativity, confusion_potential], ...] -
    characteristics of the true sample. If none, nothing happens
    :param test_mean_correlation: [[cluster size, average internode connection], ...] -
    characteristics of clustering the true sample
    :param eigenvalue: eigenvalues associated to the interconnection matrix of the true sample
    :param re_samples: how many random samples we analyzed for the default model
    :param go_interface_instance:
    :param sparse:
    :param param_set:
    :return:
    """
    if go_interface_instance is None:
        go_interface_instance = get_go_interface_instance(param_set)

    inf_sel = (go_interface_instance.calculate_informativity(selector[0]),
               go_interface_instance.calculate_informativity(selector[1]))

    fig = plt.figure()
    fig.set_size_inches(30, 20)

    # trivect: [0, :] - current; [1, :] - informativity; [2, :] - confusion potential

    plt.subplot(331)
    plt.title('current through nodes')
    bins = np.linspace(background_curr_deg_conf[0, :].min(),
                       background_curr_deg_conf[0, :].max(),
                       100)

    if true_sample_tri_corr_array is not None:
        bins = np.linspace(min(background_curr_deg_conf[0, :].min(),
                               true_sample_tri_corr_array[0, :].min()),
                           max(background_curr_deg_conf[0, :].max(),
                               true_sample_tri_corr_array[0, :].max()),
                           100)

    plt.hist(background_curr_deg_conf[0, :],
             bins=bins, histtype='step', log=True, color='b')

    if true_sample_tri_corr_array is not None:
        plt.hist(true_sample_tri_corr_array[0, :],
                 bins=bins, histtype='step', log=True, color='r')

    plt.subplot(332)
    plt.title('test current vs pure informativity')

    plt.scatter(background_curr_deg_conf[1, :],
                background_curr_deg_conf[0, :], color='b', alpha=0.1)

    if true_sample_tri_corr_array is not None:

        plt.scatter(
            true_sample_tri_corr_array[1, :],
            true_sample_tri_corr_array[0, :],
            color='r', alpha=0.5)

    plt.axvspan(inf_sel[0], inf_sel[1], facecolor='0.5', alpha=0.3)

    plt.subplot(333)
    plt.title('test current v.s. confusion potential')

    plt.scatter(background_curr_deg_conf[2, :], background_curr_deg_conf[0, :])

    if true_sample_tri_corr_array is not None:
        plt.scatter(
            true_sample_tri_corr_array[2, :],
            true_sample_tri_corr_array[0, :],
            color='r', alpha=0.5)

    plt.axvspan(selector[0], selector[1], facecolor='0.5', alpha=0.3)

    plt.subplot(334)
    plt.title('Gaussian KDE current_info')

    estimator_function = kde_compute(background_curr_deg_conf[(1, 0), :], 50, re_samples)
    current_info_rel = None

    if true_sample_tri_corr_array is not None:
        # Used to be the way to compute the p-values
        current_info_rel = estimator_function(true_sample_tri_corr_array[(1, 0), :])

    plt.subplot(335)
    plt.title('GO_term pure informativity distribution')

     # REFACTOR: this needs to be moved elsewhere - this is a structural analysis

    bins = np.linspace(
        background_curr_deg_conf[1, :].min(),
        background_curr_deg_conf[1, :].max(),
        100)

    if true_sample_tri_corr_array is not None:
        bins = np.linspace(min(background_curr_deg_conf[1, :].min(),
                               true_sample_tri_corr_array[1, :].min()),
                           max(background_curr_deg_conf[1, :].max(),
                               true_sample_tri_corr_array[1, :].max()),
                           100)

    plt.hist(background_curr_deg_conf[1, :],
             bins=bins, histtype='step', log=True, color='b')

    if true_sample_tri_corr_array is not None:
        plt.hist(true_sample_tri_corr_array[1, :],
                 bins=bins, histtype='step', log=True, color='r')

    plt.subplot(336)
    plt.title('Density of current in the highlighted area')

    bins = np.linspace(local_indexed_select(background_curr_deg_conf, 2, selector)[0, :].min(),
                       local_indexed_select(background_curr_deg_conf, 2, selector)[0, :].max(),
                       100)

    if true_sample_tri_corr_array is not None:
        bins = np.linspace(
            min(local_indexed_select(background_curr_deg_conf, 2, selector)[0, :].min(),
                local_indexed_select(true_sample_tri_corr_array, 2, selector)[0, :].min()),
            max(local_indexed_select(background_curr_deg_conf, 2, selector)[0, :].max(),
                local_indexed_select(true_sample_tri_corr_array, 2, selector)[0, :].max()),
            100)

    plt.hist(local_indexed_select(background_curr_deg_conf, 2, selector)[0, :],
             bins=bins, histtype='step', log=True, color='b')

    if true_sample_tri_corr_array is not None:
        plt.hist(local_indexed_select(true_sample_tri_corr_array, 2, selector)[0, :],
                 bins=bins, histtype='step', log=True, color='r')

    cluster_props = None

    plt.subplot(337)
    plt.title('Clustering correlation')

    # REFACTOR: that's the clustering logic to be extracted elsewhere

    if not sparse:
        # plt.scatter(mean_correlations[0, :], mean_correlations[1, :], color = 'b')
        estimator_function = kde_compute(mean_correlations[(0, 1), :], 50, re_samples)

        cluster_props = None
        if test_mean_correlation is not None:
            plt.scatter(test_mean_correlation[0, :],
                        test_mean_correlation[1, :],
                        color='k', alpha=0.8)

            cluster_props = estimator_function(test_mean_correlation[(0, 1), :])

    plt.subplot(338)
    plt.title('Eigvals_hist')

    # REFACTOR: this needs to be moved elsewhere - this is a structural analysis

    if not sparse:
        bins = np.linspace(eigenvalues.min(), eigenvalues.max(), 100)
        if true_sample_tri_corr_array is not None:
            bins = np.linspace(min(eigenvalues.min(), eigenvalue.min()),
                               max(eigenvalues.max(), eigenvalue.max()),
                               100)
        plt.hist(eigenvalues, bins=bins, histtype='step', color='b')
        if eigenvalue is not None:
            plt.hist(eigenvalue.tolist() * 3, bins=bins, histtype='step', color='r')

    plt.subplot(339)
    plt.title('confusion potential')

    bins = np.linspace(background_curr_deg_conf[2, :].min(),
                       background_curr_deg_conf[2, :].max(),
                       100)

    if true_sample_tri_corr_array is not None:
        bins = np.linspace(min(background_curr_deg_conf[2, :].min(),
                               true_sample_tri_corr_array[2, :].min()),
                           max(background_curr_deg_conf[2, :].max(),
                               true_sample_tri_corr_array[2, :].max()),
                           100)

    plt.hist(background_curr_deg_conf[2, :],
             bins=bins, histtype='step', log=True, color='b')

    if true_sample_tri_corr_array is not None:
        plt.hist(true_sample_tri_corr_array[2, :],
                 bins=bins, histtype='step', log=True, color='r')

    # # plt.show()
    plt.savefig(save_path.knowledge_network_scatterplot)

    # pull the groups corresponding to non-random associations.
    return current_info_rel, cluster_props


def deprecated_perform_clustering(inter_node_tension: spmat.csc_matrix,
                                  cluster_number: int,
                                  show: str = 'undefined clustering') -> Tuple[np.array, np.float64,
                                                                    np.array, np.array]:
    """
    Performs a clustering on the voltages of the nodes,

    :param inter_node_tension:
    :param cluster_number:
    :param show:
    """
    index_group = list(set([item
                            for key in inter_node_tension.keys()
                            for item in key]))
    local_index = dict((UP, i) for i, UP in enumerate(index_group))
    rev_idx = dict((i, UP) for i, UP in enumerate(index_group))
    relations_matrix = spmat.lil_matrix((len(index_group), len(index_group)))

    for (UP1, UP2), tension in inter_node_tension.items():
        # TODO: change the metric used to cluster the nodes.
        relations_matrix[local_index[UP1], local_index[UP2]] = -1.0 / tension
        relations_matrix[local_index[UP2], local_index[UP1]] = -1.0 / tension
        relations_matrix[local_index[UP2], local_index[UP2]] += 1.0 / tension
        relations_matrix[local_index[UP1], local_index[UP1]] += 1.0 / tension

    # underlying method is spectral clustering: do we really lie in a good zone for that?
    # NOPE - we need a dynamic clusters number
    # TODO: change clustering method to a different one
    groups = cluster_nodes(relations_matrix, cluster_number)

    relations_matrix = normalize_laplacian(relations_matrix)

    if relations_matrix.shape[0] < 5:
        eigenvals, _ = spmat.linalg.eigsh(relations_matrix, k=2)
    elif relations_matrix.shape[0] < 10:
        eigenvals, _ = spmat.linalg.eigsh(relations_matrix, k=4)
    else:
        eigenvals, _ = spmat.linalg.eigsh(relations_matrix)

    relations_matrix = - relations_matrix
    relations_matrix.setdiag(1)

    group_sets = []
    group_2_mean_off_diag = []
    for i in range(0, cluster_number):
        group_selector = groups == i
        group_indexes = group_selector.nonzero()[0].tolist()
        group_2_mean_off_diag.append(
            (tuple(rev_idx[idx] for idx in group_indexes),
                len(group_indexes),
                average_off_diag_in_sub_matrix(relations_matrix, group_indexes)))
        group_sets.append(group_indexes)

    remainder = average_interset_linkage(relations_matrix, group_sets)

    clustidx = np.array([item for itemset in group_sets for item in itemset])
    relations_matrix = relations_matrix[:, clustidx]
    relations_matrix = relations_matrix[clustidx, :]

    mean_corr_array = np.array([[items, mean_corr]
                                for _, items, mean_corr in group_2_mean_off_diag])

    if show:
        render_2d_matrix(relations_matrix.toarray(), name=show, destination='')

    return np.array(group_2_mean_off_diag), \
        remainder, \
        mean_corr_array, \
        eigenvals