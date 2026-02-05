from sqlmodel import select
from db.entity import Trashcan
from db.db import SessionDep

class DashboardService:
    def __init__(self):
        pass

    async def get_total_detection(self, db: SessionDep):
        pass

    async def get_full_trashcans(self, db: SessionDep):
        pass

    async def get_stats_charts(self, db: SessionDep):
        pass

    async def get_unconnected_trashcans_list(self, db: SessionDep):
        pass