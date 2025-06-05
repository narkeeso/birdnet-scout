from dataclasses import dataclass

import dataset

db = dataset.connect("sqlite:///scout.db")
