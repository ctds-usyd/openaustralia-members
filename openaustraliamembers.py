import warnings
import pandas as pd
from urllib.request import urlopen
import os
from lxml import etree


def _join_update(df, other):
    for column in other.columns:
        if column in df:
            df[column].update(other[column])
        else:
            df[column] = other[column]


class OpenAustraliaMembers:
    """Get DataFrames with data about Australian parliamentarians

    Key methods are `people` and `offices`.
    """

    def __init__(self, path='http://data.openaustralia.org/members',
                 cached=False):
        self._path = path
        self._cached = cached
        self._cache = {}

    def _open(self, filename):
        if ':/' in self._path:
            return urlopen(self._path + '/' + filename)
        return open(os.path.join(self._path, filename), 'rb')

    def _parse(self, filename):
        if filename in self._cache:
            return self._cache[filename]

        with self._open(filename) as f:
            out = etree.XML(f.read())

        if self._cached:
            self._cache[filename] = out
        return out

    def people(self, enhanced=True):
        """Get basic person details

        One record per person
        """
        root = self._parse('people.xml')
        df = pd.DataFrame([dict(person.attrib)
                           for person in root.findall('.//person')])
        df = df.rename(columns={'id': 'person_id'})
        df = df.set_index('person_id')
        if enhanced:
            for filename in ['wikipedia-lords',
                             'wikipedia-commons',
                             'links-register-of-interests',
                             'links-abc-qanda',
                             'websites']:
                other = self._parse_personinfo(filename + '.xml')
                _join_update(df, other)
            df['aph_id'] = df.aph_url.map(lambda s: s.rpartition('=')[-1],
                                          na_action='ignore')
        return df

    def _parse_personinfo(self, filename):
        root = self._parse(filename)
        df = pd.DataFrame([dict(personinfo.attrib)
                           for personinfo in root.findall('.//personinfo')])
        gb = df.groupby('id')
        if pd.np.any(gb.count() > 1):
            warnings.warn('Found more than one personinfo per person in ' +
                          filename)
        return gb.last()  # in case there are duplicates

    def offices(self, enhanced=True):
        """Get details on parliamentary positions

        A record for each time someone held a position in the house of
        represenatives, senate, cabinet, etc.  Data from `people`, as well as
        fields specific to these roles, is merged in redundantly when enhanced.

        The latestname field is the most reliable for name.

        The source column is one of {'representatives', 'senators',
        'ministers'}.
        """
        root = self._parse('people.xml')
        offices = []
        for person in root.findall('.//person'):
            person_id = person.attrib['id']
            for office in person.findall('./office'):
                offices.append(dict(office.attrib))
                offices[-1]['person_id'] = person_id
        df = pd.DataFrame(offices).rename(columns={'id': 'office_id'})
        df = df.set_index('office_id')
        if enhanced:
            for attr in ['senators', 'representatives', 'ministers']:
                other = getattr(self, attr)()
                _join_update(df, other)
            df = df.merge(self.people(), left_on='person_id', right_index=True)
        return df

    def senators(self):
        return self._parse_office_details('senators')

    def representatives(self):
        return self._parse_office_details('representatives')

    def ministers(self):
        return self._parse_office_details('ministers', tagname='moffice')

    def _parse_office_details(self, filename, tagname='member'):
        root = self._parse(filename + '.xml')
        df = pd.DataFrame([dict(person.attrib)
                           for person in root.findall('.//' + tagname)])
        df['source'] = filename
        df['fromdate'] = self._clean_date(df['fromdate'])
        df['todate'] = self._clean_date(df['todate'])
        return df.rename(columns={'id': 'office_id'}).set_index('office_id')

    def _clean_date(self, series):
        series = series.copy()
        series[series == '1000-01-01'] = None
        series[series == '9999-12-31'] = None
        return pd.to_datetime(series)


if __name__ == '__main__':
    obj = OpenAustraliaMembers(cached=True)
    for attr in dir(obj):
        if attr[:1].isalpha():
            method = getattr(obj, attr)
            if callable(method):
                print('===', attr, '===')
                print(method().head())
                print()
