
from usgs import api
import json
results = api.search('LANDSAT_TM', 'EE', start_date='2011-06-01', where={3653: 0}, max_results=1000)
print(json.dumps(results))
