import memberdata
import scraperwiki


df = memberdata.OpenAustraliaMembers().offices().reset_index()
scraperwiki.sqlite.save(data=df.to_dict(orient='records'))
