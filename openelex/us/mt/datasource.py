"""
Montana has CSV files containing county-level results and all offices
for all years back to 2000, with the exception of state legislative races in 2000.
All of the files are pre-processed and available on Github at
https://github.com/openelections/openelections-data-mt.

Some elections have a single statewide precinct-level file, while others have county-specific
precinct-level files.
"""
from os.path import join
import json
import datetime
import urlparse

from openelex import PROJECT_ROOT
from openelex.base.datasource import BaseDatasource
from openelex.lib import build_raw_github_url

class Datasource(BaseDatasource):

    # PUBLIC INTERFACE
    def mappings(self, year=None):
        """Return array of dicts containing source url and
        standardized filename for raw results file, along
        with other pieces of metadata
        """
        mappings = []
        for yr, elecs in self.elections(year).items():
            mappings.extend(self._build_metadata(yr, elecs))
        return mappings

    def target_urls(self, year=None):
        "Get list of source data urls, optionally filtered by year"
        return [item['raw_url'] for item in self.mappings(year)]

    def filename_url_pairs(self, year=None):
        return [(mapping['generated_filename'], self._url_for_fetch(mapping))
                for mapping in self.mappings(year)]

    def _url_for_fetch(self, mapping):
        try:
            return mapping['pre_processed_url']
        except KeyError:
            return mapping['raw_url']

    def mappings_for_url(self, url):
        return [mapping for mapping in self.mappings() if mapping['raw_url'] == url]

    # PRIVATE METHODS

    def _build_metadata(self, year, elections):
        meta = []
        year_int = int(year)
        for election in elections:
            results = [x for x in self._url_paths() if x['date'] == election['start_date']]
            for result in results:
                if result['county']:
                    ocd_id = [o['ocd_id'] for o in self._jurisdictions() if result['county'] == o['county']][0]
                    name = result['county']
                else:
                    ocd_id = 'ocd-division/country:us/state:mt'
                    name = "Montana"
                generated_filename = self._generate_filename(election['start_date'], result)
                meta.append({
                    "generated_filename": generated_filename,
                    "raw_url": result['url'],
                    "pre_processed_url": build_raw_github_url(self.state, str(year), result['path']),
                    "ocd_id": ocd_id,
                    "name": name,
                    "election": election['slug']
                })
        return meta

    def _generate_filename(self, start_date, result):
        bits = [
            start_date.replace('-',''),
            self.state,
        ]
        bits.extend([
            result['race_type'].lower(),
        ])
        filename = "__".join(bits) + '.csv'
        return filename

    def _generate_county_filename(self, start_date, result):
        bits = [
            start_date.replace('-',''),
            self.state,
        ]
        if result['party']:
            bits.append(result['party'].lower())
        bits.extend([
            result['race_type'].lower(),
            result['county'].replace(' ','_').lower()
        ])
        bits.append('precinct')
        filename = "__".join(bits) + '.csv'
        return filename

    def _jurisdictions(self):
        """Montana counties"""
        m = self.jurisdiction_mappings()
        mappings = [x for x in m if x['county'] != ""]
        return mappings

    def _url_for_fetch(self, mapping):
        if mapping['pre_processed_url']:
            return mapping['pre_processed_url']
        else:
            return mapping['raw_url']
