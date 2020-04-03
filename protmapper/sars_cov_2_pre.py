import shutil
import logging
import argparse
from pathlib import Path
from contextlib import closing
from urllib.request import urlopen
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

pre_release_url = \
    'ftp://ftp.uniprot.org/pub/databases/uniprot/pre_release/coronavirus.xml'
SARS_NAME = 'SARS-CoV-2'
UP_NS = '{http://uniprot.org/uniprot}'


def _ftp_download(fname, url=pre_release_url):
    with closing(urlopen(url)) as req:
        with open(fname, 'wb') as fo:
            logger.info('Writing xml file to %s' % fname)
            shutil.copyfileobj(req, fo)


def process_entry(entry):
    """Process one of the entry tags in the xml file

    Parameters
    ----------
    entry : xml.etree.ElementTree.Element

    Returns
    -------
    list
        A list of name,UP-ID,organism tuples
    """
    # Initialize list
    name_mapping = []

    # Get the UP ID
    up_id = entry.find(UP_NS + 'accession').text
    logger.info('Processing uniprot id %s' % up_id)

    # NOTE: skip the <name> tag for now
    # Get the <name> tag
    # name_ = entry.find(UP_NS + 'name').text
    # name_mapping.append((name_, up_id, SARS_NAME))

    # Get all names:
    # protein -> recommendedName; alternativeName
    #            recommendedName -> fullName; shortName
    #            alternativeName -> fullName; shortName
    protein = entry.find(UP_NS + 'protein')
    for child_tag in protein:
        if child_tag.tag.lower() in {UP_NS + 'recommendedname',
                                     UP_NS + 'alternativename'}:
            for fullname_tag in child_tag.findall(UP_NS + 'fullName'):
                name_mapping.append((fullname_tag.text, up_id, SARS_NAME))
            for shortname_tag in child_tag.findall(UP_NS + 'shortName'):
                name_mapping.append((shortname_tag.text, up_id, SARS_NAME))

    return name_mapping


def process_xml(fname):
    # Read file into xml.etree.ElementTree
    et = ET.parse(fname)

    # Process xml
    name_mappings = []
    for entry in et.findall(UP_NS + 'entry'):
        name_mappings.extend(process_entry(entry))

    return name_mappings


def main(tsv_outfile, ftp_path=None):
    fname = SARS_NAME + '_prerelease.xml'

    # Download file
    if ftp_path:
        path = Path(ftp_path).joinpath(fname)
        if not path.parent.is_dir():
            logger.info('The path %s does not exist. Creating... ' %
                        path.parent.as_posix())
            path.parent.mkdir(parents=True)
    _ftp_download(fname)

    # Get name mappings
    sars_mappings = process_xml(fname)

    # Write to tsv
    tsv_outfile = tsv_outfile if tsv_outfile.endswith('.tsv') else \
        tsv_outfile.split('.')[0] + '.tsv'
    with open(tsv_outfile, 'w') as tsvf:
        for mapping in sars_mappings:
            tsvf.write('%s\n' % '\t'.join(mapping))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tsv-out', required=True,
                        help='The file path for the tsv file of the output')
    # parser.add_argument(
    #     '--download-path',
    #     help='The path to where to download the xml resource file'
    # )

    args = parser.parse_args()

    main(args.tsv_out)
