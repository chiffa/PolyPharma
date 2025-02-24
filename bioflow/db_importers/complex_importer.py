"""
Imports the complexes and insert them into the neo4j database
"""
from bioflow.bio_db_parsers.ComplexPortalParser import parse_complex_portal
from bioflow.utils.log_behavior import get_logger
from bioflow.configs.main_configs import complexes_path, organism
from bioflow.neo4j_db.db_io_routines import convert_to_internal_ids
from bioflow.neo4j_db.GraphDeclarator import DatabaseGraph
from time import time
import numpy as np
import datetime


log = get_logger(__name__)


def insert_into_the_database(up_ids_2_inner_ids: dict,
                             up_ids_2_properties: dict,
                             origin: str):
    """
    Performs the insertion in the database sub-routine

    :param up_ids_2_inner_ids:
    :param up_ids_2_properties:
    :param origin:
    :return:
    """

    breakpoints = 300
    total_pairs = len(list(up_ids_2_properties.keys()))
    previous_time = time()

    for counter, (node_id, new_node) in enumerate(up_ids_2_properties.items()):

        complex_node = DatabaseGraph.create('COMPLEX',
                                            {'legacyID': node_id,
                                             'displayName': new_node['displayName'],
                                             'source': origin,
                                             'main_connex': False,
                                             'parse_type': 'physical_entity'})

        if counter % breakpoints == 0 and counter > 1:
            # TODO: [progress bar]
            compops = float(breakpoints) / (time() - previous_time)
            secs_before_termination = int((total_pairs - counter) / compops)

            log.info('inserting Complex %s out of %s; %.2f complete; inserting speed: %.2f; expected finsihing: %s',
                      counter + 1,
                      total_pairs,
                      counter / float(total_pairs) * 100,
                      compops,
                      datetime.datetime.now() + datetime.timedelta(seconds=secs_before_termination))
            previous_time = time()

        for node2_up in new_node['components']:
            if node2_up in list(up_ids_2_inner_ids.keys()):
                DatabaseGraph.link(complex_node.id, up_ids_2_inner_ids[node2_up],
                                   'is_interacting',
                                   {'source': origin,
                                    'weight': 1.0,
                                    'parse_type': 'physical_entity_molecular_interaction'})


def insert_complexes():
    """
    Performs the full kinase-substrate parsing and insertion.

    :return:
    :raise Exception: in case a non-human load

    """

    if organism != 'Human':
        raise Exception('Complexes data unavailable for organisms other than human!')

    log.info('Starting Complex Portal parsing')

    up_ids_2_properties, up_ids = parse_complex_portal(complexes_path)

    log.info('Complex Portal parsed, starting translation of UP identifiers to internal database identifiers')
    up_ids_2_inner_ids = convert_to_internal_ids(up_ids)

    log.info('UP identifier conversion finished, starting database insertion for %s complexes' % len(list(up_ids_2_properties.keys())))
    insert_into_the_database(up_ids_2_inner_ids, up_ids_2_properties, 'ComplexPortal')

    log.info('Database insertion finished. Complex Portal import finished')