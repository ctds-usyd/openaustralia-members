import openaustraliamembers
import scraperwiki


df = openaustraliamembers.OpenAustraliaMembers().offices().reset_index()
scraperwiki.sqlite.save(data=df.to_dict(orient='records'))
