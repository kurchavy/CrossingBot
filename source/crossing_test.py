import logging
from crossing_model import Crossing
from crossing_updater import CrossingUpdaterTestFactory

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)

crs = Crossing()
cu = CrossingUpdaterTestFactory().create_updater(crs)
cu.update_cycle()
print(crs.get_current_state())
