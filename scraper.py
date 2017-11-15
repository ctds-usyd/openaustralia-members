import openaustraliamembers
import scraperwiki


df = openaustraliamembers.OpenAustraliaMembers().offices().reset_index()
df = df.fillna(None)
df.todate = df.todate.astype(str)
df.fromdate = df.fromdate.astype(str)
scraperwiki.sqlite.save(unique_keys=['office_id'],
                        data=df.to_dict(orient='records'))
