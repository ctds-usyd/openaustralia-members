import openaustraliamembers
import scraperwiki


df = openaustraliamembers.OpenAustraliaMembers().offices().reset_index()
scraperwiki.sqlite.save(unique_keys=['office_id'],
                        data=df.to_dict(orient='records'))
