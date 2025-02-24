"""
This modules manages the command line interface
"""
import click


def print_version(ctx, value):
    from bioflow import __version__
    if not value or ctx.resilient_parsing:
        return
    click.echo(__version__)
    ctx.exit()


@click.command()
def about():
    """
    Information about the project

    :return:
    """
    from bioflow import __version__, __author__, __author_mail__, __current_year__

    click.echo('BioFlow \n'
               '\tversion: %s \n'
               '\tauthor: %s \n'
               '\tcontact: %s \n'
               '\tLicense: %s\n'
               '\tcite: %s\n'
               '\n 2013-%s Andrei Kucharavy all rights reserved' %
               (__version__, __author__, __author_mail__, 'BSD 3-clause',
                'https://github.com/chiffa/BioFlow', __current_year__))


@click.group()
@click.option('--version', '-v', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True)
def main():
    pass


@click.command()
@click.option('--smtplog', default=False, is_flag=True, help='Enables mail reporting. Make sure '
                                                             'SMTP configs are set properly first.')
def downloaddbs(smtplog):
    """
    Downloads the databases automatically
    \f

    :return:
    """
    click.confirm('Pulling online databases. '
                                'Please make sure you initialized the project and you are ready'
                                'to wait for a while for hte download to complete. '
                                'Some files are large (up to 3 Gb).'
                                'You can perform this step manually (cf documentation).',
                  abort=True)

    from bioflow.utils.source_dbs_download import pull_online_dbs, log

    if smtplog:
        from bioflow.utils.smtp_log_behavior import mail_handler
        log.addHandler(mail_handler)

    pull_online_dbs()


@click.command()
def purgeneo4j():
    """
    Wipes the neo4j organism-specific database
    \f

    :return:
    """
    click.confirm('Are you sure you want to purge this neo4j database instance?'
                                ' You will have to re-import all the data'
                                'for this to work properly', abort=True)

    print('neo4j will start purging the master database. It will take some time to finish.'
          ' Please do not close the shell')
    from bioflow.db_importers.import_main import destroy_db

    destroy_db()


@click.command()
@click.option('--smtplog', default=False, is_flag=True, help='Enables mail reporting. Make sure '
                                                             'SMTP configs are set properly first.')
@click.option('--refinish', default=False, is_flag=True, help='Retries the annotation computation loop')
def loadneo4j(smtplog, refinish):
    """
    Loads the information from external database into the main knowledge repository inside neo4j
    \f

    :return:
    """
    click.confirm('Are you sure you want to start loading the neo4j database?'
                    ' The process might take several hours or days', abort=True)

    print('neo4j will start loading data into the master database. It will take a couple '
          'of hours to finish. Please do not close the shell.')
    from bioflow.db_importers.import_main import build_db, log, compute_annotation_informativity

    if smtplog:
        from bioflow.utils.smtp_log_behavior import mail_handler
        log.addHandler(mail_handler)

    if not refinish:
        build_db()

    else:
        compute_annotation_informativity()


@click.command()
def diagneo4j():
    from bioflow.neo4j_db.cypher_drivers import GraphDBPipe

    neo4j_pipe = GraphDBPipe()
    neo4j_pipe.self_diag()



@click.command()
@click.option('--background', default='', help='path to file of IDs of all genes detectable by a '
                                               'method. supports weighted sets')
@click.option('--secondary', default='', help='path to the file of IDs of the secondary genes '
                                              'set. supports weighted sets')
@click.option('--smtplog', default=False, is_flag=True, help='Enables mail reporting. Make sure '
                                                             'SMTP configs are set properly first.')
@click.option('--orthologmap', default='', help='File to perform an ortholog mapping between '
                                                  'organisms, in case a direct equivalence is '
                                                  'assumed')
@click.option('--geneidlookup', default='', help='File to perform a mapping of genes from '
                                                 'internal ids to ids used by the translation '
                                                 'table')
@click.argument('source')
def mapsource(source, secondary, background, smtplog, orthologmap, geneidlookup):
    """
    Sets the source and background files that will be uses in the analysis.

    The argument source is a path to a file containing the IDs of all genes considered as a hit

    Preferred formats
    are HGCN gene names (TP53), Uniprot gene names (P53_HUMAN) or Uniprot Accession numbers (
    P04637).
    Other sources, such as ENSEMBL or PDB IDs are supported as well
    \f

    :param source:
    :param background:
    :param secondary:
    :param smtplog:
    :param orthologmap:
    :param geneidlookup:
    :return:
    """
    from bioflow.utils.top_level import map_and_save_gene_ids, log
    from bioflow.pre_processing.remap_IDs import translate_identifiers
    from bioflow.configs.main_configs import Dumps

    if smtplog:
        from bioflow.utils.smtp_log_behavior import mail_handler
        log.addHandler(mail_handler)

    if orthologmap != '':

        if geneidlookup == '':
            geneidlookup = None

        translate_identifiers(source, Dumps.translated_primary,
                              orthologmap, geneidlookup)
        source = Dumps.translated_primary

        if secondary != '':
            translate_identifiers(secondary, Dumps.translated_secondary,
                                  orthologmap, geneidlookup)
            secondary = Dumps.translated_secondary

        if background != '':
            translate_identifiers(background, Dumps.translated_background,
                                  orthologmap, geneidlookup)
            background = Dumps.translated_background

    if secondary != '':
        map_and_save_gene_ids((source, secondary), background)
    else:
        map_and_save_gene_ids(source, background)


@click.command()
@click.option('--smtplog', default=False, is_flag=True, help='Enables mail reporting. Make sure '
                                                             'SMTP configs are set properly first.')
def rebuildlaplacians(smtplog):
    """
    Extracts the Laplacian matrices from the master graph database.
    \f

    :return:
    """
    from bioflow.utils.top_level import rebuild_the_laplacians, log

    if smtplog:
        from bioflow.utils.smtp_log_behavior import mail_handler
        log.addHandler(mail_handler)

    rebuild_the_laplacians()


@click.command()
@click.option('--collection', type=click.Choice(['all', 'interactome', 'annotome']), default='all')
def purgemongo(collection):
    """
    purges the mongodb collection currently used to store all the information.
    \f

    :param collection:
    :return:
    """
    click.confirm('Are you sure you want to purge the database of existing samples?', abort=True)

    from bioflow.sample_storage.mongodb import drop_all_interactome_rand_samp
    from bioflow.sample_storage.mongodb import drop_all_annotome_rand_samp

    if collection == 'all':
        drop_all_annotome_rand_samp()
        drop_all_interactome_rand_samp()
    elif collection == 'interactome':
        drop_all_interactome_rand_samp()
    elif collection == 'annotome':
        drop_all_annotome_rand_samp()


@click.command()
@click.option('--matrix', type=click.Choice(['all', 'interactome', 'annotome']), default='all',
              help='analyse molecular entities alone (interactome), annotation entities alone ('
                   'annotome) or both')
@click.option('--depth', default=25, help='random samples used to infer flow pattern significance')
@click.option('--processors', default=1, help='processor cores used in flow patterns calculation')
@click.option('--skipsampling', default=False, is_flag=True, help='Skips random sampling step')
@click.option('--background', default=False, is_flag=True, help='Uses the background for sampling')
@click.option('--name', default='', help='name of the experiment')
@click.option('--nocluster', default=False, is_flag=True, help='performs the clustering '
                                                                'complement')
@click.option('--smtplog', default=False, is_flag=True, help='Enables mail reporting. Make sure '
                                                             'SMTP configs are set properly first.')
def analyze(name, matrix, depth, processors, skipsampling, background, nocluster, smtplog):
    """
    Performs the analysis of the information flow

    :param name:
    :param matrix:
    :param depth:
    :param processors:
    :param skipsampling:
    :param nocluster:
    :param background:
    :return:
    """
    from bioflow.utils.io_routines import get_background_bulbs_ids, get_source_bulbs_ids
    from bioflow.molecular_network.interactome_analysis import auto_analyze as interactome_analysis
    from bioflow.annotation_network.knowledge_access_analysis \
        import auto_analyze as knowledge_analysis

    if smtplog:
        from bioflow.utils.io_routines import log as logger_1
        from bioflow.molecular_network.interactome_analysis import log as logger_2
        from bioflow.annotation_network.knowledge_access_analysis import log as logger_3

        from bioflow.utils.smtp_log_behavior import mail_handler

        logger_1.addHandler(mail_handler)
        logger_2.addHandler(mail_handler)
        logger_3.addHandler(mail_handler)

    source, sec_source = get_source_bulbs_ids()

    if background:
        background = get_background_bulbs_ids()

    else:
        background = []

    if name:
        name = [name]
    else:
        name = []

    if matrix != 'annotome':
        # # perform the interactome analysis
        interactome_analysis(source_list=source,
                             secondary_source_list=sec_source,
                             output_destinations_list=name,
                             random_samples_to_test_against=depth,
                             processors=processors,
                             background_list=background,
                             skip_sampling=skipsampling,
                             cluster=not(nocluster),
                             )

    if matrix != 'interactome':
        # # perform the knowledge analysis
        knowledge_analysis(source_list=source,
                           secondary_source_list=sec_source,
                           output_destinations_list=name,
                           random_samples_to_test_against=depth,
                           processors=processors,
                           background_list=background,
                           skip_sampling=skipsampling,
                           cluster=not(nocluster),
                           )


main.add_command(downloaddbs)
main.add_command(purgeneo4j)
main.add_command(loadneo4j)
main.add_command(diagneo4j)
main.add_command(rebuildlaplacians)
main.add_command(purgemongo)
main.add_command(mapsource)
main.add_command(analyze)
main.add_command(about)


if __name__ == '__main__':
    main()
